# Onsen Analysis System

The Onsen Analysis System is a comprehensive, scalable framework for analyzing onsen data, creating visualizations, building statistical models, and generating insights. It's designed to handle everything from basic descriptive statistics to advanced machine learning models.

## Overview

The system consists of several interconnected components:

- **Data Pipeline**: Transforms raw database data into analysis-ready formats
- **Metrics Calculator**: Computes statistical metrics and summary statistics
- **Visualization Engine**: Creates charts, graphs, and interactive maps
- **Model Engine**: Trains and evaluates statistical and machine learning models
- **Analysis Engine**: Orchestrates all components for comprehensive analysis

## Features

### 🎯 **Comprehensive Analysis Types**

- **Descriptive**: Basic statistics and data summaries
- **Exploratory**: Data exploration and pattern discovery
- **Predictive**: Forecasting and prediction models
- **Correlational**: Relationship analysis between variables
- **Temporal**: Time-based patterns and trends
- **Spatial**: Geographic distribution and clustering
- **Comparative**: Group comparisons and benchmarking
- **Trend**: Trend analysis and forecasting
- **Cluster**: Data clustering and segmentation
- **Regression**: Linear and non-linear regression models
- **Classification**: Categorical prediction models
- **Time Series**: Temporal forecasting models

### 📊 **Rich Visualization Options**

- **Basic Charts**: Bar, line, scatter, histogram, box, violin, pie
- **Advanced Charts**: Correlation matrices, distribution plots, trend analysis
- **Maps**: Point maps, heat maps, choropleth maps, cluster maps
- **Interactive**: Plotly-based interactive visualizations
- **Static**: High-quality matplotlib/seaborn charts
- **Dashboards**: Multi-panel analysis dashboards

### 🔢 **Statistical Metrics**

- **Central Tendency**: Mean, median, mode
- **Dispersion**: Standard deviation, variance, range, IQR
- **Distribution**: Skewness, kurtosis
- **Counts**: Total count, unique count, null count
- **Percentiles**: 25th, 75th, 90th, 95th percentiles
- **Custom**: User-defined metric calculations

### 🤖 **Machine Learning Models**

- **Linear Models**: Linear regression, logistic regression, ridge, lasso
- **Tree Models**: Decision trees, random forests, gradient boosting
- **Clustering**: K-means, DBSCAN, hierarchical clustering
- **Dimensionality Reduction**: PCA, t-SNE, UMAP

### 🗺️ **Geographic Analysis**

- **Interactive Maps**: Folium-based interactive maps
- **Heat Maps**: Density and intensity visualizations
- **Point Maps**: Individual location markers
- **Cluster Maps**: Grouped location displays
- **Spatial Clustering**: Geographic pattern recognition

## Quick Start

### 1. Install Dependencies

The system requires several Python packages. Install them using Poetry:

```bash
poetry install
```

### 2. Run a Sample Analysis

```bash
# Run a sample analysis to see the system in action
onsendo analysis sample

# This will create a basic analysis with:
# - Data overview
# - Key metrics
# - Basic visualizations
# - Simple linear regression model
```

**Note**: Each analysis run creates its own organized subdirectory in `output/analysis/` with a timestamp and descriptive name (e.g., `descriptive_20250812_145800/`).

### 3. Explore Available Scenarios

```bash
# List all predefined analysis scenarios
onsendo analysis list-scenarios

# Run a specific scenario
onsendo analysis scenario overview
onsendo analysis scenario quality_analysis
onsendo analysis scenario spatial_analysis
onsendo analysis scenario temporal_analysis
```

### 4. Create Custom Analysis

```bash
# Run a custom analysis
onsendo analysis run descriptive \
  --data-categories "onsen_basic,visit_basic,visit_ratings" \
  --metrics "mean,median,std,count" \
  --visualizations "bar,histogram,correlation_matrix" \
  --models "linear_regression" \
  --include-statistical-tests
```

### 5. Manage Analysis Results

```bash
# View summary of all analyses and directories
onsendo analysis summary

# Clean up old analyses (keep only 5 most recent)
onsendo analysis clear-cache --cleanup_old_analyses --keep_recent 5
```

## CLI Commands

### Analysis Commands

