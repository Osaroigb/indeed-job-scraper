import os
import logging
from dotenv import load_dotenv
from colorlog import ColoredFormatter

# Load environment variables from .env file
load_dotenv()

# Constants for environment variable names
BASE_URL_VAR = "BASE_URL"
MAX_BOTS_VAR = "MAX_BOTS" # Maximum number of concurrent bots
RETRY_LIMIT_VAR = "RETRY_LIMIT"
LOCATION_VAR = "LOCATION" # Target job location
DATABASE_URI_VAR = "DATABASE_URI"
SCRAPER_API_KEY_VAR = "SCRAPER_API_KEY"
SCRAPER_API_URL_VAR = "SCRAPER_API_URL"
TIMEOUT_URLS_FILE_VAR = "TIMEOUT_URLS_FILE"
APOLLO_API_KEY_VAR = "APOLLO_API_KEY"
APOLLO_API_URL_VAR = "APOLLO_API_URL"

# Configuration class
class Config:
    BASE_URL: str = os.getenv(BASE_URL_VAR)
    MAX_BOTS: int = int(os.getenv(MAX_BOTS_VAR))
    RETRY_LIMIT: int = int(os.getenv(RETRY_LIMIT_VAR))
    LOCATION: str = os.getenv(LOCATION_VAR)
    DATABASE_URI: str = os.getenv(DATABASE_URI_VAR)
    SCRAPER_API_KEY: str = os.getenv(SCRAPER_API_KEY_VAR)
    SCRAPER_API_URL: str = os.getenv(SCRAPER_API_URL_VAR)
    TIMEOUT_URLS_FILE: str = os.getenv(TIMEOUT_URLS_FILE_VAR)
    APOLLO_API_KEY: str = os.getenv(APOLLO_API_KEY_VAR)
    APOLLO_API_URL: str = os.getenv(APOLLO_API_URL_VAR)

    @classmethod
    def validate_env(cls):
        required_vars = [
            DATABASE_URI_VAR,
            SCRAPER_API_KEY_VAR,
            SCRAPER_API_URL_VAR,
            MAX_BOTS_VAR,
            RETRY_LIMIT_VAR,
            LOCATION_VAR,
            BASE_URL_VAR,
            TIMEOUT_URLS_FILE_VAR,
            APOLLO_API_KEY_VAR,
            APOLLO_API_URL_VAR
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Define color format for log messages
formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
    },
)

# Set up logging with color formatter
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])