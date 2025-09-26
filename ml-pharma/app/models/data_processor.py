import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from typing import Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_columns = None
        self.is_fitted = False
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load and preprocess pharmaceutical data"""
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Successfully loaded data with shape: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def create_synthetic_pharma_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Create synthetic pharmaceutical data for demonstration"""
        np.random.seed(42)
        
        # Generate synthetic features
        data = {
            'drug_concentration': np.random.normal(10.0, 2.0, n_samples),
            'patient_age': np.random.randint(18, 80, n_samples),
            'patient_weight': np.random.normal(70, 15, n_samples),
            'dosage_mg': np.random.normal(500, 100, n_samples),
            'treatment_duration_days': np.random.randint(7, 90, n_samples),
            'biomarker_level': np.random.normal(5.0, 1.5, n_samples),
            'liver_function_score': np.random.uniform(0.5, 1.0, n_samples),
            'kidney_function_score': np.random.uniform(0.6, 1.0, n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Create target variable (treatment_effective: 1 = effective, 0 = not effective)
        # Higher drug concentration, optimal age range, proper dosage increase effectiveness
        effectiveness_score = (
            (df['drug_concentration'] - 10) * 0.1 +
            (1 / (1 + np.abs(df['patient_age'] - 45) * 0.02)) * 0.3 +
            (df['dosage_mg'] / 1000) * 0.2 +
            df['biomarker_level'] * 0.1 +
            df['liver_function_score'] * 0.2 +
            df['kidney_function_score'] * 0.1 +
            np.random.normal(0, 0.1, n_samples)
        )
        
        # Convert to binary classification
        df['treatment_effective'] = (effectiveness_score > effectiveness_score.median()).astype(int)
        
        logger.info(f"Created synthetic dataset with {n_samples} samples")
        logger.info(f"Treatment effectiveness distribution: {df['treatment_effective'].value_counts().to_dict()}")
        
        return df
    
    def prepare_features(self, df: pd.DataFrame, target_column: str = 'treatment_effective') -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features for training"""
        try:
            # Separate features and target
            if target_column in df.columns:
                X = df.drop(columns=[target_column])
                y = df[target_column]
            else:
                X = df
                y = None
                
            # Handle missing values
            X = X.fillna(X.median())
            
            # Store feature columns for later use
            self.feature_columns = X.columns.tolist()
            
            # Scale features
            if not self.is_fitted:
                X_scaled = self.scaler.fit_transform(X)
                self.is_fitted = True
                logger.info("Fitted scaler on training data")
            else:
                X_scaled = self.scaler.transform(X)
                logger.info("Applied existing scaler to data")
            
            X_scaled = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
            
            logger.info(f"Prepared features with shape: {X_scaled.shape}")
            return X_scaled, y
            
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            raise
    
    def split_data(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Split data into train and test sets"""
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )
            
            logger.info(f"Split data into train: {X_train.shape}, test: {X_test.shape}")
            return X_train, X_test, y_train, y_test
            
        except Exception as e:
            logger.error(f"Error splitting data: {str(e)}")
            raise
    
    def get_feature_names(self) -> Optional[list]:
        """Get the list of feature column names"""
        return self.feature_columns
    
    def transform_single_prediction(self, features: list) -> np.ndarray:
        """Transform a single set of features for prediction"""
        try:
            if not self.is_fitted:
                raise ValueError("DataProcessor must be fitted before transforming data")
            
            if len(features) != len(self.feature_columns):
                raise ValueError(f"Expected {len(self.feature_columns)} features, got {len(features)}")
            
            # Convert to DataFrame for consistency
            feature_df = pd.DataFrame([features], columns=self.feature_columns)
            
            # Transform using fitted scaler
            transformed = self.scaler.transform(feature_df)
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming features for prediction: {str(e)}")
            raise
