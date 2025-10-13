"""
Professional econometric analysis module for onsen visit data.

Provides comprehensive regression analysis with full diagnostic testing,
following econometric best practices for causal inference and robust estimation.
"""

import pandas as pd
import numpy as np
from typing import Optional, Any
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RegressionResult:
    """Container for regression results with diagnostics."""

    model_name: str
    dependent_var: str
    independent_vars: list[str]
    n_obs: int
    r_squared: float
    adj_r_squared: float
    f_statistic: float
    f_pvalue: float

    # Coefficients
    coefficients: pd.DataFrame  # columns: coef, std_err, t_stat, p_value, ci_lower, ci_upper

    # Diagnostics
    heteroskedasticity_test: dict[str, Any]
    normality_test: dict[str, Any]
    multicollinearity: pd.DataFrame  # VIF scores
    autocorrelation_test: Optional[dict[str, Any]] = None

    # Model comparison metrics
    aic: float = 0.0
    bic: float = 0.0
    log_likelihood: float = 0.0

    # Residuals for plotting
    residuals: Optional[np.ndarray] = None
    fitted_values: Optional[np.ndarray] = None

    # Quality flags
    passes_heteroskedasticity: bool = False
    passes_normality: bool = False
    passes_multicollinearity: bool = False
    overall_quality: str = "unknown"  # excellent, good, acceptable, poor

    # Notes and warnings
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class EconometricAnalyzer:
    """
    Professional econometric analysis engine.

    Provides OLS regression, diagnostic testing, robust standard errors,
    and comprehensive model evaluation following econometric best practices.
    """

    def __init__(self):
        self.models_estimated: list[RegressionResult] = []
        self.significance_level: float = 0.05

    def estimate_ols(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        independent_vars: list[str],
        model_name: str = "OLS Model",
        robust_se: bool = True,
        include_constant: bool = True,
    ) -> RegressionResult:
        """
        Estimate OLS regression with comprehensive diagnostics.

        Args:
            data: DataFrame containing all variables
            dependent_var: Name of dependent variable (typically 'personal_rating')
            independent_vars: List of independent variable names
            model_name: Descriptive name for the model
            robust_se: Use heteroskedasticity-robust standard errors (HC3)
            include_constant: Add intercept term

        Returns:
            RegressionResult object with coefficients and diagnostics
        """
        # Lazy import statsmodels
        import statsmodels.api as sm
        from statsmodels.stats.diagnostic import het_breuschpagan, het_white
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        from statsmodels.stats.stattools import durbin_watson
        import scipy.stats as stats

        logger.info(f"Estimating {model_name}: {dependent_var} ~ {len(independent_vars)} vars")

        # Prepare data
        df = data[[dependent_var] + independent_vars].dropna()

        if len(df) < len(independent_vars) + 10:
            raise ValueError(f"Insufficient observations ({len(df)}) for {len(independent_vars)} variables")

        y = df[dependent_var]
        X = df[independent_vars]

        if include_constant:
            X = sm.add_constant(X)
            var_names = ['const'] + independent_vars
        else:
            var_names = independent_vars

        # Estimate OLS
        model = sm.OLS(y, X)

        if robust_se:
            results = model.fit(cov_type='HC3')  # Heteroskedasticity-robust (White) SEs
        else:
            results = model.fit()

        # Extract coefficients with significance
        coef_df = pd.DataFrame({
            'variable': var_names,
            'coefficient': results.params.values,
            'std_error': results.bse.values,
            't_statistic': results.tvalues.values,
            'p_value': results.pvalues.values,
            'ci_lower': results.conf_int()[0].values,
            'ci_upper': results.conf_int()[1].values,
        })

        # Add significance stars
        coef_df['significance'] = coef_df['p_value'].apply(self._get_significance_stars)

        # Calculate VIF for multicollinearity
        vif_data = self._calculate_vif(X, var_names)

        # Heteroskedasticity test
        het_test = self._test_heteroskedasticity(results, X, y)

        # Normality test
        norm_test = self._test_normality(results.resid)

        # Autocorrelation test (Durbin-Watson)
        dw_stat = durbin_watson(results.resid)
        auto_test = {
            'durbin_watson': dw_stat,
            'interpretation': self._interpret_dw(dw_stat),
        }

        # Quality assessment
        passes_het = het_test['pvalue'] > self.significance_level
        passes_norm = norm_test['pvalue'] > self.significance_level
        passes_multi = (vif_data['VIF'] < 10).all()

        quality = self._assess_model_quality(
            results.rsquared_adj,
            passes_het,
            passes_norm,
            passes_multi,
            len(var_names),
            len(df),
        )

        # Collect warnings
        warnings_list = []
        if not passes_het:
            warnings_list.append(f"Heteroskedasticity detected (p={het_test['pvalue']:.4f}). Using robust SEs.")
        if not passes_norm:
            warnings_list.append(f"Residuals not normal (p={norm_test['pvalue']:.4f}). Inference may be affected.")
        if not passes_multi:
            high_vif = vif_data[vif_data['VIF'] > 10]
            warnings_list.append(f"High multicollinearity detected: {', '.join(high_vif['variable'].tolist())}")

        # Create result object
        result = RegressionResult(
            model_name=model_name,
            dependent_var=dependent_var,
            independent_vars=independent_vars,
            n_obs=int(results.nobs),
            r_squared=results.rsquared,
            adj_r_squared=results.rsquared_adj,
            f_statistic=results.fvalue,
            f_pvalue=results.f_pvalue,
            coefficients=coef_df,
            heteroskedasticity_test=het_test,
            normality_test=norm_test,
            multicollinearity=vif_data,
            autocorrelation_test=auto_test,
            aic=results.aic,
            bic=results.bic,
            log_likelihood=results.llf,
            residuals=results.resid.values,
            fitted_values=results.fittedvalues.values,
            passes_heteroskedasticity=passes_het,
            passes_normality=passes_norm,
            passes_multicollinearity=passes_multi,
            overall_quality=quality,
            warnings=warnings_list,
        )

        self.models_estimated.append(result)
        logger.info(f"Model estimated: R²={result.adj_r_squared:.3f}, Quality={quality}")

        return result

    def estimate_multiple_specifications(
        self,
        data: pd.DataFrame,
        dependent_var: str,
        specifications: dict[str, list[str]],
        robust_se: bool = True,
    ) -> list[RegressionResult]:
        """
        Estimate multiple model specifications for robustness checking.

        Args:
            data: DataFrame with all variables
            dependent_var: Dependent variable name
            specifications: Dict mapping model names to lists of independent variables
            robust_se: Use robust standard errors

        Returns:
            List of RegressionResult objects
        """
        results = []

        for model_name, indep_vars in specifications.items():
            try:
                result = self.estimate_ols(
                    data=data,
                    dependent_var=dependent_var,
                    independent_vars=indep_vars,
                    model_name=model_name,
                    robust_se=robust_se,
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to estimate {model_name}: {e}")
                continue

        return results

    def _calculate_vif(
        self,
        X: pd.DataFrame,
        var_names: list[str],
    ) -> pd.DataFrame:
        """Calculate Variance Inflation Factor for each predictor."""
        from statsmodels.stats.outliers_influence import variance_inflation_factor

        vif_data = pd.DataFrame()
        vif_data['variable'] = var_names
        vif_data['VIF'] = [
            variance_inflation_factor(X.values, i) for i in range(X.shape[1])
        ]

        return vif_data

    def _test_heteroskedasticity(
        self,
        results,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> dict[str, Any]:
        """Test for heteroskedasticity using Breusch-Pagan test."""
        from statsmodels.stats.diagnostic import het_breuschpagan

        try:
            bp_test = het_breuschpagan(results.resid, X)

            return {
                'test': 'Breusch-Pagan',
                'statistic': bp_test[0],
                'pvalue': bp_test[1],
                'f_statistic': bp_test[2],
                'f_pvalue': bp_test[3],
                'null_hypothesis': 'Homoskedasticity',
                'result': 'Homoskedastic' if bp_test[1] > 0.05 else 'Heteroskedastic',
            }
        except Exception as e:
            logger.warning(f"Heteroskedasticity test failed: {e}")
            return {'test': 'Breusch-Pagan', 'error': str(e)}

    def _test_normality(self, residuals: np.ndarray) -> dict[str, Any]:
        """Test residual normality using Jarque-Bera test."""
        import scipy.stats as stats

        jb_stat, jb_pvalue = stats.jarque_bera(residuals)

        return {
            'test': 'Jarque-Bera',
            'statistic': jb_stat,
            'pvalue': jb_pvalue,
            'null_hypothesis': 'Normality',
            'result': 'Normal' if jb_pvalue > 0.05 else 'Non-normal',
        }

    def _get_significance_stars(self, pvalue: float) -> str:
        """Convert p-value to significance stars."""
        if pvalue < 0.001:
            return '***'
        elif pvalue < 0.01:
            return '**'
        elif pvalue < 0.05:
            return '*'
        else:
            return ''

    def _interpret_dw(self, dw_stat: float) -> str:
        """Interpret Durbin-Watson statistic."""
        if dw_stat < 1.5:
            return 'Positive autocorrelation'
        elif dw_stat > 2.5:
            return 'Negative autocorrelation'
        else:
            return 'No autocorrelation'

    def _assess_model_quality(
        self,
        adj_r2: float,
        passes_het: bool,
        passes_norm: bool,
        passes_multi: bool,
        n_vars: int,
        n_obs: int,
    ) -> str:
        """Assess overall model quality based on diagnostics."""

        # Calculate quality score
        score = 0

        # Fit quality
        if adj_r2 > 0.7:
            score += 3
        elif adj_r2 > 0.5:
            score += 2
        elif adj_r2 > 0.3:
            score += 1

        # Diagnostic tests
        if passes_het:
            score += 1
        if passes_norm:
            score += 1
        if passes_multi:
            score += 1

        # Degrees of freedom
        df = n_obs - n_vars - 1
        if df > 30:
            score += 1

        # Classify
        if score >= 7:
            return 'excellent'
        elif score >= 5:
            return 'good'
        elif score >= 3:
            return 'acceptable'
        else:
            return 'poor'

    def format_regression_table(
        self,
        results: list[RegressionResult],
        output_format: str = 'markdown',
    ) -> str:
        """
        Create formatted regression table with multiple models side-by-side.

        Args:
            results: List of RegressionResult objects
            output_format: 'markdown', 'latex', or 'html'

        Returns:
            Formatted table string
        """
        if not results:
            return "No results to format"

        # Collect all unique variables across models
        all_vars = set()
        for result in results:
            all_vars.update(result.coefficients['variable'].tolist())

        all_vars = sorted(all_vars)

        # Build table
        if output_format == 'markdown':
            return self._format_markdown_table(results, all_vars)
        elif output_format == 'html':
            return self._format_html_table(results, all_vars)
        elif output_format == 'latex':
            return self._format_latex_table(results, all_vars)
        else:
            return self._format_markdown_table(results, all_vars)

    def _format_markdown_table(
        self,
        results: list[RegressionResult],
        all_vars: list[str],
    ) -> str:
        """Format as markdown table."""

        table_lines = []

        # Header
        header = "| Variable | " + " | ".join([r.model_name for r in results]) + " |"
        separator = "|----------|" + "|".join(["----------" for _ in results]) + "|"

        table_lines.append(header)
        table_lines.append(separator)

        # Coefficients
        for var in all_vars:
            row = f"| {var} | "

            for result in results:
                var_data = result.coefficients[result.coefficients['variable'] == var]

                if len(var_data) > 0:
                    coef = var_data.iloc[0]['coefficient']
                    se = var_data.iloc[0]['std_error']
                    sig = var_data.iloc[0]['significance']

                    cell = f"{coef:.4f}{sig}<br/>({se:.4f})"
                else:
                    cell = "—"

                row += cell + " | "

            table_lines.append(row)

        # Model statistics
        table_lines.append("|----------|" + "|".join(["----------" for _ in results]) + "|")

        # R-squared
        r2_row = "| R² | " + " | ".join([f"{r.r_squared:.4f}" for r in results]) + " |"
        table_lines.append(r2_row)

        # Adjusted R-squared
        adj_r2_row = "| Adj. R² | " + " | ".join([f"{r.adj_r_squared:.4f}" for r in results]) + " |"
        table_lines.append(adj_r2_row)

        # N
        n_row = "| N | " + " | ".join([str(r.n_obs) for r in results]) + " |"
        table_lines.append(n_row)

        # AIC/BIC
        aic_row = "| AIC | " + " | ".join([f"{r.aic:.2f}" for r in results]) + " |"
        bic_row = "| BIC | " + " | ".join([f"{r.bic:.2f}" for r in results]) + " |"
        table_lines.append(aic_row)
        table_lines.append(bic_row)

        # Footer note
        table_lines.append("")
        table_lines.append("*Note:* Standard errors in parentheses. *** p<0.001, ** p<0.01, * p<0.05")

        return "\n".join(table_lines)

    def _format_html_table(
        self,
        results: list[RegressionResult],
        all_vars: list[str],
    ) -> str:
        """Format as HTML table with styling."""

        html = ['<table class="regression-table" style="border-collapse: collapse; width: 100%;">']

        # Header
        html.append('<thead><tr style="background-color: #f0f0f0;">')
        html.append('<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Variable</th>')
        for result in results:
            html.append(f'<th style="border: 1px solid #ddd; padding: 8px; text-align: center;">{result.model_name}</th>')
        html.append('</tr></thead>')

        # Body
        html.append('<tbody>')

        for i, var in enumerate(all_vars):
            bg_color = '#ffffff' if i % 2 == 0 else '#f9f9f9'
            html.append(f'<tr style="background-color: {bg_color};">')
            html.append(f'<td style="border: 1px solid #ddd; padding: 8px;"><strong>{var}</strong></td>')

            for result in results:
                var_data = result.coefficients[result.coefficients['variable'] == var]

                if len(var_data) > 0:
                    coef = var_data.iloc[0]['coefficient']
                    se = var_data.iloc[0]['std_error']
                    sig = var_data.iloc[0]['significance']

                    cell = f'{coef:.4f}{sig}<br/><span style="font-size: 0.9em; color: #666;">({se:.4f})</span>'
                else:
                    cell = '—'

                html.append(f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{cell}</td>')

            html.append('</tr>')

        # Statistics
        html.append('<tr style="border-top: 2px solid #333;"><td colspan="' + str(len(results) + 1) + '" style="padding: 4px;"></td></tr>')

        # R²
        html.append('<tr><td style="border: 1px solid #ddd; padding: 8px;"><strong>R²</strong></td>')
        for result in results:
            html.append(f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{result.r_squared:.4f}</td>')
        html.append('</tr>')

        # Adj R²
        html.append('<tr><td style="border: 1px solid #ddd; padding: 8px;"><strong>Adj. R²</strong></td>')
        for result in results:
            html.append(f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{result.adj_r_squared:.4f}</td>')
        html.append('</tr>')

        # N
        html.append('<tr><td style="border: 1px solid #ddd; padding: 8px;"><strong>N</strong></td>')
        for result in results:
            html.append(f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{result.n_obs}</td>')
        html.append('</tr>')

        html.append('</tbody>')
        html.append('</table>')

        html.append('<p style="font-size: 0.9em; margin-top: 10px;"><em>Note:</em> Standard errors in parentheses. *** p&lt;0.001, ** p&lt;0.01, * p&lt;0.05</p>')

        return '\n'.join(html)

    def _format_latex_table(self, results: list[RegressionResult], all_vars: list[str]) -> str:
        """Format as LaTeX table."""
        # Placeholder for LaTeX formatting
        return "LaTeX formatting not yet implemented"

    def compare_models(self, results: list[RegressionResult]) -> pd.DataFrame:
        """
        Create model comparison table with fit statistics.

        Returns DataFrame with AIC, BIC, R², Adj R², quality for each model.
        """
        comparison = pd.DataFrame({
            'Model': [r.model_name for r in results],
            'N': [r.n_obs for r in results],
            'R²': [r.r_squared for r in results],
            'Adj. R²': [r.adj_r_squared for r in results],
            'AIC': [r.aic for r in results],
            'BIC': [r.bic for r in results],
            'F-stat': [r.f_statistic for r in results],
            'Quality': [r.overall_quality for r in results],
        })

        # Add rankings
        comparison['AIC_rank'] = comparison['AIC'].rank()
        comparison['BIC_rank'] = comparison['BIC'].rank()
        comparison['Adj_R2_rank'] = comparison['Adj. R²'].rank(ascending=False)

        return comparison.sort_values('Adj. R²', ascending=False)

    def get_significant_effects(
        self,
        result: RegressionResult,
        alpha: float = 0.05,
    ) -> pd.DataFrame:
        """
        Extract variables with statistically significant effects.

        Returns DataFrame with significant coefficients sorted by magnitude.
        """
        sig_effects = result.coefficients[result.coefficients['p_value'] < alpha].copy()
        sig_effects = sig_effects.sort_values('coefficient', key=abs, ascending=False)

        return sig_effects

    def interpret_coefficient(
        self,
        result: RegressionResult,
        variable: str,
    ) -> str:
        """
        Generate plain-language interpretation of a coefficient.

        Returns human-readable string describing the effect.
        """
        coef_data = result.coefficients[result.coefficients['variable'] == variable]

        if len(coef_data) == 0:
            return f"Variable '{variable}' not found in model"

        coef = coef_data.iloc[0]['coefficient']
        pval = coef_data.iloc[0]['p_value']
        se = coef_data.iloc[0]['std_error']
        ci_lower = coef_data.iloc[0]['ci_lower']
        ci_upper = coef_data.iloc[0]['ci_upper']

        direction = "increases" if coef > 0 else "decreases"
        significance = "significantly" if pval < 0.05 else "insignificantly"

        interpretation = (
            f"A one-unit increase in {variable} {significance} {direction} "
            f"{result.dependent_var} by {abs(coef):.4f} units "
            f"(p={pval:.4f}, 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}])."
        )

        return interpretation
