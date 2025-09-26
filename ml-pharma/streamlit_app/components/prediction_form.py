import streamlit as st
import requests
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PredictionForm:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        
        # Feature definitions with descriptions and ranges
        self.feature_config = {
            "drug_concentration": {
                "label": "Drug Concentration (mg/mL)",
                "min_value": 5.0,
                "max_value": 15.0,
                "default": 10.0,
                "step": 0.1,
                "help": "Concentration of the active pharmaceutical ingredient"
            },
            "patient_age": {
                "label": "Patient Age (years)",
                "min_value": 18,
                "max_value": 80,
                "default": 45,
                "step": 1,
                "help": "Age of the patient receiving treatment"
            },
            "patient_weight": {
                "label": "Patient Weight (kg)",
                "min_value": 40.0,
                "max_value": 120.0,
                "default": 70.0,
                "step": 0.5,
                "help": "Patient body weight in kilograms"
            },
            "dosage_mg": {
                "label": "Drug Dosage (mg)",
                "min_value": 100.0,
                "max_value": 1000.0,
                "default": 500.0,
                "step": 10.0,
                "help": "Total drug dosage in milligrams"
            },
            "treatment_duration_days": {
                "label": "Treatment Duration (days)",
                "min_value": 1,
                "max_value": 180,
                "default": 30,
                "step": 1,
                "help": "Duration of the treatment period"
            },
            "biomarker_level": {
                "label": "Biomarker Level",
                "min_value": 1.0,
                "max_value": 10.0,
                "default": 5.0,
                "step": 0.1,
                "help": "Relevant biomarker measurement"
            },
            "liver_function_score": {
                "label": "Liver Function Score",
                "min_value": 0.1,
                "max_value": 1.0,
                "default": 0.8,
                "step": 0.01,
                "help": "Liver function assessment (0-1 scale)"
            },
            "kidney_function_score": {
                "label": "Kidney Function Score",
                "min_value": 0.1,
                "max_value": 1.0,
                "default": 0.8,
                "step": 0.01,
                "help": "Kidney function assessment (0-1 scale)"
            }
        }
    
    def render(self):
        """Render the prediction form"""
        st.header("🔬 Treatment Effectiveness Prediction")
        st.markdown("Enter patient and treatment parameters to predict treatment effectiveness.")
        
        # Create form
        with st.form("prediction_form"):
            st.subheader("Patient & Treatment Parameters")
            
            # Create columns for better layout
            col1, col2 = st.columns(2)
            
            # Collect feature values
            feature_values = {}
            
            feature_names = list(self.feature_config.keys())
            mid_point = len(feature_names) // 2
            
            # First column
            with col1:
                for feature_name in feature_names[:mid_point]:
                    config = self.feature_config[feature_name]
                    
                    if isinstance(config["default"], int):
                        value = st.number_input(
                            config["label"],
                            min_value=config["min_value"],
                            max_value=config["max_value"],
                            value=config["default"],
                            step=config["step"],
                            help=config["help"]
                        )
                    else:
                        value = st.number_input(
                            config["label"],
                            min_value=float(config["min_value"]),
                            max_value=float(config["max_value"]),
                            value=float(config["default"]),
                            step=float(config["step"]),
                            help=config["help"]
                        )
                    
                    feature_values[feature_name] = float(value)
            
            # Second column
            with col2:
                for feature_name in feature_names[mid_point:]:
                    config = self.feature_config[feature_name]
                    
                    if isinstance(config["default"], int):
                        value = st.number_input(
                            config["label"],
                            min_value=config["min_value"],
                            max_value=config["max_value"],
                            value=config["default"],
                            step=config["step"],
                            help=config["help"]
                        )
                    else:
                        value = st.number_input(
                            config["label"],
                            min_value=float(config["min_value"]),
                            max_value=float(config["max_value"]),
                            value=float(config["default"]),
                            step=float(config["step"]),
                            help=config["help"]
                        )
                    
                    feature_values[feature_name] = float(value)
            
            # Submit button
            submitted = st.form_submit_button("🔍 Predict Treatment Effectiveness", use_container_width=True)
            
            if submitted:
                self._make_prediction(feature_values)
    
    def _make_prediction(self, feature_values: Dict[str, float]):
        """Make prediction API call and display results"""
        try:
            # Show loading spinner
            with st.spinner("Analyzing treatment parameters..."):
                # Prepare API request
                features = [feature_values[name] for name in self.feature_config.keys()]
                payload = {"features": features}
                
                # Make API call
                response = requests.post(
                    f"{self.api_url}/predict",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    self._display_prediction_results(response.json(), feature_values)
                else:
                    error_detail = response.json().get("detail", "Unknown error")
                    st.error(f"Prediction failed: {error_detail}")
                    
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: Unable to connect to the ML API. Please check if the service is running.")
            logger.error(f"API connection error: {str(e)}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            logger.error(f"Prediction error: {str(e)}")
    
    def _display_prediction_results(self, prediction_result: Dict[str, Any], feature_values: Dict[str, float]):
        """Display prediction results in an organized manner"""
        st.markdown("---")
        st.subheader("📊 Prediction Results")
        
        # Main prediction result
        prediction = prediction_result["prediction"]
        probability = prediction_result["probability"]
        confidence = prediction_result["confidence"]
        interpretation = prediction_result["interpretation"]
        
        # Create columns for results
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if prediction == 1:
                st.success("✅ **Treatment Effective**")
            else:
                st.error("❌ **Treatment Not Effective**")
        
        with col2:
            st.metric("Confidence", probability * 100, f"{confidence.upper()}")
        
        with col3:
            confidence_color = "🟢" if confidence == "high" else "🟡" if confidence == "medium" else "🔴"
            st.metric("Confidence Level", f"{confidence_color} {confidence.title()}")
        
        # Detailed interpretation
        st.info(f"**Interpretation:** {interpretation}")
        
        # Additional details in expandable section
        with st.expander("📋 Detailed Analysis"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Model Information:**")
                st.write(f"• Model Version: {prediction_result.get('model_version', 'N/A')}")
                st.write(f"• Prediction Probability: {probability:.3f}")
                st.write(f"• Confidence Level: {confidence.title()}")
            
            with col2:
                st.markdown("**Input Parameters:**")
                for feature_name, value in feature_values.items():
                    config = self.feature_config[feature_name]
                    st.write(f"• {config['label']}: {value}")
        
        # Recommendation section
        self._display_recommendations(prediction, probability, confidence, feature_values)
    
    def _display_recommendations(self, prediction: int, probability: float, confidence: str, feature_values: Dict[str, float]):
        """Display clinical recommendations based on prediction"""
        st.markdown("---")
        st.subheader("💡 Clinical Recommendations")
        
        if prediction == 1:  # Treatment effective
            if confidence == "high":
                st.success("""
                **High Confidence - Proceed with Treatment:**
                • The model predicts high treatment effectiveness
                • Consider maintaining current dosage and monitoring parameters
                • Schedule regular follow-ups to confirm effectiveness
                """)
            else:
                st.warning("""
                **Moderate Confidence - Proceed with Caution:**
                • Treatment is likely to be effective but monitor closely
                • Consider adjusting parameters if response is suboptimal
                • Increase monitoring frequency during initial treatment period
                """)
        else:  # Treatment not effective
            if confidence == "high":
                st.error("""
                **High Confidence - Consider Alternative Treatment:**
                • The model strongly predicts treatment ineffectiveness
                • Consider alternative treatment protocols
                • Review patient-specific factors that may affect treatment
                """)
            else:
                st.warning("""
                **Uncertain Prediction - Proceed with Close Monitoring:**
                • Treatment effectiveness is uncertain
                • Consider starting with modified parameters
                • Implement intensive monitoring protocol
                • Be prepared to adjust treatment based on early response
                """)
        
        # Parameter-specific recommendations
        recommendations = self._get_parameter_recommendations(feature_values)
        if recommendations:
            st.markdown("**Parameter-Specific Suggestions:**")
            for rec in recommendations:
                st.write(f"• {rec}")
    
    def _get_parameter_recommendations(self, feature_values: Dict[str, float]) -> list:
        """Generate parameter-specific recommendations"""
        recommendations = []
        
        # Drug concentration recommendations
        if feature_values["drug_concentration"] < 8.0:
            recommendations.append("Consider increasing drug concentration for better efficacy")
        elif feature_values["drug_concentration"] > 12.0:
            recommendations.append("Monitor for potential side effects due to high drug concentration")
        
        # Age-related recommendations
        if feature_values["patient_age"] > 65:
            recommendations.append("Consider age-related dose adjustments and closer monitoring")
        elif feature_values["patient_age"] < 30:
            recommendations.append("Monitor for different response patterns in younger patients")
        
        # Dosage recommendations
        if feature_values["dosage_mg"] < 300:
            recommendations.append("Consider if current dosage is sufficient for therapeutic effect")
        elif feature_values["dosage_mg"] > 700:
            recommendations.append("Monitor for dose-related adverse effects")
        
        # Organ function recommendations
        if feature_values["liver_function_score"] < 0.7:
            recommendations.append("Consider dose adjustment due to reduced liver function")
        
        if feature_values["kidney_function_score"] < 0.7:
            recommendations.append("Consider dose adjustment due to reduced kidney function")
        
        return recommendations
