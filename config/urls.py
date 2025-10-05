from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Movie Booking API",
        default_version='v1',
        description="""
        ## Movie Ticket Booking System API
        
        This API provides endpoints for:
        - User authentication with JWT tokens
        - Movie and show management
        - Seat booking and cancellation
        - Booking history
        
        ### Authentication
        Most endpoints require JWT authentication. To use authenticated endpoints:
        1. Register a new user via `/api/signup/`
        2. Login via `/api/login/` to get JWT tokens
        3. Click the "Authorize" button above and enter: `Bearer <your-access-token>`
        
        ### Example JWT Token Usage
        ```
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
        ```
        """,
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=[
        path('api/', include('booking.urls')),
    ],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('booking.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]
