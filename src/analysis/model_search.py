"""
Automated model search and specification testing.

Systematically explores different model specifications to find
the most robust, interpretable, and well-fitting models.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from itertools import combinations

logger = logging.getLogger(__name__)


class ModelSearchEngine:
    """
    Automated model specification search engine.

    Systematically explores:
    - Different variable combinations
    - Polynomial terms
    - Interaction effects
    - Transformations

    Ranks models by quality, robustness, and interpretability.
    """

    def __init__(self, econometric_analyzer):
        """
        Initialize with an EconometricAnalyzer instance.

        Args:
            econometric_analyzer: Instance of EconometricAnalyzer for estimation
        """
        self.analyzer = econometric_analyzer
        self.search_results: List[Any] = []

    def search_models(
        self,
        data: pd.DataFrame,
        dependent_var: str = 'personal_rating',
        max_models: int = 20,
        include_polynomials: bool = True,
        include_interactions: bool = True,
    ) -> List[Any]:
        """
        Automated model search.

        Args:
            data: DataFrame with all variables
            dependent_var: Name of dependent variable
            max_models: Maximum number of models to estimate
            include_polynomials: Test polynomial specifications
            include_interactions: Test interaction specifications

        Returns:
            List of RegressionResult objects, sorted by quality
        """
        logger.info(f"Starting automated model search for {dependent_var}")

        # Define specification levels
        specifications = self._generate_specifications(
            data=data,
            dependent_var=dependent_var,
            include_polynomials=include_polynomials,
            include_interactions=include_interactions,
        )

        # Estimate models
        results = []
        for i, (spec_name, indep_vars) in enumerate(specifications[:max_models], 1):
            try:
                logger.info(f"Estimating model {i}/{min(len(specifications), max_models)}: {spec_name}")

                result = self.analyzer.estimate_ols(
                    data=data,
                    dependent_var=dependent_var,
                    independent_vars=indep_vars,
                    model_name=spec_name,
                    robust_se=True,
                )

                results.append(result)

            except Exception as e:
                logger.warning(f"Failed to estimate {spec_name}: {e}")
                continue

        # Rank models
        ranked_results = self._rank_models(results)

        self.search_results = ranked_results
        logger.info(f"Search complete. Estimated {len(ranked_results)} models")

        return ranked_results

    def _generate_specifications(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        include_polynomials: bool,
        include_interactions: bool,
    ) -> List[Tuple[str, List[str]]]:
        """
        Generate model specifications to test.

        Returns:
            List of (model_name, independent_vars) tuples
        """
        specs = []

        # Define core variable groups based on domain knowledge
        core_quality_vars = [
            'cleanliness_rating',
            'atmosphere_rating',
            'view_rating',
        ]

        facility_vars = [
            'had_sauna',
            'had_outdoor_bath',
            'had_rest_area',
            'had_food_service',
        ]

        physical_vars = [
            'main_bath_temperature',
            'stay_length_minutes',
            'entry_fee_yen',
        ]

        experience_vars = [
            'crowd_level',
            'weather',
            'time_of_day',
        ]

        heart_rate_vars = [col for col in ['average_heart_rate', 'hr_range', 'hr_pct_max']
                           if col in data.columns]

        # Specification 1: Baseline (core quality vars only)
        available_core = [v for v in core_quality_vars if v in data.columns]
        if available_core:
            specs.append(("Baseline: Core Quality", available_core))

        # Specification 2: Core + Physical
        available_physical = [v for v in physical_vars if v in data.columns]
        if available_core and available_physical:
            specs.append(("Core + Physical", available_core + available_physical))

        # Specification 3: Core + Physical + Experience
        available_experience = [v for v in experience_vars if v in data.columns]
        if available_core and available_physical and available_experience:
            specs.append(("Core + Physical + Experience",
                         available_core + available_physical + available_experience))

        # Specification 4: Full model (all main effects)
        available_facility = [v for v in facility_vars if v in data.columns]
        all_vars = (available_core + available_physical +
                    available_experience + available_facility)
        if all_vars:
            specs.append(("Full Model: All Main Effects", all_vars))

        # Specification 5: Add heart rate if available
        if heart_rate_vars and all_vars:
            specs.append(("Full + Heart Rate", all_vars + heart_rate_vars))

        # Add polynomial specifications
        if include_polynomials:
            poly_vars = [col for col in data.columns
                        if col.endswith('_deg2') or col.endswith('_squared')]

            if poly_vars:
                # Core + key polynomials
                key_polys = [v for v in poly_vars
                            if 'main_bath_temperature' in v or 'stay_length' in v]
                if available_core and key_polys:
                    specs.append(("Core + Non-linear Effects",
                                 available_core + available_physical + key_polys))

                # Full + all polynomials
                if all_vars:
                    specs.append(("Full + Polynomials", all_vars + poly_vars))

        # Add interaction specifications
        if include_interactions:
            interaction_vars = [col for col in data.columns if '_X_' in col]

            if interaction_vars:
                # Key interactions
                key_interactions = [v for v in interaction_vars
                                   if ('main_bath_temperature' in v or
                                       'entry_fee_yen' in v or
                                       'cleanliness_rating' in v)]

                if all_vars and key_interactions:
                    specs.append(("Full + Key Interactions",
                                 all_vars + key_interactions[:5]))  # Limit to 5

        # Add transformed variable specifications
        log_vars = [col for col in data.columns if col.startswith('log_')]
        sqrt_vars = [col for col in data.columns if col.startswith('sqrt_')]

        if log_vars:
            # Replace original vars with log versions where available
            transformed = available_core.copy()
            for var in available_physical:
                log_ver = f'log_{var}'
                transformed.append(log_ver if log_ver in log_vars else var)

            specs.append(("Core + Log Transformed", transformed))

        # Add aggregated/derived variable specifications
        agg_vars = [col for col in data.columns
                   if col.startswith('onsen_avg') or col.startswith('onsen_median')]

        if agg_vars and available_core:
            specs.append(("Core + Onsen Aggregates",
                         available_core + agg_vars[:5]))  # Limit to 5

        # Temporal specification
        temporal_vars = [col for col in data.columns
                        if col.startswith('is_') and ('season' in col or 'weekend' in col or 'time' in col)]

        if temporal_vars and all_vars:
            specs.append(("Full + Temporal",
                         all_vars + temporal_vars[:5]))

        logger.info(f"Generated {len(specs)} model specifications")
        return specs

    def _rank_models(self, results: List[Any]) -> List[Any]:
        """
        Rank models by overall quality.

        Ranking criteria:
        1. Adjusted R²
        2. Diagnostic test passes
        3. Parsimony (fewer variables preferred, all else equal)
        4. Statistical significance of key variables

        Returns:
            Sorted list of results (best first)
        """
        if not results:
            return []

        # Calculate quality scores
        scored_results = []

        for result in results:
            score = 0

            # Fit quality (0-40 points)
            adj_r2 = result.adj_r_squared
            if adj_r2 > 0.7:
                score += 40
            elif adj_r2 > 0.5:
                score += 30
            elif adj_r2 > 0.3:
                score += 20
            else:
                score += 10

            # Diagnostic tests (0-30 points, 10 each)
            if result.passes_heteroskedasticity:
                score += 10
            if result.passes_normality:
                score += 10
            if result.passes_multicollinearity:
                score += 10

            # Parsimony bonus (0-10 points)
            # Prefer simpler models, all else equal
            n_vars = len(result.independent_vars)
            if n_vars <= 5:
                score += 10
            elif n_vars <= 10:
                score += 7
            elif n_vars <= 15:
                score += 4
            else:
                score += 2

            # Significance of coefficients (0-20 points)
            # Higher score if more coefficients are significant
            sig_count = (result.coefficients['p_value'] < 0.05).sum()
            total_count = len(result.coefficients)
            sig_pct = sig_count / total_count if total_count > 0 else 0

            score += int(sig_pct * 20)

            scored_results.append((score, result))

        # Sort by score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)

        # Return just the results
        ranked = [result for score, result in scored_results]

        return ranked

    def get_best_models(self, top_n: int = 5) -> List[Any]:
        """
        Get the top N models from search results.

        Args:
            top_n: Number of top models to return

        Returns:
            List of top RegressionResult objects
        """
        if not self.search_results:
            logger.warning("No search results available")
            return []

        return self.search_results[:top_n]

    def get_robust_specifications(self) -> List[Any]:
        """
        Get models that pass all diagnostic tests.

        Returns:
            List of RegressionResult objects that pass all tests
        """
        robust = [
            r for r in self.search_results
            if r.passes_heteroskedasticity and
               r.passes_normality and
               r.passes_multicollinearity
        ]

        logger.info(f"Found {len(robust)} fully robust specifications")
        return robust

    def compare_specifications(self) -> pd.DataFrame:
        """
        Create comparison table of all estimated models.

        Returns:
            DataFrame with model comparison
        """
        if not self.search_results:
            return pd.DataFrame()

        comparison_data = []

        for i, result in enumerate(self.search_results, 1):
            comparison_data.append({
                'Rank': i,
                'Model': result.model_name,
                'N_Vars': len(result.independent_vars),
                'N_Obs': result.n_obs,
                'R²': result.r_squared,
                'Adj_R²': result.adj_r_squared,
                'AIC': result.aic,
                'BIC': result.bic,
                'F_stat': result.f_statistic,
                'F_pval': result.f_pvalue,
                'Het_Test': '✓' if result.passes_heteroskedasticity else '✗',
                'Norm_Test': '✓' if result.passes_normality else '✗',
                'VIF_Test': '✓' if result.passes_multicollinearity else '✗',
                'Quality': result.overall_quality,
            })

        return pd.DataFrame(comparison_data)

    def identify_consistent_effects(
        self,
        variable: str,
        min_models: int = 3,
    ) -> Dict[str, Any]:
        """
        Identify variables with consistent effects across specifications.

        Args:
            variable: Variable name to check
            min_models: Minimum number of models variable must appear in

        Returns:
            Dict with consistency analysis
        """
        appearances = []

        for result in self.search_results:
            coef_data = result.coefficients[
                result.coefficients['variable'] == variable
            ]

            if len(coef_data) > 0:
                row = coef_data.iloc[0]
                appearances.append({
                    'model': result.model_name,
                    'coefficient': row['coefficient'],
                    'p_value': row['p_value'],
                    'significant': row['p_value'] < 0.05,
                })

        if len(appearances) < min_models:
            return {
                'variable': variable,
                'consistent': False,
                'reason': f'Appears in only {len(appearances)} models (< {min_models})',
            }

        # Check for consistency
        coefficients = [a['coefficient'] for a in appearances]
        all_positive = all(c > 0 for c in coefficients)
        all_negative = all(c < 0 for c in coefficients)
        sign_consistent = all_positive or all_negative

        significant_count = sum(1 for a in appearances if a['significant'])
        sig_pct = significant_count / len(appearances)

        return {
            'variable': variable,
            'consistent': sign_consistent and sig_pct >= 0.7,
            'appearances': len(appearances),
            'significant_pct': sig_pct,
            'sign_consistent': sign_consistent,
            'avg_coefficient': np.mean(coefficients),
            'std_coefficient': np.std(coefficients),
            'direction': 'positive' if all_positive else ('negative' if all_negative else 'mixed'),
        }
