from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()

class JobSearch(Base):
    __tablename__ = 'job_search'
    
    id = Column(Integer, primary_key=True)
    job_title = Column(String, nullable=False)
    generated_link = Column(String, nullable=False)
    date_scraped = Column(DateTime, default=datetime.now(datetime.timezone.utc))