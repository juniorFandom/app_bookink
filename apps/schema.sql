-- ============================================================================
-- NORMALIZED TOURISM PLATFORM DATABASE SCHEMA
-- Django-ready with proper naming conventions and relationships
-- ============================================================================

-- Core Authentication and User Management
-- ============================================================================

-- Roles table for flexible user role management
CREATE TABLE IF NOT EXISTS "role" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(50) NOT NULL UNIQUE,
    "code" VARCHAR(20) NOT NULL UNIQUE,
    "description" TEXT,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Enhanced User model extending Django's AbstractUser
CREATE TABLE IF NOT EXISTS "user" (
    "id" SERIAL PRIMARY KEY,
    "password" VARCHAR(128) NOT NULL,
    "last_login" TIMESTAMP WITH TIME ZONE,
    "is_superuser" BOOLEAN NOT NULL DEFAULT FALSE,
    "username" VARCHAR(150) UNIQUE,
    "first_name" VARCHAR(150),
    "last_name" VARCHAR(150),
    "email" VARCHAR(254) NOT NULL UNIQUE,
    "phone_number" VARCHAR(20),
    "is_staff" BOOLEAN NOT NULL DEFAULT FALSE,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "date_joined" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "avatar" VARCHAR(100),
    "date_of_birth" DATE,
    "gender" VARCHAR(10) CHECK (gender IN ('M', 'F', 'OTHER')),
    "language_preference" VARCHAR(10) DEFAULT 'en',
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- User roles many-to-many relationship
CREATE TABLE IF NOT EXISTS "user_role" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NOT NULL REFERENCES "user"("id") ON DELETE CASCADE,
    "role_id" INTEGER NOT NULL REFERENCES "role"("id") ON DELETE CASCADE,
    "assigned_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "assigned_by_id" INTEGER REFERENCES "user"("id"),
    UNIQUE("user_id", "role_id")
);

