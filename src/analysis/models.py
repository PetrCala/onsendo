"""
Modeling system for onsen analysis - clustering and dimensionality reduction only.

Note: Regression analysis is handled by src/analysis/econometrics.py
"""

from typing import Optional, Any
from datetime import datetime
from pathlib import Path
import warnings

import pandas as pd
import numpy as np
from loguru import logger

from src.types.analysis import ModelType, ModelConfig

warnings.filterwarnings("ignore")


class ModelEngine:
    """
    Engine for clustering and dimensionality reduction models.

    For regression analysis, use EconometricAnalyzer from src.analysis.econometrics
    """

    def __init__(self, save_dir: Optional[str] = None):
        self.save_dir = Path(save_dir) if save_dir else Path("output/models")
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.models: dict[str, Any] = {}
        self.scalers: dict[str, Any] = {}

    def create_clustering_model(
        self, data: pd.DataFrame, config: ModelConfig, n_clusters: Optional[int] = None
    ) -> dict[str, Any]:
        """Create a clustering model."""
        if config.type not in [ModelType.KMEANS, ModelType.DBSCAN]:
            raise ValueError(f"Model type {config.type} is not a clustering model")

        # pylint: disable=import-outside-toplevel
        # Lazy import for optional heavy dependency - improves startup time
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import silhouette_score

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
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Broad exception justified: silhouette score calculation may fail for various reasons
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

        return results

    def create_dimensionality_reduction_model(
        self,
        data: pd.DataFrame,
        config: ModelConfig,
        n_components: Optional[int] = None,
    ) -> dict[str, Any]:
        """Create a dimensionality reduction model."""
        if config.type not in [ModelType.PCA, ModelType.TSNE]:
            raise ValueError(
                f"Model type {config.type} is not a dimensionality reduction model"
            )

        # pylint: disable=import-outside-toplevel
        # Lazy import for optional heavy dependency - improves startup time
        from sklearn.preprocessing import StandardScaler

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

        return results

    def _create_model_instance(self, config: ModelConfig) -> Any:
        # pylint: disable=import-outside-toplevel
        # Lazy import for optional heavy dependency - improves startup time
        """Create a model instance based on the configuration."""
        if config.type == ModelType.KMEANS:
            from sklearn.cluster import KMeans

            return KMeans(**config.hyperparameters or {})
        if config.type == ModelType.DBSCAN:
            from sklearn.cluster import DBSCAN

            return DBSCAN(**config.hyperparameters or {})
        if config.type == ModelType.PCA:
            from sklearn.decomposition import PCA

            return PCA(**config.hyperparameters or {})
        if config.type == ModelType.TSNE:
            from sklearn.manifold import TSNE

            return TSNE(**config.hyperparameters or {})
        raise ValueError(f"Unsupported model type: {config.type}")

    def _find_optimal_clusters(self, X: np.ndarray, max_clusters: int = 10) -> int:
        # pylint: disable=import-outside-toplevel
        # Lazy import for optional heavy dependency - improves startup time
        """Find optimal number of clusters using elbow method."""
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score

        silhouette_scores = []
        K_range = range(2, min(max_clusters + 1, X.shape[0]))

        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)

            try:
                score = silhouette_score(X, kmeans.labels_)
                silhouette_scores.append(score)
            except Exception:  # pylint: disable=broad-exception-caught
                # Broad exception justified: silhouette score calculation may fail
                silhouette_scores.append(0)

        # Return k with highest silhouette score
        if silhouette_scores:
            return K_range[np.argmax(silhouette_scores)]
        return 3  # Default fallback

    def get_model_summary(self, model_key: str) -> Optional[dict[str, Any]]:
        """Get a summary of a trained model."""
        if model_key not in self.models:
            return None

        model = self.models[model_key]

        summary = {
            "model_key": model_key,
            "model_type": type(model).__name__,
            "parameters": model.get_params() if hasattr(model, "get_params") else {},
        }

        # Add model-specific information
        if hasattr(model, "n_clusters"):
            summary["n_clusters"] = model.n_clusters
        if hasattr(model, "n_components"):
            summary["n_components"] = model.n_components

        return summary

    def list_models(self) -> list[str]:
        """List all available models."""
        return list(self.models.keys())

    def delete_model(self, model_key: str) -> bool:
        """Delete a model."""
        if model_key in self.models:
            del self.models[model_key]

            # Also remove associated scaler
            if model_key in self.scalers:
                del self.scalers[model_key]

            logger.info(f"Model {model_key} deleted")
            return True
        logger.warning(f"Model {model_key} not found")
        return False

    def clear_all_models(self) -> None:
        """Clear all models and associated data."""
        self.models.clear()
        self.scalers.clear()
        logger.info("All models cleared")
