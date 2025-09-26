from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
import time
import logging
import os
from contextlib import asynccontextmanager

# Import application modules
try:
    # For uvicorn/production
    from .models.logistic_regression import PharmaLogisticRegression
    from .models.data_processor import DataProcessor
    from .database.cosmos_client import cosmos_client
    from .monitoring.metrics import metrics_collector
except ImportError:
    # For direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.models.logistic_regression import PharmaLogisticRegression
    from app.models.data_processor import DataProcessor
    from app.database.cosmos_client import cosmos_client
    from app.monitoring.metrics import metrics_collector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model and processor instances
ml_model = None
data_processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("Starting up ML Pharma API...")
    
    global ml_model, data_processor
    
    try:
        # Initialize data processor
        data_processor = DataProcessor()
        logger.info("Data processor initialized")
        
        # Initialize and train ML model
        ml_model = PharmaLogisticRegression()
        
        # Check if pre-trained model exists
        model_path = "models/pharma_model.joblib"
        if os.path.exists(model_path):
            logger.info("Loading pre-trained model...")
            ml_model.load_model(model_path)
        else:
            logger.info("Training new model...")
            # Create synthetic data for training
            df = data_processor.create_synthetic_pharma_data(n_samples=2000)
            X, y = data_processor.prepare_features(df)
            X_train, X_test, y_train, y_test = data_processor.split_data(X, y)
            
            # Train the model
            training_metrics = ml_model.train(X_train, y_train, X_test, y_test)
            logger.info(f"Model training completed: {training_metrics}")
            
            # Save the trained model
            os.makedirs("models", exist_ok=True)
            ml_model.save_model(model_path)
        
        # Initialize Cosmos DB connection
        await cosmos_client.initialize()
        
        logger.info("ML Pharma API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down ML Pharma API...")
    await cosmos_client.close()
    logger.info("ML Pharma API shutdown completed")

# Create FastAPI app with lifespan manager
app = FastAPI(
    title="Pharma ML API",
    description="Machine Learning API for Pharmaceutical Treatment Effectiveness Prediction",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class PredictionRequest(BaseModel):
    features: List[float] = Field(..., description="List of feature values for prediction")
    
    class Config:
        schema_extra = {
            "example": {
                "features": [10.5, 45, 70.0, 500.0, 30, 5.2, 0.85, 0.90]
            }
        }

class PredictionResponse(BaseModel):
    prediction: int = Field(..., description="Predicted treatment effectiveness (0 or 1)")
    probability: float = Field(..., description="Prediction probability")
    confidence: str = Field(..., description="Confidence level (low, medium, high)")
    interpretation: str = Field(..., description="Human-readable interpretation")
    feature_names: List[str] = Field(..., description="Names of input features")
    model_version: str = Field(..., description="Version of the ML model used")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    model_loaded: bool
    cosmos_db_status: bool
    version: str

class MetricsResponse(BaseModel):
    system: Dict[str, Any]
    application: Optional[Dict[str, Any]] = None
    status: str

# Middleware for request metrics collection
@app.middleware("http")
async def collect_request_metrics(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Record metrics
    metrics_collector.record_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        duration=duration
    )
    
    return response

# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Pharma ML API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check Cosmos DB status
        cosmos_status = await cosmos_client.health_check()
        
        return HealthResponse(
            status="healthy",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            model_loaded=ml_model is not None and ml_model.is_trained,
            cosmos_db_status=cosmos_status,
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make a prediction for treatment effectiveness"""
    try:
        if ml_model is None or not ml_model.is_trained:
            raise HTTPException(status_code=503, detail="Model not loaded or trained")
        
        if data_processor is None:
            raise HTTPException(status_code=503, detail="Data processor not initialized")
        
        start_time = time.time()
        
        # Transform features
        transformed_features = data_processor.transform_single_prediction(request.features)
        
        # Make prediction
        prediction_result = ml_model.predict_single(transformed_features[0])
        
        # Record inference time
        inference_time = time.time() - start_time
        metrics_collector.record_prediction(prediction_result['prediction'], inference_time)
        
        # Store prediction in Cosmos DB
        await cosmos_client.store_prediction({
            "features": request.features,
            "prediction": prediction_result['prediction'],
            "probability": prediction_result['max_probability'],
            "confidence": prediction_result['confidence']
        })
        
        # Prepare response
        response = PredictionResponse(
            prediction=prediction_result['prediction'],
            probability=prediction_result['max_probability'],
            confidence=prediction_result['confidence'],
            interpretation=prediction_result['interpretation'],
            feature_names=data_processor.get_feature_names(),
            model_version=ml_model.model_version
        )
        
        logger.info(f"Prediction completed in {inference_time:.3f}s: {prediction_result['prediction']}")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in prediction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Prediction failed")

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system and application metrics"""
    try:
        comprehensive_metrics = metrics_collector.get_comprehensive_metrics()
        
        return MetricsResponse(
            system=comprehensive_metrics.get("system", {}),
            application=comprehensive_metrics.get("application"),
            status=comprehensive_metrics.get("status", "unknown")
        )
        
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

@app.get("/model/info")
async def get_model_info():
    """Get information about the loaded ML model"""
    try:
        if ml_model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        model_info = ml_model.get_model_info()
        return model_info
        
    except Exception as e:
        logger.error(f"Error retrieving model info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model info")

@app.get("/model/features")
async def get_feature_info():
    """Get information about model features"""
    try:
        if data_processor is None:
            raise HTTPException(status_code=503, detail="Data processor not initialized")
        
        feature_names = data_processor.get_feature_names()
        
        if feature_names is None:
            raise HTTPException(status_code=503, detail="Feature information not available")
        
        feature_info = {
            "feature_names": feature_names,
            "feature_count": len(feature_names),
            "feature_descriptions": {
                "drug_concentration": "Concentration of the drug in mg/mL",
                "patient_age": "Patient age in years",
                "patient_weight": "Patient weight in kg",
                "dosage_mg": "Drug dosage in milligrams",
                "treatment_duration_days": "Treatment duration in days",
                "biomarker_level": "Relevant biomarker level",
                "liver_function_score": "Liver function score (0-1)",
                "kidney_function_score": "Kidney function score (0-1)"
            }
        }
        
        return feature_info
        
    except Exception as e:
        logger.error(f"Error retrieving feature info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feature info")

@app.get("/predictions/stats")
async def get_prediction_stats():
    """Get prediction statistics from database"""
    try:
        stats = await cosmos_client.get_prediction_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving prediction stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve prediction statistics")

@app.get("/predictions/recent")
async def get_recent_predictions(limit: int = 10):
    """Get recent predictions from database"""
    try:
        if limit > 100:
            limit = 100  # Limit to prevent excessive data transfer
        
        predictions = await cosmos_client.get_predictions(limit=limit)
        return {"predictions": predictions, "count": len(predictions)}
        
    except Exception as e:
        logger.error(f"Error retrieving recent predictions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent predictions")

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found", "path": str(request.url.path)}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}
    )

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
