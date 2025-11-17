"""Graph definitions for onsen visit data.

This module defines all the graphs to be generated for visit analytics.
"""

from src.lib.graphing.base import (
    DataSource,
    GraphCategory,
    GraphDefinition,
    GraphType,
)

# Group 1: Financial & Logistics
FINANCIAL_GRAPHS = [
    GraphDefinition(
        title="Entry Fee Distribution",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.FINANCIAL,
        field="entry_fee_yen",
        bins=25,
        show_kde=True,
        notes="Distribution of entry fees paid across all visits",
    ),
    GraphDefinition(
        title="Payment Method Usage",
        graph_type=GraphType.PIE,
        data_source=DataSource.VISIT,
        category=GraphCategory.FINANCIAL,
        field="payment_method",
        notes="Breakdown of payment methods used",
    ),
    GraphDefinition(
        title="Travel Time Distribution",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.FINANCIAL,
        field="travel_time_minutes",
        bins=20,
        show_kde=True,
        notes="How long it takes to reach onsens",
    ),
]

# Group 2: Categorical Breakdowns
CATEGORICAL_GRAPHS = [
    GraphDefinition(
        title="Weather Conditions",
        graph_type=GraphType.PIE,
        data_source=DataSource.VISIT,
        category=GraphCategory.CATEGORICAL,
        field="weather",
        notes="Weather conditions during visits",
    ),
    GraphDefinition(
        title="Visit Companions",
        graph_type=GraphType.BAR,
        data_source=DataSource.VISIT,
        category=GraphCategory.CATEGORICAL,
        field="visited_with",
        sort_by="value",
        notes="Who you visited onsens with",
    ),
    GraphDefinition(
        title="Travel Mode Distribution",
        graph_type=GraphType.BAR,
        data_source=DataSource.VISIT,
        category=GraphCategory.CATEGORICAL,
        field="travel_mode",
        sort_by="value",
        notes="How you traveled to onsens",
    ),
    GraphDefinition(
        title="Crowd Levels",
        graph_type=GraphType.BAR,
        data_source=DataSource.VISIT,
        category=GraphCategory.CATEGORICAL,
        field="crowd_level",
        sort_by="value",
        notes="How crowded onsens were during visits",
    ),
    GraphDefinition(
        title="Main Bath Types",
        graph_type=GraphType.PIE,
        data_source=DataSource.VISIT,
        category=GraphCategory.CATEGORICAL,
        field="main_bath_type",
        notes="Types of main baths experienced",
    ),
    GraphDefinition(
        title="Water Color Distribution",
        graph_type=GraphType.PIE,
        data_source=DataSource.VISIT,
        category=GraphCategory.CATEGORICAL,
        field="water_color",
        notes="Colors of onsen water",
    ),
]

# Group 3: Physical Conditions
PHYSICAL_GRAPHS = [
    GraphDefinition(
        title="Outdoor Temperature Distribution",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.PHYSICAL,
        field="temperature_outside_celsius",
        bins=20,
        show_kde=True,
        notes="Outdoor temperature during visits",
    ),
    GraphDefinition(
        title="Bath Temperature Distribution",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.PHYSICAL,
        field="main_bath_temperature",
        bins=20,
        show_kde=True,
        notes="Main bath water temperature",
    ),
    GraphDefinition(
        title="Temperature Comparison",
        graph_type=GraphType.BOX,
        data_source=DataSource.VISIT,
        category=GraphCategory.PHYSICAL,
        field="main_bath_temperature",
        notes="Comparison of different temperature measurements (requires data transformation)",
    ),
    GraphDefinition(
        title="Sauna Duration",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.PHYSICAL,
        field="sauna_duration_minutes",
        bins=15,
        notes="Time spent in sauna when available",
    ),
]

# Group 4: Time Analysis
TIME_GRAPHS = [
    GraphDefinition(
        title="Visit Time of Day",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.TIME,
        field="visit_hour",
        bins=24,
        notes="What time of day visits occurred (requires derived field)",
    ),
    GraphDefinition(
        title="Stay Length Distribution",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.TIME,
        field="stay_length_minutes",
        bins=20,
        show_kde=True,
        notes="How long visits lasted",
    ),
    GraphDefinition(
        title="Visits by Day of Week",
        graph_type=GraphType.BAR,
        data_source=DataSource.VISIT,
        category=GraphCategory.TIME,
        field="day_of_week",
        notes="Which days of the week you visit onsens (requires derived field)",
    ),
    GraphDefinition(
        title="Visits by Month",
        graph_type=GraphType.BAR,
        data_source=DataSource.VISIT,
        category=GraphCategory.TIME,
        field="month",
        notes="Seasonal patterns in visits (requires derived field)",
    ),
]

