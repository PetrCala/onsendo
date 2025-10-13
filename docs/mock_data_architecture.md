# Mock Data Architecture

## Overview

Onsendo has two mock data generation systems:

1. **Basic System** (legacy) - For simple unit testing
2. **Advanced System** (recommended) - For realistic analysis with econometric relationships

## Systems Comparison

### Basic System (Legacy)

**Purpose:** Quick unit tests and simple scenarios

**Components:**
- `mock_visit_data.py` - Foundation dataclass and basic generators
- `mock_data.py` - CLI command (DEPRECATED)

**Features:**
- Random ratings within realistic ranges
- Simple scenario templates (weekend_warrior, daily_visitor, etc.)
- Seasonal temperature variations
- Fast generation for testing

**Limitations:**
- No econometric relationships (price-quality correlation ≈ 0)
- Random ratings independent of onsen characteristics
- No user profile heterogeneity
- Not suitable for regression analysis or econometric studies

**When to use:**
- Unit tests requiring simple visit objects
- Quick prototype testing
- Scenarios where data realism doesn't matter

**CLI Command:**
```bash
# DEPRECATED - Shows warning
poetry run onsendo database insert-mock-visits --scenario weekend_warrior
```

### Advanced System (Recommended)

**Purpose:** Analysis-ready data with realistic correlations

**Components:**
- `user_profiles.py` - 8 behavioral personas
- `scenario_builder.py` - Advanced generator with correlations
- `integrated_scenario.py` - Heart rate data integration
- `generate_realistic_data.py` - CLI interface

**Features:**
- **Econometric Relationships:**
  - Price-quality correlation (R² ≈ 0.5-0.7)
  - Cleanliness-atmosphere correlation (r ≈ 0.6)
  - Entry fee → facility quality
  - Weather → view ratings

- **User Profiles:**
  - Quality Seeker (high standards, low price sensitivity)
  - Budget Traveler (price-conscious, value-focused)
  - Health Enthusiast (sauna focus, high exercise rate)
  - Relaxation Seeker (atmosphere priority)
  - Explorer (travel distance tolerance)
  - Social Visitor (group visits, food service usage)
  - Local Regular (consistency, loyalty patterns)
  - Tourist (multi-onsen days, geographic breadth)

- **Realistic Effects:**
  - Seasonal patterns (winter → higher temp preference)
  - Weather impacts (rain → lower view ratings)
  - Crowd level → rating adjustments
  - Profile heterogeneity (different preferences per user)

- **Heart Rate Integration:**
  - Bath temperature → HR elevation (+5 BPM/°C above 38°C)
  - Sauna → significant HR spike (+20-40 BPM)
  - Exercise → elevated baseline
  - Recovery patterns

**Pre-configured Scenarios:**

1. **comprehensive** (Default)
   - 100 visits over 90 days
   - All 8 profiles equally represented
   - Full seasonal/weather/correlation effects
   - Ideal for: Overview analysis, general testing

2. **econometric**
   - 200 visits optimized for regression
   - Strong price-quality correlations
   - Profile heterogeneity for fixed effects
   - Ideal for: Enjoyment drivers, pricing studies

3. **heart_rate**
   - 150 visits, 85% with HR data
   - Health enthusiast profiles dominant
   - Clear temperature-HR relationships
   - Ideal for: Physiological impact analysis

4. **pricing**
   - 200 visits, wide price range
   - Quality seekers vs budget travelers (50/50)
   - Clear price-quality stratification
   - Ideal for: Pricing optimization analysis

5. **spatial**
   - 150 visits, explorers/tourists dominant
   - Wide geographic distribution
   - Multi-onsen day patterns
   - Ideal for: Spatial analysis, travel patterns

6. **temporal**
   - 250 visits over 12 months
   - Local regular profiles (consistent visitor)
   - Clear seasonal patterns
   - Ideal for: Time series, seasonal analysis

7. **tourist**
   - 7-day trip, 3 visits/day
   - Intensive multi-onsen exploration
   - Ideal for: Tourism behavior studies

8. **local_regular**
   - 8 visits/month over 6 months
   - Single profile consistency
   - Ideal for: Loyalty, repeat visit patterns

