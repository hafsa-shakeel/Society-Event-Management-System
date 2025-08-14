-- Drop tables if they exist
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS artists;
DROP TABLE IF EXISTS users;

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create artists table
CREATE TABLE artists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create events table
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    date DATE NOT NULL,
    venue VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    available_tickets INTEGER NOT NULL,
    artist_id INTEGER NOT NULL REFERENCES artists(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create bookings table
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    event_id INTEGER NOT NULL REFERENCES events(id),
    num_tickets INTEGER NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    booking_date DATE NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
-- Insert sample artists
INSERT INTO artists (name, description) VALUES
('John Doe', 'Famous rock artist'),
('Jane Smith', 'Popular pop singer'),
('The Band', 'Indie rock band');

-- Insert sample events
INSERT INTO events (name, description, date, venue, price, available_tickets, artist_id, status) VALUES
('Summer Concert', 'Annual summer concert with great music', '2024-07-15', 'Venue A', 50.00, 200, 1, 'active'),
('Rock Festival', 'The biggest rock festival of the year', '2024-08-20', 'Venue B', 75.00, 500, 2, 'active'),
('Acoustic Night', 'A night of acoustic performances', '2024-06-10', 'Venue C', 30.00, 100, 3, 'active'),
('Jazz Evening', 'Enjoy the best jazz music', '2024-09-05', 'Venue A', 45.00, 150, 1, 'active');