| Command | Description |
|---------|-------------|
| `analysis run` | Run a custom analysis with specified parameters |
| `analysis scenario` | Run a predefined analysis scenario |
| `analysis list-scenarios` | List available analysis scenarios |
| `analysis list-options` | List available analysis options |
| `analysis summary` | Show summary of all analyses performed |
| `analysis clear-cache` | Clear the analysis cache and optionally clean up old directories |
| `analysis export` | Export analysis results |
| `analysis sample` | Create a sample analysis |

### Command Examples

#### Basic Analysis

```bash
# Simple descriptive analysis
onsendo analysis run descriptive \
  --data-categories "onsen_basic,visit_basic" \
  --metrics "mean,count" \
  --visualizations "bar,histogram"
```

#### Advanced Analysis

```bash
# Comprehensive analysis with models
onsendo analysis run correlational \
  --data-categories "visit_ratings,visit_experience" \
  --metrics "mean,std,correlation" \
  --visualizations "correlation_matrix,scatter,heatmap" \
  --models "linear_regression,random_forest" \
  --grouping "region,time_of_day" \
  --include-statistical-tests
```

#### Spatial Analysis

```bash
# Geographic analysis
onsendo analysis run spatial \
  --data-categories "spatial,onsen_basic,visit_ratings" \
  --visualizations "point_map,heat_map,cluster_map" \
  --models "kmeans" \
  --spatial-bounds "33.0,34.0,130.0,131.0"
```

#### Temporal Analysis

```bash
# Time-based analysis
onsendo analysis run temporal \
  --data-categories "temporal,visit_basic,weather" \
  --visualizations "line,trend,seasonal" \
  --time-range "2023-01-01 00:00,2023-12-31 23:59"
```

#### Analysis Maintenance and Cleanup

```bash
# View summary of all analyses and directories
onsendo analysis summary

# Clear cache and clean up old analysis directories
onsendo analysis clear-cache --cleanup_old_analyses --keep_recent 5

# Clean up old shared directories
onsendo analysis clear-cache --cleanup_shared_dirs

# Perform comprehensive cleanup
onsendo analysis clear-cache --cleanup_old_analyses --keep_recent 3 --cleanup_shared_dirs
```

## Analysis Scenarios

### 1. Overview Scenario

**Purpose**: General overview of all onsen data

- **Analysis Types**: Descriptive, Exploratory
- **Data Categories**: Onsen basic, Visit basic, Ratings, Spatial, Temporal
- **Visualizations**: Bar charts, Histograms, Point maps, Heatmaps
- **Focus**: Data overview, key statistics, data quality

### 2. Quality Analysis Scenario

**Purpose**: Deep dive into onsen quality metrics

- **Analysis Types**: Descriptive, Correlational, Comparative
- **Data Categories**: Visit ratings, Onsen features, Experience
- **Visualizations**: Box plots, Violin plots, Correlation matrices
- **Models**: Linear regression
- **Focus**: Rating patterns, quality factors, improvement areas

### 3. Spatial Analysis Scenario

**Purpose**: Geographic analysis and clustering

- **Analysis Types**: Spatial, Cluster, Comparative
- **Data Categories**: Spatial, Onsen basic, Visit ratings
- **Visualizations**: Point maps, Heat maps, Cluster maps
- **Models**: K-means, DBSCAN
- **Focus**: Geographic patterns, clusters, spatial correlations

### 4. Temporal Analysis Scenario

**Purpose**: Time-based patterns and trends

- **Analysis Types**: Temporal, Trend, Seasonal
- **Data Categories**: Temporal, Visit basic, Weather
- **Visualizations**: Line charts, Trend plots, Seasonal plots
- **Models**: Exponential smoothing
- **Focus**: Temporal trends, seasonal patterns, time-based recommendations

## Data Categories

The system organizes data into logical categories for analysis:

### Onsen Data

- **ONSEN_BASIC**: Basic onsen information (name, location, features)
- **ONSEN_FEATURES**: Amenities and facilities (sauna, outdoor baths, etc.)

### Visit Data

- **VISIT_BASIC**: Basic visit information (time, duration, cost)
- **VISIT_RATINGS**: All rating fields (cleanliness, atmosphere, etc.)
- **VISIT_EXPERIENCE**: Experience-related fields (mood, energy, etc.)
- **VISIT_LOGISTICS**: Travel and timing information
- **VISIT_PHYSICAL**: Physical aspects (temperature, water type, etc.)

### Specialized Data

- **HEART_RATE**: Heart rate monitoring data
- **SPATIAL**: Location and distance data
- **TEMPORAL**: Time-based data
- **WEATHER**: Weather conditions during visits
- **EXERCISE**: Exercise-related data

