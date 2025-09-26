import streamlit as st
import requests
import os
import logging
from components.prediction_form import PredictionForm
from components.metrics_dashboard import MetricsDashboard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Pharma ML Application",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/ml-pharma',
        'Report a bug': 'https://github.com/your-repo/ml-pharma/issues',
        'About': "# ML Pharma Application\nMachine Learning for Pharmaceutical Treatment Effectiveness"
    }
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
    }
    
    .status-indicator {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: bold;
    }
    
    .status-healthy {
        background-color: #d4edda;
        color: #155724;
    }
    
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

def get_api_url():
    """Get API URL from environment or use default"""
    return os.getenv('API_URL', 'http://localhost:8000')

def check_api_status():
    """Check if the FastAPI backend is accessible"""
    api_url = get_api_url()
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"API health check failed: {str(e)}")
        return False, None

def display_header():
    """Display the application header"""
    st.markdown('<div class="main-header">💊 Pharmaceutical ML Application</div>', unsafe_allow_html=True)
    st.markdown("---")

def display_api_status():
    """Display API connection status in sidebar"""
    st.sidebar.markdown("### 🔗 System Status")
    
    api_healthy, health_data = check_api_status()
    
    if api_healthy and health_data:
        st.sidebar.success("✅ API Connected")
        
        # Display detailed status
        with st.sidebar.expander("📊 Detailed Status"):
            st.write(f"**API Status:** {health_data.get('status', 'unknown').title()}")
            st.write(f"**Model Loaded:** {'✅' if health_data.get('model_loaded') else '❌'}")
            st.write(f"**Database:** {'✅' if health_data.get('cosmos_db_status') else '❌'}")
            st.write(f"**Version:** {health_data.get('version', 'N/A')}")
            st.write(f"**Last Check:** {health_data.get('timestamp', 'N/A')}")
        
        return True
    else:
        st.sidebar.error("❌ API Disconnected")
        st.sidebar.warning(f"Cannot connect to API at: {get_api_url()}")
        return False

def display_model_info():
    """Display model information in sidebar"""
    api_url = get_api_url()
    
    try:
        response = requests.get(f"{api_url}/model/info", timeout=5)
        if response.status_code == 200:
            model_info = response.json()
            
            st.sidebar.markdown("### 🤖 Model Information")
            with st.sidebar.expander("📋 Model Details"):
                st.write(f"**Type:** {model_info.get('model_type', 'N/A')}")
                st.write(f"**Version:** {model_info.get('model_version', 'N/A')}")
                st.write(f"**Features:** {model_info.get('feature_count', 0)}")
                st.write(f"**Trained:** {'✅' if model_info.get('is_trained') else '❌'}")
                
                # Training metrics if available
                training_metrics = model_info.get('training_metrics', {})
                if training_metrics:
                    st.write("**Performance:**")
                    if 'test_accuracy' in training_metrics:
                        st.write(f"• Accuracy: {training_metrics['test_accuracy']:.3f}")
                    if 'test_auc' in training_metrics:
                        st.write(f"• AUC: {training_metrics['test_auc']:.3f}")
                    
    except Exception as e:
        logger.error(f"Error fetching model info: {str(e)}")

def display_feature_info():
    """Display feature information in sidebar"""
    api_url = get_api_url()
    
    try:
        response = requests.get(f"{api_url}/model/features", timeout=5)
        if response.status_code == 200:
            feature_info = response.json()
            
            st.sidebar.markdown("### 📊 Feature Information")
            with st.sidebar.expander("🔍 Feature Descriptions"):
                feature_descriptions = feature_info.get('feature_descriptions', {})
                for feature, description in feature_descriptions.items():
                    st.write(f"**{feature.replace('_', ' ').title()}:** {description}")
                    
    except Exception as e:
        logger.error(f"Error fetching feature info: {str(e)}")

def main():
    """Main application function"""
    # Display header
    display_header()
    
    # Sidebar navigation
    st.sidebar.markdown("### 🧭 Navigation")
    
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🔬 Prediction", "📊 Metrics Dashboard"],
        index=0
    )
    
    # API URL configuration (for development)
    if st.sidebar.checkbox("⚙️ Advanced Settings", value=False):
        current_api_url = get_api_url()
        new_api_url = st.sidebar.text_input("API URL", value=current_api_url)
        if new_api_url != current_api_url:
            os.environ['API_URL'] = new_api_url
            st.sidebar.success("API URL updated! Please refresh the page.")
    
    st.sidebar.markdown("---")

    # Check API status and display in sidebar
    api_connected = display_api_status()
    
    if api_connected:
        display_model_info()
        display_feature_info()

    # Main content area
    if not api_connected:
        st.error("""
        🚨 **API Connection Error**
        
        The Streamlit application cannot connect to the FastAPI backend. Please ensure:
        
        1. The FastAPI server is running on the correct port
        2. The API URL is correctly configured
        3. There are no network connectivity issues
        
        **Expected API URL:** `{}`
        
        **To start the FastAPI server:**
        ```bash
        uvicorn app.main:app --host 0.0.0.0 --port 8000
        ```
        """.format(get_api_url()))
        
        # Still show navigation for demo purposes
        if st.button("🔄 Retry Connection"):
            st.rerun()
    
    # Route to selected page
    api_url = get_api_url()
    
    if page == "🔬 Prediction":
        if api_connected:
            prediction_form = PredictionForm(api_url=api_url)
            prediction_form.render()
        else:
            st.info("Prediction functionality requires API connection.")
            
    elif page == "📊 Metrics Dashboard":
        if api_connected:
            metrics_dashboard = MetricsDashboard(api_url=api_url)
            metrics_dashboard.render()
        else:
            st.info("Metrics dashboard requires API connection.")
            

if __name__ == "__main__":
    main()
