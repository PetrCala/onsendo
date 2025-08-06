from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


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

    id = Column(Integer, primary_key=True, autoincrement=True)
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
    - excercise_before_onsen: whether I exercised before the onsen
    - excercise_type: the type of exercise I did before the onsen (e.g., "running", "walking", "cycling", "other")
    - excercise_length_minutes: how long I exercised before the onsen
    - crowd_level: the crowd level at the onsen ("busy", "moderate", "quiet", "empty")
    - heart_rate_data: can store some textual or JSON data about heart rate
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
    - rest_area_rating: my rating of the rest area (1-10)
    - had_food_service: whether there was food service at the onsen
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
    excercise_before_onsen = Column(Boolean)
    excercise_type = Column(String)
    excercise_length_minutes = Column(Integer)
    crowd_level = Column(String)
    heart_rate_data = Column(String)
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
    rest_area_rating = Column(Integer)
    had_food_service = Column(Boolean)
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

    onsen = relationship("Onsen", back_populates="visits")
