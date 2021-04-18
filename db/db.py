from config import DATABASE_URI
from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from models import Model, Player, CareerBatStats, CareerFieldStats, CareerBowlStats

engine = create_engine(DATABASE_URI)

session = sessionmaker(bind=engine)


def recreate_database():
    Model.metadata.drop_all(engine)
    Model.metadata.create_all(engine)


if __name__ == "__main__":
    recreate_database()

    # Update players list
    