from typing import Optional
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, relationship
from loguru import logger

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
    - visit_time: date/time of the visit
    - length_minutes: how long you stayed
    - rating: your personal rating (1-10, or 1-5, or whatever you choose)
    - heart_rate_data: can store some textual or JSON data about heart rate
    - sauna_visited: whether you used the sauna
    - any other columns you'd like to add
    """
    __tablename__ = "onsen_visits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    onsen_id = Column(Integer, ForeignKey("onsens.id"), nullable=False)
    visit_time = Column(DateTime)
    length_minutes = Column(Integer)
    rating = Column(Integer)
    heart_rate_data = Column(String)
    sauna_visited = Column(Boolean, default=False)

    onsen = relationship("Onsen", back_populates="visits")
