from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, event
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Location(Base):
    """
    The Location table. Stores user-defined locations for distance calculations.

    Columns:
    - id: primary key
    - name: name of the location
    - latitude, longitude: map coordinates
    - description: optional description of the location
    """

    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(String)


class Onsen(Base):
    """
    The Onsen table. Stores info about each hot spring.

    Columns:
    - id: primary key
    - ban_number: a "ban" code or unique number for the onsen (string or integer)
    - name: name of the onsen
    - region: region in the city (e.g., area of Beppu)
    - latitude, longitude: map coordinates
    - description: textual description
    - business_form (営業形態)
    - address (住所)
    - phone (電話)
    - admission_fee (入浴料金)
    - usage_time (利用時間)
    - closed_days (定休日ほか)
    - private_bath (家族湯(貸切湯))
    - spring_quality (泉質)
    - nearest_bus_stop (最寄バス停)
    - nearest_station (最寄駅(徒歩))
    - parking (駐車場)
    - remarks (備考)
    """

    __tablename__ = "onsens"

    # Allow explicit assignment of IDs from scraped data
    id = Column(Integer, primary_key=True, autoincrement=False)
    ban_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    region = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    description = Column(String)

    business_form = Column(String)
    address = Column(String)
    phone = Column(String)
    admission_fee = Column(String)
    usage_time = Column(String)
    closed_days = Column(String)
    private_bath = Column(String)
    spring_quality = Column(String)
    nearest_bus_stop = Column(String)
    nearest_station = Column(String)
    parking = Column(String)
    remarks = Column(String)

    # Relationship to visits
    visits = relationship("OnsenVisit", back_populates="onsen")


