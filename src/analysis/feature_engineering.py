"""
Advanced feature engineering for onsen analysis.

This module provides comprehensive feature transformation, interaction creation,
and aggregation capabilities for sophisticated econometric analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Advanced feature engineering system for onsen visit analysis.

    Provides transformations, interactions, polynomial terms, and aggregations
    to enable comprehensive econometric modeling.
    """

    def __init__(self):
        self.transformations_applied: List[str] = []
        self.interactions_created: List[Tuple[str, str]] = []
        self.polynomials_created: List[Tuple[str, int]] = []
        self.aggregations_created: List[str] = []

    def engineer_features(
        self,
        data: pd.DataFrame,
        include_transformations: bool = True,
        include_interactions: bool = True,
        include_polynomials: bool = True,
        include_temporal: bool = True,
        include_aggregations: bool = True,
        include_heart_rate: bool = True,
        custom_interactions: Optional[List[Tuple[str, str]]] = None,
    ) -> pd.DataFrame:
        """
        Apply comprehensive feature engineering pipeline.

        Args:
            data: Input DataFrame
            include_transformations: Apply log, sqrt, square transformations
            include_interactions: Create pairwise interactions
            include_polynomials: Add quadratic/cubic terms
            include_temporal: Extract temporal features
            include_aggregations: Add onsen-level aggregated statistics
            include_heart_rate: Integrate heart rate metrics
            custom_interactions: Specific variable pairs to interact

        Returns:
            Enhanced DataFrame with engineered features
        """
        logger.info("Starting feature engineering pipeline...")
        df = data.copy()

        if include_transformations:
            df = self.add_transformations(df)

        if include_interactions:
            df = self.add_interactions(df, custom_pairs=custom_interactions)

        if include_polynomials:
            df = self.add_polynomials(df)

        if include_temporal:
            df = self.add_temporal_features(df)

        if include_aggregations:
            df = self.add_aggregated_features(df)

        if include_heart_rate and self._has_heart_rate_data(df):
            df = self.add_heart_rate_features(df)

        logger.info(f"Feature engineering complete. Added {len(df.columns) - len(data.columns)} features")
        return df

    def add_transformations(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add mathematical transformations of numeric variables.

        Applies: log, sqrt, square, cube, inverse transformations
        Useful for addressing non-linearity and heteroskedasticity.
        """
        df = data.copy()

        # Identify numeric columns suitable for transformation
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        # Columns to transform (exclude IDs, binary, and already-transformed vars)
        transform_candidates = []
        for col in numeric_cols:
            if col in ['id', 'onsen_id', 'visit_id', 'ban_number']:
                continue
            if col.startswith('log_') or col.startswith('sqrt_') or col.endswith('_squared'):
                continue
            try:
                if df[col].nunique() > 10:  # Exclude binary/categorical
                    transform_candidates.append(col)
            except (TypeError, ValueError):
                continue

        for col in transform_candidates:
            try:
                # Skip if column has NaN or non-numeric data
                if not pd.api.types.is_numeric_dtype(df[col]) or df[col].isna().all():
                    continue

                # Log transformation (for positive, skewed variables)
                if (df[col].dropna() > 0).all():
                    col_mean = df[col].mean()
                    col_std = df[col].std()
                    if col_mean > 0 and col_std / col_mean > 0.5:
                        df[f'log_{col}'] = np.log(df[col] + 1)  # +1 to handle zeros
                        self.transformations_applied.append(f'log_{col}')

                # Square root (for positive variables)
                if (df[col].dropna() >= 0).all():
                    df[f'sqrt_{col}'] = np.sqrt(df[col])
                    self.transformations_applied.append(f'sqrt_{col}')

                # Square (for capturing quadratic relationships)
                if col in ['entry_fee_yen', 'stay_length_minutes', 'travel_time_minutes',
                           'main_bath_temperature', 'temperature_outside_celsius']:
                    df[f'{col}_squared'] = df[col] ** 2
                    self.transformations_applied.append(f'{col}_squared')

                # Inverse (for diminishing returns effects)
                if (df[col].dropna() > 0).all() and col in ['travel_time_minutes', 'stay_length_minutes']:
                    df[f'inv_{col}'] = 1 / (df[col] + 1)
                    self.transformations_applied.append(f'inv_{col}')
            except (TypeError, ValueError) as e:
                logger.warning(f"Skipping transformation for {col}: {e}")
                continue

        logger.info(f"Applied {len(self.transformations_applied)} transformations")
        return df

    def add_interactions(
        self,
        data: pd.DataFrame,
        custom_pairs: Optional[List[Tuple[str, str]]] = None,
    ) -> pd.DataFrame:
        """
        Create interaction terms between key variables.

        Interactions capture moderation effects (e.g., sauna effect varies by weather).
        """
        df = data.copy()

        # Define key interaction pairs based on domain knowledge
        default_pairs = [
            # Temperature interactions
            ('main_bath_temperature', 'temperature_outside_celsius'),
            ('sauna_temperature', 'temperature_outside_celsius'),
            ('outdoor_bath_temperature', 'temperature_outside_celsius'),

            # Facility interactions
            ('had_sauna', 'weather'),
            ('had_outdoor_bath', 'weather'),
            ('had_sauna', 'main_bath_temperature'),

            # Price-quality interactions
            ('entry_fee_yen', 'cleanliness_rating'),
            ('entry_fee_yen', 'atmosphere_rating'),

            # Time interactions
            ('stay_length_minutes', 'crowd_level'),
            ('stay_length_minutes', 'time_of_day'),

            # Experience interactions
            ('view_rating', 'weather'),
            ('atmosphere_rating', 'crowd_level'),

            # Heart rate (if available)
            ('average_heart_rate', 'main_bath_temperature'),
            ('average_heart_rate', 'stay_length_minutes'),
        ]

        pairs_to_create = custom_pairs if custom_pairs else default_pairs

        for var1, var2 in pairs_to_create:
            if var1 in df.columns and var2 in df.columns:
                # For numeric * numeric
                if pd.api.types.is_numeric_dtype(df[var1]) and pd.api.types.is_numeric_dtype(df[var2]):
                    interaction_name = f'{var1}_X_{var2}'
                    df[interaction_name] = df[var1] * df[var2]
                    self.interactions_created.append((var1, var2))

                # For numeric * categorical (create separate indicators)
                elif pd.api.types.is_numeric_dtype(df[var1]) and not pd.api.types.is_numeric_dtype(df[var2]):
                    categories = df[var2].unique()
                    for category in categories:
                        if pd.notna(category):
                            interaction_name = f'{var1}_X_{var2}_{category}'
                            df[interaction_name] = df[var1] * (df[var2] == category).astype(int)

                # For categorical * categorical (create cross-categories)
                elif not pd.api.types.is_numeric_dtype(df[var1]) and not pd.api.types.is_numeric_dtype(df[var2]):
                    df[f'{var1}_X_{var2}'] = df[var1].astype(str) + '_' + df[var2].astype(str)

        logger.info(f"Created {len(self.interactions_created)} interaction terms")
        return df

    def add_polynomials(
        self,
        data: pd.DataFrame,
        degree: int = 2,
        key_vars: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Add polynomial terms for capturing non-linear relationships.

        Useful for testing U-shaped or inverted-U relationships (e.g., optimal temperature).
        """
        df = data.copy()

        # Default key variables where non-linearity is expected
        default_key_vars = [
            'main_bath_temperature',
            'stay_length_minutes',
            'entry_fee_yen',
            'temperature_outside_celsius',
            'travel_time_minutes',
            'crowd_level',
        ]

        vars_to_poly = key_vars if key_vars else default_key_vars
        vars_to_poly = [v for v in vars_to_poly if v in df.columns]

        for var in vars_to_poly:
            if pd.api.types.is_numeric_dtype(df[var]):
                # Standardize first to avoid numerical issues
                var_std = (df[var] - df[var].mean()) / df[var].std()

                for deg in range(2, degree + 1):
                    poly_name = f'{var}_deg{deg}'
                    df[poly_name] = var_std ** deg
                    self.polynomials_created.append((var, deg))

        logger.info(f"Created {len(self.polynomials_created)} polynomial terms")
        return df

    def add_temporal_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract comprehensive temporal features from visit_time.

        Captures seasonality, day-of-week effects, and trends.
        """
        df = data.copy()

        if 'visit_time' not in df.columns:
            logger.warning("No visit_time column found, skipping temporal features")
            return df

        df['visit_time'] = pd.to_datetime(df['visit_time'])

        # Basic temporal features (some may already exist)
        if 'visit_month' not in df.columns:
            df['visit_month'] = df['visit_time'].dt.month
        if 'visit_year' not in df.columns:
            df['visit_year'] = df['visit_time'].dt.year
        if 'visit_day_of_week' not in df.columns:
            df['visit_day_of_week'] = df['visit_time'].dt.dayofweek
        if 'visit_hour' not in df.columns:
            df['visit_hour'] = df['visit_time'].dt.hour

        # Weekend indicator
        df['is_weekend'] = (df['visit_day_of_week'] >= 5).astype(int)

        # Quarter
        df['visit_quarter'] = df['visit_time'].dt.quarter

        # Season indicators (Japan-specific)
        df['is_winter'] = df['visit_month'].isin([12, 1, 2]).astype(int)
        df['is_spring'] = df['visit_month'].isin([3, 4, 5]).astype(int)
        df['is_summer'] = df['visit_month'].isin([6, 7, 8]).astype(int)
        df['is_autumn'] = df['visit_month'].isin([9, 10, 11]).astype(int)

        # Time of day indicators
        df['is_morning'] = ((df['visit_hour'] >= 6) & (df['visit_hour'] < 12)).astype(int)
        df['is_afternoon'] = ((df['visit_hour'] >= 12) & (df['visit_hour'] < 18)).astype(int)
        df['is_evening'] = ((df['visit_hour'] >= 18) & (df['visit_hour'] < 22)).astype(int)
        df['is_night'] = ((df['visit_hour'] >= 22) | (df['visit_hour'] < 6)).astype(int)

        # Days since first visit (trend)
        if len(df) > 0:
            first_visit = df['visit_time'].min()
            df['days_since_first_visit'] = (df['visit_time'] - first_visit).dt.days

        # Visit count over time (cumulative for panel analysis)
        df = df.sort_values('visit_time')
        df['cumulative_visit_count'] = range(1, len(df) + 1)

        logger.info("Added temporal features")
        return df

    def add_aggregated_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add onsen-level and location-level aggregated statistics.

        Creates features like avg_rating_per_onsen, visit_frequency, etc.
        """
        df = data.copy()

        if 'onsen_id' not in df.columns:
            logger.warning("No onsen_id column found, skipping aggregations")
            return df

        # Build aggregation dict dynamically based on available columns
        agg_dict = {}

        if 'personal_rating' in df.columns:
            agg_dict['personal_rating'] = ['mean', 'std', 'count']

        if 'entry_fee_yen' in df.columns:
            agg_dict['entry_fee_yen'] = ['mean', 'min', 'max']

        if 'stay_length_minutes' in df.columns:
            agg_dict['stay_length_minutes'] = ['mean', 'median']

        if 'cleanliness_rating' in df.columns:
            agg_dict['cleanliness_rating'] = 'mean'

        if 'atmosphere_rating' in df.columns:
            agg_dict['atmosphere_rating'] = 'mean'

        if 'view_rating' in df.columns:
            agg_dict['view_rating'] = 'mean'

        if not agg_dict:
            logger.warning("No suitable columns for aggregation found")
            return df

        # Onsen-level aggregations
        onsen_aggs = df.groupby('onsen_id').agg(agg_dict).reset_index()

        # Flatten column names
        onsen_aggs.columns = ['_'.join(col).strip() if col[1] else col[0]
                               for col in onsen_aggs.columns.values]
        onsen_aggs.columns = [col.replace('onsen_id_', 'onsen_id') for col in onsen_aggs.columns]

        # Rename for clarity
        rename_dict = {
            'personal_rating_mean': 'onsen_avg_rating',
            'personal_rating_std': 'onsen_rating_std',
            'personal_rating_count': 'onsen_visit_count',
            'entry_fee_yen_mean': 'onsen_avg_fee',
            'entry_fee_yen_min': 'onsen_min_fee',
            'entry_fee_yen_max': 'onsen_max_fee',
            'stay_length_minutes_mean': 'onsen_avg_stay',
            'stay_length_minutes_median': 'onsen_median_stay',
            'cleanliness_rating_mean': 'onsen_avg_cleanliness',
            'atmosphere_rating_mean': 'onsen_avg_atmosphere',
            'view_rating_mean': 'onsen_avg_view',
        }
        onsen_aggs = onsen_aggs.rename(columns=rename_dict)

        # Merge back to main data
        df = df.merge(onsen_aggs, on='onsen_id', how='left', suffixes=('', '_agg'))

        # Deviation from onsen average (individual visit quality relative to onsen norm)
        if 'personal_rating' in df.columns and 'onsen_avg_rating' in df.columns:
            df['rating_deviation_from_onsen_avg'] = df['personal_rating'] - df['onsen_avg_rating']

        # Repeat visitor indicator
        df['is_repeat_visitor'] = (df['onsen_visit_count'] > 1).astype(int)

        # Fee relative to onsen average
        if 'entry_fee_yen' in df.columns and 'onsen_avg_fee' in df.columns:
            df['fee_vs_onsen_avg'] = df['entry_fee_yen'] - df['onsen_avg_fee']

        logger.info(f"Added aggregated features at onsen level")
        return df

    def add_heart_rate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Integrate and engineer heart rate features.

        Creates recovery metrics, stress indicators, and HR-based interactions.
        """
        df = data.copy()

        hr_cols = ['average_heart_rate', 'min_heart_rate', 'max_heart_rate',
                   'total_recording_minutes']

        if not any(col in df.columns for col in hr_cols):
            logger.warning("No heart rate data found")
            return df

        # Heart rate variability (simple measure)
        if 'max_heart_rate' in df.columns and 'min_heart_rate' in df.columns:
            df['hr_range'] = df['max_heart_rate'] - df['min_heart_rate']
            df['hr_range_pct'] = (df['hr_range'] / df['average_heart_rate'] * 100).fillna(0)

        # Normalized heart rate (assuming max HR = 220 - age; use 30 as default)
        if 'average_heart_rate' in df.columns:
            assumed_max_hr = 190  # For 30-year-old
            df['hr_pct_max'] = (df['average_heart_rate'] / assumed_max_hr * 100).fillna(0)

            # Relaxation indicator (low HR = relaxed)
            df['is_relaxed_hr'] = (df['average_heart_rate'] < 80).astype(int)
            df['is_elevated_hr'] = (df['average_heart_rate'] > 100).astype(int)

        # Heart rate recovery (if multiple measurements)
        # This would require time-series HR data within a visit
        # For now, create placeholder for future enhancement

        # Interaction: HR × temperature (heat stress)
        if 'average_heart_rate' in df.columns and 'main_bath_temperature' in df.columns:
            df['hr_temp_interaction'] = df['average_heart_rate'] * df['main_bath_temperature']

        logger.info("Added heart rate features")
        return df

    def _has_heart_rate_data(self, data: pd.DataFrame) -> bool:
        """Check if dataset contains heart rate measurements."""
        hr_cols = ['average_heart_rate', 'min_heart_rate', 'max_heart_rate']
        return any(col in data.columns for col in hr_cols)

    def create_rating_bins(
        self,
        data: pd.DataFrame,
        n_bins: int = 3,
    ) -> pd.DataFrame:
        """
        Create categorical bins from continuous rating variables.

        Useful for non-parametric analysis and interaction effects.
        """
        df = data.copy()

        rating_cols = [col for col in df.columns if col.endswith('_rating')]

        for col in rating_cols:
            if pd.api.types.is_numeric_dtype(df[col]):
                bin_col = f'{col}_bin'
                df[bin_col] = pd.qcut(df[col], q=n_bins, labels=['low', 'medium', 'high'],
                                       duplicates='drop')

        return df

    def get_feature_summary(self) -> Dict[str, Any]:
        """
        Get summary of all features created.

        Returns:
            Dictionary with counts and lists of engineered features
        """
        return {
            'transformations': {
                'count': len(self.transformations_applied),
                'features': self.transformations_applied,
            },
            'interactions': {
                'count': len(self.interactions_created),
                'pairs': self.interactions_created,
            },
            'polynomials': {
                'count': len(self.polynomials_created),
                'terms': self.polynomials_created,
            },
            'aggregations': {
                'count': len(self.aggregations_created),
                'features': self.aggregations_created,
            },
        }
