from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
import time
import random
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Movie, Show, Booking
from .serializers import (
    SignupSerializer, MovieSerializer, ShowSerializer, BookingSerializer
)
from django.shortcuts import get_object_or_404

# Signup
class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=SignupSerializer,
        responses={
            201: openapi.Response('User created successfully', SignupSerializer),
            400: openapi.Response('Validation failed'),
            500: openapi.Response('Internal server error')
        }
    )
    def post(self, request):
        try:
            serializer = SignupSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return Response(
                    {"message": "User created successfully", "user_id": user.id}, 
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {"error": "Validation failed", "details": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred during registration", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Login (returns JWT)
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Authenticate user and return JWT tokens",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password')
            }
        ),
        responses={
            200: openapi.Response('Login successful', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'username': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            400: openapi.Response('Missing credentials'),
            401: openapi.Response('Invalid credentials'),
            500: openapi.Response('Internal server error')
        }
    )
    def post(self, request):
        try:
            from django.contrib.auth import authenticate
            
            username = request.data.get('username')
            password = request.data.get('password')
            
            # Input validation
            if not username or not password:
                return Response(
                    {"error": "Both username and password are required", "fields": ["username", "password"]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = authenticate(username=username, password=password)
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user_id": user.id,
                    "username": user.username
                })
            return Response(
                {"error": "Invalid credentials", "message": "Please check your username and password"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred during login", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# List Movies
class MovieListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        movies = Movie.objects.all()
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)

# List Shows for a Movie
class ShowListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, movie_id):
        shows = Show.objects.filter(movie_id=movie_id)
        serializer = ShowSerializer(shows, many=True)
        return Response(serializer.data)

# Get Available Seats for a Show
class AvailableSeatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, show_id):
        show = get_object_or_404(Show, id=show_id)
        
        # Get booked seat numbers
        booked_seats = set(
            Booking.objects.filter(show=show, status="booked")
            .values_list('seat_number', flat=True)
        )
        
        # Get all available seats
        all_seats = set(range(1, show.total_seats + 1))
        available_seats = sorted(list(all_seats - booked_seats))
        
        return Response({
            "show_id": show_id,
            "total_seats": show.total_seats,
            "booked_seats": sorted(list(booked_seats)),
            "available_seats": available_seats,
            "available_count": len(available_seats)
        })

