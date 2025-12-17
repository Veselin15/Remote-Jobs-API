from django.db import models

class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, default="Remote")
    url = models.URLField(unique=True)  # unique=True prevents duplicate jobs
    source = models.CharField(max_length=50) # e.g., "PyJobs", "RemoteOK"
    posted_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True) # When we scraped it

    def __str__(self):
        return f"{self.title} at {self.company}"