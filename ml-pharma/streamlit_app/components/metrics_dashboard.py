import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MetricsDashboard:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
    
    def render(self):
        """Render the metrics dashboard"""
        st.header("📊 Container Metrics Dashboard")
        st.markdown("Real-time monitoring of application and system performance")
        
        # Auto-refresh controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("**Live Metrics Monitoring**")
        
        with col2:
            auto_refresh = st.checkbox("Auto-refresh", value=False)
        
        with col3:
            if st.button("🔄 Refresh Now", use_container_width=True):
                st.rerun()
        
        # Auto-refresh logic
        if auto_refresh:
            time.sleep(5)
            st.rerun()
        
        # Fetch and display metrics
        try:
            self._display_system_metrics()
            self._display_application_metrics()
            self._display_prediction_statistics()
            
        except Exception as e:
            st.error(f"Error loading metrics: {str(e)}")
            logger.error(f"Metrics dashboard error: {str(e)}")
    
    def _display_system_metrics(self):
        """Display system performance metrics"""
        st.subheader("🖥️ System Performance")
        
        try:
            # Fetch metrics from API
            response = requests.get(f"{self.api_url}/metrics", timeout=10)
            
            if response.status_code == 200:
                metrics_data = response.json()
                system_metrics = metrics_data.get("system", {})
                
                if system_metrics and not system_metrics.get("error"):
                    self._render_system_metrics_charts(system_metrics)
                else:
                    st.warning("System metrics not available")
            else:
                st.error(f"Failed to fetch metrics: {response.status_code}")
                
        except requests.exceptions.RequestException:
            st.error("Unable to connect to the metrics API. Please ensure the FastAPI service is running.")
        except Exception as e:
            st.error(f"Error fetching system metrics: {str(e)}")
    
    def _render_system_metrics_charts(self, metrics: Dict[str, Any]):
        """Render system metrics charts"""
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_usage = metrics.get("cpu_usage_percent", 0)
            delta_color = "normal" if cpu_usage < 70 else "inverse"
            st.metric(
                label="CPU Usage",
                value=f"{cpu_usage:.1f}%",
                delta=f"{'🟢' if cpu_usage < 70 else '🟡' if cpu_usage < 85 else '🔴'}"
            )
        
        with col2:
            memory_percent = metrics.get("memory_usage_percent", 0)
            st.metric(
                label="Memory Usage",
                value=f"{memory_percent:.1f}%",
                delta=f"{'🟢' if memory_percent < 70 else '🟡' if memory_percent < 85 else '🔴'}"
            )
        
        with col3:
            disk_usage = metrics.get("disk_usage_percent", 0)
            st.metric(
                label="Disk Usage",
                value=f"{disk_usage:.1f}%",
                delta=f"{'🟢' if disk_usage < 70 else '🟡' if disk_usage < 85 else '🔴'}"
            )
        
        with col4:
            # Convert bytes to GB for memory
            memory_used_gb = metrics.get("memory_usage_bytes", 0) / (1024**3)
            st.metric(
                label="Memory Used",
                value=f"{memory_used_gb:.2f} GB"
            )
        
        # Detailed charts
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU Usage Gauge
            fig_cpu = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=metrics.get("cpu_usage_percent", 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "CPU Usage (%)"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_cpu.update_layout(height=300)
            st.plotly_chart(fig_cpu, use_container_width=True)
        
        with col2:
            # Memory Usage Gauge
            fig_memory = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=metrics.get("memory_usage_percent", 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Memory Usage (%)"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "green"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_memory.update_layout(height=300)
            st.plotly_chart(fig_memory, use_container_width=True)
        
        # System information
        with st.expander("📋 Detailed System Information"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Memory Details:**")
                memory_total_gb = metrics.get("memory_total_bytes", 0) / (1024**3)
                memory_available_gb = metrics.get("memory_available_bytes", 0) / (1024**3)
                st.write(f"• Total: {memory_total_gb:.2f} GB")
                st.write(f"• Available: {memory_available_gb:.2f} GB")
                st.write(f"• Used: {memory_used_gb:.2f} GB")
            
            with col2:
                st.markdown("**Disk Details:**")
                disk_total_gb = metrics.get("disk_total_bytes", 0) / (1024**3)
                disk_free_gb = metrics.get("disk_free_bytes", 0) / (1024**3)
                disk_used_gb = metrics.get("disk_used_bytes", 0) / (1024**3)
                st.write(f"• Total: {disk_total_gb:.2f} GB")
                st.write(f"• Free: {disk_free_gb:.2f} GB")
                st.write(f"• Used: {disk_used_gb:.2f} GB")
    
    def _display_application_metrics(self):
        """Display application-specific metrics"""
        st.subheader("🚀 Application Performance")
        
        try:
            response = requests.get(f"{self.api_url}/metrics", timeout=10)
            
            if response.status_code == 200:
                metrics_data = response.json()
                app_metrics = metrics_data.get("application", {})
                
                if app_metrics and not app_metrics.get("error"):
                    self._render_application_metrics(app_metrics)
                else:
                    st.info("Application metrics will be available after some API usage")
            else:
                st.warning("Application metrics not available")
                
        except Exception as e:
            st.warning("Application metrics not available")
    
    def _render_application_metrics(self, metrics: Dict[str, Any]):
        """Render application metrics"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Requests",
                value=f"{metrics.get('total_requests', 0):.0f}"
            )
        
        with col2:
            st.metric(
                label="Total Predictions",
                value=f"{metrics.get('total_predictions', 0):.0f}"
            )
        
        with col3:
            avg_request_duration = metrics.get('average_request_duration', 0)
            st.metric(
                label="Avg Request Time",
                value=f"{avg_request_duration:.3f}s"
            )
        
        with col4:
            avg_inference_time = metrics.get('average_inference_time', 0)
            st.metric(
                label="Avg Inference Time",
                value=f"{avg_inference_time:.3f}s"
            )
    
    def _display_prediction_statistics(self):
        """Display prediction statistics from database"""
        st.subheader("📈 Prediction Analytics")
        
        try:
            # Fetch prediction statistics
            response = requests.get(f"{self.api_url}/predictions/stats", timeout=10)
            
            if response.status_code == 200:
                stats = response.json()
                
                if stats:
                    self._render_prediction_stats(stats)
                else:
                    st.info("No prediction data available yet. Make some predictions to see statistics.")
            else:
                st.info("Prediction statistics not available")
                
        except Exception as e:
            st.info("Prediction statistics will be available after database connection is established")
    
    def _render_prediction_stats(self, stats: Dict[str, Any]):
        """Render prediction statistics"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Predictions",
                value=f"{stats.get('total_predictions', 0)}"
            )
        
        with col2:
            st.metric(
                label="Effective Treatments",
                value=f"{stats.get('effective_predictions', 0)}"
            )
        
        with col3:
            st.metric(
                label="Non-Effective Treatments",
                value=f"{stats.get('non_effective_predictions', 0)}"
            )
        
        with col4:
            effectiveness_rate = stats.get('effectiveness_rate', 0)
            st.metric(
                label="Effectiveness Rate",
                value=f"{effectiveness_rate:.1f}%"
            )
        
        # Effectiveness distribution chart
        if stats.get('total_predictions', 0) > 0:
            fig = go.Figure(data=[
                go.Pie(
                    labels=['Effective', 'Not Effective'],
                    values=[
                        stats.get('effective_predictions', 0),
                        stats.get('non_effective_predictions', 0)
                    ],
                    hole=0.3,
                    marker_colors=['#2E8B57', '#DC143C']
                )
            ])
            
            fig.update_layout(
                title="Treatment Effectiveness Distribution",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent predictions
        self._display_recent_predictions()
    
    def _display_recent_predictions(self):
        """Display recent predictions table"""
        try:
            response = requests.get(f"{self.api_url}/predictions/recent?limit=10", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                predictions = data.get('predictions', [])
                
                if predictions:
                    st.markdown("**Recent Predictions:**")
                    
                    # Prepare data for display
                    display_data = []
                    for pred in predictions:
                        display_data.append({
                            'Timestamp': pred.get('timestamp', 'N/A')[:19],  # Remove microseconds
                            'Prediction': '✅ Effective' if pred.get('prediction') == 1 else '❌ Not Effective',
                            'Probability': f"{pred.get('probability', 0):.3f}",
                            'Confidence': pred.get('confidence', 'unknown').title()
                        })
                    
                    df = pd.DataFrame(display_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No recent predictions available")
            
        except Exception as e:
            logger.error(f"Error fetching recent predictions: {str(e)}")
    
    def _render_status_indicators(self):
        """Render system status indicators"""
        st.markdown("---")
        st.subheader("🔧 System Status")
        
        try:
            # Check API health
            response = requests.get(f"{self.api_url}/health", timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    status = "🟢 Healthy" if health_data.get("status") == "healthy" else "🔴 Unhealthy"
                    st.metric("API Status", status)
                
                with col2:
                    model_status = "🟢 Loaded" if health_data.get("model_loaded") else "🔴 Not Loaded"
                    st.metric("ML Model", model_status)
                
                with col3:
                    db_status = "🟢 Connected" if health_data.get("cosmos_db_status") else "🔴 Disconnected"
                    st.metric("Database", db_status)
                
                with col4:
                    st.metric("Version", health_data.get("version", "N/A"))
            
        except Exception as e:
            st.error("Unable to fetch system status")
