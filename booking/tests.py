from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Movie, Show, Booking


class MovieBookingTestCase(APITestCase):
    """Comprehensive test suite for the Movie Booking System"""
    
    def setUp(self):
        """Set up test data"""
        
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        
        self.movie = Movie.objects.create(
            title='Test Movie',
            duration_minutes=120
        )
        
        
        self.show = Show.objects.create(
            movie=self.movie,
            screen_name='Screen 1',
            date_time=timezone.now() + timedelta(days=1),
            total_seats=10
        )
        
      
        self.refresh1 = RefreshToken.for_user(self.user1)
        self.access_token1 = str(self.refresh1.access_token)
        self.refresh2 = RefreshToken.for_user(self.user2)
        self.access_token2 = str(self.refresh2.access_token)

    def test_user_signup(self):
        """Test user registration"""
        url = reverse('signup')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_login(self):
        """Test user login and JWT token generation"""
        url = reverse('login')
        data = {
            'username': 'testuser1',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        url = reverse('login')
        data = {
            'username': 'testuser1',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_movies(self):
        """Test listing all movies"""
        url = reverse('movie-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Movie')

    def test_list_shows_for_movie(self):
        """Test listing shows for a specific movie"""
        url = reverse('show-list', kwargs={'movie_id': self.movie.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['screen_name'], 'Screen 1')

    def test_available_seats(self):
        """Test checking available seats"""
        url = reverse('available-seats', kwargs={'show_id': self.show.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_seats'], 10)
        self.assertEqual(len(response.data['available_seats']), 10)
        self.assertEqual(response.data['available_count'], 10)

    def test_book_seat_success(self):
        """Test successful seat booking"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token1}')
        url = reverse('book-show', kwargs={'show_id': self.show.id})
        data = {'seat_number': 5}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['seat_number'], 5)
        self.assertEqual(response.data['status'], 'booked')
        
    
        booking = Booking.objects.get(id=response.data['id'])
        self.assertEqual(booking.user, self.user1)
        self.assertEqual(booking.show, self.show)
        self.assertEqual(booking.seat_number, 5)

    def test_book_seat_authentication_required(self):
        """Test that booking requires authentication"""
        url = reverse('book-show', kwargs={'show_id': self.show.id})
        data = {'seat_number': 5}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_book_seat_double_booking_prevention(self):
        """Test prevention of double booking"""
   
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token1}')
        url = reverse('book-show', kwargs={'show_id': self.show.id})
        data = {'seat_number': 5}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
     
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token2}')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('already booked', response.data['error'])

    def test_book_seat_invalid_seat_number(self):
        """Test booking with invalid seat number"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token1}')
        url = reverse('book-show', kwargs={'show_id': self.show.id})
        
        data = {'seat_number': 0}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    
        data = {'seat_number': 15}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_book_seat_missing_seat_number(self):
        """Test booking without seat number"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token1}')
        url = reverse('book-show', kwargs={'show_id': self.show.id})
        data = {}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_booking_success(self):
        """Test successful booking cancellation"""
     
        booking = Booking.objects.create(
            user=self.user1,
            show=self.show,
            seat_number=3,
            status='booked'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token1}')
        url = reverse('cancel-booking', kwargs={'booking_id': booking.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['booking']['status'], 'cancelled')
        
       
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')

    def test_cancel_booking_authentication_required(self):
        """Test that cancellation requires authentication"""
        booking = Booking.objects.create(
            user=self.user1,
            show=self.show,
            seat_number=3,
            status='booked'
        )
        
        url = reverse('cancel-booking', kwargs={'booking_id': booking.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cancel_others_booking_forbidden(self):
        """Test that users cannot cancel other users' bookings"""
     
        booking = Booking.objects.create(
            user=self.user1,
            show=self.show,
            seat_number=3,
            status='booked'
        )
        
      
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token2}')
        url = reverse('cancel-booking', kwargs={'booking_id': booking.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_my_bookings_list(self):
        """Test listing user's bookings"""
     
        Booking.objects.create(
            user=self.user1,
            show=self.show,
            seat_number=1,
            status='booked'
        )
        Booking.objects.create(
            user=self.user1,
            show=self.show,
            seat_number=2,
            status='cancelled'
        )
        
    
        Booking.objects.create(
            user=self.user2,
            show=self.show,
            seat_number=3,
            status='booked'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token1}')
        url = reverse('my-bookings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  
        
        
        booking_ids = [booking['id'] for booking in response.data]
        self.assertNotIn(
            Booking.objects.get(user=self.user2, seat_number=3).id,
            booking_ids
        )

    def test_my_bookings_authentication_required(self):
        """Test that my-bookings requires authentication"""
        url = reverse('my-bookings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_booking_after_cancellation(self):
        """Test that seats can be rebooked after cancellation"""
       
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token1}')
        url = reverse('book-show', kwargs={'show_id': self.show.id})
        data = {'seat_number': 5}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking_id = response.data['id']
        
     
        url = reverse('cancel-booking', kwargs={'booking_id': booking_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token2}')
        url = reverse('book-show', kwargs={'show_id': self.show.id})
        data = {'seat_number': 5}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_available_seats_after_booking(self):
        """Test available seats count after bookings"""
        url = reverse('available-seats', kwargs={'show_id': self.show.id})
        
       
        response = self.client.get(url)
        self.assertEqual(response.data['available_count'], 10)
        self.assertEqual(len(response.data['available_seats']), 10)
        
     
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token1}')
        book_url = reverse('book-show', kwargs={'show_id': self.show.id})
        data = {'seat_number': 7}
        self.client.post(book_url, data, format='json')
        
 
        self.client.credentials()  
        response = self.client.get(url)
        self.assertEqual(response.data['available_count'], 9)
        self.assertEqual(len(response.data['available_seats']), 9)
        self.assertNotIn(7, response.data['available_seats'])
        self.assertIn(7, response.data['booked_seats'])

    def test_concurrent_booking_attempts(self):
        """Test handling of concurrent booking attempts"""
       
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token1}')
        url = reverse('book-show', kwargs={'show_id': self.show.id})
        data = {'seat_number': 8}
        
      
        response1 = self.client.post(url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        
        response2 = self.client.post(url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_409_CONFLICT)


class ModelTestCase(TestCase):
    """Test cases for model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='modeltest',
            email='modeltest@example.com',
            password='testpass123'
        )
        self.movie = Movie.objects.create(
            title='Model Test Movie',
            duration_minutes=90
        )
        self.show = Show.objects.create(
            movie=self.movie,
            screen_name='Test Screen',
            date_time=timezone.now() + timedelta(days=1),
            total_seats=5
        )

    def test_movie_str_representation(self):
        """Test Movie model string representation"""
        self.assertEqual(str(self.movie), 'Model Test Movie')

    def test_show_str_representation(self):
        """Test Show model string representation"""
        expected = f"Model Test Movie - Test Screen at {self.show.date_time}"
        self.assertEqual(str(self.show), expected)

    def test_booking_str_representation(self):
        """Test Booking model string representation"""
        booking = Booking.objects.create(
            user=self.user,
            show=self.show,
            seat_number=3,
            status='booked'
        )
        expected = f"modeltest - {self.show} - Seat 3"
        self.assertEqual(str(booking), expected)

    def test_booking_default_status(self):
        """Test that booking defaults to 'booked' status"""
        booking = Booking.objects.create(
            user=self.user,
            show=self.show,
            seat_number=4
        )
        self.assertEqual(booking.status, 'booked')

    def test_booking_created_at_auto_populated(self):
        """Test that created_at is automatically populated"""
        booking = Booking.objects.create(
            user=self.user,
            show=self.show,
            seat_number=2,
            status='booked'
        )
        self.assertIsNotNone(booking.created_at)
        self.assertLess(
            (timezone.now() - booking.created_at).total_seconds(),
            5  
        )
