import os
from dotenv import load_dotenv

load_dotenv()

BOT_LIMIT = 80  # Maximum number of concurrent bots
LOCATION = 'London'  # Target job location
DATABASE_URI = os.getenv("DATABASE_URI")
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")