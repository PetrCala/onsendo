"""
Data pipeline for transforming raw database data into analysis-ready formats.
"""

from typing import Optional, Any
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger

from src.db.models import Onsen, OnsenVisit, HeartRateData, Activity
from src.types.analysis import DataCategory
from src.types.exercise import ExerciseType


class DataPipeline:
    """
    Pipeline for transforming raw database data into analysis-ready formats.
    """

    def __init__(self, session: Session):
        self.session = session
        self._cached_data: dict[str, pd.DataFrame] = {}
        self._data_mappings = self._initialize_data_mappings()

    def _initialize_data_mappings(self) -> dict[DataCategory, dict[str, Any]]:
        """Initialize mappings for different data categories."""
        return {
            DataCategory.ONSEN_BASIC: {
                "table": "onsens",
                "columns": [
                    "id",
                    "ban_number",
                    "name",
                    "region",
                    "latitude",
                    "longitude",
                    "description",
                    "business_form",
                    "address",
                    "phone",
                    "admission_fee",
                    "usage_time",
                    "closed_days",
                    "private_bath",
                    "spring_quality",
                    "nearest_bus_stop",
                    "nearest_station",
                    "parking",
                    "remarks",
                ],
                "alias": "o",
                "filters": {},
                "joins": [],
            },
            DataCategory.ONSEN_FEATURES: {
                "table": "onsens",
                "columns": [
                    "id",
                    "name",
                    "private_bath",
                    "spring_quality",
                    "parking",
                    "had_soap",
                    "had_sauna",
                    "had_outdoor_bath",
                    "had_rest_area",
                    "had_food_service",
                    "massage_chair_available",
                ],
                "alias": "o",
                "filters": {},
                "joins": [],
            },
            DataCategory.VISIT_BASIC: {
                "table": "onsen_visits",
                "columns": [
                    "id",
                    "onsen_id",
                    "entry_fee_yen",
                    "payment_method",
                    "weather",
                    "temperature_outside_celsius",
                    "visit_time",
                    "stay_length_minutes",
                    "visited_with",
                    "travel_mode",
                    "travel_time_minutes",
                    "multi_onsen_day",
                    "visit_order",
                ],
                "alias": "v",
                "filters": {},
                "joins": [("onsens", "onsen_id", "id")],
            },
            DataCategory.VISIT_RATINGS: {
                "table": "onsen_visits",
                "columns": [
                    "id",
                    "onsen_id",
                    "accessibility_rating",
                    "cleanliness_rating",
                    "navigability_rating",
                    "view_rating",
                    "atmosphere_rating",
                    "personal_rating",
                    "rest_area_rating",
                    "food_quality_rating",
                    "sauna_rating",
                    "outdoor_bath_rating",
                ],
                "alias": "v",
                "filters": {},
                "joins": [("onsens", "onsen_id", "id")],
            },
            DataCategory.VISIT_EXPERIENCE: {
                "table": "onsen_visits",
                "columns": [
                    "id",
                    "onsen_id",
                    "pre_visit_mood",
                    "post_visit_mood",
                    "energy_level_change",
                    "hydration_level",
                    "crowd_level",
                    "main_bath_type",
                    "main_bath_temperature",
                    "water_color",
                    "smell_intensity_rating",
                ],
                "alias": "v",
                "filters": {},
                "joins": [("onsens", "onsen_id", "id")],
            },
            DataCategory.VISIT_LOGISTICS: {
                "table": "onsen_visits",
                "columns": [
                    "id",
                    "onsen_id",
                    "travel_mode",
                    "travel_time_minutes",
                    "accessibility_rating",
                    "visit_time",
                    "stay_length_minutes",
                    "multi_onsen_day",
                    "visit_order",
                ],
                "alias": "v",
                "filters": {},
                "joins": [("onsens", "onsen_id", "id")],
            },
            DataCategory.VISIT_PHYSICAL: {
                "table": "onsen_visits",
                "columns": [
                    "id",
                    "onsen_id",
                    "main_bath_temperature",
                    "sauna_temperature",
                    "outdoor_bath_temperature",
                    "changing_room_cleanliness_rating",
                    "locker_availability_rating",
                    "sauna_duration_minutes",
                ],
                "alias": "v",
                "filters": {},
                "joins": [("onsens", "onsen_id", "id")],
            },
            DataCategory.HEART_RATE: {
                "table": "heart_rate_data",
                "columns": [
                    "id",
                    "visit_id",
                    "recording_start",
                    "recording_end",
                    "average_heart_rate",
                    "min_heart_rate",
                    "max_heart_rate",
                    "total_recording_minutes",
                    "data_points_count",
                    "notes",
                ],
                "alias": "h",
                "filters": {},
                "joins": [("onsen_visits", "visit_id", "id")],
            },
            DataCategory.SPATIAL: {
                "table": "onsens",
                "columns": ["id", "name", "latitude", "longitude", "region", "address"],
                "alias": "o",
                "filters": {"latitude__notnull": True, "longitude__notnull": True},
                "joins": [],
            },
            DataCategory.TEMPORAL: {
                "table": "onsen_visits",
                "columns": [
                    "id",
                    "onsen_id",
                    "visit_time",
                    "weather",
                    "temperature_outside_celsius",
                ],
                "alias": "v",
                "filters": {"visit_time__notnull": True},
                "joins": [("onsens", "onsen_id", "id")],
            },
            DataCategory.WEATHER: {
                "table": "onsen_visits",
                "columns": [
                    "id",
                    "onsen_id",
                    "weather",
                    "temperature_outside_celsius",
                    "visit_time",
                ],
                "alias": "v",
                "filters": {},
                "joins": [("onsens", "onsen_id", "id")],
            },
            # Unified Activity System categories
            DataCategory.ACTIVITY_ALL: {
                "table": "activities",
                "columns": [
                    "id",
                    "strava_id",
                    "visit_id",
                    "recording_start",
                    "recording_end",
                    "duration_minutes",
                    "activity_type",
                    "activity_name",
                    "distance_km",
                    "calories_burned",
                    "elevation_gain_m",
                    "avg_heart_rate",
                    "min_heart_rate",
                    "max_heart_rate",
                    "indoor_outdoor",
                    "weather_conditions",
                    "notes",
                    "created_at",
                ],
                "alias": "a",
                "filters": {},
                "joins": [],
            },
            DataCategory.ACTIVITY_ONSEN: {
                "table": "activities",
                "columns": [
                    "id",
                    "strava_id",
                    "visit_id",
                    "recording_start",
                    "recording_end",
                    "duration_minutes",
                    "activity_name",
                    "avg_heart_rate",
                    "min_heart_rate",
                    "max_heart_rate",
                    "notes",
                ],
                "alias": "a",
                "filters": {"activity_type": "onsen_monitoring"},
                "joins": [("onsen_visits", "visit_id", "id", "LEFT")],
            },
            DataCategory.ACTIVITY_EXERCISE: {
                "table": "activities",
                "columns": [
                    "id",
                    "strava_id",
                    "activity_type",
                    "activity_name",
                    "recording_start",
                    "recording_end",
                    "duration_minutes",
                    "distance_km",
                    "calories_burned",
                    "elevation_gain_m",
                    "avg_heart_rate",
                    "indoor_outdoor",
                ],
                "alias": "a",
                "filters": {"activity_type__ne": "onsen_monitoring"},
                "joins": [],
            },
            DataCategory.ACTIVITY_METRICS: {
                "table": "activities",
                "columns": [
                    "id",
                    "strava_id",
                    "activity_type",
                    "duration_minutes",
                    "distance_km",
                    "calories_burned",
                    "elevation_gain_m",
                    "avg_heart_rate",
                    "max_heart_rate",
                ],
                "alias": "a",
                "filters": {},
                "joins": [],
            },
            DataCategory.ACTIVITY_HR_TIMESERIES: {
                "table": "activities",
                "columns": [
                    "id",
                    "strava_id",
                    "activity_type",
                    "activity_name",
                    "recording_start",
                    "route_data",  # JSON column with HR timeseries
                ],
                "alias": "a",
                "filters": {"avg_heart_rate__notnull": True},  # Only activities with HR data
                "joins": [],
                "parser": "_parse_hr_timeseries",  # Custom parser for JSON expansion
            },
        }

    def get_data_for_categories(
        self,
        categories: list[DataCategory],
        filters: Optional[dict[str, Any]] = None,
        time_range: Optional[tuple[datetime, datetime]] = None,
        spatial_bounds: Optional[tuple[float, float, float, float]] = None,
    ) -> pd.DataFrame:
        # pylint: disable=too-complex,too-many-locals,too-many-branches
        # Complexity justified: handles multiple data categories with joins and filtering
        """
        Get data for specified categories with optional filtering.

        Args:
            categories: List of data categories to retrieve
            filters: Additional filters to apply
            time_range: Time range filter (start, end)
            spatial_bounds: Spatial bounds (min_lat, max_lat, min_lon, max_lon)

        Returns:
            Combined DataFrame with data from all categories
        """
        if not categories:
            raise ValueError("At least one data category must be specified")

        # Build the main query
        main_category = categories[0]
        main_config = self._data_mappings[main_category]

        start_table = main_config["table"]
        start_alias = main_config["alias"]
        base_columns = ", ".join(
            [f"{start_alias}.{col}" for col in main_config["columns"]]
        )

        query = f"""
        SELECT DISTINCT {base_columns}
        FROM {start_table} {start_alias}
        """

        # Add joins for other categories
        join_tables = set()
        table_aliases = {start_table: start_alias}  # Track table aliases

        # If we didn't start with onsens, add the join to onsens first
        if start_table != "onsens":
            query += f"\nLEFT JOIN onsens o ON {start_alias}.onsen_id = o.id"
            table_aliases["onsens"] = "o"
            join_tables.add("onsens")

        for category in categories:
            config = self._data_mappings[category]
            for join_table, join_col, ref_col in config.get("joins", []):
                if join_table not in join_tables:
                    if join_table == "onsens":
                        continue
                    alias = join_table[0]
                    query += f"\nLEFT JOIN {join_table} {alias} ON {alias}.{join_col} = o.{ref_col}"
                    table_aliases[join_table] = alias
                    join_tables.add(join_table)

        # Add columns from all categories
        select_columns = []
        for category in categories:
            config = self._data_mappings[category]

            for col in config["columns"]:
                if col not in [
                    "id",
                    "onsen_id",
                    "name",
                    "region",
                    "latitude",
                    "longitude",
                    "address",
                ]:
                    # Use the correct table alias for each column
                    if config["table"] == "onsens":
                        table_alias = "o"
                    elif config["table"] == "onsen_visits":
                        if "onsen_visits" not in table_aliases:
                            query += "\nLEFT JOIN onsen_visits v ON v.onsen_id = o.id"
                            table_aliases["onsen_visits"] = "v"
                        table_alias = "v"
                    else:
                        table_alias = table_aliases.get(
                            config["table"], config["table"][0]
                        )

                    select_columns.append(f"{table_alias}.{col}")

        # Reconstruct the query with all columns in the SELECT statement
        if select_columns:
            # Remove the original SELECT DISTINCT line and replace it
            lines = query.split("\n")
            select_line = lines[0]
            from_line = lines[1]
            remaining_lines = lines[2:]

            # Create new SELECT statement with all columns
            all_columns = base_columns + ", " + ", ".join(select_columns)
            new_query = f"{select_line.replace(base_columns, all_columns)}\n{from_line}"

            # Add remaining lines (joins, WHERE, etc.)
            for line in remaining_lines:
                new_query += f"\n{line}"

            query = new_query

        # Add WHERE clause
        where_conditions = []

        # Apply filters
        if filters:
            for key, value in filters.items():
                if "__" in key:
                    field, operator = key.split("__", 1)
                    if operator == "notnull":
                        where_conditions.append(f"{field} IS NOT NULL")
                    elif operator == "isnull":
                        where_conditions.append(f"{field} IS NULL")
                    elif operator == "in":
                        if isinstance(value, (list, tuple)):
                            value_list = ", ".join([f"'{v}'" for v in value])
                            where_conditions.append(f"{field} IN ({value_list})")
                    elif operator == "gte":
                        where_conditions.append(f"{field} >= {value}")
                    elif operator == "lte":
                        where_conditions.append(f"{field} <= {value}")
                elif isinstance(value, str):
                    where_conditions.append(f"{key} = '{value}'")
                else:
                    where_conditions.append(f"{key} = {value}")

        # Apply time range filter
        if time_range:
            start_time, end_time = time_range
            where_conditions.append(f"visit_time >= '{start_time}'")
            where_conditions.append(f"visit_time <= '{end_time}'")

        # Apply spatial bounds filter
        if spatial_bounds:
            min_lat, max_lat, min_lon, max_lon = spatial_bounds
            where_conditions.append(f"latitude BETWEEN {min_lat} AND {max_lat}")
            where_conditions.append(f"longitude BETWEEN {min_lon} AND {max_lon}")

        if where_conditions:
            query += f"\nWHERE {' AND '.join(where_conditions)}"

        # Execute query
        try:
            result = self.session.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

            # Clean and preprocess the data
            df = self._clean_dataframe(df)

            # Apply custom parser if specified for the main category
            if "parser" in main_config:
                parser_method_name = main_config["parser"]
                if hasattr(self, parser_method_name):
                    parser_method = getattr(self, parser_method_name)
                    df = parser_method(df)
                else:
                    logger.warning(
                        f"Parser method {parser_method_name} not found for {main_category}"
                    )

            return df

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Broad exception justified: fallback to ORM on any query error
            logger.error(f"Error executing query: {e}")
            # Fallback to ORM approach
            return self._get_data_orm(categories, filters, time_range, spatial_bounds)

    def _get_data_orm(
        self,
        categories: list[DataCategory],
        filters: Optional[dict[str, Any]] = None,  # pylint: disable=unused-argument
        time_range: Optional[tuple[datetime, datetime]] = None,
        spatial_bounds: Optional[tuple[float, float, float, float]] = None,
    ) -> pd.DataFrame:
        # pylint: disable=too-complex
        # Complexity justified: ORM fallback handles multiple data category types
        """Fallback method using ORM queries."""
        dfs = []

        for category in categories:
            if category == DataCategory.ONSEN_BASIC:
                query = self.session.query(Onsen)
                if spatial_bounds:
                    min_lat, max_lat, min_lon, max_lon = spatial_bounds
                    query = query.filter(
                        Onsen.latitude.between(min_lat, max_lat),
                        Onsen.longitude.between(min_lon, max_lon),
                    )
                df = pd.read_sql(query.statement, self.session.bind)
                dfs.append(df)

            elif category in [
                DataCategory.VISIT_BASIC,
                DataCategory.VISIT_RATINGS,
                DataCategory.VISIT_EXPERIENCE,
                DataCategory.VISIT_LOGISTICS,
                DataCategory.VISIT_PHYSICAL,
                DataCategory.TEMPORAL,
                DataCategory.WEATHER,
                DataCategory.EXERCISE,
            ]:
                query = self.session.query(OnsenVisit).join(Onsen)

                if time_range:
                    start_time, end_time = time_range
                    query = query.filter(
                        OnsenVisit.visit_time.between(start_time, end_time)
                    )

                if spatial_bounds:
                    min_lat, max_lat, min_lon, max_lon = spatial_bounds
                    query = query.filter(
                        Onsen.latitude.between(min_lat, max_lat),
                        Onsen.longitude.between(min_lon, max_lon),
                    )

                df = pd.read_sql(query.statement, self.session.bind)
                dfs.append(df)

            elif category == DataCategory.HEART_RATE:
                query = self.session.query(HeartRateData).join(OnsenVisit, isouter=True)
                df = pd.read_sql(query.statement, self.session.bind)
                dfs.append(df)

            elif category in [
                DataCategory.ACTIVITY_ALL,
                DataCategory.ACTIVITY_EXERCISE,
                DataCategory.ACTIVITY_METRICS,
            ]:
                query = self.session.query(Activity)

                # Apply filters based on category
                if category == DataCategory.ACTIVITY_EXERCISE:
                    query = query.filter(Activity.activity_type != ExerciseType.ONSEN_MONITORING.value)

                if time_range:
                    start_time, end_time = time_range
                    query = query.filter(
                        Activity.recording_start.between(start_time, end_time)
                    )

                df = pd.read_sql(query.statement, self.session.bind)
                dfs.append(df)

            elif category == DataCategory.ACTIVITY_ONSEN:
                # Join with visits for onsen monitoring activities
                query = (
                    self.session.query(Activity)
                    .outerjoin(OnsenVisit, Activity.visit_id == OnsenVisit.id)
                    .filter(Activity.activity_type == ExerciseType.ONSEN_MONITORING.value)
                )

                if time_range:
                    start_time, end_time = time_range
                    query = query.filter(
                        Activity.recording_start.between(start_time, end_time)
                    )

                df = pd.read_sql(query.statement, self.session.bind)
                dfs.append(df)

        # Combine all dataframes
        if dfs:
            # Use onsen_id as the key for joining
            result_df = dfs[0]
            for df in dfs[1:]:
                if "onsen_id" in df.columns and "onsen_id" in result_df.columns:
                    result_df = result_df.merge(
                        df, on="onsen_id", how="outer", suffixes=("", f"_{len(dfs)}")
                    )
                else:
                    result_df = pd.concat([result_df, df], axis=1)

            return self._clean_dataframe(result_df)

        return pd.DataFrame()

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess the dataframe."""
        if df.empty:
            return df

        # Convert date columns
        date_columns = ["visit_time", "recording_start", "recording_end"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Convert numeric columns
        numeric_columns = [
            "latitude",
            "longitude",
            "entry_fee_yen",
            "temperature_outside_celsius",
            "stay_length_minutes",
            "travel_time_minutes",
            "accessibility_rating",
            "cleanliness_rating",
            "navigability_rating",
            "view_rating",
            "atmosphere_rating",
            "personal_rating",
            "main_bath_temperature",
            "sauna_temperature",
            "outdoor_bath_temperature",
            "smell_intensity_rating",
            "changing_room_cleanliness_rating",
            "locker_availability_rating",
            "rest_area_rating",
            "food_quality_rating",
            "sauna_rating",
            "outdoor_bath_rating",
            # Activity columns
            "duration_minutes",
            "distance_km",
            "calories_burned",
            "elevation_gain_m",
            "avg_heart_rate",
            "min_heart_rate",
            "max_heart_rate",
            "energy_level_change",
            "hydration_level",
            "average_heart_rate",
            "min_heart_rate",
            "max_heart_rate",
            "total_recording_minutes",
            "data_points_count",
        ]

        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Convert boolean columns
        boolean_columns = [
            "had_soap",
            "had_sauna",
            "had_outdoor_bath",
            "had_rest_area",
            "had_food_service",
            "massage_chair_available",
            "sauna_visited",
            "sauna_steam",
            "outdoor_bath_visited",
            "multi_onsen_day",
        ]

        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].astype(bool)

        # Handle missing values
        df = df.replace([np.inf, -np.inf], np.nan)

        # Add derived columns
        df = self._add_derived_columns(df)

        return df

    def _add_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add useful derived columns for analysis."""
        # Time-based columns
        if "visit_time" in df.columns:
            df["visit_date"] = df["visit_time"].dt.date
            df["visit_month"] = df["visit_time"].dt.month
            df["visit_year"] = df["visit_time"].dt.year
            df["visit_day_of_week"] = df["visit_time"].dt.day_name()
            df["visit_hour"] = df["visit_time"].dt.hour
            df["visit_season"] = df["visit_time"].dt.month.map(
                {
                    12: "Winter",
                    1: "Winter",
                    2: "Winter",
                    3: "Spring",
                    4: "Spring",
                    5: "Spring",
                    6: "Summer",
                    7: "Summer",
                    8: "Summer",
                    9: "Autumn",
                    10: "Autumn",
                    11: "Autumn",
                }
            )

        # Rating aggregates
        rating_columns = [
            col
            for col in df.columns
            if col.endswith("_rating") and col != "personal_rating"
        ]
        if rating_columns:
            df["average_rating"] = df[rating_columns].mean(axis=1)
            df["rating_count"] = df[rating_columns].notna().sum(axis=1)

        # Distance calculations (if we have location data)
        if all(col in df.columns for col in ("latitude", "longitude")):
            # This would need to be enhanced with actual location data
            pass

        # Experience quality score
        experience_columns = [
            "cleanliness_rating",
            "navigability_rating",
            "view_rating",
            "atmosphere_rating",
            "changing_room_cleanliness_rating",
        ]
        if all(col in df.columns for col in experience_columns):
            df["experience_quality_score"] = df[experience_columns].mean(axis=1)

        return df

    def get_onsen_summary_data(self) -> pd.DataFrame:
        """Get summary data for all onsens with visit statistics."""
        query = """
        SELECT 
            o.id, o.name, o.region, o.latitude, o.longitude, o.address,
            o.admission_fee, o.spring_quality,
            COUNT(v.id) as visit_count,
            AVG(v.personal_rating) as avg_personal_rating,
            AVG(v.cleanliness_rating) as avg_cleanliness_rating,
            AVG(v.atmosphere_rating) as avg_atmosphere_rating,
            AVG(v.entry_fee_yen) as avg_entry_fee,
            AVG(v.stay_length_minutes) as avg_stay_length,
            MIN(v.visit_time) as first_visit,
            MAX(v.visit_time) as last_visit
        FROM onsens o
        LEFT JOIN onsen_visits v ON o.id = v.onsen_id
        WHERE o.latitude IS NOT NULL AND o.longitude IS NOT NULL
        GROUP BY o.id, o.name, o.region, o.latitude, o.longitude, o.address, o.admission_fee, o.spring_quality
        """

        try:
            result = self.session.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return self._clean_dataframe(df)
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Broad exception justified: any query error should return empty DataFrame
            logger.error(f"Error getting onsen summary data: {e}")
            return pd.DataFrame()

    def get_visit_trends_data(self, days: int = 365) -> pd.DataFrame:
        """Get visit trends data over time."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query = """
        SELECT 
            DATE(visit_time) as visit_date,
            COUNT(*) as visit_count,
            AVG(personal_rating) as avg_rating,
            AVG(entry_fee_yen) as avg_entry_fee,
            AVG(stay_length_minutes) as avg_stay_length,
            COUNT(DISTINCT onsen_id) as unique_onsens_visited
        FROM onsen_visits
        WHERE visit_time BETWEEN :start_date AND :end_date
        GROUP BY DATE(visit_time)
        ORDER BY visit_date
        """

        try:
            result = self.session.execute(
                text(query), {"start_date": start_date, "end_date": end_date}
            )
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            df["visit_date"] = pd.to_datetime(df["visit_date"])
            return df
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Broad exception justified: any query error should return empty DataFrame
            logger.error(f"Error getting visit trends data: {e}")
            return pd.DataFrame()

    def get_spatial_analysis_data(self) -> pd.DataFrame:
        """Get data specifically for spatial analysis."""
        query = """
        SELECT 
            o.id, o.name, o.region, o.latitude, o.longitude, o.address,
            o.admission_fee, o.spring_quality,
            COUNT(v.id) as visit_count,
            AVG(v.personal_rating) as avg_rating,
            AVG(v.entry_fee_yen) as avg_entry_fee,
            AVG(v.cleanliness_rating) as avg_cleanliness,
            AVG(v.atmosphere_rating) as avg_atmosphere
        FROM onsens o
        LEFT JOIN onsen_visits v ON o.id = v.onsen_id
        WHERE o.latitude IS NOT NULL AND o.longitude IS NOT NULL
        GROUP BY o.id, o.name, o.region, o.latitude, o.longitude, o.address, o.admission_fee, o.spring_quality
        """

        try:
            result = self.session.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return self._clean_dataframe(df)
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Broad exception justified: any query error should return empty DataFrame
            logger.error(f"Error getting spatial analysis data: {e}")
            return pd.DataFrame()

    def _parse_hr_timeseries(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse heart rate time-series JSON from route_data into expanded DataFrame.

        Transforms route_data JSON column into individual rows with HR measurements.
        Each row represents one time point with HR data from an activity.

        Args:
            df: DataFrame with route_data JSON column

        Returns:
            Expanded DataFrame with one row per HR measurement point:
                - activity_id: Original activity ID
                - strava_id: Strava activity ID
                - activity_type: Type of activity
                - activity_name: Activity name
                - timestamp: ISO timestamp of measurement
                - time_offset: Seconds from activity start
                - hr: Heart rate in bpm
                - lat: Latitude (optional)
                - lon: Longitude (optional)
                - elevation: Elevation in meters (optional)
                - speed_mps: Speed in m/s (optional)
        """
        import json

        rows = []
        for _, row in df.iterrows():
            if pd.isna(row["route_data"]) or not row["route_data"]:
                continue

            try:
                route_points = json.loads(row["route_data"])

                # Filter to only points with HR data
                for point in route_points:
                    if "hr" not in point:
                        continue

                    # Calculate time offset from activity start
                    point_timestamp = pd.to_datetime(point["timestamp"])
                    activity_start = pd.to_datetime(row["recording_start"])
                    time_offset = (point_timestamp - activity_start).total_seconds()

                    # Build expanded row
                    expanded_row = {
                        "activity_id": row["id"],
                        "strava_id": row["strava_id"],
                        "activity_type": row["activity_type"],
                        "activity_name": row.get("activity_name"),
                        "timestamp": point["timestamp"],
                        "time_offset": time_offset,
                        "hr": point["hr"],
                    }

                    # Add optional fields if present
                    if "lat" in point:
                        expanded_row["lat"] = point["lat"]
                    if "lon" in point:
                        expanded_row["lon"] = point["lon"]
                    if "elevation" in point:
                        expanded_row["elevation"] = point["elevation"]
                    if "speed_mps" in point:
                        expanded_row["speed_mps"] = point["speed_mps"]

                    rows.append(expanded_row)

            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to parse route_data for activity {row['id']}: {e}"
                )
                continue
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning(
                    f"Error processing HR timeseries for activity {row['id']}: {e}"
                )
                continue

        if not rows:
            logger.warning("No HR timeseries data found in activities")
            return pd.DataFrame()

        result_df = pd.DataFrame(rows)
        result_df["timestamp"] = pd.to_datetime(result_df["timestamp"])
        return result_df

    def clear_cache(self) -> None:
        """Clear the data cache."""
        self._cached_data.clear()

    def get_cached_data(self, key: str) -> Optional[pd.DataFrame]:
        """Get cached data if available."""
        return self._cached_data.get(key)

    def cache_data(self, key: str, data: pd.DataFrame) -> None:
        """Cache data for future use."""
        self._cached_data[key] = data.copy()
