from itemadapter import ItemAdapter
from jobs.models import Job
from asgiref.sync import sync_to_async
from .utils import parse_salary  # <--- Crucial Import

class ScraperServicePipeline:
    async def process_item(self, item, spider):
        await sync_to_async(self.save_job)(item)
        return item

    def save_job(self, item):
        # Scan BOTH title and description for salary
        # We prefer title (higher accuracy), but fallback to description
        text_to_scan = f"{item.get('title')} {item.get('company')} {item.get('description')}"

        min_sal, max_sal, curr = parse_salary(text_to_scan)

        job, created = Job.objects.update_or_create(
            url=item.get('url'),
            defaults={
                'title': item.get('title'),
                'company': item.get('company'),
                'location': item.get('location') or "Remote",
                'source': item.get('source'),
                'posted_at': item.get('posted_at'),
                # Save the new description field
                'description': item.get('description'),
                'salary_min': min_sal,
                'salary_max': max_sal,
                'currency': curr,
            }
        )
        return job