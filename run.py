from config import logging, Config
from bots.bot_manager import run_bot_manager
from database.export_to_csv import export_tables_to_csv
from main import log_performance_metrics, scraper_api_health_check


def run():
    # Run the ScraperAPI health check before proceeding
    if not scraper_api_health_check():
        logging.error("ScraperAPI is down or unreachable. Exiting script.")
        return  # Exit script if ScraperAPI is not accessible
    
    # Validate environment variables
    Config.validate_env()

    # Run the bot manager to handle concurrent job scraping and detailed job information retrieval
    run_bot_manager(phase="job_search_scraping")

    # Export tables to CSV files
    export_tables_to_csv()

    # Log performance metrics after scraping
    log_performance_metrics()
    logging.warning("All tasks completed and performance metrics logged")


if __name__ == "__main__":
    run()