9. **integrated**
   - Combined visit + HR data (60% coverage)
   - Profile-based tracking probability
   - Ideal for: Multi-modal analysis

**CLI Commands:**
```bash
# Generate econometric test data
poetry run onsendo database generate-realistic-data --scenario econometric --num-visits 200

# View available profiles
poetry run onsendo database list-profiles

# View scenario details
poetry run onsendo database scenario-info pricing

# Generate comprehensive dataset
poetry run onsendo database generate-realistic-data --scenario comprehensive
```

## Shared Foundation

Both systems use the same `MockOnsenVisit` dataclass from `mock_visit_data.py`:

```python
@dataclass
class MockOnsenVisit:
    """Mock onsen visit data with validation logic."""

    # Basic information
    onsen_id: int
    entry_fee_yen: int
    payment_method: str
    # ... 50+ fields

    def __post_init__(self):
        """Validate and adjust data based on logic chains."""
        self._validate_sauna_logic()
        self._validate_outdoor_bath_logic()
        # ...
```

This ensures:
- Consistent data structure across all mock systems
- Logic chain validation (e.g., no sauna rating if sauna not visited)
- Easy conversion to database models

## Migration Guide

### For Test Authors

**If you're writing unit tests:**
- Continue using `mock_visit_data.py` for simple test fixtures
- Use `create_single_visit()` or `MockVisitDataGenerator` directly

```python
from src.testing.mocks.mock_visit_data import create_single_visit

def test_visit_calculation():
    visit = create_single_visit(onsen_id=1, entry_fee_yen=500)
    result = calculate_something(visit)
    assert result == expected
```

**If you need realistic data for integration tests:**
- Switch to `scenario_builder.py` for analysis-ready data

```python
from src.testing.mocks.scenario_builder import create_analysis_ready_dataset

def test_regression_model():
    visits = create_analysis_ready_dataset(
        onsen_ids=[1, 2, 3],
        num_visits=100,
    )
    model = train_model(visits)
    assert model.rsquared > 0.4  # Realistic R²
```

### For CLI Users

**Replace old commands:**
```bash
# OLD (deprecated)
onsendo database insert-mock-visits --scenario weekend_warrior

# NEW (recommended)
onsendo database generate-realistic-data --scenario comprehensive
```

**View available options:**
```bash
# List user profiles
onsendo database list-profiles

# View scenario info
onsendo database scenario-info econometric

# See all database commands
onsendo database --help
```

## Implementation Details

### Profile-Based Rating Generation

Each profile generates ratings based on personal preferences:

```python
class UserProfile:
    rating_correlations: Dict[str, float]  # Component weights

    def generate_personal_rating(
        self,
        cleanliness: int,
        atmosphere: int,
        view: int,
        entry_fee: int,
        crowd_level: str,
        weather: str,
    ) -> int:
        # Weighted component ratings
        base_score = sum(
            rating * self.rating_correlations[component]
            for component, rating in components.items()
        )

        # Price sensitivity effect
        price_effect = -self.price_sensitivity * (entry_fee / 1000)

        # Crowd aversion
        crowd_penalty = self.crowd_aversion * crowd_penalties[crowd_level]

        # Weather preference
        weather_bonus = self.weather_preferences[weather]

        return clamp(base_score + price_effect + crowd_penalty + weather_bonus, 1, 10)
```

### Realistic Correlations

**Price-Quality Relationship:**
```python
def _generate_correlated_ratings(entry_fee: int) -> Dict[str, int]:
    # Price tiers affect facility quality
    tier = get_price_tier(entry_fee)
    cleanliness_boost = tier['cleanliness_boost']  # -1 to +3
    facility_prob = tier['facility_probability']  # 0.3 to 0.95

    cleanliness = base_cleanliness + cleanliness_boost

    # Atmosphere correlates with cleanliness
    atmosphere = cleanliness + np.random.normal(0, 1)

    return {'cleanliness': cleanliness, 'atmosphere': atmosphere, ...}
```

