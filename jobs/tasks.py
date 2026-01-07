from celery import shared_task
import subprocess

@shared_task
def run_scrapers(keyword='Python', location='Europe'):
    # Run ONLY the LinkedIn Spider
    subprocess.run([
        "scrapy", "crawl", "linkedin",
        "-a", f"keyword={keyword}",
        "-a", f"location={location}"
    ], cwd="/app/scraper_service")

    return f"LinkedIn Scraping Finished for {keyword} in {location}"