## Visualization Types

### Basic Charts

- **BAR**: Bar charts for categorical data
- **LINE**: Line charts for trends
- **SCATTER**: Scatter plots for relationships
- **HISTOGRAM**: Distribution histograms
- **BOX**: Box plots for distributions
- **VIOLIN**: Violin plots for detailed distributions
- **PIE**: Pie charts for proportions
- **HEATMAP**: Heat maps for matrices

### Advanced Charts

- **CORRELATION_MATRIX**: Correlation analysis
- **DISTRIBUTION**: Distribution plots
- **TREND**: Trend analysis with trend lines
- **SEASONAL**: Seasonal pattern analysis
- **CLUSTER**: Cluster visualization

### Maps

- **POINT_MAP**: Individual location markers
- **HEAT_MAP**: Density-based heat maps
- **CHOROPLETH**: Area-based color coding
- **CLUSTER_MAP**: Grouped location clusters

### Interactive

- **INTERACTIVE_CHART**: Enhanced interactive features
- **DASHBOARD**: Multi-panel dashboards

## Model Types

### Regression Models

- **LINEAR_REGRESSION**: Standard linear regression
- **RIDGE_REGRESSION**: Ridge regression with regularization
- **LASSO_REGRESSION**: Lasso regression with feature selection
- **GRADIENT_BOOSTING**: Gradient boosting regression

### Classification Models

- **LOGISTIC_REGRESSION**: Binary classification
- **DECISION_TREE**: Decision tree classifier
- **RANDOM_FOREST**: Random forest classifier

### Clustering Models

- **KMEANS**: K-means clustering
- **DBSCAN**: Density-based clustering
- **HIERARCHICAL**: Hierarchical clustering

### Dimensionality Reduction

- **PCA**: Principal component analysis
- **TSNE**: t-distributed stochastic neighbor embedding
- **UMAP**: Uniform manifold approximation and projection

## Output and Export

### Generated Files

The system creates several types of output files:

1. **Visualizations**: PNG images and HTML files
2. **Data Exports**: JSON and CSV files
3. **Model Files**: Pickled model objects
4. **Analysis Reports**: Summary files and metadata
5. **Interactive Maps**: HTML map files

### Export Formats

- **JSON**: Structured data export
- **CSV**: Tabular data export
- **HTML**: Interactive visualizations
- **PNG**: Static chart images

### Output Structure

The system now organizes analysis results in separate subdirectories for each analysis run:

```plain
output/analysis/
├── descriptive_20250812_145800/     # Individual analysis directory
│   ├── analysis_summary.json        # Analysis summary
│   ├── metrics.json                 # Calculated metrics
│   ├── insights.txt                 # Generated insights
│   ├── metadata.json                # Analysis metadata
│   ├── export.json                  # Complete results export
│   ├── data_export.csv              # Data export (if requested)
│   ├── visualizations/              # Generated charts and graphs
│   └── models/                      # Trained models
├── spatial_20250812_150000/         # Another analysis directory
│   └── [same structure]
├── temporal_20250812_151500/        # Yet another analysis directory
│   └── [same structure]
└── README.md                        # Directory documentation
```

**Benefits of the New Structure:**

- **Organization**: Each analysis is self-contained in its own directory
- **Versioning**: Clear tracking of different analysis runs over time
- **Cleanup**: Easy to remove old analyses while keeping recent ones
- **Sharing**: Simple to share specific analysis results by copying individual directories
- **Reproducibility**: Each analysis directory contains all necessary files

### Analysis Cleanup and Maintenance

The system provides tools to manage analysis output directories and prevent disk space issues:

#### Automatic Directory Organization

Each analysis run automatically creates a timestamped subdirectory:

- **Naming Convention**: `{analysis_type}_{timestamp}/`
- **Example**: `descriptive_20250812_145800/`
- **Self-Contained**: All analysis files are stored within the subdirectory

#### Cleanup Commands

Manage old analysis directories and shared resources:

```bash
# View summary of all analysis directories
onsendo analysis summary

# Clean up old analysis directories (keep only recent ones)
onsendo analysis clear-cache --cleanup_old_analyses --keep_recent 5

# Clean up old shared directories (models, visualizations)
onsendo analysis clear-cache --cleanup_shared_dirs

# Perform both cleanup operations
onsendo analysis clear-cache --cleanup_old_analyses --keep_recent 3 --cleanup_shared_dirs
```

