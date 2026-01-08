from celery import shared_task
import subprocess
from datetime import timedelta
from django.utils import timezone
from .models import Job

@shared_task
def run_scrapers(keyword='Python', location='Europe'):
    # Run ONLY the LinkedIn Spider
    subprocess.run([
        "scrapy", "crawl", "linkedin",
        "-a", f"keyword={keyword}",
        "-a", f"location={location}"
    ], cwd="/app/scraper_service")

    return f"LinkedIn Scraping Finished for {keyword} in {location}"


@shared_task
def run_bulk_scrape():
    """
    Runs sequentially to populate the database with diverse jobs.
    Takes longer but gets much more data.
    """
    # 1. Define what you want to stock in your warehouse
    tech_stack = ["Python", "Java", "JavaScript", "React", "DevOps", "Data Analyst", "C++", "C#"]
    regions = ["Europe", "United States", "Remote"]

    results = []

    # 2. Loop through them (Sequentially to be safe with rate limits)
    for tech in tech_stack:
        for region in regions:
            print(f"Starting bulk scrape for: {tech} - {region}")

            # We use subprocess directly here to wait for each one to finish
            # before starting the next (prevents getting banned)
            subprocess.run([
                "scrapy", "crawl", "linkedin",
                "-a", f"keyword={tech}",
                "-a", f"location={region}"
            ], cwd="/app/scraper_service")

            results.append(f"{tech}-{region}")

    return f"Bulk Scrape Complete. Covered: {', '.join(results)}"

@shared_task
def cleanup_old_jobs():
    """
    Deletes jobs that were posted more than 30 days ago.
    """
    # 1. Calculate the cutoff date
    cutoff_date = timezone.now().date() - timedelta(days=30)

    # 2. Delete the old records
    deleted_count, _ = Job.objects.filter(posted_at__lt=cutoff_date).delete()

    return f"Janitor Report: Deleted {deleted_count} jobs older than {cutoff_date}"
