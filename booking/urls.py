from django.urls import path
from .views import (
    SignupView,
    LoginView,
    MovieListView,
    ShowListView,
    AvailableSeatsView,
    BookShowView,
    CancelBookingView,
    MyBookingsView
)

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("movies/", MovieListView.as_view(), name="movie-list"),
    path("movies/<int:movie_id>/shows/", ShowListView.as_view(), name="show-list"),
    path("shows/<int:show_id>/available-seats/", AvailableSeatsView.as_view(), name="available-seats"),
    path("shows/<int:show_id>/book/", BookShowView.as_view(), name="book-show"),
    path("bookings/<int:booking_id>/cancel/", CancelBookingView.as_view(), name="cancel-booking"),
    path("my-bookings/", MyBookingsView.as_view(), name="my-bookings"),
]
