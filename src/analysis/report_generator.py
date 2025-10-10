"""
Professional report generation for econometric analysis results.

Creates publication-quality HTML and Markdown reports with embedded
visualizations, regression tables, diagnostics, and insights.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import logging
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Professional report generator for analysis results.

    Creates formatted HTML reports with:
    - Executive summary with key insights
    - Regression tables with significance stars
    - Diagnostic test results
    - Embedded visualizations
    - Model comparison tables
    - Technical appendix
    """

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(
        self,
        regression_results: List[Any],  # List[RegressionResult]
        insights: List[Any],  # List[Insight]
        visualizations: Dict[str, Any],
        data_summary: Dict[str, Any],
        analysis_name: str = "Econometric Analysis",
    ) -> Path:
        """
        Generate comprehensive HTML report.

        Args:
            regression_results: List of RegressionResult objects
            insights: List of Insight objects from discovery
            visualizations: Dict mapping viz names to figure objects
            data_summary: Summary statistics about the dataset
            analysis_name: Title for the report

        Returns:
            Path to generated HTML file
        """
        logger.info(f"Generating HTML report: {analysis_name}")

        # Build HTML content
        html_parts = []

        # Header and styling
        html_parts.append(self._generate_html_header(analysis_name))

        # Executive Summary
        html_parts.append(self._generate_executive_summary(insights))

        # Data Overview
        html_parts.append(self._generate_data_overview(data_summary))

        # Key Findings (Insights)
        html_parts.append(self._generate_insights_section(insights))

        # Regression Results
        html_parts.append(self._generate_regression_section(regression_results))

        # Model Diagnostics
        html_parts.append(self._generate_diagnostics_section(regression_results))

        # Visualizations
        if visualizations:
            html_parts.append(self._generate_visualizations_section(visualizations))

        # Model Comparison
        if len(regression_results) > 1:
            html_parts.append(self._generate_model_comparison(regression_results))

        # Technical Appendix
        html_parts.append(self._generate_technical_appendix(regression_results))

        # Footer
        html_parts.append(self._generate_html_footer())

        # Combine and save
        html_content = "\n".join(html_parts)
        report_path = self.output_dir / "analysis_report.html"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Report saved to: {report_path}")
        return report_path

    def _generate_html_header(self, title: str) -> str:
        """Generate HTML header with styling."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
        }}
        .executive-summary {{
            background-color: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
        }}
        .insight {{
            background-color: #f9f9f9;
            border-left: 4px solid #2ecc71;
            padding: 12px;
            margin: 10px 0;
        }}
        .insight.high-priority {{
            border-left-color: #e74c3c;
        }}
        .insight.medium-priority {{
            border-left-color: #f39c12;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #34495e;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .coefficient-table th {{
            background-color: #2c3e50;
        }}
        .diagnostic-pass {{
            color: #27ae60;
            font-weight: bold;
        }}
        .diagnostic-fail {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .stat-box {{
            display: inline-block;
            background-color: #ecf0f1;
            padding: 10px 15px;
            margin: 5px;
            border-radius: 5px;
        }}
        .stat-label {{
            font-size: 0.9em;
            color: #7f8c8d;
        }}
        .stat-value {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .visualization {{
            margin: 20px 0;
            text-align: center;
        }}
        .visualization img {{
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px;
        }}
        .technical-note {{
            font-size: 0.9em;
            color: #7f8c8d;
            font-style: italic;
        }}
        .warning {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 0.9em;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 {title}</h1>
        <p><em>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
"""

    def _generate_executive_summary(self, insights: List[Any]) -> str:
        """Generate executive summary section."""
        html = ['<div class="executive-summary">']
        html.append('<h2>Executive Summary</h2>')

        if not insights:
            html.append('<p>No significant insights were automatically discovered.</p>')
        else:
            high_priority = [i for i in insights if i.priority == 'high'][:5]

            if high_priority:
                html.append('<p><strong>Key Findings:</strong></p>')
                html.append('<ul>')
                for insight in high_priority:
                    html.append(f'<li>{insight.interpretation}</li>')
                html.append('</ul>')

        html.append('</div>')
        return '\n'.join(html)

    def _generate_data_overview(self, data_summary: Dict[str, Any]) -> str:
        """Generate data overview section."""
        html = ['<h2>📈 Data Overview</h2>']

        if data_summary:
            html.append('<div>')

            # Key statistics
            if 'n_observations' in data_summary:
                html.append(f'<div class="stat-box">')
                html.append(f'<div class="stat-label">Observations</div>')
                html.append(f'<div class="stat-value">{data_summary["n_observations"]}</div>')
                html.append('</div>')

            if 'n_variables' in data_summary:
                html.append(f'<div class="stat-box">')
                html.append(f'<div class="stat-label">Variables</div>')
                html.append(f'<div class="stat-value">{data_summary["n_variables"]}</div>')
                html.append('</div>')

            if 'date_range' in data_summary:
                html.append(f'<div class="stat-box">')
                html.append(f'<div class="stat-label">Date Range</div>')
                html.append(f'<div class="stat-value">{data_summary["date_range"]}</div>')
                html.append('</div>')

            html.append('</div>')

        return '\n'.join(html)

    def _generate_insights_section(self, insights: List[Any]) -> str:
        """Generate insights section."""
        html = ['<h2>🔍 Key Insights</h2>']

        if not insights:
            html.append('<p>No insights discovered.</p>')
            return '\n'.join(html)

        # Group by category
        categories = {}
        for insight in insights:
            if insight.category not in categories:
                categories[insight.category] = []
            categories[insight.category].append(insight)

        category_names = {
            'strong_effect': '💪 Strong Effects',
            'surprising': '⚠️ Surprising Findings',
            'non_linear': '📉 Non-Linear Relationships',
            'interaction': '🔗 Interaction Effects',
            'threshold': '📊 Threshold Effects',
            'heart_rate': '❤️ Heart Rate Insights',
            'temporal': '⏰ Temporal Patterns',
        }

        for category, category_insights in categories.items():
            html.append(f'<h3>{category_names.get(category, category.title())}</h3>')

            for insight in category_insights[:5]:  # Limit to top 5 per category
                priority_class = f"{insight.priority}-priority"
                html.append(f'<div class="insight {priority_class}">')
                html.append(f'<p><strong>{insight.interpretation}</strong></p>')
                html.append(f'<p class="technical-note">{insight.technical_note}</p>')
                html.append('</div>')

        return '\n'.join(html)

    def _generate_regression_section(self, results: List[Any]) -> str:
        """Generate regression results section."""
        html = ['<h2>📊 Regression Analysis</h2>']

        for i, result in enumerate(results, 1):
            html.append(f'<h3>Model {i}: {result.model_name}</h3>')

            # Model statistics
            html.append('<div>')
            html.append(f'<div class="stat-box">')
            html.append(f'<div class="stat-label">R²</div>')
            html.append(f'<div class="stat-value">{result.r_squared:.4f}</div>')
            html.append('</div>')

            html.append(f'<div class="stat-box">')
            html.append(f'<div class="stat-label">Adj. R²</div>')
            html.append(f'<div class="stat-value">{result.adj_r_squared:.4f}</div>')
            html.append('</div>')

            html.append(f'<div class="stat-box">')
            html.append(f'<div class="stat-label">F-statistic</div>')
            html.append(f'<div class="stat-value">{result.f_statistic:.2f}</div>')
            html.append('</div>')

            html.append(f'<div class="stat-box">')
            html.append(f'<div class="stat-label">N</div>')
            html.append(f'<div class="stat-value">{result.n_obs}</div>')
            html.append('</div>')
            html.append('</div>')

            # Coefficient table
            html.append('<table class="coefficient-table">')
            html.append('<thead>')
            html.append('<tr>')
            html.append('<th>Variable</th>')
            html.append('<th>Coefficient</th>')
            html.append('<th>Std. Error</th>')
            html.append('<th>t-statistic</th>')
            html.append('<th>p-value</th>')
            html.append('<th>95% CI</th>')
            html.append('</tr>')
            html.append('</thead>')
            html.append('<tbody>')

            for _, row in result.coefficients.iterrows():
                html.append('<tr>')
                html.append(f'<td><strong>{row["variable"]}</strong></td>')
                html.append(f'<td>{row["coefficient"]:.4f}{row["significance"]}</td>')
                html.append(f'<td>{row["std_error"]:.4f}</td>')
                html.append(f'<td>{row["t_statistic"]:.3f}</td>')
                html.append(f'<td>{row["p_value"]:.4f}</td>')
                html.append(f'<td>[{row["ci_lower"]:.4f}, {row["ci_upper"]:.4f}]</td>')
                html.append('</tr>')

            html.append('</tbody>')
            html.append('</table>')
            html.append('<p class="technical-note">*** p&lt;0.001, ** p&lt;0.01, * p&lt;0.05</p>')

            # Warnings
            if result.warnings:
                html.append('<div class="warning">')
                html.append('<strong>⚠️ Warnings:</strong>')
                html.append('<ul>')
                for warning in result.warnings:
                    html.append(f'<li>{warning}</li>')
                html.append('</ul>')
                html.append('</div>')

        return '\n'.join(html)

    def _generate_diagnostics_section(self, results: List[Any]) -> str:
        """Generate diagnostics section."""
        html = ['<h2>🔬 Model Diagnostics</h2>']

        for i, result in enumerate(results, 1):
            html.append(f'<h3>Model {i}: {result.model_name}</h3>')

            # Diagnostic tests table
            html.append('<table>')
            html.append('<thead>')
            html.append('<tr><th>Test</th><th>Statistic</th><th>p-value</th><th>Result</th></tr>')
            html.append('</thead>')
            html.append('<tbody>')

            # Heteroskedasticity
            het_test = result.heteroskedasticity_test
            het_class = "diagnostic-pass" if result.passes_heteroskedasticity else "diagnostic-fail"
            html.append('<tr>')
            html.append(f'<td>{het_test.get("test", "Heteroskedasticity")}</td>')
            html.append(f'<td>{het_test.get("statistic", 0):.3f}</td>')
            html.append(f'<td>{het_test.get("pvalue", 0):.4f}</td>')
            html.append(f'<td class="{het_class}">{het_test.get("result", "Unknown")}</td>')
            html.append('</tr>')

            # Normality
            norm_test = result.normality_test
            norm_class = "diagnostic-pass" if result.passes_normality else "diagnostic-fail"
            html.append('<tr>')
            html.append(f'<td>{norm_test.get("test", "Normality")}</td>')
            html.append(f'<td>{norm_test.get("statistic", 0):.3f}</td>')
            html.append(f'<td>{norm_test.get("pvalue", 0):.4f}</td>')
            html.append(f'<td class="{norm_class}">{norm_test.get("result", "Unknown")}</td>')
            html.append('</tr>')

            # Autocorrelation
            if result.autocorrelation_test:
                auto_test = result.autocorrelation_test
                html.append('<tr>')
                html.append('<td>Durbin-Watson</td>')
                html.append(f'<td>{auto_test.get("durbin_watson", 0):.3f}</td>')
                html.append('<td>N/A</td>')
                html.append(f'<td>{auto_test.get("interpretation", "Unknown")}</td>')
                html.append('</tr>')

            html.append('</tbody>')
            html.append('</table>')

            # Multicollinearity (VIF)
            html.append('<h4>Variance Inflation Factors (VIF)</h4>')
            vif_data = result.multicollinearity

            html.append('<table>')
            html.append('<thead><tr><th>Variable</th><th>VIF</th><th>Status</th></tr></thead>')
            html.append('<tbody>')

            for _, row in vif_data.iterrows():
                vif = row['VIF']
                status_class = "diagnostic-pass" if vif < 10 else "diagnostic-fail"
                status = "✓ OK" if vif < 10 else "⚠ High"
                html.append(f'<tr>')
                html.append(f'<td>{row["variable"]}</td>')
                html.append(f'<td>{vif:.2f}</td>')
                html.append(f'<td class="{status_class}">{status}</td>')
                html.append('</tr>')

            html.append('</tbody>')
            html.append('</table>')

            # Overall quality
            quality_emoji = {'excellent': '🟢', 'good': '🟡', 'acceptable': '🟠', 'poor': '🔴'}
            html.append(f'<p><strong>Overall Quality:</strong> {quality_emoji.get(result.overall_quality, "")} {result.overall_quality.upper()}</p>')

        return '\n'.join(html)

    def _generate_visualizations_section(self, visualizations: Dict[str, Any]) -> str:
        """Generate visualizations section."""
        html = ['<h2>📈 Visualizations</h2>']

        for viz_name, viz_data in visualizations.items():
            html.append(f'<h3>{viz_name.replace("_", " ").title()}</h3>')
            html.append(f'<div class="visualization">')

            # Check if visualization has a save path
            if isinstance(viz_data, dict) and 'config' in viz_data:
                save_path = viz_data['config'].save_path
                if save_path and Path(save_path).exists():
                    # For HTML visualizations (maps)
                    if save_path.endswith('.html'):
                        html.append(f'<p><a href="{save_path}" target="_blank">Open Interactive Visualization →</a></p>')
                    # For image visualizations
                    else:
                        html.append(f'<img src="{save_path}" alt="{viz_name}">')

            html.append('</div>')

        return '\n'.join(html)

    def _generate_model_comparison(self, results: List[Any]) -> str:
        """Generate model comparison table."""
        html = ['<h2>🔄 Model Comparison</h2>']

        html.append('<table>')
        html.append('<thead>')
        html.append('<tr>')
        html.append('<th>Model</th>')
        html.append('<th>R²</th>')
        html.append('<th>Adj. R²</th>')
        html.append('<th>AIC</th>')
        html.append('<th>BIC</th>')
        html.append('<th>N</th>')
        html.append('<th>Quality</th>')
        html.append('</tr>')
        html.append('</thead>')
        html.append('<tbody>')

        for result in results:
            html.append('<tr>')
            html.append(f'<td>{result.model_name}</td>')
            html.append(f'<td>{result.r_squared:.4f}</td>')
            html.append(f'<td>{result.adj_r_squared:.4f}</td>')
            html.append(f'<td>{result.aic:.2f}</td>')
            html.append(f'<td>{result.bic:.2f}</td>')
            html.append(f'<td>{result.n_obs}</td>')
            html.append(f'<td>{result.overall_quality}</td>')
            html.append('</tr>')

        html.append('</tbody>')
        html.append('</table>')

        # Highlight best model
        if results:
            best_model = max(results, key=lambda r: r.adj_r_squared)
            html.append(f'<p><strong>Best model by Adj. R²:</strong> {best_model.model_name} (Adj. R² = {best_model.adj_r_squared:.4f})</p>')

        return '\n'.join(html)

    def _generate_technical_appendix(self, results: List[Any]) -> str:
        """Generate technical appendix."""
        html = ['<h2>📚 Technical Appendix</h2>']

        html.append('<h3>Methodology</h3>')
        html.append('<p>All regression models were estimated using Ordinary Least Squares (OLS) with heteroskedasticity-robust standard errors (HC3). ')
        html.append('Diagnostic tests include the Breusch-Pagan test for heteroskedasticity, Jarque-Bera test for normality, ')
        html.append('and Variance Inflation Factors (VIF) for multicollinearity detection. ')
        html.append('Statistical significance is denoted as: *** p&lt;0.001, ** p&lt;0.01, * p&lt;0.05.</p>')

        html.append('<h3>Model Specifications</h3>')
        html.append('<ul>')
        for i, result in enumerate(results, 1):
            html.append(f'<li><strong>Model {i}:</strong> {result.dependent_var} ~ {len(result.independent_vars)} variables</li>')
        html.append('</ul>')

        return '\n'.join(html)

    def _generate_html_footer(self) -> str:
        """Generate HTML footer."""
        return """
    <div class="footer">
        <p>Generated by Onsendo Analysis System</p>
        <p>For questions or issues, please refer to the documentation.</p>
    </div>
    </div>
</body>
</html>
"""

    def generate_markdown_summary(
        self,
        regression_results: List[Any],
        insights: List[Any],
    ) -> Path:
        """
        Generate concise Markdown summary.

        Returns:
            Path to generated Markdown file
        """
        md_lines = []

        md_lines.append("# Analysis Summary\n")
        md_lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

        # Executive Summary
        md_lines.append("## Executive Summary\n")
        if insights:
            for i, insight in enumerate(insights[:7], 1):
                md_lines.append(f"{i}. {insight.interpretation}")
        md_lines.append("")

        # Key Results
        md_lines.append("## Key Results\n")
        for result in regression_results:
            md_lines.append(f"### {result.model_name}")
            md_lines.append(f"- **R²**: {result.r_squared:.4f}")
            md_lines.append(f"- **Adj. R²**: {result.adj_r_squared:.4f}")
            md_lines.append(f"- **N**: {result.n_obs}")
            md_lines.append(f"- **Quality**: {result.overall_quality}\n")

        # Save
        md_path = self.output_dir / "summary.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))

        logger.info(f"Markdown summary saved to: {md_path}")
        return md_path
