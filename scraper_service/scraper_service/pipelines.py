from itemadapter import ItemAdapter
from jobs.models import Job
from asgiref.sync import sync_to_async
from .utils import parse_salary, extract_skills, extract_seniority

class ScraperServicePipeline:
    async def process_item(self, item, spider):
        await sync_to_async(self.save_job)(item)
        return item

    def save_job(self, item):
        title = item.get('title')
        description = item.get('description')
        company = item.get('company')

        # Combine text for analysis
        text_to_scan = f"{title} {company} {description}"

        min_sal, max_sal, curr = parse_salary(text_to_scan)
        skills_found = extract_skills(text_to_scan)
        seniority_level = extract_seniority(title, description)

        job, created = Job.objects.update_or_create(
            url=item.get('url'),
            defaults={
                'title': title,
                'company': company,
                'location': item.get('location') or "Remote",
                'source': item.get('source'),
                'posted_at': item.get('posted_at'),
                'description': description,
                'skills': skills_found,
                'seniority': seniority_level,  # <--- Save it
                'salary_min': min_sal,
                'salary_max': max_sal,
                'currency': curr,
            }
        )
        return job