-- Address model for structured location data
CREATE TABLE IF NOT EXISTS "address" (
    "id" SERIAL PRIMARY KEY,
    "street_address" VARCHAR(255),
    "neighborhood" VARCHAR(100),
    "city" VARCHAR(100) NOT NULL,
    "region" VARCHAR(100) NOT NULL,
    "country" VARCHAR(100) NOT NULL DEFAULT 'Cameroon',
    "postal_code" VARCHAR(20),
    "latitude" DECIMAL(10, 8),
    "longitude" DECIMAL(11, 8),
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- User profiles for role-specific data
CREATE TABLE IF NOT EXISTS "guide_profile" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NOT NULL UNIQUE REFERENCES "user"("id") ON DELETE CASCADE,
    "license_number" VARCHAR(100),
    "years_of_experience" INTEGER CHECK (years_of_experience >= 0),
    "languages_spoken" TEXT, -- JSON array of language codes
    "specializations" TEXT, -- JSON array of specialization areas
    "hourly_rate" DECIMAL(10, 2),
    "is_verified" BOOLEAN NOT NULL DEFAULT FALSE,
    "verification_document" VARCHAR(100),
    "bio" TEXT,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Wallet system for user balance management
CREATE TABLE IF NOT EXISTS "wallet" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NOT NULL UNIQUE REFERENCES "user"("id") ON DELETE CASCADE,
    "balance" DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    "currency" VARCHAR(3) NOT NULL DEFAULT 'XAF',
    "is_frozen" BOOLEAN NOT NULL DEFAULT FALSE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Transaction history for wallet operations
CREATE TABLE IF NOT EXISTS "transaction" (
    "id" SERIAL PRIMARY KEY,
    "wallet_id" INTEGER NOT NULL REFERENCES "wallet"("id") ON DELETE CASCADE,
    "transaction_type" VARCHAR(20) NOT NULL CHECK (transaction_type IN ('CREDIT', 'DEBIT', 'REFUND', 'COMMISSION')),
    "amount" DECIMAL(10, 2) NOT NULL,
    "description" VARCHAR(255) NOT NULL,
    "reference_id" VARCHAR(100), -- External payment reference
    "status" VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    "metadata" JSONB, -- Additional transaction data
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Business Management
-- ============================================================================

-- Service categories
CREATE TABLE IF NOT EXISTS "service_category" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "code" VARCHAR(20) NOT NULL UNIQUE,
    "description" TEXT,
    "icon" VARCHAR(100),
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Business entities
CREATE TABLE IF NOT EXISTS "business" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "slug" VARCHAR(255) NOT NULL UNIQUE,
    "description" TEXT,
    "logo" VARCHAR(100),
    "phone_number" VARCHAR(20) NOT NULL,
    "email" VARCHAR(254),
    "website" VARCHAR(200),
    "registration_number" VARCHAR(100),
    "registration_document" VARCHAR(100),
    "tax_id" VARCHAR(100),
    "owner_id" INTEGER NOT NULL REFERENCES "user"("id"),
    "address_id" INTEGER REFERENCES "address"("id"),
    "status" VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED')),
    "approved_by_id" INTEGER REFERENCES "user"("id"),
    "approved_at" TIMESTAMP WITH TIME ZONE,
    "commission_rate" DECIMAL(5, 2) NOT NULL DEFAULT 10.00, -- Platform commission percentage
    "is_featured" BOOLEAN NOT NULL DEFAULT FALSE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Business services many-to-many
CREATE TABLE IF NOT EXISTS "business_service" (
    "id" SERIAL PRIMARY KEY,
    "business_id" INTEGER NOT NULL REFERENCES "business"("id") ON DELETE CASCADE,
    "service_category_id" INTEGER NOT NULL REFERENCES "service_category"("id") ON DELETE CASCADE,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE("business_id", "service_category_id")
);

-- Physical locations for businesses (for chains)
CREATE TABLE IF NOT EXISTS "business_location" (
    "id" SERIAL PRIMARY KEY,
    "business_id" INTEGER NOT NULL REFERENCES "business"("id") ON DELETE CASCADE,
    "name" VARCHAR(255) NOT NULL,
    "address_id" INTEGER NOT NULL REFERENCES "address"("id"),
    "phone_number" VARCHAR(20),
    "manager_id" INTEGER REFERENCES "user"("id"),
    "is_main_location" BOOLEAN NOT NULL DEFAULT FALSE,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Tourism Services
-- ============================================================================

-- Tour packages and guide services
CREATE TABLE IF NOT EXISTS "tour_package" (
    "id" SERIAL PRIMARY KEY,
    "guide_id" INTEGER NOT NULL REFERENCES "user"("id"),
    "title" VARCHAR(200) NOT NULL,
    "slug" VARCHAR(255) NOT NULL UNIQUE,
    "description" TEXT NOT NULL,
    "duration_hours" DECIMAL(5, 2),
    "max_participants" INTEGER CHECK (max_participants > 0),
    "price_per_person" DECIMAL(10, 2) NOT NULL,
    "meeting_point" VARCHAR(255),
    "included_services" TEXT, -- JSON array
    "requirements" TEXT,
    "difficulty_level" VARCHAR(20) CHECK (difficulty_level IN ('EASY', 'MODERATE', 'DIFFICULT')),
    "main_image" VARCHAR(100),
    "is_published" BOOLEAN NOT NULL DEFAULT FALSE,
    "is_featured" BOOLEAN NOT NULL DEFAULT FALSE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Tour package images
CREATE TABLE IF NOT EXISTS "tour_package_image" (
    "id" SERIAL PRIMARY KEY,
    "tour_package_id" INTEGER NOT NULL REFERENCES "tour_package"("id") ON DELETE CASCADE,
    "image" VARCHAR(100) NOT NULL,
    "caption" VARCHAR(255),
    "order" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Scheduled tours
CREATE TABLE IF NOT EXISTS "tour_schedule" (
    "id" SERIAL PRIMARY KEY,
    "tour_package_id" INTEGER NOT NULL REFERENCES "tour_package"("id") ON DELETE CASCADE,
    "start_datetime" TIMESTAMP WITH TIME ZONE NOT NULL,
    "end_datetime" TIMESTAMP WITH TIME ZONE,
    "available_spots" INTEGER NOT NULL,
    "price_override" DECIMAL(10, 2), -- For dynamic pricing
    "status" VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED' CHECK (status IN ('SCHEDULED', 'CONFIRMED', 'CANCELLED', 'COMPLETED')),
    "cancellation_reason" TEXT,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Tour activities
CREATE TABLE IF NOT EXISTS "tour_activity" (
    "id" SERIAL PRIMARY KEY,
    "tour_schedule_id" INTEGER NOT NULL REFERENCES "tour_schedule"("id"),
    "activity_id" INTEGER NOT NULL REFERENCES "activity"("id"),
    "day_number" INTEGER NOT NULL,
    "start_time" TIME NOT NULL,
    "is_optional" BOOLEAN NOT NULL DEFAULT FALSE,
    "additional_price" DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    "notes" TEXT,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Tour bookings
CREATE TABLE IF NOT EXISTS "tour_booking" (
    "id" SERIAL PRIMARY KEY,
    "tour_schedule_id" INTEGER NOT NULL REFERENCES "tour_schedule"("id"),
    "customer_id" INTEGER NOT NULL REFERENCES "user"("id"),
    "number_of_participants" INTEGER NOT NULL CHECK (number_of_participants > 0),
    "total_amount" DECIMAL(10, 2) NOT NULL,
    "commission_amount" DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    "status" VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'NO_SHOW')),
    "payment_status" VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (payment_status IN ('PENDING', 'PAID', 'REFUNDED', 'FAILED')),
    "booking_reference" VARCHAR(50) NOT NULL UNIQUE,
    "special_requests" TEXT,
    "customer_notes" TEXT,
    "guide_notes" TEXT,
    "cancellation_reason" TEXT,
    "cancelled_at" TIMESTAMP WITH TIME ZONE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE("tour_schedule_id", "customer_id")
);

-- Events (separate from tours)
CREATE TABLE IF NOT EXISTS "event" (
    "id" SERIAL PRIMARY KEY,
    "organizer_id" INTEGER NOT NULL REFERENCES "user"("id"),
    "title" VARCHAR(200) NOT NULL,
    "slug" VARCHAR(255) NOT NULL UNIQUE,
    "description" TEXT NOT NULL,
    "start_datetime" TIMESTAMP WITH TIME ZONE NOT NULL,
    "end_datetime" TIMESTAMP WITH TIME ZONE NOT NULL,
    "location" VARCHAR(255),
    "address_id" INTEGER REFERENCES "address"("id"),
    "max_attendees" INTEGER,
    "ticket_price" DECIMAL(10, 2) DEFAULT 0.00,
    "main_image" VARCHAR(100),
    "status" VARCHAR(20) NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'PUBLISHED', 'CANCELLED', 'COMPLETED')),
    "is_featured" BOOLEAN NOT NULL DEFAULT FALSE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Accommodation Management
-- ============================================================================

-- Room types
CREATE TABLE IF NOT EXISTS "room_type" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "code" VARCHAR(30) UNIQUE,
    "description" TEXT,
    "max_occupancy" INTEGER NOT NULL CHECK (max_occupancy > 0),
    "base_price" DECIMAL(10, 2),
    "amenities" TEXT, -- JSON array
    "image" VARCHAR(100),
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Hotel rooms
CREATE TABLE IF NOT EXISTS "room" (
    "id" SERIAL PRIMARY KEY,
    "business_location_id" INTEGER NOT NULL REFERENCES "business_location"("id") ON DELETE CASCADE,
    "room_type_id" INTEGER NOT NULL REFERENCES "room_type"("id"),
    "room_number" VARCHAR(50),
    "floor" INTEGER,
    "description" TEXT,
    "price_per_night" DECIMAL(10, 2) NOT NULL,
    "max_occupancy" INTEGER NOT NULL CHECK (max_occupancy > 0),
    "amenities" TEXT, -- JSON array, room-specific amenities
    "main_image" VARCHAR(100),
    "is_available" BOOLEAN NOT NULL DEFAULT TRUE,
    "maintenance_mode" BOOLEAN NOT NULL DEFAULT FALSE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE("business_location_id", "room_number")
);

-- Room images
CREATE TABLE IF NOT EXISTS "room_image" (
    "id" SERIAL PRIMARY KEY,
    "room_id" INTEGER NOT NULL REFERENCES "room"("id") ON DELETE CASCADE,
    "image" VARCHAR(100) NOT NULL,
    "caption" VARCHAR(255),
    "order" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Room reservations
CREATE TABLE IF NOT EXISTS "room_reservation" (
    "id" SERIAL PRIMARY KEY,
    "room_id" INTEGER NOT NULL REFERENCES "room"("id"),
    "customer_id" INTEGER NOT NULL REFERENCES "user"("id"),
    "business_location_id" INTEGER NOT NULL REFERENCES "business_location"("id"),
    "check_in_date" DATE NOT NULL,
    "check_out_date" DATE NOT NULL,
    "adults_count" INTEGER NOT NULL DEFAULT 1 CHECK (adults_count > 0),
    "children_count" INTEGER NOT NULL DEFAULT 0 CHECK (children_count >= 0),
    "total_nights" INTEGER NOT NULL CHECK (total_nights > 0),
    "total_amount" DECIMAL(10, 2) NOT NULL,
    "commission_amount" DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    "status" VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT', 'CANCELLED', 'NO_SHOW')),
    "payment_status" VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (payment_status IN ('PENDING', 'PAID', 'REFUNDED', 'FAILED')),
    "reservation_reference" VARCHAR(50) NOT NULL UNIQUE,
    "customer_notes" TEXT,
    "hotel_notes" TEXT,
    "special_requests" TEXT,
    "cancellation_reason" TEXT,
    "cancelled_at" TIMESTAMP WITH TIME ZONE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Vehicle Rental Management
-- ============================================================================

-- Vehicle categories
CREATE TABLE IF NOT EXISTS "vehicle_category" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "code" VARCHAR(20) NOT NULL UNIQUE,
    "description" TEXT,
    "icon" VARCHAR(100),
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Vehicles
CREATE TABLE IF NOT EXISTS "vehicle" (
    "id" SERIAL PRIMARY KEY,
    "business_location_id" INTEGER NOT NULL REFERENCES "business_location"("id") ON DELETE CASCADE,
    "vehicle_category_id" INTEGER NOT NULL REFERENCES "vehicle_category"("id"),
    "make" VARCHAR(100) NOT NULL,
    "model" VARCHAR(100) NOT NULL,
    "year" INTEGER CHECK (year > 1900),
    "license_plate" VARCHAR(50) NOT NULL UNIQUE,
    "color" VARCHAR(50),
    "passenger_capacity" INTEGER NOT NULL CHECK (passenger_capacity > 0),
    "transmission" VARCHAR(20) CHECK (transmission IN ('MANUAL', 'AUTOMATIC')),
    "fuel_type" VARCHAR(20) CHECK (fuel_type IN ('PETROL', 'DIESEL', 'ELECTRIC', 'HYBRID')),
    "daily_rate" DECIMAL(10, 2) NOT NULL,
    "description" TEXT,
    "features" TEXT, -- JSON array
    "main_image" VARCHAR(100),
    "mileage" INTEGER DEFAULT 0,
    "is_available" BOOLEAN NOT NULL DEFAULT TRUE,
    "maintenance_mode" BOOLEAN NOT NULL DEFAULT FALSE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Vehicle images
CREATE TABLE IF NOT EXISTS "vehicle_image" (
    "id" SERIAL PRIMARY KEY,
    "vehicle_id" INTEGER NOT NULL REFERENCES "vehicle"("id") ON DELETE CASCADE,
    "image" VARCHAR(100) NOT NULL,
    "caption" VARCHAR(255),
    "order" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Drivers/Chauffeurs
CREATE TABLE IF NOT EXISTS "driver" (
    "id" SERIAL PRIMARY KEY,
    "business_location_id" INTEGER NOT NULL REFERENCES "business_location"("id") ON DELETE CASCADE,
    "user_id" INTEGER REFERENCES "user"("id"), -- Optional: if driver has user account
    "first_name" VARCHAR(150) NOT NULL,
    "last_name" VARCHAR(150) NOT NULL,
    "phone_number" VARCHAR(20) NOT NULL,
    "email" VARCHAR(254),
    "license_number" VARCHAR(100) NOT NULL,
    "license_expiry_date" DATE,
    "license_document" VARCHAR(100),
    "years_of_experience" INTEGER CHECK (years_of_experience >= 0),
    "languages_spoken" TEXT, -- JSON array
    "daily_rate" DECIMAL(10, 2) NOT NULL,
    "photo" VARCHAR(100),
    "is_available" BOOLEAN NOT NULL DEFAULT TRUE,
    "is_verified" BOOLEAN NOT NULL DEFAULT FALSE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Vehicle rental contracts
CREATE TABLE IF NOT EXISTS "vehicle_rental" (
    "id" SERIAL PRIMARY KEY,
    "vehicle_id" INTEGER NOT NULL REFERENCES "vehicle"("id"),
    "driver_id" INTEGER REFERENCES "driver"("id"), -- Optional driver
    "customer_id" INTEGER NOT NULL REFERENCES "user"("id"),
    "business_location_id" INTEGER NOT NULL REFERENCES "business_location"("id"),
    "pickup_datetime" TIMESTAMP WITH TIME ZONE NOT NULL,
    "return_datetime" TIMESTAMP WITH TIME ZONE NOT NULL,
    "pickup_location" VARCHAR(255),
    "return_location" VARCHAR(255),
    "total_days" INTEGER NOT NULL CHECK (total_days > 0),
    "vehicle_rate" DECIMAL(10, 2) NOT NULL,
    "driver_rate" DECIMAL(10, 2) DEFAULT 0.00,
    "total_amount" DECIMAL(10, 2) NOT NULL,
    "commission_amount" DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    "security_deposit" DECIMAL(10, 2) DEFAULT 0.00,
    "status" VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'CONFIRMED', 'PICKED_UP', 'RETURNED', 'CANCELLED', 'NO_SHOW')),
    "payment_status" VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (payment_status IN ('PENDING', 'PAID', 'REFUNDED', 'FAILED')),
    "rental_reference" VARCHAR(50) NOT NULL UNIQUE,
    "customer_notes" TEXT,
    "special_requirements" TEXT,
    "terms_accepted" BOOLEAN NOT NULL DEFAULT FALSE,
    "cancellation_reason" TEXT,
    "cancelled_at" TIMESTAMP WITH TIME ZONE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Restaurant Management
-- ============================================================================

-- Food categories
CREATE TABLE IF NOT EXISTS "food_category" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "description" TEXT,
    "image" VARCHAR(100),
    "order" INTEGER NOT NULL DEFAULT 0,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Menu items
CREATE TABLE IF NOT EXISTS "menu_item" (
    "id" SERIAL PRIMARY KEY,
    "business_location_id" INTEGER NOT NULL REFERENCES "business_location"("id") ON DELETE CASCADE,
    "food_category_id" INTEGER NOT NULL REFERENCES "food_category"("id"),
    "name" VARCHAR(200) NOT NULL,
    "slug" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "price" DECIMAL(10, 2) NOT NULL,
    "preparation_time_minutes" INTEGER,
    "calories" INTEGER,
    "ingredients" TEXT, -- JSON array
    "allergens" TEXT, -- JSON array
    "dietary_info" TEXT, -- JSON array (vegetarian, vegan, gluten-free, etc.)
    "main_image" VARCHAR(100),
    "is_available" BOOLEAN NOT NULL DEFAULT TRUE,
    "is_featured" BOOLEAN NOT NULL DEFAULT FALSE,
    "order" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE("business_location_id", "slug")
);

-- Menu item images
CREATE TABLE IF NOT EXISTS "menu_item_image" (
    "id" SERIAL PRIMARY KEY,
    "menu_item_id" INTEGER NOT NULL REFERENCES "menu_item"("id") ON DELETE CASCADE,
    "image" VARCHAR(100) NOT NULL,
    "caption" VARCHAR(255),
    "order" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Restaurant orders
CREATE TABLE IF NOT EXISTS "restaurant_order" (
    "id" SERIAL PRIMARY KEY,
    "business_location_id" INTEGER NOT NULL REFERENCES "business_location"("id"),
    "customer_id" INTEGER NOT NULL REFERENCES "user"("id"),
    "order_number" VARCHAR(50) NOT NULL UNIQUE,
    "order_type" VARCHAR(20) NOT NULL DEFAULT 'DINE_IN' CHECK (order_type IN ('DINE_IN', 'TAKEAWAY', 'DELIVERY')),
    "table_number" VARCHAR(20),
    "delivery_address_id" INTEGER REFERENCES "address"("id"),
    "subtotal" DECIMAL(10, 2) NOT NULL,
    "tax_amount" DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    "delivery_fee" DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    "total_amount" DECIMAL(10, 2) NOT NULL,
    "commission_amount" DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    "status" VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'DELIVERED', 'CANCELLED', 'REFUNDED')),
    "payment_status" VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (payment_status IN ('PENDING', 'PAID', 'REFUNDED', 'FAILED')),
    "estimated_preparation_time" INTEGER, -- minutes
    "special_instructions" TEXT,
    "customer_notes" TEXT,
    "restaurant_notes" TEXT,
    "cancellation_reason" TEXT,
    "cancelled_at" TIMESTAMP WITH TIME ZONE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Order items
CREATE TABLE IF NOT EXISTS "order_item" (
    "id" SERIAL PRIMARY KEY,
    "restaurant_order_id" INTEGER NOT NULL REFERENCES "restaurant_order"("id") ON DELETE CASCADE,
    "menu_item_id" INTEGER NOT NULL REFERENCES "menu_item"("id"),
    "quantity" INTEGER NOT NULL CHECK (quantity > 0),
    "unit_price" DECIMAL(10, 2) NOT NULL,
    "total_price" DECIMAL(10, 2) NOT NULL,
    "special_instructions" TEXT,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Reviews and Ratings
-- ============================================================================

-- Generic review system
CREATE TABLE IF NOT EXISTS "review" (
    "id" SERIAL PRIMARY KEY,
    "reviewer_id" INTEGER NOT NULL REFERENCES "user"("id"),
    "content_type" VARCHAR(50) NOT NULL, -- 'business', 'guide', 'tour_package', etc.
    "object_id" INTEGER NOT NULL,
    "rating" INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    "title" VARCHAR(200),
    "comment" TEXT,
    "is_approved" BOOLEAN NOT NULL DEFAULT FALSE,
    "approved_by_id" INTEGER REFERENCES "user"("id"),
    "approved_at" TIMESTAMP WITH TIME ZONE,
    "response_text" TEXT, -- Business response
    "response_date" TIMESTAMP WITH TIME ZONE,
    "is_verified_purchase" BOOLEAN NOT NULL DEFAULT FALSE,
    "helpful_count" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE("reviewer_id", "content_type", "object_id")
);

-- Review helpfulness tracking
CREATE TABLE IF NOT EXISTS "review_helpful" (
    "id" SERIAL PRIMARY KEY,
    "review_id" INTEGER NOT NULL REFERENCES "review"("id") ON DELETE CASCADE,
    "user_id" INTEGER NOT NULL REFERENCES "user"("id") ON DELETE CASCADE,
    "is_helpful" BOOLEAN NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE("review_id", "user_id")
);

-- Payment Management
-- ============================================================================

-- Unified payment transactions
CREATE TABLE IF NOT EXISTS "payment_transaction" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NOT NULL REFERENCES "user"("id"),
    "business_id" INTEGER REFERENCES "business"("id"),
    "transaction_reference" VARCHAR(100) NOT NULL UNIQUE,
    "external_reference" VARCHAR(255), -- Payment provider reference
    "amount" DECIMAL(10, 2) NOT NULL,
    "currency" VARCHAR(3) NOT NULL DEFAULT 'XAF',
    "commission_amount" DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    "service_type" VARCHAR(30) NOT NULL CHECK (service_type IN ('TOUR_BOOKING', 'ROOM_RESERVATION', 'VEHICLE_RENTAL', 'RESTAURANT_ORDER', 'EVENT_TICKET')),
    "service_id" INTEGER NOT NULL, -- ID of the related service booking
    "payment_method" VARCHAR(50),
    "payment_provider" VARCHAR(50) NOT NULL DEFAULT 'CINETPAY',
    "status" VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED', 'REFUNDED')),
    "description" VARCHAR(255) NOT NULL,
    "provider_response" JSONB, -- Raw provider response
    "failure_reason" TEXT,
    "processed_at" TIMESTAMP WITH TIME ZONE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Refund management
CREATE TABLE IF NOT EXISTS "refund" (
    "id" SERIAL PRIMARY KEY,
    "payment_transaction_id" INTEGER NOT NULL REFERENCES "payment_transaction"("id"),
    "refund_reference" VARCHAR(100) NOT NULL UNIQUE,
    "amount" DECIMAL(10, 2) NOT NULL,
    "reason" TEXT NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'REQUESTED' CHECK (status IN ('REQUESTED', 'PROCESSING', 'COMPLETED', 'REJECTED')),
    "processed_by_id" INTEGER REFERENCES "user"("id"),
    "processed_at" TIMESTAMP WITH TIME ZONE,
    "provider_response" JSONB,
    "admin_notes" TEXT,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Safety and Reporting
-- ============================================================================

-- Danger types
CREATE TABLE IF NOT EXISTS "danger_type" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "description" TEXT,
    "severity_level" INTEGER NOT NULL DEFAULT 1 CHECK (severity_level >= 1 AND severity_level <= 5),
    "icon" VARCHAR(100),
    "color_code" VARCHAR(7), -- Hex color
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Danger zones reporting
CREATE TABLE IF NOT EXISTS "danger_zone" (
    "id" SERIAL PRIMARY KEY,
    "reporter_id" INTEGER NOT NULL REFERENCES "user"("id"),
    "danger_type_id" INTEGER NOT NULL REFERENCES "danger_type"("id"),
    "title" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "location_name" VARCHAR(255) NOT NULL,
    "address_id" INTEGER REFERENCES "address"("id"),
    "severity_level" INTEGER NOT NULL DEFAULT 1 CHECK (severity_level >= 1 AND severity_level <= 5),
    "is_verified" BOOLEAN NOT NULL DEFAULT
    "reported_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,-- Date du signalement
    "reporter_id" integer NOT NULL                           -- Utilisateur ayant signalé
        REFERENCES "user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "is_active" boolean NOT NULL DEFAULT true,               -- Actif / résolu
    "created_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
);