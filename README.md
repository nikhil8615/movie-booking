# 🎬 Movie Ticket Booking System

A Django REST Framework based backend system for movie ticket booking with JWT authentication and comprehensive API documentation.

## 🚀 Features

- **User Authentication**: Signup and Login with JWT tokens
- **Movie Management**: List movies and their shows
- **Seat Booking**: Book and cancel movie tickets
- **Real-time Availability**: Check available seats for shows
- **API Documentation**: Complete Swagger/OpenAPI documentation
- **Security**: JWT authentication for protected endpoints

## 🛠 Tech Stack

- **Backend**: Python 3.11+, Django 5.0.6, Django REST Framework 3.15.2
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Documentation**: drf-yasg (Swagger/OpenAPI)
- **Database**: SQLite (configurable for PostgreSQL)
- **Testing**: Django Test Framework

## 📦 Installation & Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd movie-booking
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 6. Run the Server

```bash
python manage.py runserver
```

The API will be available at: `http://127.0.0.1:8000/`

## 📚 API Documentation

### Swagger UI

Visit: `http://127.0.0.1:8000/swagger/` for interactive API documentation

### Access the admin panel

Visit: `http://127.0.0.1:8000/admin/` Only superusers can log in here. Use python manage.py createsuperuser to create a superuser.

#### Using JWT Authentication in Swagger UI

1. **Login first**: Use the `POST /api/login/` endpoint to get your JWT token
2. **Authorize**: Click the **"Authorize"** button (🔒) at the top right
3. **Enter token**: In the "Value" field, enter: `Bearer YOUR_ACCESS_TOKEN_HERE`
4. **Test endpoints**: Now you can test all authenticated endpoints directly in Swagger UI

**Alternative Documentation:**

- **ReDoc**: `http://127.0.0.1:8000/redoc/`
- **JSON Schema**: `http://127.0.0.1:8000/swagger.json`

### Available Endpoints

| Method | Endpoint                           | Description             | Authentication |
| ------ | ---------------------------------- | ----------------------- | -------------- |
| POST   | `/api/signup/`                     | User registration       | ❌             |
| POST   | `/api/login/`                      | User login (get JWT)    | ❌             |
| GET    | `/api/movies/`                     | List all movies         | ❌             |
| GET    | `/api/movies/<id>/shows/`          | List shows for a movie  | ❌             |
| GET    | `/api/shows/<id>/available-seats/` | Check seat availability | ❌             |
| POST   | `/api/shows/<id>/book/`            | Book a seat             | ✅             |
| POST   | `/api/bookings/<id>/cancel/`       | Cancel booking          | ✅             |
| GET    | `/api/my-bookings/`                | List user's bookings    | ✅             |

## 🔐 JWT Authentication

### Getting JWT Tokens

1. **Register a new user:**

```bash
curl -X POST http://127.0.0.1:8000/api/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

2. **Login to get JWT tokens:**

```bash
curl -X POST http://127.0.0.1:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepassword123"
  }'
```

**Response:**

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Using JWT Tokens

Include the access token in the Authorization header for protected endpoints:

```bash
curl -X GET http://127.0.0.1:8000/api/my-bookings/ \
  -H "Authorization: Bearer <your-access-token>"
```

## 📖 API Usage Examples

### 1. List Movies

```bash
curl -X GET http://127.0.0.1:8000/api/movies/
```

### 2. Get Shows for a Movie

```bash
curl -X GET http://127.0.0.1:8000/api/movies/<movie_id>/shows/
```

### 3. Check Available Seats

```bash
curl -X GET http://127.0.0.1:8000/api/shows/<show_id>/available-seats/
```

### 4. Book a Seat

**Request Body Required:**

```json
{
  "seat_number": 5
}
```

**Example:**

```bash
curl -X POST http://127.0.0.1:8000/api/shows/<show_id>/book/ \
  -H "Authorization: Bearer <your-access-token>" \
  -H "Content-Type: application/json" \
  -d '{"seat_number": 5}'
```

**Note:** The `seat_number` field is required in the request body. Use the available seats endpoint to check which seats are available before booking.

### 5. Cancel a Booking

```bash
curl -X POST http://127.0.0.1:8000/api/bookings/<booking_id>/cancel/ \
  -H "Authorization: Bearer <your-access-token>"
```

### 6. View My Bookings

```bash
curl -X GET http://127.0.0.1:8000/api/my-bookings/ \
  -H "Authorization: Bearer <your-access-token>"
```

## 🧪 Testing

Run the test suite:

```bash
python manage.py test
```

Run specific test modules:

```bash
# Test booking logic
python manage.py test booking.tests.BookingTestCase

# Test authentication
python manage.py test booking.tests.AuthTestCase
```

## 🗃️ Database Models

### Movie

- `id`: Primary key
- `title`: Movie title (CharField)
- `duration_minutes`: Movie duration (PositiveIntegerField)

### Show

- `id`: Primary key
- `movie`: Foreign key to Movie
- `screen_name`: Screen name (CharField)
- `date_time`: Show date and time (DateTimeField)
- `total_seats`: Total seats available (PositiveIntegerField)

### Booking

- `id`: Primary key
- `user`: Foreign key to User
- `show`: Foreign key to Show
- `seat_number`: Seat number (PositiveIntegerField)
- `status`: Booking status - 'booked' or 'cancelled' (CharField)
- `created_at`: Booking creation timestamp (DateTimeField)

## 🔒 Business Rules

1. **Double Booking Prevention**: A seat cannot be booked twice for the same show
2. **Overbooking Prevention**: Bookings cannot exceed show capacity
3. **Cancellation**: Cancelled bookings free up seats for rebooking
4. **User Ownership**: Users can only cancel their own bookings
5. **Input Validation**: Seat numbers must be within valid range (1 to total_seats)

## 🚨 Error Handling

The API provides clear error messages for common scenarios:

- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Missing or invalid JWT token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Seat already booked

## 🔧 Configuration

### JWT Settings

- Access token lifetime: 24 hours (extended for testing)
- Refresh token lifetime: 7 days (extended for testing)
- Token rotation: Disabled

### Database

- Default: SQLite (development)
- Production: PostgreSQL (configure in settings.py)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 👨‍💻 Author

**Nikhil Singh**

- GitHub: [@nikhilsingh](https://github.com/nikhil8615)
- Email: nikhilsingh8185@gmail.com

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Swagger documentation](http://127.0.0.1:8000/swagger/) (after running the server this link is active)
2. Review the test cases for usage examples
3. Open an issue on GitHub

---

**Happy Movie Booking! 🍿🎬**
