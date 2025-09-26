import psutil
import time
import threading
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self, enable_prometheus_server: bool = True):
        # Create a custom registry to avoid conflicts
        self.registry = CollectorRegistry()
        
        # Define Prometheus metrics
        self.cpu_usage = Gauge(
            'container_cpu_usage_percent', 
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'container_memory_usage_bytes', 
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.disk_usage = Gauge(
            'container_disk_usage_percent', 
            'Disk usage percentage',
            registry=self.registry
        )
        
        self.request_count = Counter(
            'http_requests_total', 
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'http_request_duration_seconds', 
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.prediction_count = Counter(
            'ml_predictions_total',
            'Total ML predictions made',
            ['prediction_result'],
            registry=self.registry
        )
        
        self.model_inference_time = Histogram(
            'ml_model_inference_seconds',
            'Time taken for model inference',
            registry=self.registry
        )
        
        # Internal metrics storage
        self.metrics_cache = {}
        self.cache_ttl = 5  # Cache metrics for 5 seconds
        self.last_update = 0
        
        # Start Prometheus HTTP server
        if enable_prometheus_server:
            try:
                start_http_server(9090, registry=self.registry)
                logger.info("Prometheus metrics server started on port 9090")
            except Exception as e:
                logger.warning(f"Could not start Prometheus server: {str(e)}")
        
        # Start background metrics collection
        self._start_background_collection()
    
    def _start_background_collection(self):
        """Start background thread for continuous metrics collection"""
        def collect_metrics():
            while True:
                try:
                    self._update_system_metrics()
                    time.sleep(10)  # Update every 10 seconds
                except Exception as e:
                    logger.error(f"Error in background metrics collection: {str(e)}")
                    time.sleep(30)  # Wait longer on error
        
        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()
        logger.info("Background metrics collection started")
    
    def _update_system_metrics(self):
        """Update system metrics and Prometheus gauges"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Update Prometheus metrics
            self.cpu_usage.set(cpu_percent)
            self.memory_usage.set(memory.used)
            self.disk_usage.set(disk.percent)
            
            # Update cache
            self.metrics_cache = {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_bytes": memory.used,
                "memory_usage_percent": memory.percent,
                "memory_total_bytes": memory.total,
                "memory_available_bytes": memory.available,
                "disk_usage_percent": disk.percent,
                "disk_total_bytes": disk.total,
                "disk_used_bytes": disk.used,
                "disk_free_bytes": disk.free,
                "timestamp": time.time()
            }
            self.last_update = time.time()
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {str(e)}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # Check if cache is still valid
            if time.time() - self.last_update > self.cache_ttl:
                self._update_system_metrics()
            
            return self.metrics_cache.copy()
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            return {
                "error": "Unable to retrieve system metrics",
                "timestamp": time.time()
            }
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        try:
            self.request_count.labels(
                method=method, 
                endpoint=endpoint, 
                status_code=str(status_code)
            ).inc()
            
            self.request_duration.labels(
                method=method, 
                endpoint=endpoint
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"Error recording request metrics: {str(e)}")
    
    def record_prediction(self, prediction_result: int, inference_time: float):
        """Record ML prediction metrics"""
        try:
            # Record prediction count
            result_label = "effective" if prediction_result == 1 else "not_effective"
            self.prediction_count.labels(prediction_result=result_label).inc()
            
            # Record inference time
            self.model_inference_time.observe(inference_time)
            
        except Exception as e:
            logger.error(f"Error recording prediction metrics: {str(e)}")
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        try:
            # Get Prometheus metric values
            app_metrics = {
                "total_requests": sum([
                    sample.value for sample in self.request_count.collect()[0].samples
                ]),
                "total_predictions": sum([
                    sample.value for sample in self.prediction_count.collect()[0].samples
                ]),
                "average_request_duration": self._get_histogram_average(self.request_duration),
                "average_inference_time": self._get_histogram_average(self.model_inference_time),
                "timestamp": time.time()
            }
            
            return app_metrics
            
        except Exception as e:
            logger.error(f"Error getting application metrics: {str(e)}")
            return {"error": "Unable to retrieve application metrics"}
    
    def _get_histogram_average(self, histogram) -> float:
        """Calculate average from Prometheus histogram"""
        try:
            samples = histogram.collect()[0].samples
            total_sum = 0
            total_count = 0
            
            for sample in samples:
                if sample.name.endswith('_sum'):
                    total_sum = sample.value
                elif sample.name.endswith('_count'):
                    total_count = sample.value
            
            return total_sum / total_count if total_count > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating histogram average: {str(e)}")
            return 0
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get all metrics combined"""
        try:
            system_metrics = self.get_system_metrics()
            app_metrics = self.get_application_metrics()
            
            return {
                "system": system_metrics,
                "application": app_metrics,
                "status": "healthy",
                "last_updated": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive metrics: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "last_updated": time.time()
            }

# Global metrics collector instance
metrics_collector = MetricsCollector()