#### Cleanup Options

- **`--cleanup_old_analyses`**: Remove old analysis directories
- **`--keep_recent N`**: Keep only the N most recent analyses (default: 5)
- **`--cleanup_shared_dirs`**: Remove old shared directories that are no longer needed

#### Best Practices for Cleanup

1. **Regular Maintenance**: Run cleanup monthly to prevent disk space issues
2. **Retention Policy**: Keep 5-10 most recent analyses for reference
3. **Shared Directory Cleanup**: Use after major system updates
4. **Backup Important Results**: Copy important analysis directories before cleanup

#### Directory Information

The `analysis summary` command provides detailed information about each analysis directory:

- Creation date and time
- Total file size and count
- Path information
- Analysis type and configuration

## Advanced Usage

### Custom Metrics

Define custom metrics using mathematical expressions:

```bash
onsendo analysis run descriptive \
  --custom-metrics '{"value_score": "mean(personal_rating) * 0.7 + mean(cleanliness_rating) * 0.3"}'
```

### Filtering Data

Apply filters to focus on specific data subsets:

```bash
onsendo analysis run descriptive \
  --filters '{"region": "Beppu", "entry_fee_yen__gte": 500}'
```

### Grouping Analysis

Group data by specific columns:

```bash
onsendo analysis run comparative \
  --grouping "region,time_of_day" \
  --metrics "mean,std"
```

### Time Ranges

Analyze specific time periods:

```bash
onsendo analysis run temporal \
  --time-range "2023-06-01 00:00,2023-08-31 23:59"
```

### Spatial Bounds

Focus on specific geographic areas:

```bash
onsendo analysis run spatial \
  --spatial-bounds "33.0,34.0,130.0,131.0"
```

## Performance and Caching

### Caching Strategy

- **Data Cache**: Cached data queries for repeated analysis
- **Result Cache**: Cached analysis results
- **Model Cache**: Cached trained models

### Memory Management

- **Efficient Data Loading**: Lazy loading of large datasets
- **Streaming Processing**: Process data in chunks when needed
- **Garbage Collection**: Automatic cleanup of temporary objects

## Error Handling

The system includes comprehensive error handling:

- **Data Validation**: Checks data quality and completeness
- **Graceful Degradation**: Continues analysis with available data
- **Error Reporting**: Detailed error messages and suggestions
- **Fallback Strategies**: Alternative approaches when primary methods fail

## Extending the System

### Adding New Analysis Types

1. Extend the `AnalysisType` enum
2. Implement analysis logic in the engine
3. Add corresponding CLI commands

### Adding New Visualizations

1. Extend the `VisualizationType` enum
2. Implement visualization method in `VisualizationEngine`
3. Update configuration handling

### Adding New Models

1. Extend the `ModelType` enum
2. Implement model creation in `ModelEngine`
3. Add model-specific configuration options

## Best Practices

### Data Preparation

- Ensure data quality before analysis
- Handle missing values appropriately
- Normalize data for modeling

### Visualization Selection

- Choose appropriate chart types for data
- Use consistent color schemes
- Include proper labels and titles

### Model Selection

- Start with simple models
- Validate model assumptions
- Use cross-validation for evaluation

### Performance Optimization

- Use caching for repeated operations
- Process data in appropriate chunks
- Monitor memory usage

## Troubleshooting

### Common Issues

1. **Memory Errors**: Reduce data size or use chunking
2. **Missing Dependencies**: Install required packages
3. **Data Quality Issues**: Check data completeness and format
4. **Visualization Errors**: Verify data types and column names

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
onsendo analysis run descriptive
```

## Future Enhancements

### Planned Features

- **Report Generation**: Automated PDF/HTML reports
- **Dashboard Creation**: Interactive web dashboards
- **API Integration**: REST API for programmatic access
- **Real-time Analysis**: Streaming data analysis
- **Advanced ML**: Deep learning and neural networks

### Community Contributions

The system is designed to be extensible. Contributions are welcome for:

- New analysis types
- Additional visualization methods
- Enhanced model algorithms
- Performance optimizations

## Conclusion

The Onsen Analysis System provides a robust, scalable foundation for comprehensive onsen data analysis. Whether you need simple descriptive statistics or complex machine learning models, the system offers the tools and flexibility to meet your analysis needs.

For questions, issues, or contributions, please refer to the project documentation or create an issue in the project repository.
