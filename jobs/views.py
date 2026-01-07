from rest_framework import generics, filters, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters import rest_framework as django_filters # <--- Rename for clarity
from drf_spectacular.utils import extend_schema
from .models import Job
from .serializers import JobSerializer
from .tasks import run_scrapers

# --- 1. Define the Custom Filter (The Input Boxes) ---
class JobFilter(django_filters.FilterSet):
    # specific boxes for searching
    title = django_filters.CharFilter(lookup_expr='icontains')
    company = django_filters.CharFilter(lookup_expr='icontains')
    location = django_filters.CharFilter(lookup_expr='icontains')

    # The "Skills" box you wanted!
    # (We search the text inside the JSON list)
    skills = django_filters.CharFilter(field_name='skills', lookup_expr='icontains')

    # Keep salary filter
    salary_min = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')

    class Meta:
        model = Job
        # We explicitly list ONLY what we want. 'currency' is excluded.
        fields = ['title', 'company', 'location', 'skills', 'salary_min', 'source']

class JobListAPI(generics.ListAPIView):
    queryset = Job.objects.all().order_by('-posted_at')
    serializer_class = JobSerializer

    # Use our new custom filter class
    filter_backends = [django_filters.DjangoFilterBackend]
    filterset_class = JobFilter  # <--- Connect the class here

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        # If the database returns empty results AND the user searched for something
        if len(response.data['results']) == 0:
            search_term = request.query_params.get('search')
            if search_term:
                # Automatically trigger the robot to go find this for next time
                print(f"No results for {search_term}. Triggering scraper...")
                run_scrapers.delay(keyword=search_term, location="Europe")

                # Tell the user what happened
                return Response({
                    "message": "No jobs found yet. We have started a live scrape for you. Check back in 2 minutes!",
                    "results": []
                })

        return response


# --- 3. The Scraper Trigger (No changes here) ---

class ScrapeRequestSerializer(serializers.Serializer):
    keyword = serializers.CharField(default="Python", help_text="Job title or skill")
    location = serializers.CharField(default="Europe", help_text="Region or City")


class ScrapeTriggerAPI(APIView):
    @extend_schema(request=ScrapeRequestSerializer)
    def post(self, request):
        serializer = ScrapeRequestSerializer(data=request.data)
        if serializer.is_valid():
            keyword = serializer.validated_data['keyword']
            location = serializer.validated_data['location']

            run_scrapers.delay(keyword, location)

            return Response({
                "message": "Scraper started successfully",
                "target": f"{keyword} jobs in {location}",
                "note": "Check back in 2-3 minutes for results."
            })
        return Response(serializer.errors, status=400)