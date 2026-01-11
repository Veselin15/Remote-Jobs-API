import scrapy
from datetime import date
from ..utils import parse_relative_date
from ..items import JobItem


class LinkedInSpider(scrapy.Spider):
    name = "linkedin"

    def start_requests(self):
        keyword = getattr(self, 'keyword', 'Python')
        location = getattr(self, 'location', 'Europe')
        base_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location={location}&start={{}}"

        # Scrape 0 to 100 (keep it low for testing, increase later)
        for i in range(0, 101, 25):
            yield scrapy.Request(url=base_url.format(i), callback=self.parse_list)

    def parse_list(self, response):
        for job in response.css("li"):
            title = job.css("h3.base-search-card__title::text").get()
            company = job.css("h4.base-search-card__subtitle a::text").get()
            location = job.css("span.job-search-card__location::text").get()
            raw_url = job.css("a.base-card__full-link::attr(href)").get()
            date_text = job.css('time.job-search-card__listdate::text').get()

            if not title or not raw_url:
                continue

            clean_title = title.strip()
            clean_company = company.strip() if company else "Unknown"
            clean_location = location.strip() if location else "Remote"
            clean_url = raw_url.split('?')[0]
            real_date = parse_relative_date(date_text)

            # --- Create the JobItem ---
            item = JobItem()
            item['title'] = clean_title
            item['company'] = clean_company
            item['location'] = clean_location
            item['url'] = clean_url
            item['source'] = "LinkedIn"
            item['posted_at'] = real_date
            item['skills'] = []  # Default empty list
            item['salary_min'] = None
            item['salary_max'] = None
            item['currency'] = None

            try:
                # Extract ID to get full description
                slug = raw_url.split("view/")[1].split("/")[0].split("?")[0]
                job_id = slug.split('-')[-1]

                if not job_id.isdigit():
                    job_id = slug if slug.isdigit() else None

                if job_id:
                    detail_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
                    yield scrapy.Request(url=detail_url, callback=self.parse_detail, meta={'item': item})
                else:
                    item['description'] = ""
                    yield item

            except (IndexError, ValueError):
                item['description'] = ""
                yield item

    def parse_detail(self, response):
        item = response.meta['item']

        # Extract Description
        description_html = response.css("div.show-more-less-html__markup").get()
        if description_html:
            text_content = response.css("div.show-more-less-html__markup *::text").getall()
            item['description'] = " ".join(text_content).strip()
        else:
            item['description'] = ""

        yield item