## player.py ##

from sqlalchemy import Column, Date, Enum, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import UserDefinedType

from .base import Model

from .enum import Format


class Player(Model):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)

    # Name fields
    fname = Column(String)
    mname = Column(String)
    lname = Column(String)
    inits = Column(String)

    dob = Column(Date)

    # Relationships
    stats_bat = relationship("CareerBatStats")
    stats_field = relationship("CareerFieldStats")
    stats_bowl = relationship("CareerBowlStats")


class CareerBatStats(Model):
    __tablename__ = "career_batting_stats"

    id = Column(Integer, primary_key=True)

    format = Column(Enum(Format))
    matches = Column(Integer)
    innings = Column(Integer)
    not_outs = Column(Integer)
    runs = Column(Integer)
    high_score = Column(Integer)
    average = Column(Float)
    balls_faced = Column(Float)
    strike_rate = Column(Float)
    hundreds = Column(Integer)
    fifties = Column(Integer)
    fours = Column(Integer)
    sixes = Column(Integer)

    player_id = Column(Integer, ForeignKey("players.id"))


class CareerFieldStats(Model):
    __tablename__ = "career_fielding_stats"

    id = Column(Integer, primary_key=True)

    format = Column(Enum(Format))
    catches = Column(Integer)
    stumpings = Column(Integer)

    player_id = Column(Integer, ForeignKey("players.id"))


class BowlFigures(UserDefinedType):
    pass


class CareerBowlStats(Model):
    __tablename__ = "career_bowling_stats"

    id = Column(Integer, primary_key=True)

    format = Column(Enum(Format))
    matches = Column(Integer)
    balls = Column(Integer)
    runs = Column(Integer)
    wickets = Column(Integer)
    # bb_innings = Column(BowlFigures)
    # bb_match = Column(BowlFigures)
    average = Column(Float)
    economy = Column(Float)
    strike_rate = Column(Float)
    four_wh = Column(Integer)
    five_wh = Column(Integer)
    ten_wh = Column(Integer)

    player_id = Column(Integer, ForeignKey("players.id"))
