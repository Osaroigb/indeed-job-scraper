from .models import Base
from config import DATABASE_URI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

#? Create the SQLAlchemy engine
engine = create_engine(DATABASE_URI)

#* Create a configured "Session" class
Session = sessionmaker(bind=engine)

#! Create a session instance
session = Session()

#? Create all tables in the engine (if they don't exist)
Base.metadata.create_all(engine)

print("Database initialized and tables created.")