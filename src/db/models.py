from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
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
    - time_of_day: the time of day of the visit (morning, afternoon, evening)
    - temperature_outside_celsius: the temperature outside the onsen
    - visit_time: date/time of the visit
    - stay_length_minutes: how long I stayed
    - visited_with: who I visited the onsen with (e.g., "friend", "group", "alone")
    - travel_mode: how I got to the onsen (e.g., "car", "train", "bus", "walk", "run", "bike", "other")
    - travel_time_minutes: how long it took to get to the onsen
    - accessibility_rating: how easy it was to find / enter the onsen (1-10)
    - exercise_before_onsen: whether I exercised before the onsen
    - exercise_type: the type of exercise I did before the onsen (e.g., "running", "walking", "cycling", "other")
    - exercise_length_minutes: how long I exercised before the onsen
    - crowd_level: the crowd level at the onsen ("busy", "moderate", "quiet", "empty")
    - view_rating: my rating of the view from the onsen (1-10)
    - navigability_rating: my rating of the navigability inside the onsen (1-10)
    - cleanliness_rating: my rating of the cleanliness (1-10)
    - main_bath_type: the type of main bath (e.g., "open air", "indoor", "other")
    - main_bath_temperature: the temperature of the main bath
    - main_bath_water_type: the type of water in the main bath (e.g., "sulfur", "salt", "other")
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
    - previous_location: onsen visit before this one (foreign key)
    - next_location: onsen visit after this one (foreign key)
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
    time_of_day = Column(String)
    temperature_outside_celsius = Column(Float)
    visit_time = Column(DateTime)
    stay_length_minutes = Column(Integer)
    visited_with = Column(String)
    travel_mode = Column(String)
    travel_time_minutes = Column(Integer)
    accessibility_rating = Column(Integer)
    exercise_before_onsen = Column(Boolean)
    exercise_type = Column(String)
    exercise_length_minutes = Column(Integer)
    crowd_level = Column(String)
    cleanliness_rating = Column(Integer)
    navigability_rating = Column(Integer)
    view_rating = Column(Integer)
    main_bath_type = Column(String)
    main_bath_temperature = Column(Float)
    main_bath_water_type = Column(String)
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
    previous_location = Column(Integer, ForeignKey("onsen_visits.id"))
    next_location = Column(Integer, ForeignKey("onsen_visits.id"))
    multi_onsen_day = Column(Boolean)
    visit_order = Column(Integer)
    atmosphere_rating = Column(Integer)
    personal_rating = Column(Integer)
    notes = Column(String)

    onsen = relationship("Onsen", back_populates="visits")


class HeartRateData(Base):
    """
    Heart rate data recorded during onsen visits or other activities.

    Columns:
    - id: primary key
    - recording_start: when the recording started
    - recording_end: when the recording ended
    - data_format: format of the data (e.g., "garmin_fit", "apple_health", "csv")
    - data_file_path: path to the original data file
    - data_hash: hash of the data for integrity verification
    - average_heart_rate: average heart rate during the recording
    - min_heart_rate: minimum heart rate recorded
    - max_heart_rate: maximum heart rate recorded
    - total_recording_minutes: total duration of the recording
    - data_points_count: number of heart rate measurements
    - notes: optional notes about the recording
    - created_at: when this record was created in the database
    """

    __tablename__ = "heart_rate_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    visit_id = Column(Integer, ForeignKey("onsen_visits.id"), nullable=True)
    recording_start = Column(DateTime, nullable=False)
    recording_end = Column(DateTime, nullable=False)
    data_format = Column(String, nullable=False)
    data_file_path = Column(String, nullable=False)
    data_hash = Column(String, nullable=False)
    average_heart_rate = Column(Float, nullable=False)
    min_heart_rate = Column(Float, nullable=False)
    max_heart_rate = Column(Float, nullable=False)
    total_recording_minutes = Column(Integer, nullable=False)
    data_points_count = Column(Integer, nullable=False)
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    visit = relationship("OnsenVisit")


class ExerciseSession(Base):
    """
    Exercise session data recorded during various activities.

    Comprehensive tracking of workout sessions from various sources
    (Apple Watch, Garmin, manual entry) with support for GPS routes,
    heart rate data, and linking to onsen visits.

    Columns:
    - id: primary key
    - visit_id: optional foreign key to onsen visit (if exercise was before/after onsen)
    - heart_rate_id: optional foreign key to heart rate data (if HR was recorded)
    - recording_start: when the exercise started
    - recording_end: when the exercise ended
    - duration_minutes: total duration in minutes
    - exercise_type: type of exercise (running, gym, hiking, cycling, etc.)
    - activity_name: specific activity name (e.g., "Morning Run", "Leg Day")
    - workout_type: Apple Health workout type (if from Apple Health)
    - data_source: where the data came from (apple_health, garmin, manual, etc.)
    - data_file_path: path to the original data file (if imported)
    - data_hash: SHA-256 hash of the data file for integrity verification
    - distance_km: distance covered in kilometers (for cardio activities)
    - calories_burned: estimated calories burned
    - elevation_gain_m: total elevation gain in meters (for running/hiking)
    - avg_heart_rate: average heart rate during exercise
    - min_heart_rate: minimum heart rate recorded
    - max_heart_rate: maximum heart rate recorded
    - indoor_outdoor: whether exercise was indoor or outdoor
    - weather_conditions: weather during outdoor exercise
    - route_data: JSON-encoded GPS route data (lat/lon points, timestamps)
    - notes: optional notes about the exercise session
    - created_at: when this record was created in the database
    """

    __tablename__ = "exercise_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    visit_id = Column(Integer, ForeignKey("onsen_visits.id"), nullable=True)
    heart_rate_id = Column(Integer, ForeignKey("heart_rate_data.id"), nullable=True)
    recording_start = Column(DateTime, nullable=False, index=True)
    recording_end = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    exercise_type = Column(String, nullable=False, index=True)
    activity_name = Column(String)
    workout_type = Column(String)
    data_source = Column(String, nullable=False)
    data_file_path = Column(String)
    data_hash = Column(String)
    distance_km = Column(Float)
    calories_burned = Column(Integer)
    elevation_gain_m = Column(Float)
    avg_heart_rate = Column(Float)
    min_heart_rate = Column(Float)
    max_heart_rate = Column(Float)
    indoor_outdoor = Column(String)
    weather_conditions = Column(String)
    route_data = Column(String)  # JSON string
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    visit = relationship("OnsenVisit", foreign_keys=[visit_id])
    heart_rate = relationship("HeartRateData", foreign_keys=[heart_rate_id])


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
    - hike_completed: whether the weekly hike was completed
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
    hike_completed = Column(Boolean)
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
