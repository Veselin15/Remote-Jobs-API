import scrapy
from datetime import date


class LinkedInSpider(scrapy.Spider):
    name = "linkedin"

    def start_requests(self):
        # Search for Python jobs in Europe
        base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Python&location=Europe&start={}"
        # We scrape pages 0, 25, 50, 75, 100
        for i in range(0, 101, 25):
            yield scrapy.Request(url=base_url.format(i), callback=self.parse_list)

    def parse_list(self, response):
        # Loop through each job card
        for job in response.css("li"):

            # Extract basic info
            title = job.css("h3.base-search-card__title::text").get()
            company = job.css("h4.base-search-card__subtitle a::text").get()
            location = job.css("span.job-search-card__location::text").get()
            raw_url = job.css("a.base-card__full-link::attr(href)").get()

            if not title or not raw_url:
                continue

            # TRICK: Extract the Job ID to call the Detail API
            # URL looks like: https://uk.linkedin.com/jobs/view/412345678?...
            # We want "412345678"
            try:
                # Split by 'view/' and take the part after it, then split by '?' or '/'
                job_id = raw_url.split("view/")[1].split("/")[0].split("?")[0]

                # Construct the "Secret" Guest Detail API URL
                detail_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

                # Clean strings
                item = {
                    'title': title.strip(),
                    'company': company.strip() if company else "Unknown",
                    'location': location.strip() if location else "Remote",
                    'url': raw_url.split('?')[0],
                    'source': "LinkedIn",
                    'posted_at': date.today()
                }

                # Follow the link to get the description
                yield scrapy.Request(url=detail_url, callback=self.parse_detail, meta={'item': item})

            except IndexError:
                # If URL format is weird, skip detail parsing and just save what we have
                yield {
                    'title': title.strip(),
                    'company': company.strip() if company else "Unknown",
                    'location': location.strip() if location else "Remote",
                    'url': raw_url.split('?')[0],
                    'source': "LinkedIn",
                    'posted_at': date.today(),
                    'description': ""
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