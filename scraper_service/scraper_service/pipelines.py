from itemadapter import ItemAdapter
from jobs.models import Job
from asgiref.sync import sync_to_async

class ScraperServicePipeline:
    async def process_item(self, item, spider):
        await sync_to_async(self.save_job)(item)
        return item

    def save_job(self, item):
        job, created = Job.objects.update_or_create(
            url=item.get('url'),
            defaults={
                'title': item.get('title'),
                'company': item.get('company'),
                # Fix: Use 'or "Remote"' to handle None values
                'location': item.get('location') or "Remote",
                'source': item.get('source'),
                'posted_at': item.get('posted_at'),
            }
        )
        return job