# Group 5: Ratings & Experience
RATINGS_GRAPHS = [
    GraphDefinition(
        title="All Ratings Comparison",
        graph_type=GraphType.BAR,
        data_source=DataSource.VISIT,
        category=GraphCategory.RATINGS,
        field="rating_type",
        field_y="rating_value",
        aggregation="mean",
        notes="Average ratings across all categories (requires data transformation)",
    ),
    GraphDefinition(
        title="Personal Rating Distribution",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.RATINGS,
        field="personal_rating",
        bins=10,
        notes="Your personal ratings distribution",
    ),
    GraphDefinition(
        title="Accessibility Rating",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.RATINGS,
        field="accessibility_rating",
        bins=10,
        notes="How easy onsens were to find and access",
    ),
    GraphDefinition(
        title="Cleanliness Rating",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.RATINGS,
        field="cleanliness_rating",
        bins=10,
        notes="Overall cleanliness ratings",
    ),
    GraphDefinition(
        title="View Rating",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.RATINGS,
        field="view_rating",
        bins=10,
        notes="Quality of views from onsens",
    ),
    GraphDefinition(
        title="Atmosphere Rating",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.RATINGS,
        field="atmosphere_rating",
        bins=10,
        notes="Overall atmosphere ratings",
    ),
    GraphDefinition(
        title="Hydration Level",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.RATINGS,
        field="hydration_level",
        bins=10,
        notes="Hydration levels during visits",
    ),
]

# Group 6: Mood & Energy
MOOD_GRAPHS = [
    GraphDefinition(
        title="Energy Level Change",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.MOOD,
        field="energy_level_change",
        bins=21,  # -10 to +10
        notes="How visits affected energy levels",
    ),
    GraphDefinition(
        title="Pre-Visit Mood",
        graph_type=GraphType.BAR,
        data_source=DataSource.VISIT,
        category=GraphCategory.MOOD,
        field="pre_visit_mood",
        notes="Mood before visiting onsen",
    ),
    GraphDefinition(
        title="Post-Visit Mood",
        graph_type=GraphType.BAR,
        data_source=DataSource.VISIT,
        category=GraphCategory.MOOD,
        field="post_visit_mood",
        notes="Mood after visiting onsen",
    ),
]

# Additional interesting graphs
ADDITIONAL_GRAPHS = [
    GraphDefinition(
        title="Sauna Availability vs Usage",
        graph_type=GraphType.BAR,
        data_source=DataSource.VISIT,
        category=GraphCategory.CATEGORICAL,
        field="sauna_usage_status",
        notes="Comparison of sauna availability and actual usage (requires derived field)",
    ),
    GraphDefinition(
        title="Outdoor Bath Availability vs Usage",
        graph_type=GraphType.BAR,
        data_source=DataSource.VISIT,
        category=GraphCategory.CATEGORICAL,
        field="outdoor_bath_usage_status",
        notes="Comparison of outdoor bath availability and usage (requires derived field)",
    ),
    GraphDefinition(
        title="Multi-Onsen Days",
        graph_type=GraphType.BAR,
        data_source=DataSource.VISIT,
        category=GraphCategory.TIME,
        field="visits_per_day",
        notes="How often you visit multiple onsens in one day (requires derived field)",
    ),
    GraphDefinition(
        title="Local Interaction Quality",
        graph_type=GraphType.HISTOGRAM,
        data_source=DataSource.VISIT,
        category=GraphCategory.MOOD,
        field="local_interaction_quality_rating",
        bins=10,
        notes="Quality of interactions with locals",
    ),
]

# Organize graphs by category for easy access
GRAPHS_BY_CATEGORY = {
    GraphCategory.FINANCIAL: FINANCIAL_GRAPHS,
    GraphCategory.CATEGORICAL: CATEGORICAL_GRAPHS,
    GraphCategory.PHYSICAL: PHYSICAL_GRAPHS,
    GraphCategory.TIME: TIME_GRAPHS,
    GraphCategory.RATINGS: RATINGS_GRAPHS,
    GraphCategory.MOOD: MOOD_GRAPHS,
}

# All graphs in one list
ALL_VISIT_GRAPHS = (
    FINANCIAL_GRAPHS
    + CATEGORICAL_GRAPHS
    + PHYSICAL_GRAPHS
    + TIME_GRAPHS
    + RATINGS_GRAPHS
    + MOOD_GRAPHS
    + ADDITIONAL_GRAPHS
)


def get_graphs_for_category(category: GraphCategory) -> list[GraphDefinition]:
    """Get all graph definitions for a specific category.

    Args:
        category: The graph category

    Returns:
        List of graph definitions for that category
    """
    return GRAPHS_BY_CATEGORY.get(category, [])


def get_all_graphs() -> list[GraphDefinition]:
    """Get all visit graph definitions.

    Returns:
        List of all graph definitions
    """
    return ALL_VISIT_GRAPHS
