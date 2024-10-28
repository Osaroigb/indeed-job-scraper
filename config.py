import os
import logging
from dotenv import load_dotenv
from colorlog import ColoredFormatter

load_dotenv()


MAX_BOTS = 80 # Maximum number of concurrent bots
RETRY_LIMIT = 3
LOCATION = 'London'  # Target job location
DATABASE_URI = os.getenv("DATABASE_URI")
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")
SCRAPER_API_URL = os.getenv("SCRAPER_API_URL")


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


def validate_env():
    required_vars = ["DATABASE_URI", "SCRAPER_API_KEY", "SCRAPER_API_URL"]

    for var in required_vars:

        if not os.getenv(var):
            raise EnvironmentError(f"Missing required environment variable: {var}")