class OnsenVisit(Base):
    """
    A single onsen visit. Ties to one onsen (foreign key).

    Columns:
    - id: primary key
    - onsen_id: foreign key referencing Onsen
    - entry_fee_yen: the entry fee for the onsen
    - payment_method: the payment method used (cash, credit card, etc.)
    - weather: the weather at the time of the visit
    - temperature_outside_celsius: the temperature outside the onsen
    - visit_time: date/time of the visit
    - stay_length_minutes: how long I stayed
    - visited_with: who I visited the onsen with (e.g., "friend", "group", "alone")
    - travel_mode: how I got to the onsen (e.g., "car", "train", "bus", "walk", "run", "bike", "other")
    - travel_time_minutes: how long it took to get to the onsen
    - accessibility_rating: how easy it was to find / enter the onsen (1-10)
    - crowd_level: the crowd level at the onsen ("busy", "moderate", "quiet", "empty")
    - interacted_with_locals: whether I talked with locals inside the onsen
    - local_interaction_quality_rating: how pleasant the interaction with locals was (1-10)
    - view_rating: my rating of the view from the onsen (1-10)
    - navigability_rating: my rating of the navigability inside the onsen (1-10)
    - cleanliness_rating: my rating of the cleanliness (1-10)
    - main_bath_type: the type of main bath (e.g., "open air", "indoor", "other")
    - main_bath_temperature: the temperature of the main bath
    - water_color: the color of the water in the main bath (e.g., "clear", "brown", "green", "other")
    - smell_intensity_rating: my rating of the smell intensity in the main bath (1-10)
    - changing_room_cleanliness_rating: my rating of the cleanliness of the changing room (1-10)
    - locker_availability_rating: my rating of the availability of lockers (1-10)
    - had_soap: whether there was soap at the onsen
    - had_sauna: whether there was a sauna at the onsen
    - had_outdoor_bath: whether there was an outdoor bath at the onsen
    - had_rest_area: whether there was a rest area at the onsen
    - rest_area_used: whether I used the rest area
    - rest_area_rating: my rating of the rest area (1-10)
    - had_food_service: whether there was food service at the onsen
    - food_service_used: whether I used the food service
    - food_quality_rating: my rating of the quality of the food (1-10)
    - massage_chair_available: whether there was a massage chair at the onsen
    - sauna_visited: whether I used the sauna
    - sauna_temperature: the temperature of the sauna
    - sauna_steam: whether the sauna had steam
    - sauna_duration_minutes: how long I stayed in the sauna
    - sauna_rating: my rating of the sauna (1-10)
    - outdoor_bath_visited: whether I used the outdoor bath
    - outdoor_bath_temperature: the temperature of the outdoor bath
    - outdoor_bath_rating: my rating of the outdoor bath (1-10)
    - pre_visit_mood: my mood before the onsen (e.g., "relaxed", "stressed", "anxious", "other")
    - post_visit_mood: my mood after the onsen (e.g., "relaxed", "stressed", "anxious", "other")
    - energy_level_change: how much my energy level changed before and after the onsen (scale to -5 to +5 before to after)
    - hydration_level: before entering, to track impact on well-being (scale to 1 to 10)
    - multi_onsen_day: whether this was a multi-onsen day (boolean)
    - visit_order: the order of this visit in the multi-onsen day (integer)
    - atmosphere_rating: my rating of the atmosphere (1-10)
    - personal_rating: my personal rating (1-10)
    - notes: optional notes about the visit
    """

    __tablename__ = "onsen_visits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    onsen_id = Column(Integer, ForeignKey("onsens.id"), nullable=False)
    entry_fee_yen = Column(Integer)
    payment_method = Column(String)
    weather = Column(String)
    temperature_outside_celsius = Column(Float)
    visit_time = Column(DateTime)
    stay_length_minutes = Column(Integer)
    visited_with = Column(String)
    travel_mode = Column(String)
    travel_time_minutes = Column(Integer)
    accessibility_rating = Column(Integer)
    crowd_level = Column(String)
    interacted_with_locals = Column(Boolean)
    local_interaction_quality_rating = Column(Integer)
    cleanliness_rating = Column(Integer)
    navigability_rating = Column(Integer)
    view_rating = Column(Integer)
    main_bath_type = Column(String)
    main_bath_temperature = Column(Float)
    water_color = Column(String)
    smell_intensity_rating = Column(Integer)
    changing_room_cleanliness_rating = Column(Integer)
    locker_availability_rating = Column(Integer)
    had_soap = Column(Boolean)
    had_sauna = Column(Boolean)
    had_outdoor_bath = Column(Boolean)
    had_rest_area = Column(Boolean)
    rest_area_used = Column(Boolean)
    rest_area_rating = Column(Integer)
    had_food_service = Column(Boolean)
    food_service_used = Column(Boolean)
    food_quality_rating = Column(Integer)
    massage_chair_available = Column(Boolean)
    sauna_visited = Column(Boolean)
    sauna_temperature = Column(Float)
    sauna_steam = Column(Boolean)
    sauna_duration_minutes = Column(Integer)
    sauna_rating = Column(Integer)
    outdoor_bath_visited = Column(Boolean)
    outdoor_bath_temperature = Column(Float)
    outdoor_bath_rating = Column(Integer)
    pre_visit_mood = Column(String)
    post_visit_mood = Column(String)
    energy_level_change = Column(Integer)
    hydration_level = Column(Integer)
    multi_onsen_day = Column(Boolean)
    visit_order = Column(Integer)
    atmosphere_rating = Column(Integer)
    personal_rating = Column(Integer)
    notes = Column(String)

    onsen = relationship("Onsen", back_populates="visits")


