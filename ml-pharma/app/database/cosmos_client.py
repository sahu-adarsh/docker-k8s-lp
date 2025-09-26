import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.cosmos import exceptions
import uuid

from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CosmosClient:
    def __init__(self):
        # Get Cosmos DB configuration from environment variables
        self.endpoint = os.getenv('COSMOS_ENDPOINT', '')
        self.key = os.getenv('COSMOS_KEY', '')
        self.database_name = 'pharma-cosmos'
        self.container_name = 'predictions'
        
        # Initialize client
        self.client = None
        self.database = None
        self.container = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize Cosmos DB client and create database/container if needed"""
        try:
            if self.is_initialized:
                return
            
            # Create async client
            self.client = AsyncCosmosClient(self.endpoint, self.key)
            
            # Create database if it doesn't exist
            try:
                self.database = await self.client.create_database_if_not_exists(id=self.database_name)
                logger.info(f"Database '{self.database_name}' ready")
            except exceptions.CosmosResourceExistsError:
                self.database = self.client.get_database_client(self.database_name)
                logger.info(f"Using existing database '{self.database_name}'")
            
            # Create container if it doesn't exist
            try:
                self.container = await self.database.create_container_if_not_exists(
                    id=self.container_name,
                    partition_key="/prediction_id",
                    offer_throughput=400  # Minimum throughput for cost optimization
                )
                logger.info(f"Container '{self.container_name}' ready")
            except exceptions.CosmosResourceExistsError:
                self.container = self.database.get_container_client(self.container_name)
                logger.info(f"Using existing container '{self.container_name}'")
            
            self.is_initialized = True
            logger.info("Cosmos DB client initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Cosmos DB client: {str(e)}")
            # For development, we'll continue without Cosmos DB
            logger.warning("Continuing without Cosmos DB connection (development mode)")
    
    async def store_prediction(self, prediction_data: Dict[str, Any]) -> Optional[str]:
        """Store a prediction result in Cosmos DB"""
        try:
            await self.initialize()
            
            if not self.is_initialized:
                logger.warning("Cosmos DB not initialized, skipping storage")
                return None
            
            # Prepare document
            document = {
                "id": str(uuid.uuid4()),
                "prediction_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "features": prediction_data.get("features", []),
                "prediction": prediction_data.get("prediction"),
                "probability": prediction_data.get("probability"),
                "confidence": prediction_data.get("confidence", "unknown"),
                "model_version": "1.0.0",
                "request_source": "api"
            }
            
            # Store in Cosmos DB
            response = await self.container.create_item(body=document)
            logger.info(f"Prediction stored with ID: {document['id']}")
            return document['id']
            
        except Exception as e:
            logger.error(f"Error storing prediction: {str(e)}")
            return None
    
    async def get_predictions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent predictions from Cosmos DB"""
        try:
            await self.initialize()
            
            if not self.is_initialized:
                logger.warning("Cosmos DB not initialized, returning empty list")
                return []
            
            # Query for recent predictions
            query = f"SELECT * FROM c ORDER BY c.timestamp DESC OFFSET 0 LIMIT {limit}"
            
            items = []
            async for item in self.container.query_items(query=query, enable_cross_partition_query=True):
                items.append(item)
            
            logger.info(f"Retrieved {len(items)} predictions from Cosmos DB")
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving predictions: {str(e)}")
            return []
    
    async def get_prediction_stats(self) -> Dict[str, Any]:
        """Get prediction statistics from Cosmos DB"""
        try:
            await self.initialize()
            
            if not self.is_initialized:
                logger.warning("Cosmos DB not initialized, returning empty stats")
                return {}
            
            # Count total predictions
            count_query = "SELECT VALUE COUNT(1) FROM c"
            count_items = []
            async for item in self.container.query_items(query=count_query, enable_cross_partition_query=True):
                count_items.append(item)
            
            total_predictions = count_items[0] if count_items else 0
            
            # Get effective vs non-effective predictions
            effective_query = "SELECT VALUE COUNT(1) FROM c WHERE c.prediction = 1"
            effective_items = []
            async for item in self.container.query_items(query=effective_query, enable_cross_partition_query=True):
                effective_items.append(item)
            
            effective_count = effective_items[0] if effective_items else 0
            
            # Calculate statistics
            stats = {
                "total_predictions": total_predictions,
                "effective_predictions": effective_count,
                "non_effective_predictions": total_predictions - effective_count,
                "effectiveness_rate": (effective_count / total_predictions * 100) if total_predictions > 0 else 0,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Retrieved prediction statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error retrieving prediction statistics: {str(e)}")
            return {}
    
    async def health_check(self) -> bool:
        """Check if Cosmos DB connection is healthy"""
        try:
            await self.initialize()
            
            if not self.is_initialized:
                return False
            
            # Try to query the database
            query = "SELECT VALUE COUNT(1) FROM c"
            count = 0
            async for item in self.container.query_items(query=query, enable_cross_partition_query=True):
                count = item
                break
            
            logger.info("Cosmos DB health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Cosmos DB health check failed: {str(e)}")
            return False
    
    async def close(self):
        """Close Cosmos DB client connection"""
        if self.client:
            await self.client.close()
            logger.info("Cosmos DB client connection closed")

# Global instance for use across the application
cosmos_client = CosmosClient()