**Heart Rate Physiological Effects:**
```python
def _apply_onsen_effects_to_hr(session: MockHeartRateSession, visit: MockOnsenVisit):
    # Temperature effect: +5 BPM per °C above 38°C
    temp_effect = (visit.main_bath_temperature - 38.0) * 5

    # Sauna effect: +20-40 BPM spike
    if visit.sauna_visited:
        sauna_peak_effect = 30 + (visit.sauna_temperature - 80) * 0.5

    # Apply to heart rate time series
    for timestamp, hr, confidence in session.data_points:
        if in_bath_period(timestamp):
            hr_adjusted = hr + temp_effect
        if in_sauna_period(timestamp):
            hr_adjusted += sauna_peak_effect
```

## Testing and Validation

### Verify Correlations

After generating data, verify realistic correlations:

```python
import pandas as pd
from scipy.stats import pearsonr

# Load generated data
df = pd.DataFrame([visit.__dict__ for visit in visits])

# Check price-quality correlation
price_quality_corr = df[['entry_fee_yen', 'cleanliness_rating']].corr()
print(f"Price-quality correlation: {price_quality_corr.iloc[0, 1]:.3f}")
# Expected: 0.5-0.7

# Check cleanliness-atmosphere correlation
clean_atmos_corr = df[['cleanliness_rating', 'atmosphere_rating']].corr()
print(f"Cleanliness-atmosphere correlation: {clean_atmos_corr.iloc[0, 1]:.3f}")
# Expected: 0.5-0.7
```

### Regression Analysis Ready

Generate econometric data and verify it's suitable for analysis:

```bash
# Generate econometric dataset
poetry run onsendo database generate-realistic-data --scenario econometric --num-visits 200

# Run enjoyment drivers analysis
poetry run onsendo analysis scenario enjoyment_drivers
```

Expected output:
```
✅ OLS Regression Results
Dependent Variable: personal_rating
R-squared: 0.515
Adj. R-squared: 0.498

Coefficients:
  cleanliness_rating:    0.45*** (p<0.001)
  atmosphere_rating:     0.38*** (p<0.001)
  entry_fee_yen:        -0.12**  (p<0.01)
  crowd_level_busy:     -0.31*   (p<0.05)
```

## File Structure

```
src/testing/mocks/
├── mock_visit_data.py          # Foundation: MockOnsenVisit dataclass, basic generators
├── user_profiles.py            # 8 behavioral personas with preferences
├── scenario_builder.py         # Advanced generator with correlations
├── integrated_scenario.py      # Heart rate data integration
├── mock_heart_rate_data.py     # HR data generators
├── mock_db.py                  # Database connection utilities
├── mock_onsen_data.py          # Scraper test data (HTML)
└── mock_interactive_data.py    # CLI input sequences

src/cli/commands/database/
├── mock_data.py                # [DEPRECATED] CLI for basic system
└── generate_realistic_data.py  # CLI for advanced system
```

## Best Practices

1. **For Unit Tests:** Use `mock_visit_data.py` directly
   - Fast generation
   - Simple test fixtures
   - No unnecessary complexity

2. **For Integration Tests:** Use `scenario_builder.py`
   - Analysis-ready data
   - Realistic correlations
   - Econometrically valid

3. **For Analysis Development:** Use pre-configured scenarios
   - CLI: `database generate-realistic-data --scenario <name>`
   - Optimized for specific analysis types
   - Instant realistic datasets

4. **For Custom Scenarios:** Extend `ScenarioConfig`
   - Adjust profile weights
   - Enable/disable effects
   - Custom date ranges

## Deprecation Timeline

- **Current:** Both systems available, old system marked DEPRECATED
- **Next Release:** Runtime warnings added to old CLI command
- **Future:** Old CLI command may be removed (mock_visit_data.py remains)

The basic `mock_visit_data.py` module will remain indefinitely as the foundation dataclass and for simple unit testing.

## Further Reading

- User Profiles: See `src/testing/mocks/user_profiles.py` for all 8 personas
- Scenario Builder: See `src/testing/mocks/scenario_builder.py` for correlation logic
- HR Integration: See `src/testing/mocks/integrated_scenario.py` for physiological effects
- CLI Usage: Run `poetry run onsendo database --help`