class Activity(Base):
    """
    Unified activity model for all Strava-sourced activities.

    Replaces the separate heart_rate_data and exercise_sessions tables with a
    single unified model. Activities can be imported from Strava or created manually.
    Activities with activity_type='onsen_monitoring' represent onsen heart rate monitoring sessions.

    Columns:
    - id: primary key
    - strava_id: Strava activity ID (unique, optional - only for Strava-sourced activities)
    - visit_id: optional foreign key to onsen visit (only for onsen monitoring activities)
    - recording_start: when the activity started (renamed from start_time for clarity)
    - recording_end: when the activity ended (renamed from end_time for clarity)
    - duration_minutes: total duration in minutes
    - activity_type: type of activity (running, cycling, yoga, onsen_monitoring, etc.)
    - activity_name: specific activity name from Strava
    - workout_type: Strava workout type (preserved for reference)
    - distance_km: distance covered in kilometers
    - calories_burned: estimated calories burned
    - elevation_gain_m: total elevation gain in meters
    - avg_heart_rate: average heart rate during activity
    - min_heart_rate: minimum heart rate recorded
    - max_heart_rate: maximum heart rate recorded
    - indoor_outdoor: whether activity was indoor or outdoor
    - weather_conditions: weather during outdoor activity
    - route_data: JSON-encoded time-series data including GPS coordinates, elevation,
      heart rate, and speed. Each point in the array contains:
        * timestamp: ISO 8601 timestamp
        * lat/lon: GPS coordinates (optional, for outdoor activities)
        * elevation: Elevation in meters (optional)
        * hr: Heart rate in beats per minute (optional, enables detailed HR analysis)
        * speed_mps: Speed in meters per second (optional)
      Format: JSON string of list[dict], e.g.:
        '[{"timestamp":"2025-10-30T10:00:00","lat":33.279,"lon":131.500,"elevation":50,"hr":120,"speed_mps":3.5},...]'
    - strava_data_hash: SHA-256 hash of Strava data for sync detection (optional)
    - last_synced_at: timestamp of last sync from Strava (optional)
    - notes: optional notes about the activity
    - created_at: when this record was created in the database
    """

    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strava_id = Column(String, unique=True, nullable=True, index=True)
    visit_id = Column(Integer, ForeignKey("onsen_visits.id"), nullable=True)
    recording_start = Column(DateTime, nullable=False, index=True)
    recording_end = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    activity_type = Column(String, nullable=False, index=True)
    activity_name = Column(String)
    workout_type = Column(String)
    distance_km = Column(Float)
    calories_burned = Column(Integer)
    elevation_gain_m = Column(Float)
    avg_heart_rate = Column(Float)
    min_heart_rate = Column(Float)
    max_heart_rate = Column(Float)
    indoor_outdoor = Column(String)
    weather_conditions = Column(String)
    route_data = Column(String)  # JSON string
    strava_data_hash = Column(String, nullable=True)
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    visit = relationship("OnsenVisit", foreign_keys=[visit_id])


# Event listener to auto-calculate duration_minutes if not provided
@event.listens_for(Activity, "before_insert")
@event.listens_for(Activity, "before_update")
def calculate_duration_minutes(mapper, connection, target):
    """
    Automatically calculate duration_minutes from recording_start and recording_end
    if duration_minutes is not provided.
    """
    if target.duration_minutes is None and target.recording_start and target.recording_end:
        delta = target.recording_end - target.recording_start
        target.duration_minutes = int(delta.total_seconds() / 60)


class WeightMeasurement(Base):
    """
    Weight measurement tracking for the Onsendo challenge.

    Tracks body weight over time to monitor health trends during the challenge.
    Measurements can be manually entered or imported from various sources
    (smart scales, Apple Health, etc.).

    Columns:
    - id: primary key
    - measurement_time: when the weight was measured (with timezone awareness)
    - weight_kg: body weight in kilograms
    - measurement_conditions: conditions at time of measurement (e.g., "fasted", "after_meal", "post_workout")
    - time_of_day: general time of day (e.g., "morning", "afternoon", "evening")
    - hydrated_before: whether water was consumed before measurement (True if hydrated, False/None if empty stomach)
    - data_source: source of the measurement (manual, scale, apple_health, etc.)
    - data_file_path: path to original data file if imported
    - data_hash: SHA-256 hash of data file for integrity verification
    - notes: optional notes about the measurement
    - created_at: when this record was created in the database
    """

    __tablename__ = "weight_measurements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    measurement_time = Column(DateTime, nullable=False, index=True)
    weight_kg = Column(Float, nullable=False)
    measurement_conditions = Column(
        String
    )  # Optional: fasted, after_meal, post_workout, etc.
    time_of_day = Column(String)  # Optional: morning, afternoon, evening
    hydrated_before = Column(Boolean)  # Optional: True if drank water before measurement
    data_source = Column(String, nullable=False)  # manual, scale, apple_health, etc.
    data_file_path = Column(String)  # Optional: path if imported from file
    data_hash = Column(String)  # Optional: SHA-256 hash for file integrity
    notes = Column(String)  # Optional: additional notes
    created_at = Column(DateTime, default=datetime.utcnow)


