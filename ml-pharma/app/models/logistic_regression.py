import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score
from typing import Dict, Any, Optional, Tuple
import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PharmaLogisticRegression:
    def __init__(self, random_state: int = 42):
        self.model = LogisticRegression(
            random_state=random_state,
            max_iter=1000,
            solver='liblinear'  # Good for small datasets
        )
        self.is_trained = False
        self.feature_names = None
        self.training_metrics = {}
        self.model_version = "1.0.0"
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series, X_test: Optional[pd.DataFrame] = None, y_test: Optional[pd.Series] = None) -> Dict[str, Any]:
        """Train the logistic regression model"""
        try:
            logger.info("Starting model training...")
            
            # Store feature names
            self.feature_names = X_train.columns.tolist()
            
            # Train the model
            self.model.fit(X_train, y_train)
            self.is_trained = True
            
            # Calculate training metrics
            train_predictions = self.model.predict(X_train)
            train_proba = self.model.predict_proba(X_train)[:, 1]
            
            metrics = {
                'train_accuracy': accuracy_score(y_train, train_predictions),
                'train_auc': roc_auc_score(y_train, train_proba),
                'training_date': datetime.now().isoformat(),
                'n_samples': len(X_train),
                'n_features': len(self.feature_names),
                'feature_names': self.feature_names
            }
            
            # If test data is provided, calculate test metrics
            if X_test is not None and y_test is not None:
                test_predictions = self.model.predict(X_test)
                test_proba = self.model.predict_proba(X_test)[:, 1]
                
                metrics.update({
                    'test_accuracy': accuracy_score(y_test, test_predictions),
                    'test_auc': roc_auc_score(y_test, test_proba),
                    'test_samples': len(X_test)
                })
                
                # Detailed classification report for test set
                test_report = classification_report(y_test, test_predictions, output_dict=True)
                metrics['test_classification_report'] = test_report
                
                logger.info(f"Test Accuracy: {metrics['test_accuracy']:.4f}")
                logger.info(f"Test AUC: {metrics['test_auc']:.4f}")
            
            self.training_metrics = metrics
            
            logger.info(f"Model training completed successfully!")
            logger.info(f"Training Accuracy: {metrics['train_accuracy']:.4f}")
            logger.info(f"Training AUC: {metrics['train_auc']:.4f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error during model training: {str(e)}")
            raise
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        try:
            if not self.is_trained:
                raise ValueError("Model must be trained before making predictions")
            
            predictions = self.model.predict(X)
            logger.info(f"Made predictions for {len(X)} samples")
            return predictions
            
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}")
            raise
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get prediction probabilities"""
        try:
            if not self.is_trained:
                raise ValueError("Model must be trained before making predictions")
            
            probabilities = self.model.predict_proba(X)
            logger.info(f"Generated probabilities for {len(X)} samples")
            return probabilities
            
        except Exception as e:
            logger.error(f"Error during probability prediction: {str(e)}")
            raise
    
    def predict_single(self, features: list) -> Dict[str, Any]:
        """Make prediction for a single sample with detailed output"""
        try:
            if not self.is_trained:
                raise ValueError("Model must be trained before making predictions")
            
            # Convert to numpy array and reshape
            features_array = np.array(features).reshape(1, -1)
            
            # Get prediction and probability
            prediction = self.model.predict(features_array)[0]
            probabilities = self.model.predict_proba(features_array)[0]
            
            # Calculate confidence based on probability
            max_prob = max(probabilities)
            confidence = "high" if max_prob > 0.8 else "medium" if max_prob > 0.6 else "low"
            
            result = {
                'prediction': int(prediction),
                'probability_class_0': float(probabilities[0]),
                'probability_class_1': float(probabilities[1]),
                'max_probability': float(max_prob),
                'confidence': confidence,
                'interpretation': self._interpret_prediction(prediction, max_prob)
            }
            
            logger.info(f"Single prediction completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during single prediction: {str(e)}")
            raise
    
    def _interpret_prediction(self, prediction: int, probability: float) -> str:
        """Provide human-readable interpretation of the prediction"""
        if prediction == 1:
            if probability > 0.8:
                return "Treatment is highly likely to be effective"
            elif probability > 0.6:
                return "Treatment is likely to be effective"
            else:
                return "Treatment may be effective (low confidence)"
        else:
            if probability > 0.8:
                return "Treatment is highly unlikely to be effective"
            elif probability > 0.6:
                return "Treatment is unlikely to be effective"
            else:
                return "Treatment effectiveness is uncertain"
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance based on model coefficients"""
        try:
            if not self.is_trained:
                raise ValueError("Model must be trained before getting feature importance")
            
            if self.feature_names is None:
                raise ValueError("Feature names not available")
            
            # Get absolute coefficients as importance
            coefficients = np.abs(self.model.coef_[0])
            
            # Create feature importance dictionary
            feature_importance = dict(zip(self.feature_names, coefficients))
            
            # Sort by importance
            feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            
            logger.info("Feature importance calculated successfully")
            return feature_importance
            
        except Exception as e:
            logger.error(f"Error calculating feature importance: {str(e)}")
            raise
    
    def save_model(self, filepath: str) -> None:
        """Save trained model"""
        try:
            if not self.is_trained:
                raise ValueError("Cannot save untrained model")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Prepare model data
            model_data = {
                'model': self.model,
                'feature_names': self.feature_names,
                'training_metrics': self.training_metrics,
                'model_version': self.model_version,
                'is_trained': self.is_trained
            }
            
            # Save the model
            joblib.dump(model_data, filepath)
            logger.info(f"Model saved successfully to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def load_model(self, filepath: str) -> None:
        """Load trained model"""
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Model file not found: {filepath}")
            
            # Load the model data
            model_data = joblib.load(filepath)
            
            # Restore model state
            self.model = model_data['model']
            self.feature_names = model_data['feature_names']
            self.training_metrics = model_data.get('training_metrics', {})
            self.model_version = model_data.get('model_version', '1.0.0')
            self.is_trained = model_data.get('is_trained', True)
            
            logger.info(f"Model loaded successfully from {filepath}")
            logger.info(f"Model version: {self.model_version}")
            logger.info(f"Features: {len(self.feature_names) if self.feature_names else 0}")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information"""
        info = {
            'is_trained': self.is_trained,
            'model_version': self.model_version,
            'model_type': 'Logistic Regression',
            'feature_count': len(self.feature_names) if self.feature_names else 0,
            'feature_names': self.feature_names,
            'training_metrics': self.training_metrics
        }
        
        if self.is_trained:
            info['model_parameters'] = {
                'C': self.model.C,
                'solver': self.model.solver,
                'max_iter': self.model.max_iter,
                'random_state': self.model.random_state
            }
        
        return info
