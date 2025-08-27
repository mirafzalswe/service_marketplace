from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import User, WorkerProfile
from .serializers import UserSerializer, WorkerProfileSerializer, LoginSerializer
from .permissions import IsAdmin, IsOwnerOrAdmin

@extend_schema(
    summary="Register a new user",
    description="Create a new user account. Available roles: client, worker, admin",
    tags=["Authentication"]
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

@extend_schema(
    summary="User login",
    description="Authenticate user and get JWT tokens",
    tags=["Authentication"]
)
class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="List all users",
    description="Get a list of all users (admin only)",
    tags=["Users"]
)
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

@extend_schema_view(
    get=extend_schema(
        summary="Get user details",
        description="Retrieve user information",
        tags=["Users"]
    ),
    put=extend_schema(
        summary="Update user",
        description="Update user information",
        tags=["Users"]
    ),
    patch=extend_schema(
        summary="Partially update user",
        description="Partially update user information",
        tags=["Users"]
    )
)
class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrAdmin]

@extend_schema_view(
    get=extend_schema(
        summary="Get worker profile",
        description="Retrieve worker profile information",
        tags=["Workers"]
    ),
    put=extend_schema(
        summary="Update worker profile",
        description="Update worker profile information",
        tags=["Workers"]
    ),
    patch=extend_schema(
        summary="Partially update worker profile",
        description="Partially update worker profile information",
        tags=["Workers"]
    )
)
class WorkerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = WorkerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Only workers should access worker profiles
        if self.request.user.role != 'worker':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only workers can access worker profiles")
        
        profile, created = WorkerProfile.objects.get_or_create(user=self.request.user)
        return profile