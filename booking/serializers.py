from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Movie, Show, Booking

# User Signup
class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user

# Movie Serializer
class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['id', 'title', 'duration_minutes']

# Show Serializer
class ShowSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = Show
        fields = ['id', 'movie', 'screen_name', 'date_time', 'total_seats']

# Booking Serializer
class BookingSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    show = ShowSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'user', 'show', 'seat_number', 'status', 'created_at']
