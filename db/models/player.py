## player.py ##

from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)

    # Name fields
    fname = Column(String)
    mname = Column(String)
    lname = Column(String)
    inits = Column(String)

    dob = Column(Date)
