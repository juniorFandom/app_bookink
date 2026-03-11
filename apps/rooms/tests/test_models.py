from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from apps.rooms.models import RoomType, Room, RoomImage, RoomBooking
from apps.business.models import BusinessLocation

User = get_user_model()


class RoomTypeModelTest(TestCase):
    """Test cases for RoomType model."""

    def setUp(self):
        self.room_type = RoomType.objects.create(
            name='Standard Double',
            code='STD_DBL',
            description='Comfortable double room',
            max_occupancy=2,
            base_price=Decimal('50000.00'),
            amenities=['WiFi', 'TV', 'AC'],
            is_active=True
        )

    def test_room_type_creation(self):
        """Test room type creation."""
        self.assertEqual(self.room_type.name, 'Standard Double')
        self.assertEqual(self.room_type.code, 'STD_DBL')
        self.assertEqual(self.room_type.max_occupancy, 2)
        self.assertEqual(self.room_type.base_price, Decimal('50000.00'))
        self.assertTrue(self.room_type.is_active)

    def test_room_type_str(self):
        """Test room type string representation."""
        self.assertEqual(str(self.room_type), 'Standard Double')

    def test_unique_name_constraint(self):
        """Test that room type names must be unique."""
        with self.assertRaises(Exception):
            RoomType.objects.create(
                name='Standard Double',
                code='STD_DBL_2',
                max_occupancy=2,
                base_price=Decimal('50000.00')
            )

    def test_unique_code_constraint(self):
        """Test that room type codes must be unique."""
        with self.assertRaises(Exception):
            RoomType.objects.create(
                name='Standard Single',
                code='STD_DBL',
                max_occupancy=1,
                base_price=Decimal('40000.00')
            )


class RoomModelTest(TestCase):
    """Test cases for Room model."""

    def setUp(self):
        self.business_location = BusinessLocation.objects.create(
            name='Test Hotel',
            address='123 Test Street'
        )
        self.room_type = RoomType.objects.create(
            name='Standard Double',
            code='STD_DBL',
            max_occupancy=2,
            base_price=Decimal('50000.00')
        )
        self.room = Room.objects.create(
            business_location=self.business_location,
            room_type=self.room_type,
            room_number='101',
            floor=1,
            description='Comfortable room with city view',
            price_per_night=Decimal('55000.00'),
            max_occupancy=2,
            amenities=['WiFi', 'TV', 'AC', 'Mini Bar'],
            is_available=True,
            maintenance_mode=False
        )

    def test_room_creation(self):
        """Test room creation."""
        self.assertEqual(self.room.room_number, '101')
        self.assertEqual(self.room.floor, 1)
        self.assertEqual(self.room.price_per_night, Decimal('55000.00'))
        self.assertEqual(self.room.max_occupancy, 2)
        self.assertTrue(self.room.is_available)
        self.assertFalse(self.room.maintenance_mode)

    def test_room_str(self):
        """Test room string representation."""
        expected = f"{self.business_location.name} - Room {self.room.room_number}"
        self.assertEqual(str(self.room), expected)

    def test_unique_room_number_per_location(self):
        """Test that room numbers must be unique per business location."""
        with self.assertRaises(Exception):
            Room.objects.create(
                business_location=self.business_location,
                room_type=self.room_type,
                room_number='101',
                price_per_night=Decimal('60000.00'),
                max_occupancy=2
            )

    def test_room_amenities_json(self):
        """Test that amenities are stored as JSON."""
        self.assertEqual(self.room.amenities, ['WiFi', 'TV', 'AC', 'Mini Bar'])


class RoomImageModelTest(TestCase):
    """Test cases for RoomImage model."""

    def setUp(self):
        self.business_location = BusinessLocation.objects.create(
            name='Test Hotel',
            address='123 Test Street'
        )
        self.room_type = RoomType.objects.create(
            name='Standard Double',
            code='STD_DBL',
            max_occupancy=2,
            base_price=Decimal('50000.00')
        )
        self.room = Room.objects.create(
            business_location=self.business_location,
            room_type=self.room_type,
            room_number='101',
            price_per_night=Decimal('55000.00'),
            max_occupancy=2
        )

    def test_room_image_str(self):
        """Test room image string representation."""
        # Note: In a real test, you'd need to create an actual image file
        # For this test, we'll just test the string format
        image = RoomImage.objects.create(
            room=self.room,
            caption='Room view',
            order=1
        )
        expected = f"Image {image.order} for {self.room}"
        self.assertEqual(str(image), expected)


class RoomBookingModelTest(TestCase):
    """Test cases for RoomBooking model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.business_location = BusinessLocation.objects.create(
            name='Test Hotel',
            address='123 Test Street'
        )
        self.room_type = RoomType.objects.create(
            name='Standard Double',
            code='STD_DBL',
            max_occupancy=2,
            base_price=Decimal('50000.00')
        )
        self.room = Room.objects.create(
            business_location=self.business_location,
            room_type=self.room_type,
            room_number='101',
            price_per_night=Decimal('55000.00'),
            max_occupancy=2
        )
        self.booking = RoomBooking.objects.create(
            room=self.room,
            customer=self.user,
            business_location=self.business_location,
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=3),
            adults_count=2,
            children_count=0,
            hotel_notes='Early check-in requested'
        )

    def test_booking_creation(self):
        """Test booking creation."""
        self.assertEqual(self.booking.room, self.room)
        self.assertEqual(self.booking.customer, self.user)
        self.assertEqual(self.booking.adults_count, 2)
        self.assertEqual(self.booking.children_count, 0)
        self.assertEqual(self.booking.hotel_notes, 'Early check-in requested')

    def test_booking_str(self):
        """Test booking string representation."""
        expected = f"Room Booking {self.booking.booking_reference} - {self.room}"
        self.assertEqual(str(self.booking), expected)

    def test_duration_nights_property(self):
        """Test duration_nights property calculation."""
        self.assertEqual(self.booking.duration_nights, 2)

    def test_unique_room_date_constraint(self):
        """Test that a room can only have one booking per date."""
        with self.assertRaises(Exception):
            RoomBooking.objects.create(
                room=self.room,
                customer=self.user,
                business_location=self.business_location,
                check_in_date=date.today() + timedelta(days=1),
                check_out_date=date.today() + timedelta(days=3),
                adults_count=1,
                children_count=0
            )

    def test_booking_reference_generation(self):
        """Test that booking reference is generated."""
        self.assertIsNotNone(self.booking.booking_reference)
        self.assertTrue(self.booking.booking_reference.startswith('RB'))
        self.assertEqual(len(self.booking.booking_reference), 10)  # RB + 8 chars 