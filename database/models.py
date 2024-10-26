from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, JSON

Base = declarative_base()

class JobSearch(Base):
    __tablename__ = 'job_search'
    
    id = Column(Integer, primary_key=True)
    job_title = Column(String, nullable=False)
    generated_link = Column(String, nullable=False)
    last_page_number = Column(Integer) # New column for last page
    pagination_links = Column(JSON, nullable=True)  # Store pagination links for each page
    date_scraped = Column(DateTime, default=datetime.now(timezone.utc))