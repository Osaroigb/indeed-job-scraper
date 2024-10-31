from .models import Base
from config import Config, logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use Config class to access DATABASE_URI
DATABASE_URI = Config.DATABASE_URI

#? Create the SQLAlchemy engine
engine = create_engine(DATABASE_URI)

#* Create a configured "Session" class
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

#? Create all tables in the engine (if they don't exist)
Base.metadata.create_all(engine)
logging.info("Database initialized and tables created.")