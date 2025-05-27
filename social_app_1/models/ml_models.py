"""
Machine learning models for eligibility assessment and risk scoring.
Implements scikit-learn models for classification and prediction.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EligibilityModel:
    """
    Machine learning model for predicting eligibility for social support.
    Provides options for different algorithms and feature engineering.
    """
    
    def __init__(self, model_type: str = "random_forest"):
        """
        Initialize the eligibility prediction model.
        
        Args:
            model_type: Type of ML model to use ('random_forest', 'gradient_boosting', or 'logistic')
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.preprocessor = None
        self.feature_importance = None
        
        logger.info(f"EligibilityModel initialized with {model_type} model")

    def build_model(self):
        """
        Build the machine learning model pipeline.
        
        Returns:
            The configured model pipeline
        """
        # Define numeric and categorical features
        numeric_features = ['income', 'family_size', 'income_per_member', 
                           'debt_to_income_ratio', 'assets_to_income_ratio', 'age']
        categorical_features = ['employment_status', 'gender', 'nationality']
        
        # Create preprocessor for features
        numeric_transformer = Pipeline(steps=[
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline(steps=[
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])
        
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ],
            remainder='drop'
        )
        
        # Choose the model based on type
        if self.model_type == "random_forest":
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
        elif self.model_type == "gradient_boosting":
            model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
        elif self.model_type == "logistic":
            model = LogisticRegression(
                C=1.0,
                solver='liblinear',
                random_state=42,
                class_weight='balanced'
            )
        else:
            logger.warning(f"Unknown model type: {self.model_type}, defaulting to RandomForest")
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Create full pipeline
        self.model = Pipeline(steps=[
            ('preprocessor', self.preprocessor),
            ('model', model)
        ])
        
        return self.model

    def train(self, X: pd.DataFrame, y: pd.Series, tune_hyperparameters: bool = False):
        """
        Train the eligibility model on the provided data.
        
        Args:
            X: Feature DataFrame
            y: Target Series
            tune_hyperparameters: Whether to perform hyperparameter tuning
        """
        if self.model is None:
            self.build_model()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Tune hyperparameters if requested
        if tune_hyperparameters:
            self._tune_hyperparameters(X_train, y_train)
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        self._evaluate_model(y_test, y_pred)
        
        # Calculate feature importance if possible
        self._calculate_feature_importance(X)

    def _tune_hyperparameters(self, X_train: pd.DataFrame, y_train: pd.Series):
        """
        Perform hyperparameter tuning using GridSearchCV.
        
        Args:
            X_train: Training features
            y_train: Training targets
        """
        logger.info("Performing hyperparameter tuning...")
        
        # Define parameter grid based on model type
        if self.model_type == "random_forest":
            param_grid = {
                'model__n_estimators': [50, 100, 200],
                'model__max_depth': [5, 10, 15],
                'model__min_samples_split': [2, 5, 10]
            }
        elif self.model_type == "gradient_boosting":
            param_grid = {
                'model__n_estimators': [50, 100, 200],
                'model__learning_rate': [0.01, 0.1, 0.2],
                'model__max_depth': [3, 5, 7]
            }
        elif self.model_type == "logistic":
            param_grid = {
                'model__C': [0.1, 1.0, 10.0],
                'model__solver': ['liblinear', 'saga'],
                'model__penalty': ['l1', 'l2']
            }
        else:
            param_grid = {}
        
        # Perform grid search
        grid_search = GridSearchCV(
            self.model,
            param_grid,
            cv=5,
            scoring='f1',
            n_jobs=-1
        )
        
        grid_search.fit(X_train, y_train)
        
        # Update model with best parameters
        self.model = grid_search.best_estimator_
        logger.info(f"Best parameters: {grid_search.best_params_}")

    def _evaluate_model(self, y_true: pd.Series, y_pred: np.ndarray):
        """
        Evaluate model performance using multiple metrics.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
        """
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred)
        recall = recall_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)
        conf_matrix = confusion_matrix(y_true, y_pred)
        
        # Log results
        logger.info(f"Model Evaluation Results:")
        logger.info(f"Accuracy: {accuracy:.4f}")
        logger.info(f"Precision: {precision:.4f}")
        logger.info(f"Recall: {recall:.4f}")
        logger.info(f"F1 Score: {f1:.4f}")
        logger.info(f"Confusion Matrix:\n{conf_matrix}")

    def _calculate_feature_importance(self, X: pd.DataFrame):
        """
        Calculate and store feature importance.
        
        Args:
            X: Feature DataFrame for column names
        """
        # Get feature importance if model supports it
        if self.model_type in ["random_forest", "gradient_boosting"]:
            # Get model from pipeline
            model_step = self.model.named_steps['model']
            
            # Get feature names after preprocessing
            if hasattr(self.preprocessor, 'get_feature_names_out'):
                feature_names = self.preprocessor.get_feature_names_out()
            else:
                # Fallback for older scikit-learn versions
                feature_names = [f"feature_{i}" for i in range(len(model_step.feature_importances_))]
            
            # Create feature importance dictionary
            self.feature_importance = dict(zip(
                feature_names,
                model_step.feature_importances_
            ))
            
            # Log top features
            top_features = sorted(
                self.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            logger.info("Top 5 important features:")
            for feature, importance in top_features:
                logger.info(f"{feature}: {importance:.4f}")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make eligibility predictions for new data.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of predicted classes (0 or 1)
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet")
        
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get probability estimates for eligibility.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of class probabilities
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet")
        
        return self.model.predict_proba(X)

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if self.feature_importance is None:
            logger.warning("Feature importance not available")
            return {}
        
        return self.feature_importance


class RiskScoringModel:
    """
    Machine learning model for risk scoring of applications.
    Provides risk level predictions and scoring.
    """
    
    def __init__(self, model_type: str = "gradient_boosting"):
        """
        Initialize the risk scoring model.
        
        Args:
            model_type: Type of ML model to use
        """
        self.model_type = model_type
        self.model = None
        self.preprocessor = None
        
        logger.info(f"RiskScoringModel initialized with {model_type} model")

    def build_model(self):
        """
        Build the risk scoring model pipeline.
        
        Returns:
            The configured model pipeline
        """
        # Define numeric and categorical features
        numeric_features = ['income', 'family_size', 'income_per_member', 
                           'debt_to_income_ratio', 'assets_to_income_ratio', 'age']
        categorical_features = ['employment_status']
        
        # Create preprocessor for features
        numeric_transformer = Pipeline(steps=[
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline(steps=[
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])
        
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ],
            remainder='drop'
        )
        
        # Choose the model based on type
        if self.model_type == "gradient_boosting":
            model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
        elif self.model_type == "random_forest":
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
        else:
            logger.warning(f"Unknown model type: {self.model_type}, defaulting to GradientBoosting")
            model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        
        # Create full pipeline
        self.model = Pipeline(steps=[
            ('preprocessor', self.preprocessor),
            ('model', model)
        ])
        
        return self.model

    def train(self, X: pd.DataFrame, y: pd.Series):
        """
        Train the risk scoring model on the provided data.
        
        Args:
            X: Feature DataFrame
            y: Target Series (risk levels as classes)
        """
        if self.model is None:
            self.build_model()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        self._evaluate_model(y_test, y_pred)

    def _evaluate_model(self, y_true: pd.Series, y_pred: np.ndarray):
        """
        Evaluate model performance using multiple metrics.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
        """
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        
        # For multi-class, use macro averaging
        precision = precision_score(y_true, y_pred, average='macro')
        recall = recall_score(y_true, y_pred, average='macro')
        f1 = f1_score(y_true, y_pred, average='macro')
        
        # Log results
        logger.info(f"Risk Scoring Model Evaluation Results:")
        logger.info(f"Accuracy: {accuracy:.4f}")
        logger.info(f"Precision: {precision:.4f}")
        logger.info(f"Recall: {recall:.4f}")
        logger.info(f"F1 Score: {f1:.4f}")

    def predict_risk(self, X: pd.DataFrame) -> List[str]:
        """
        Predict risk levels for new applications.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            List of risk level strings ('low', 'medium', 'high')
        """
        if self.model is None:
            raise ValueError("Model has not been trained yet")
        
        # Get numeric predictions
        risk_indices = self.model.predict(X)
        
        # Convert to risk level strings
        risk_levels = ['low', 'medium', 'high']
        return [risk_levels[idx] for idx in risk_indices]

    def calculate_risk_score(self, data: Dict[str, Any]) -> Tuple[str, float]:
        """
        Calculate risk score for a single application using rule-based approach.
        
        Args:
            data: Dictionary of application data
            
        Returns:
            Tuple of (risk_level, risk_score)
        """
        risk_score = 0
        
        # Extract data
        income = data.get('income', 0)
        family_size = data.get('family_size', 0)
        liabilities = data.get('liabilities', 0)
        assets = data.get('assets', 0)
        employment_status = data.get('employment_status', '').lower()
        
        # Income risk
        if income < 30000:
            risk_score += 3
        elif income < 50000:
            risk_score += 2
        elif income < 70000:
            risk_score += 1
        
        # Family size risk
        if family_size > 5:
            risk_score += 2
        elif family_size > 3:
            risk_score += 1
        
        # Debt risk
        debt_to_income = liabilities / income if income > 0 else 0
        if debt_to_income > 0.5:
            risk_score += 3
        elif debt_to_income > 0.3:
            risk_score += 2
        elif debt_to_income > 0.1:
            risk_score += 1
        
        # Employment risk
        if 'unemployed' in employment_status:
            risk_score += 3
        elif 'part-time' in employment_status or 'temporary' in employment_status:
            risk_score += 2
        elif 'self-employed' in employment_status:
            risk_score += 1
        
        # Assets risk
        assets_to_income = assets / income if income > 0 else 0
        if assets_to_income < 0.2:
            risk_score += 2
        elif assets_to_income < 0.5:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 7:
            risk_level = "high"
        elif risk_score >= 4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return risk_level, risk_score