# Book a Seat
class BookShowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Book a seat for a specific show",
        operation_summary="Book a Seat",
        tags=['Bookings'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['seat_number'],
            properties={
                'seat_number': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Seat number to book (1 to total_seats)',
                    example=5
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Seat booked successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Booking ID'),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                        'show': openapi.Schema(type=openapi.TYPE_INTEGER, description='Show ID'),
                        'seat_number': openapi.Schema(type=openapi.TYPE_INTEGER, description='Seat number'),
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Booking status'),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, description='Creation timestamp'),
                    }
                )
            ),
            400: openapi.Response(description="Bad Request - Invalid seat number or missing required field"),
            401: openapi.Response(description="Authentication credentials were not provided"),
            404: openapi.Response(description="Show not found"),
            409: openapi.Response(description="Conflict - Seat already booked or user already has booking for this seat"),
        },
        security=[{'Bearer': []}]
    )
    def post(self, request, show_id):
        show = get_object_or_404(Show, id=show_id)
        seat_number = request.data.get('seat_number')

        # Input validation
        if not seat_number:
            return Response(
                {"error": "seat_number is required", "field": "seat_number"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            seat_number = int(seat_number)
        except (ValueError, TypeError):
            return Response(
                {"error": "seat_number must be a valid integer", "field": "seat_number"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if seat_number < 1 or seat_number > show.total_seats:
            return Response(
                {"error": f"Seat number must be between 1 and {show.total_seats}", "field": "seat_number"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retry logic for concurrent booking attempts
        max_retries = 3
        retry_delay = 0.1  # 100ms
        
        for attempt in range(max_retries):
            try:
                with transaction.atomic():
                    # Check if seat is already booked (only check active bookings)
                    existing_booking = Booking.objects.select_for_update().filter(
                        show=show, seat_number=seat_number, status="booked"
                    ).first()
                    
                    if existing_booking:
                        return Response(
                            {"error": "Seat already booked", "seat_number": seat_number}, 
                            status=status.HTTP_409_CONFLICT
                        )
                    
                    # Check if user already has a booking for this seat (to prevent duplicate bookings)
                    user_existing_booking = Booking.objects.filter(
                        show=show, seat_number=seat_number, user=request.user, status="booked"
                    ).first()
                    
                    if user_existing_booking:
                        return Response(
                            {"error": "You already have a booking for this seat", "seat_number": seat_number}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Create the booking
                    booking = Booking.objects.create(
                        user=request.user,
                        show=show,
                        seat_number=seat_number,
                        status="booked"
                    )
                    
                    serializer = BookingSerializer(booking)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                    
            except IntegrityError as e:
                if attempt < max_retries - 1:
                    # Random delay to reduce collision probability
                    time.sleep(retry_delay + random.uniform(0, 0.05))
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    return Response(
                        {"error": "Booking failed due to concurrent access. Please try again.", "details": str(e)}, 
                        status=status.HTTP_409_CONFLICT
                    )
            except ValidationError as e:
                return Response(
                    {"error": "Invalid booking data", "details": str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {"error": "An unexpected error occurred", "details": str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

# Cancel Booking
class CancelBookingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Cancel a booking by booking ID",
        operation_summary="Cancel Booking",
        tags=['Bookings'],
        responses={
            200: openapi.Response(
                description="Booking cancelled successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                        'booking': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Booking ID'),
                                'user': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                                'show': openapi.Schema(type=openapi.TYPE_INTEGER, description='Show ID'),
                                'seat_number': openapi.Schema(type=openapi.TYPE_INTEGER, description='Seat number'),
                                'status': openapi.Schema(type=openapi.TYPE_STRING, description='Booking status'),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, description='Creation timestamp'),
                            }
                        )
                    }
                )
            ),
            401: openapi.Response(description="Authentication credentials were not provided"),
            403: openapi.Response(description="Forbidden - Cannot cancel someone else's booking"),
            404: openapi.Response(description="Booking not found"),
            400: openapi.Response(description="Bad Request - Booking already cancelled"),
        },
        security=[{'Bearer': []}]
    )
    def post(self, request, booking_id):
        try:
            booking = get_object_or_404(Booking, id=booking_id)

            # Only owner can cancel
            if booking.user != request.user:
                return Response(
                    {"error": "You cannot cancel someone else's booking", "booking_id": booking_id}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check if booking is already cancelled
            if booking.status == "cancelled":
                return Response(
                    {"error": "Booking is already cancelled", "booking_id": booking_id}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            booking.status = "cancelled"
            booking.save()
            serializer = BookingSerializer(booking)
            return Response({
                "message": "Booking cancelled successfully",
                "booking": serializer.data
            })
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred during cancellation", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# List My Bookings
class MyBookingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get all bookings for the authenticated user",
        operation_summary="Get My Bookings",
        tags=['Bookings'],
        responses={
            200: openapi.Response(
                description="List of user's bookings",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Booking ID'),
                            'user': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                            'show': openapi.Schema(type=openapi.TYPE_INTEGER, description='Show ID'),
                            'seat_number': openapi.Schema(type=openapi.TYPE_INTEGER, description='Seat number'),
                            'status': openapi.Schema(type=openapi.TYPE_STRING, description='Booking status'),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, description='Creation timestamp'),
                        }
                    )
                )
            ),
            401: openapi.Response(description="Authentication credentials were not provided"),
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        bookings = Booking.objects.filter(user=request.user)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)
