from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Service, ServiceCategory
from .serializers import ServiceSerializer, ServiceCategorySerializer

@extend_schema_view(
    get=extend_schema(
        summary="List all service categories",
        description="Retrieve a list of all available service categories",
        tags=["Services"]
    ),
    post=extend_schema(
        summary="Create a new service category",
        description="Create a new service category (admin only)",
        tags=["Services"]
    )
)
class ServiceCategoryListView(generics.ListCreateAPIView):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

@extend_schema_view(
    get=extend_schema(
        summary="List all services",
        description="Retrieve a list of all active services",
        tags=["Services"]
    ),
    post=extend_schema(
        summary="Create a new service",
        description="Create a new service (admin only)",
        tags=["Services"]
    )
)
class ServiceListView(generics.ListCreateAPIView):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

@extend_schema_view(
    get=extend_schema(
        summary="Get service details",
        description="Retrieve detailed information about a specific service",
        tags=["Services"]
    ),
    put=extend_schema(
        summary="Update service",
        description="Update service information (admin only)",
        tags=["Services"]
    ),
    patch=extend_schema(
        summary="Partially update service",
        description="Partially update service information (admin only)",
        tags=["Services"]
    ),
    delete=extend_schema(
        summary="Delete service",
        description="Delete a service (admin only)",
        tags=["Services"]
    )
)
class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]