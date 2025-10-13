"""
Automated insight discovery system for econometric analysis.

This module automatically detects interesting patterns, surprising findings,
and actionable insights from regression results and exploratory analysis.
"""

import pandas as pd
import numpy as np
from typing import Optional, Any
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class Insight:
    """Container for a single discovered insight."""

    category: str  # 'strong_effect', 'surprising', 'non_linear', 'interaction', 'threshold', 'heart_rate'
    priority: str  # 'high', 'medium', 'low'
    variable: str
    effect_size: float
    p_value: float
    confidence_interval: tuple[float, float]
    interpretation: str
    technical_note: str
    related_variables: list[str] = field(default_factory=list)


class InsightDiscovery:
    """
    Automated insight discovery engine.

    Analyzes regression results and data patterns to automatically
    identify interesting, surprising, or actionable findings.
    """

    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level
        self.insights: list[Insight] = []

    def discover_insights(
        self,
        regression_results: list[Any],  # list[RegressionResult]
        data: pd.DataFrame,
        dependent_var: str = 'personal_rating',
    ) -> list[Insight]:
        """
        Comprehensive insight discovery from regression results and data.

        Args:
            regression_results: List of RegressionResult objects from econometric analysis
            data: Original DataFrame for exploratory insights
            dependent_var: Name of dependent variable

        Returns:
            List of Insight objects, sorted by priority
        """
        logger.info("Starting automated insight discovery...")
        self.insights = []

        for result in regression_results:
            # Strong effects
            self.insights.extend(self._find_strong_effects(result, dependent_var))

            # Surprising findings
            self.insights.extend(self._find_surprising_findings(result, dependent_var))

            # Non-linear relationships
            self.insights.extend(self._find_nonlinear_relationships(result))

            # Interaction effects
            self.insights.extend(self._find_interaction_effects(result))

        # Exploratory insights from data
        if data is not None:
            self.insights.extend(self._find_threshold_effects(data, dependent_var))
            self.insights.extend(self._find_heart_rate_insights(data, dependent_var))
            self.insights.extend(self._find_temporal_patterns(data, dependent_var))

        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        self.insights.sort(key=lambda x: (priority_order[x.priority], -abs(x.effect_size)))

        logger.info(f"Discovered {len(self.insights)} insights")
        return self.insights

    def _find_strong_effects(self, result, dependent_var: str) -> list[Insight]:
        """Identify variables with strong, statistically significant effects."""
        insights = []

        # Get significant coefficients
        sig_coefs = result.coefficients[result.coefficients['p_value'] < self.significance_level]

        for _, row in sig_coefs.iterrows():
            variable = row['variable']
            coef = row['coefficient']
            pval = row['p_value']
            ci = (row['ci_lower'], row['ci_upper'])

            # Skip constant term
            if variable == 'const':
                continue

            # Determine if effect is strong based on magnitude and significance
            is_strong = abs(coef) > 0.3 and pval < 0.01

            if is_strong:
                direction = "increases" if coef > 0 else "decreases"
                significance_desc = "highly significant" if pval < 0.001 else "significant"

                interpretation = (
                    f"Each unit increase in {self._humanize_variable(variable)} "
                    f"{significance_desc} {direction} {dependent_var} by {abs(coef):.3f} points"
                )

                technical_note = (
                    f"β={coef:.4f}, p={pval:.4f}, 95% CI: [{ci[0]:.4f}, {ci[1]:.4f}]"
                )

                insight = Insight(
                    category='strong_effect',
                    priority='high' if pval < 0.001 else 'medium',
                    variable=variable,
                    effect_size=coef,
                    p_value=pval,
                    confidence_interval=ci,
                    interpretation=interpretation,
                    technical_note=technical_note,
                )

                insights.append(insight)

        return insights

    def _find_surprising_findings(self, result, dependent_var: str) -> list[Insight]:
        """Identify counterintuitive or unexpected relationships."""
        insights = []

        # Define expected signs based on domain knowledge
        expected_positive = {
            'cleanliness_rating': 'higher cleanliness should improve ratings',
            'atmosphere_rating': 'better atmosphere should improve ratings',
            'view_rating': 'better views should improve ratings',
            'sauna_rating': 'better sauna should improve ratings',
            'outdoor_bath_rating': 'better outdoor baths should improve ratings',
            'rest_area_rating': 'better rest areas should improve ratings',
        }

        expected_negative = {
            'entry_fee_yen': 'higher fees might reduce satisfaction',
            'travel_time_minutes': 'longer travel might reduce satisfaction',
            'crowd_level': 'crowdedness might reduce satisfaction',
        }

        sig_coefs = result.coefficients[result.coefficients['p_value'] < self.significance_level]

        for _, row in sig_coefs.iterrows():
            variable = row['variable']
            coef = row['coefficient']
            pval = row['p_value']
            ci = (row['ci_lower'], row['ci_upper'])

            # Check if sign contradicts expectations
            is_surprising = False
            reason = ""

            if variable in expected_positive and coef < 0:
                is_surprising = True
                reason = f"Unexpectedly negative: {expected_positive[variable]}"
            elif variable in expected_negative and coef > 0:
                is_surprising = True
                reason = f"Unexpectedly positive: {expected_negative[variable]}"

            if is_surprising:
                interpretation = (
                    f"⚠️ Surprising finding: {self._humanize_variable(variable)} "
                    f"has an unexpected {'positive' if coef > 0 else 'negative'} effect "
                    f"on {dependent_var} (β={coef:.3f}, p={pval:.4f}). "
                    f"This contradicts expectations as {reason.lower()}."
                )

                technical_note = f"β={coef:.4f}, p={pval:.4f}, 95% CI: [{ci[0]:.4f}, {ci[1]:.4f}]"

                insight = Insight(
                    category='surprising',
                    priority='high',
                    variable=variable,
                    effect_size=coef,
                    p_value=pval,
                    confidence_interval=ci,
                    interpretation=interpretation,
                    technical_note=technical_note,
                )

                insights.append(insight)

        return insights

    def _find_nonlinear_relationships(self, result) -> list[Insight]:
        """Detect non-linear (quadratic/cubic) relationships."""
        insights = []

        # Find polynomial terms
        poly_terms = result.coefficients[
            result.coefficients['variable'].str.contains('_deg', na=False)
        ]

        for _, row in poly_terms.iterrows():
            if row['p_value'] < self.significance_level:
                variable = row['variable']
                coef = row['coefficient']
                pval = row['p_value']
                ci = (row['ci_lower'], row['ci_upper'])

                # Extract base variable
                base_var = variable.split('_deg')[0]
                degree = variable.split('_deg')[1] if '_deg' in variable else '2'

                # Interpret quadratic term
                if degree == '2':
                    if coef < 0:
                        shape = "inverted-U (diminishing returns)"
                        implication = "suggesting an optimal level exists"
                    else:
                        shape = "U-shaped (increasing returns)"
                        implication = "suggesting accelerating effects"

                    interpretation = (
                        f"Non-linear relationship detected for {self._humanize_variable(base_var)}: "
                        f"{shape}, {implication} (β={coef:.4f}, p={pval:.4f})"
                    )

                    technical_note = f"Quadratic term: β={coef:.4f}, p={pval:.4f}"

                    insight = Insight(
                        category='non_linear',
                        priority='high' if pval < 0.01 else 'medium',
                        variable=base_var,
                        effect_size=coef,
                        p_value=pval,
                        confidence_interval=ci,
                        interpretation=interpretation,
                        technical_note=technical_note,
                    )

                    insights.append(insight)

        return insights

    def _find_interaction_effects(self, result) -> list[Insight]:
        """Identify significant interaction/moderation effects."""
        insights = []

        # Find interaction terms (contain '_X_')
        interaction_terms = result.coefficients[
            result.coefficients['variable'].str.contains('_X_', na=False)
        ]

        for _, row in interaction_terms.iterrows():
            if row['p_value'] < self.significance_level:
                variable = row['variable']
                coef = row['coefficient']
                pval = row['p_value']
                ci = (row['ci_lower'], row['ci_upper'])

                # Extract interacting variables
                parts = variable.split('_X_')
                if len(parts) == 2:
                    var1, var2 = parts

                    direction = "strengthens" if coef > 0 else "weakens"

                    interpretation = (
                        f"Interaction effect: The effect of {self._humanize_variable(var1)} "
                        f"{direction} when {self._humanize_variable(var2)} is higher "
                        f"(interaction coefficient: β={coef:.3f}, p={pval:.4f})"
                    )

                    technical_note = f"Interaction β={coef:.4f}, p={pval:.4f}"

                    insight = Insight(
                        category='interaction',
                        priority='high' if pval < 0.01 else 'medium',
                        variable=variable,
                        effect_size=coef,
                        p_value=pval,
                        confidence_interval=ci,
                        interpretation=interpretation,
                        technical_note=technical_note,
                        related_variables=[var1, var2],
                    )

                    insights.append(insight)

        return insights

    def _find_threshold_effects(self, data: pd.DataFrame, dependent_var: str) -> list[Insight]:
        """Identify threshold effects using binned analysis."""
        insights = []

        if dependent_var not in data.columns:
            return insights

        # Check common threshold candidates
        threshold_vars = {
            'stay_length_minutes': [30, 45, 60],
            'entry_fee_yen': [300, 500, 1000],
            'main_bath_temperature': [40, 42, 44],
            'temperature_outside_celsius': [10, 15, 25],
        }

        for var, thresholds in threshold_vars.items():
            if var not in data.columns:
                continue

            valid_data = data[[var, dependent_var]].dropna()

            for threshold in thresholds:
                below = valid_data[valid_data[var] <= threshold][dependent_var]
                above = valid_data[valid_data[var] > threshold][dependent_var]

                if len(below) > 10 and len(above) > 10:
                    # T-test for difference
                    from scipy import stats
                    t_stat, p_val = stats.ttest_ind(below, above)

                    if p_val < self.significance_level:
                        diff = above.mean() - below.mean()

                        interpretation = (
                            f"Threshold effect at {threshold} for {self._humanize_variable(var)}: "
                            f"ratings {'increase' if diff > 0 else 'decrease'} by {abs(diff):.2f} points "
                            f"above this threshold (t={t_stat:.2f}, p={p_val:.4f})"
                        )

                        technical_note = f"Below: μ={below.mean():.2f}, Above: μ={above.mean():.2f}, t={t_stat:.2f}"

                        insight = Insight(
                            category='threshold',
                            priority='medium',
                            variable=var,
                            effect_size=diff,
                            p_value=p_val,
                            confidence_interval=(diff - 1.96 * below.std(), diff + 1.96 * below.std()),
                            interpretation=interpretation,
                            technical_note=technical_note,
                        )

                        insights.append(insight)
                        break  # Only report one threshold per variable

        return insights

    def _find_heart_rate_insights(self, data: pd.DataFrame, dependent_var: str) -> list[Insight]:
        """Discover insights related to heart rate data."""
        insights = []

        hr_vars = ['average_heart_rate', 'hr_range', 'hr_pct_max']

        for hr_var in hr_vars:
            if hr_var in data.columns and dependent_var in data.columns:
                valid_data = data[[hr_var, dependent_var]].dropna()

                if len(valid_data) > 30:
                    # Correlation analysis
                    corr = valid_data[hr_var].corr(valid_data[dependent_var])

                    # Simple significance test
                    n = len(valid_data)
                    t_stat = corr * np.sqrt(n - 2) / np.sqrt(1 - corr**2)
                    from scipy import stats
                    p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))

                    if p_val < self.significance_level and abs(corr) > 0.2:
                        direction = "positively" if corr > 0 else "negatively"
                        strength = "strongly" if abs(corr) > 0.5 else "moderately"

                        interpretation = (
                            f"Heart rate finding: {self._humanize_variable(hr_var)} is "
                            f"{strength} {direction} correlated with {dependent_var} "
                            f"(r={corr:.3f}, p={p_val:.4f}). "
                            f"{'Lower' if corr < 0 else 'Higher'} heart rate associated with better ratings."
                        )

                        technical_note = f"Correlation: r={corr:.4f}, n={n}, p={p_val:.4f}"

                        insight = Insight(
                            category='heart_rate',
                            priority='high' if abs(corr) > 0.4 else 'medium',
                            variable=hr_var,
                            effect_size=corr,
                            p_value=p_val,
                            confidence_interval=(corr - 0.2, corr + 0.2),  # Approximate
                            interpretation=interpretation,
                            technical_note=technical_note,
                        )

                        insights.append(insight)

        return insights

    def _find_temporal_patterns(self, data: pd.DataFrame, dependent_var: str) -> list[Insight]:
        """Discover temporal patterns (seasonality, day-of-week effects)."""
        insights = []

        # Season effects
        if 'visit_season' in data.columns and dependent_var in data.columns:
            season_means = data.groupby('visit_season')[dependent_var].agg(['mean', 'count'])

            if (season_means['count'] > 5).all():
                best_season = season_means['mean'].idxmax()
                worst_season = season_means['mean'].idxmin()
                diff = season_means.loc[best_season, 'mean'] - season_means.loc[worst_season, 'mean']

                # ANOVA test
                from scipy import stats
                groups = [data[data['visit_season'] == season][dependent_var].dropna()
                          for season in season_means.index]
                f_stat, p_val = stats.f_oneway(*groups)

                if p_val < self.significance_level and diff > 0.3:
                    interpretation = (
                        f"Seasonal pattern: Visits during {best_season} rated {diff:.2f} points higher "
                        f"than {worst_season} (F={f_stat:.2f}, p={p_val:.4f})"
                    )

                    technical_note = f"Best: {best_season} (μ={season_means.loc[best_season, 'mean']:.2f})"

                    insight = Insight(
                        category='temporal',
                        priority='medium',
                        variable='visit_season',
                        effect_size=diff,
                        p_value=p_val,
                        confidence_interval=(diff - 0.5, diff + 0.5),
                        interpretation=interpretation,
                        technical_note=technical_note,
                    )

                    insights.append(insight)

        # Weekend vs weekday
        if 'is_weekend' in data.columns and dependent_var in data.columns:
            weekend_data = data[data['is_weekend'] == 1][dependent_var].dropna()
            weekday_data = data[data['is_weekend'] == 0][dependent_var].dropna()

            if len(weekend_data) > 10 and len(weekday_data) > 10:
                from scipy import stats
                t_stat, p_val = stats.ttest_ind(weekend_data, weekday_data)
                diff = weekend_data.mean() - weekday_data.mean()

                if p_val < self.significance_level and abs(diff) > 0.3:
                    which_better = "weekend" if diff > 0 else "weekday"

                    interpretation = (
                        f"Day-of-week effect: {which_better.capitalize()} visits rated "
                        f"{abs(diff):.2f} points higher (t={t_stat:.2f}, p={p_val:.4f})"
                    )

                    technical_note = f"Weekend: μ={weekend_data.mean():.2f}, Weekday: μ={weekday_data.mean():.2f}"

                    insight = Insight(
                        category='temporal',
                        priority='medium',
                        variable='is_weekend',
                        effect_size=diff,
                        p_value=p_val,
                        confidence_interval=(diff - 0.5, diff + 0.5),
                        interpretation=interpretation,
                        technical_note=technical_note,
                    )

                    insights.append(insight)

        return insights

    def _humanize_variable(self, var_name: str) -> str:
        """Convert variable name to human-readable form."""
        # Remove common prefixes/suffixes
        var_name = var_name.replace('_deg2', '').replace('_deg3', '')
        var_name = var_name.replace('log_', 'log(').replace('sqrt_', 'sqrt(')

        if var_name.startswith('sqrt('):
            var_name += ')'
        elif var_name.startswith('log('):
            var_name += ')'

        # Replace underscores with spaces and title case
        var_name = var_name.replace('_', ' ').title()

        return var_name

    def generate_executive_summary(self, top_n: int = 7) -> str:
        """
        Generate executive summary with top N insights.

        Returns formatted text suitable for report inclusion.
        """
        if not self.insights:
            return "No significant insights discovered."

        summary_lines = ["# Key Findings\n"]

        for i, insight in enumerate(self.insights[:top_n], 1):
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            emoji = priority_emoji.get(insight.priority, '')

            summary_lines.append(f"{i}. {emoji} **{insight.interpretation}**")

        summary_lines.append(f"\n*Based on analysis of {len(self.insights)} discovered patterns.*")

        return "\n".join(summary_lines)
