from rest_framework import generics
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from .models import Job
from .serializers import JobSerializer
from rest_framework.response import Response
from .tasks import run_scrapers

class JobListAPI(generics.ListAPIView):
    queryset = Job.objects.all().order_by('-posted_at')
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]

    # Add salary_min and currency here
    filterset_fields = ['company', 'source', 'location', 'currency', 'salary_min']
    search_fields = ['title', 'company', 'location']


class ScrapeTriggerAPI(APIView):
    # Apply your security settings (API Key required)
    # You might want to use a stricter throttle here (e.g., 1 request/hour)

    def post(self, request):
        # 1. Get params from the user's POST data (default to Python/Europe)
        keyword = request.data.get('keyword', 'Python')
        location = request.data.get('location', 'Europe')

        # 2. Trigger the Celery Task in the background
        run_scrapers.delay(keyword, location)

        return Response({
            "message": "Scraper started successfully",
            "target": f"{keyword} jobs in {location}",
            "note": "Check back in 2-3 minutes for results."
        })