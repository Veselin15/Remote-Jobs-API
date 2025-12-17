from rest_framework import generics
from .models import Job
from .serializers import JobSerializer

class JobListAPI(generics.ListAPIView):
    # Get all jobs, ordered by newest first
    queryset = Job.objects.all().order_by('-posted_at')
    serializer_class = JobSerializer