from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey

Base = declarative_base()

class JobSearch(Base):
    __tablename__ = 'job_search'
    
    id = Column(Integer, primary_key=True)
    job_title = Column(String, nullable=False)
    generated_link = Column(String, nullable=False)
    last_page_number = Column(Integer) # New column for last page
    pagination_links = Column(JSON, nullable=True)  # Store pagination links for each page
    date_scraped = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationship to JobListing
    job_listings = relationship("JobListing", back_populates="job_search")


class JobListing(Base):
    __tablename__ = 'job_listing'
    
    id = Column(Integer, primary_key=True)
    job_search_id = Column(Integer, ForeignKey('job_search.id'), nullable=False)
    date_scraped = Column(DateTime, default=datetime.now(timezone.utc))
    page_number = Column(Integer, nullable=False)
    job_title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    location = Column(String, nullable=True)
    posted_date = Column(String, nullable=True)  # May not always be a datetime
    job_link = Column(String, nullable=False)
    
    # Relationship back to JobSearch
    job_search = relationship("JobSearch", back_populates="job_listings")