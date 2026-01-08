import scrapy
from datetime import date
from ..utils import parse_relative_date

class LinkedInSpider(scrapy.Spider):
    name = "linkedin"

    def start_requests(self):
        keyword = getattr(self, 'keyword', 'Python')
        location = getattr(self, 'location', 'Europe')
        base_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location={location}&start={{}}"

        # --- UPDATED: Scrape deeper (0 to 400 instead of 100) ---
        for i in range(0, 401, 25):
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

            # --- FIX STARTS HERE ---
            try:
                # 1. Get the slug part: "view/freelance-job-name-123456"
                slug = raw_url.split("view/")[1].split("/")[0].split("?")[0]

                # 2. The ID is usually the LAST part of the slug separated by dashes
                # Example: "python-dev-12345" -> "12345"
                job_id = slug.split('-')[-1]

                # Verify it's a number (sometimes urls are weird)
                if not job_id.isdigit():
                    # Fallback: sometimes the ID is just the slug itself if it's purely numeric
                    if slug.isdigit():
                        job_id = slug
                    else:
                        raise IndexError("ID not found")

                detail_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

                item = {
                    'title': clean_title,
                    'company': clean_company,
                    'location': clean_location,
                    'url': clean_url,
                    'source': "LinkedIn",
                    'posted_at': real_date,
                }
                yield scrapy.Request(url=detail_url, callback=self.parse_detail, meta={'item': item})

            except (IndexError, ValueError):
                # Fallback: Save without description if we can't get the ID
                yield {
                    'title': clean_title,
                    'company': clean_company,
                    'location': clean_location,
                    'url': clean_url,
                    'source': "LinkedIn",
                    'posted_at': real_date,
                    'description': "",
                    'salary_min': None,
                    'salary_max': None,
                    'currency': None
                }

    def parse_detail(self, response):
        # Retrieve the item we passed from the previous function
        item = response.meta['item']

        # Extract the full description text
        # LinkedIn Guest view usually puts it in 'div.show-more-less-html__markup'
        description_html = response.css("div.show-more-less-html__markup").get()

        # We strip HTML tags to just get the text for scanning
        if description_html:
            # Simple text extraction (removes <br>, <div> etc)
            text_content = response.css("div.show-more-less-html__markup *::text").getall()
            item['description'] = " ".join(text_content).strip()
        else:
            item['description'] = ""

        yield item