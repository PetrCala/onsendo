"""
Modeling system for onsen analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
import warnings
from datetime import datetime
import pickle
from pathlib import Path

from src.types.analysis import ModelType, ModelConfig
from src.analysis.metrics import MetricsCalculator

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


class ModelEngine:
    """
    Engine for creating and training statistical and machine learning models.
    """

    def __init__(self, save_dir: Optional[str] = None):
        self.save_dir = Path(save_dir) if save_dir else Path("output/models")
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_calculator = MetricsCalculator()
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.label_encoders: Dict[str, Any] = {}

    def _get_sklearn_models(self):
        """Lazy import scikit-learn models."""
        from sklearn.linear_model import (
            LinearRegression,
            LogisticRegression,
            Ridge,
            Lasso,
        )
        from sklearn.ensemble import (
            RandomForestRegressor,
            RandomForestClassifier,
            GradientBoostingRegressor,
        )
        from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
        from sklearn.cluster import KMeans, DBSCAN
        from sklearn.decomposition import PCA
        from sklearn.manifold import TSNE
        from sklearn.model_selection import (
            train_test_split,
            cross_val_score,
            GridSearchCV,
        )
        from sklearn.metrics import (
            mean_squared_error,
            r2_score,
            accuracy_score,
            classification_report,
            confusion_matrix,
            silhouette_score,
            mean_absolute_error,
        )
        from sklearn.preprocessing import StandardScaler, LabelEncoder

        return (
            LinearRegression,
            LogisticRegression,
            Ridge,
            Lasso,
            RandomForestRegressor,
            RandomForestClassifier,
            GradientBoostingRegressor,
            DecisionTreeRegressor,
            DecisionTreeClassifier,
            KMeans,
            DBSCAN,
            PCA,
            TSNE,
            train_test_split,
            cross_val_score,
            GridSearchCV,
            mean_squared_error,
            r2_score,
            accuracy_score,
            classification_report,
            confusion_matrix,
            silhouette_score,
            mean_absolute_error,
            StandardScaler,
            LabelEncoder,
        )

    def _get_sklearn_linear_models(self):
        """Lazy import sklearn linear models."""
        from sklearn.linear_model import (
            LinearRegression,
            LogisticRegression,
            Ridge,
            Lasso,
        )

        return LinearRegression, LogisticRegression, Ridge, Lasso

    def _get_sklearn_ensemble_models(self):
        """Lazy import sklearn ensemble models."""
        from sklearn.ensemble import (
            RandomForestRegressor,
            RandomForestClassifier,
            GradientBoostingRegressor,
        )

        return RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor

    def _get_sklearn_tree_models(self):
        """Lazy import sklearn tree models."""
        from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier

        return DecisionTreeRegressor, DecisionTreeClassifier

    def _get_sklearn_clustering_models(self):
        """Lazy import sklearn clustering models."""
        from sklearn.cluster import KMeans, DBSCAN

        return KMeans, DBSCAN

    def _get_sklearn_dimensionality_reduction(self):
        """Lazy import sklearn dimensionality reduction models."""
        from sklearn.decomposition import PCA
        from sklearn.manifold import TSNE

        return PCA, TSNE

    def _get_sklearn_model_selection(self):
        """Lazy import sklearn model selection utilities."""
        from sklearn.model_selection import (
            train_test_split,
            cross_val_score,
            GridSearchCV,
        )

        return train_test_split, cross_val_score, GridSearchCV

    def _get_sklearn_regression_metrics(self):
        """Lazy import sklearn regression metrics."""
        from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

        return mean_squared_error, r2_score, mean_absolute_error

    def _get_sklearn_classification_metrics(self):
        """Lazy import sklearn classification metrics."""
        from sklearn.metrics import (
            accuracy_score,
            classification_report,
            confusion_matrix,
        )

        return accuracy_score, classification_report, confusion_matrix

    def _get_sklearn_clustering_metrics(self):
        """Lazy import sklearn clustering metrics."""
        from sklearn.metrics import silhouette_score

        return silhouette_score

    def create_model(self, data: pd.DataFrame, config: ModelConfig) -> Dict[str, Any]:
        """
        Create and train a model based on the configuration.

        Args:
            data: DataFrame to train on
            config: Model configuration

        Returns:
            Dictionary containing model results and metadata
        """
        if data.empty:
            raise ValueError("Cannot create model with empty data")

        # Prepare the data
        X, y, feature_names = self._prepare_data(data, config)

        if X.empty or y.empty:
            raise ValueError("Failed to prepare data for modeling")

        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=config.validation_split, random_state=config.random_state
        )

        # Scale the features if needed
        if config.type in [
            ModelType.LINEAR_REGRESSION,
            ModelType.RIDGE_REGRESSION,
            ModelType.LASSO_REGRESSION,
            ModelType.LOGISTIC_REGRESSION,
        ]:
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            self.scalers[config.type.value] = scaler
        else:
            X_train_scaled = X_train
            X_test_scaled = X_test

        # Create and train the model
        model = self._create_model_instance(config)

        # Train the model
        model.fit(X_train_scaled, y_train)

        # Make predictions
        y_pred = model.predict(X_test_scaled)

        # Evaluate the model
        metrics = self._evaluate_model(y_test, y_pred, config.type)

        # Cross-validation
        cv_scores = cross_val_score(
            model, X_train_scaled, y_train, cv=config.cross_validation_folds
        )

        # Store the model
        model_key = f"{config.type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.models[model_key] = model

        # Create results
        results = {
            "model_type": config.type.value,
            "model": model,
            "feature_names": feature_names,
            "target_column": config.target_column,
            "feature_columns": config.feature_columns,
            "training_data_shape": X_train.shape,
            "test_data_shape": X_test.shape,
            "metrics": metrics,
            "cross_validation_scores": cv_scores.tolist(),
            "cross_validation_mean": cv_scores.mean(),
            "cross_validation_std": cv_scores.std(),
            "hyperparameters": config.hyperparameters,
            "training_date": datetime.now().isoformat(),
            "feature_importance": self._get_feature_importance(
                model, feature_names, config.type
            ),
        }
        # Save the model
        self._save_model(model_key, results)

        return results

    def _prepare_data(
        self, data: pd.DataFrame, config: ModelConfig
    ) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """Prepare data for modeling."""

        # Check if required columns exist
        missing_cols = [
            col for col in config.feature_columns if col not in data.columns
        ]
        if missing_cols:
            raise ValueError(f"Missing feature columns: {missing_cols}")

        if config.target_column not in data.columns:
            raise ValueError(
                f"Target column '{config.target_column}' not found in data"
            )

        # Filter data to only include required columns
        model_data = data[config.feature_columns + [config.target_column]].copy()

        # Remove rows with missing values
        model_data = model_data.dropna()

        if model_data.empty:
            raise ValueError("No data remaining after removing missing values")

        # Separate features and target
        X = model_data[config.feature_columns]
        y = model_data[config.target_column]

        # Handle categorical features
        feature_names = []
        for col in config.feature_columns:
            # Use pandas dtype access method
            col_dtype = str(X[col].dtype)
            if col_dtype == "object":
                # Encode categorical variables
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                self.label_encoders[f"{col}_encoder"] = le
                feature_names.append(f"{col}_encoded")
            else:
                feature_names.append(col)

        # Handle categorical target for classification
        if config.type in [
            ModelType.LOGISTIC_REGRESSION,
            ModelType.DECISION_TREE,
            ModelType.RANDOM_FOREST,
            ModelType.GRADIENT_BOOSTING,
        ]:
            # Use pandas dtype access method
            y_dtype = str(y.dtype)
            if y_dtype == "object":
                le = LabelEncoder()
                y = le.fit_transform(y.astype(str))
                self.label_encoders[f"{config.target_column}_encoder"] = le

        return X, y, feature_names

    def _create_model_instance(self, config: ModelConfig) -> Any:
        """Create a model instance based on the configuration."""

        if config.type == ModelType.LINEAR_REGRESSION:
            return LinearRegression(**config.hyperparameters or {})
        elif config.type == ModelType.LOGISTIC_REGRESSION:
            return LogisticRegression(**config.hyperparameters or {})
        elif config.type == ModelType.RIDGE_REGRESSION:
            return Ridge(**config.hyperparameters or {})
        elif config.type == ModelType.LASSO_REGRESSION:
            return Lasso(**config.hyperparameters or {})
        elif config.type == ModelType.DECISION_TREE:
            if config.target_column in self.label_encoders:
                return DecisionTreeClassifier(**config.hyperparameters or {})
            else:
                return DecisionTreeRegressor(**config.hyperparameters or {})
        elif config.type == ModelType.RANDOM_FOREST:
            if config.target_column in self.label_encoders:
                return RandomForestClassifier(**config.hyperparameters or {})
            else:
                return RandomForestRegressor(**config.hyperparameters or {})
        elif config.type == ModelType.GRADIENT_BOOSTING:
            return GradientBoostingRegressor(**config.hyperparameters or {})
        elif config.type == ModelType.KMEANS:
            return KMeans(**config.hyperparameters or {})
        elif config.type == ModelType.DBSCAN:
            return DBSCAN(**config.hyperparameters or {})
        elif config.type == ModelType.PCA:
            return PCA(**config.hyperparameters or {})
        elif config.type == ModelType.TSNE:
            return TSNE(**config.hyperparameters or {})
        else:
            raise ValueError(f"Unsupported model type: {config.type}")

    def _evaluate_model(
        self, y_true: pd.Series, y_pred: np.ndarray, model_type: ModelType
    ) -> Dict[str, float]:
        """Evaluate the model performance."""
        metrics = {}

        if model_type in [
            ModelType.LINEAR_REGRESSION,
            ModelType.RIDGE_REGRESSION,
            ModelType.LASSO_REGRESSION,
            ModelType.DECISION_TREE,
            ModelType.RANDOM_FOREST,
            ModelType.GRADIENT_BOOSTING,
        ]:
            # Regression metrics
            metrics["mse"] = mean_squared_error(y_true, y_pred)
            metrics["rmse"] = np.sqrt(metrics["mse"])
            metrics["mae"] = mean_absolute_error(y_true, y_pred)
            metrics["r2"] = r2_score(y_true, y_pred)

        elif model_type in [
            ModelType.LOGISTIC_REGRESSION,
            ModelType.DECISION_TREE,
            ModelType.RANDOM_FOREST,
        ]:
            # Classification metrics
            metrics["accuracy"] = accuracy_score(y_true, y_pred)

            # Additional classification metrics
            try:
                report = classification_report(y_true, y_pred, output_dict=True)
                metrics["precision_macro"] = report["macro avg"]["precision"]
                metrics["recall_macro"] = report["macro avg"]["recall"]
                metrics["f1_macro"] = report["macro avg"]["f1-score"]
            except Exception as e:
                logger.warning(
                    f"Could not calculate detailed classification metrics: {e}"
                )

        elif model_type in [ModelType.KMEANS, ModelType.DBSCAN]:
            # Clustering metrics
            try:
                metrics["silhouette_score"] = silhouette_score(y_true, y_pred)
            except Exception as e:
                logger.warning(f"Could not calculate silhouette score: {e}")

        return metrics

    def _get_feature_importance(
        self, model: Any, feature_names: List[str], model_type: ModelType
    ) -> Optional[Dict[str, float]]:
        """Get feature importance from the model."""
        try:
            if hasattr(model, "feature_importances_"):
                return dict(zip(feature_names, model.feature_importances_))
            elif hasattr(model, "coef_"):
                return dict(zip(feature_names, model.coef_))
            else:
                return None
        except Exception as e:
            logger.warning(f"Could not extract feature importance: {e}")
            return None

    def _save_model(self, model_key: str, results: Dict[str, Any]) -> None:
        """Save the trained model and results."""
        try:
            model_path = self.save_dir / f"{model_key}.pkl"

            # Save the model object
            with open(model_path, "wb") as f:
                pickle.dump(results, f)

            logger.info(f"Model saved to {model_path}")

        except Exception as e:
            logger.error(f"Failed to save model: {e}")

    def load_model(self, model_path: str) -> Optional[Dict[str, Any]]:
        """Load a saved model."""
        try:
            with open(model_path, "rb") as f:
                results = pickle.load(f)

            # Store the loaded model
            model_key = Path(model_path).stem
            self.models[model_key] = results["model"]

            logger.info(f"Model loaded from {model_path}")
            return results

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None

    def predict(self, model_key: str, data: pd.DataFrame) -> Optional[np.ndarray]:
        """Make predictions using a trained model."""
        if model_key not in self.models:
            logger.error(f"Model {model_key} not found")
            return None

        model = self.models[model_key]

        try:
            # Prepare the data (this is a simplified version)
            # In production, you'd want to use the same preprocessing as training
            feature_cols = [
                col for col in data.columns if col in model.feature_names_in_
            ]
            X = data[feature_cols].dropna()

            if X.empty:
                logger.warning("No valid data for prediction")
                return None

            # Scale if needed
            if model_key in self.scalers:
                X_scaled = self.scalers[model_key].transform(X)
            else:
                X_scaled = X

            # Make prediction
            predictions = model.predict(X_scaled)
            return predictions

        except Exception as e:
            logger.error(f"Failed to make predictions: {e}")
            return None

    def create_clustering_model(
        self, data: pd.DataFrame, config: ModelConfig, n_clusters: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a clustering model."""
        if config.type not in [ModelType.KMEANS, ModelType.DBSCAN]:
            raise ValueError(f"Model type {config.type} is not a clustering model")

        # Prepare data
        X = data[config.feature_columns].dropna()

        if X.empty:
            raise ValueError("No data remaining after removing missing values")

        # Scale the data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers[config.type.value] = scaler

        # Determine number of clusters for KMeans
        if config.type == ModelType.KMEANS and n_clusters is None:
            # Use elbow method to find optimal number of clusters
            n_clusters = self._find_optimal_clusters(X_scaled)

        # Update hyperparameters
        if config.hyperparameters is None:
            config.hyperparameters = {}

        if config.type == ModelType.KMEANS and n_clusters:
            config.hyperparameters["n_clusters"] = n_clusters

        # Create and fit the model
        model = self._create_model_instance(config)
        model.fit(X_scaled)

        # Get cluster labels
        cluster_labels = model.labels_

        # Calculate metrics
        metrics = {}
        try:
            metrics["silhouette_score"] = silhouette_score(X_scaled, cluster_labels)
        except Exception as e:
            logger.warning(f"Could not calculate silhouette score: {e}")

        # Store the model
        model_key = f"{config.type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.models[model_key] = model

        # Create results
        results = {
            "model_type": config.type.value,
            "model": model,
            "feature_names": config.feature_columns,
            "n_clusters": (
                n_clusters
                if config.type == ModelType.KMEANS
                else len(set(cluster_labels))
            ),
            "cluster_labels": cluster_labels,
            "metrics": metrics,
            "training_date": datetime.now().isoformat(),
            "data_shape": X.shape,
        }

        # Save the model
        self._save_model(model_key, results)

        return results

    def _find_optimal_clusters(self, X: np.ndarray, max_clusters: int = 10) -> int:
        """Find optimal number of clusters using elbow method."""
        inertias = []
        silhouette_scores = []
        K_range = range(2, min(max_clusters + 1, X.shape[0]))
        logger.info(
            f"Finding optimal number of clusters using elbow method with range {K_range}"
        )

        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)
            inertias.append(kmeans.inertia_)

            try:
                score = silhouette_score(X, kmeans.labels_)
                silhouette_scores.append(score)
            except:
                silhouette_scores.append(0)

        # Simple elbow method (you could implement more sophisticated methods)
        # For now, just return the k with highest silhouette score
        if silhouette_scores:
            return K_range[np.argmax(silhouette_scores)]
        else:
            return 3  # Default fallback

    def create_dimensionality_reduction_model(
        self,
        data: pd.DataFrame,
        config: ModelConfig,
        n_components: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a dimensionality reduction model."""
        if config.type not in [ModelType.PCA, ModelType.TSNE]:
            raise ValueError(
                f"Model type {config.type} is not a dimensionality reduction model"
            )

        # Prepare data
        X = data[config.feature_columns].dropna()

        if X.empty:
            raise ValueError("No data remaining after removing missing values")

        # Scale the data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers[config.type.value] = scaler

        # Determine number of components
        if n_components is None:
            n_components = min(2, X.shape[1])  # Default to 2D for visualization

        # Update hyperparameters
        if config.hyperparameters is None:
            config.hyperparameters = {}

        if config.type == ModelType.PCA:
            config.hyperparameters["n_components"] = n_components
        elif config.type == ModelType.TSNE:
            config.hyperparameters["n_components"] = n_components

        # Create and fit the model
        model = self._create_model_instance(config)

        if config.type == ModelType.PCA:
            transformed_data = model.fit_transform(X_scaled)
        else:  # TSNE
            transformed_data = model.fit_transform(X_scaled)

        # Store the model
        model_key = f"{config.type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.models[model_key] = model

        # Create results
        results = {
            "model_type": config.type.value,
            "model": model,
            "feature_names": config.feature_columns,
            "n_components": n_components,
            "transformed_data": transformed_data,
            "training_date": datetime.now().isoformat(),
            "original_data_shape": X.shape,
            "transformed_data_shape": transformed_data.shape,
        }

        # Add explained variance for PCA
        if config.type == ModelType.PCA:
            results["explained_variance_ratio"] = (
                model.explained_variance_ratio_.tolist()
            )
            results["cumulative_explained_variance"] = np.cumsum(
                model.explained_variance_ratio_
            ).tolist()

        # Save the model
        self._save_model(model_key, results)

        return results

    def get_model_summary(self, model_key: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a trained model."""
        if model_key not in self.models:
            return None

        model = self.models[model_key]

        summary = {
            "model_key": model_key,
            "model_type": type(model).__name__,
            "parameters": model.get_params() if hasattr(model, "get_params") else {},
            "feature_names": getattr(model, "feature_names_in_", []),
            "n_features": getattr(model, "n_features_in_", 0),
        }

        # Add model-specific information
        if hasattr(model, "n_clusters"):
            summary["n_clusters"] = model.n_clusters
        if hasattr(model, "n_components"):
            summary["n_components"] = model.n_components

        return summary

    def list_models(self) -> List[str]:
        """List all available models."""
        return list(self.models.keys())

    def delete_model(self, model_key: str) -> bool:
        """Delete a model."""
        if model_key in self.models:
            del self.models[model_key]

            # Also remove associated scaler and encoders
            for key in list(self.scalers.keys()):
                if model_key in key:
                    del self.scalers[key]

            for key in list(self.label_encoders.keys()):
                if model_key in key:
                    del self.label_encoders[key]

            logger.info(f"Model {model_key} deleted")
            return True
        else:
            logger.warning(f"Model {model_key} not found")
            return False

    def clear_all_models(self) -> None:
        """Clear all models and associated data."""
        self.models.clear()
        self.scalers.clear()
        self.label_encoders.clear()
        logger.info("All models cleared")