class RuleRevision(Base):
    """
    Rule revisions for the Onsendo challenge ruleset.

    Tracks weekly reviews and rule modifications following the Rule Review Sunday template.

    Columns:
    - id: primary key
    - version_number: sequential version number (unique)
    - revision_date: when the revision was created
    - effective_date: when the rule changes take effect
    - week_start_date: start of the week being reviewed
    - week_end_date: end of the week being reviewed

    Weekly Review Data (Summary Metrics):
    - onsen_visits_count: number of onsen visits this week
    - total_soaking_hours: total hours spent soaking
    - sauna_sessions_count: number of sauna sessions
    - running_distance_km: total running distance in km
    - gym_sessions_count: number of gym sessions
    - long_exercise_completed: whether a long exercise session was completed (hike or long run >= 15km/2.5hr)
    - rest_days_count: number of rest days

    Health and Wellbeing:
    - energy_level: energy level rating (1-10)
    - sleep_hours: average sleep hours per night
    - sleep_quality_rating: subjective sleep quality description
    - soreness_notes: notes about soreness, pain, or warning signs
    - hydration_nutrition_notes: notes about hydration and nutrition
    - mood_mental_state: mood and mental state notes

    Reflections:
    - reflection_positive: what went particularly well
    - reflection_patterns: patterns or improvements noticed
    - reflection_warnings: any warning signs (fatigue, skin, dehydration)
    - reflection_standout_onsens: which onsens stood out and why
    - reflection_routine_notes: which elements felt natural or forced

    Rule Adjustment Context:
    - adjustment_reason: reason for adjustment (fatigue, injury, schedule, etc.)
    - adjustment_description: high-level description of modification
    - expected_duration: temporary or permanent
    - health_safeguard_applied: health safeguard measures taken

    Plans for Next Week:
    - next_week_focus: focus area (recovery, pace stabilization, exploration)
    - next_week_goals: intentional goals (specific onsens, route clusters, workout balance)
    - next_week_sauna_limit: sauna limit for the week
    - next_week_run_volume: estimated total run volume
    - next_week_hike_destination: hike destination idea

    Revision Metadata:
    - sections_modified: JSON array of section numbers/names modified
    - revision_summary: brief description for listings
    - markdown_file_path: path to detailed revision markdown
    - created_at: when this record was created in the database
    """

    __tablename__ = "rule_revisions"

    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    version_number = Column(Integer, unique=True, nullable=False)
    revision_date = Column(DateTime, nullable=False)
    effective_date = Column(DateTime, nullable=False)
    week_start_date = Column(String, nullable=False)  # YYYY-MM-DD format
    week_end_date = Column(String, nullable=False)  # YYYY-MM-DD format

    # Weekly Review Data - Summary Metrics
    onsen_visits_count = Column(Integer)
    total_soaking_hours = Column(Float)
    sauna_sessions_count = Column(Integer)
    running_distance_km = Column(Float)
    gym_sessions_count = Column(Integer)
    long_exercise_completed = Column(Boolean)
    rest_days_count = Column(Integer)

    # Health and Wellbeing
    energy_level = Column(Integer)  # 1-10
    sleep_hours = Column(Float)
    sleep_quality_rating = Column(String)
    soreness_notes = Column(String)
    hydration_nutrition_notes = Column(String)
    mood_mental_state = Column(String)

    # Reflections
    reflection_positive = Column(String)
    reflection_patterns = Column(String)
    reflection_warnings = Column(String)
    reflection_standout_onsens = Column(String)
    reflection_routine_notes = Column(String)

    # Rule Adjustment Context
    adjustment_reason = Column(String)
    adjustment_description = Column(String)
    expected_duration = Column(String)  # temporary/permanent
    health_safeguard_applied = Column(String)

    # Plans for Next Week
    next_week_focus = Column(String)
    next_week_goals = Column(String)
    next_week_sauna_limit = Column(Integer)
    next_week_run_volume = Column(Float)
    next_week_hike_destination = Column(String)

    # Revision Metadata
    sections_modified = Column(String)  # JSON array
    revision_summary = Column(String)
    markdown_file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
