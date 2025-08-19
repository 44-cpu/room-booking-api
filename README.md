🏨 Room Booking API

This is a Room Booking System built with FastAPI and PostgreSQL. The project allows users to register, log in securely, and book rooms with specific dates and times. It manages a total of 10 rooms along with 2 meeting rooms, and also provides functionality to check available time slots before booking. The system uses SQLAlchemy as the ORM and Alembic for database migrations, ensuring smooth integration with PostgreSQL.

To run the project, you need to clone the repository, install dependencies from requirements.txt, and set up a PostgreSQL database (for example, room_booking_db). After configuring the database, run Alembic migrations and start the FastAPI server with Uvicorn. Once running, you can access the API documentation at http://127.0.0.1:8000/docs, where you can test endpoints for user registration, booking rooms, checking availability, and retrieving user-specific bookings.

This project is designed to be a base for a complete booking management system, with possible future improvements such as email or SMS notifications, role-based access (admin and users), and payment integration for premium booking features.
