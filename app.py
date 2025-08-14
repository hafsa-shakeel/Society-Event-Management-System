from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')

# Database connection function
def get_db_connection():
    try:
        # Connect to your PostgreSQL database
        conn = psycopg2.connect(
            dbname=os.environ.get('DB_NAME', 'event_booking'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', 'postgres'),
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432')
        )
        conn.autocommit = False
        print("Successfully connected to database")
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Initialize database
def init_db():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database for initialization")
        return False
    
    try:
        with conn.cursor() as cur:
            # Check if tables exist
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'users'
                )
            """)
            tables_exist = cur.fetchone()[0]
            
            if not tables_exist:
                # Create tables from schema.sql
                print("Creating database tables...")
                with open('schema.sql', 'r') as f:
                    cur.execute(f.read())
                conn.commit()
                print("Database initialized successfully")
                return True
            else:
                print("Tables already exist, checking data...")
                # Check if events table has data
                cur.execute("SELECT COUNT(*) FROM events")
                event_count = cur.fetchone()[0]
                print(f"Found {event_count} events in database")
                
                # If no events exist, insert sample events
                if event_count == 0:
                    print("No events found. Creating sample events...")
                    # Insert sample artists if needed
                    cur.execute("SELECT COUNT(*) FROM artists")
                    artist_count = cur.fetchone()[0]
                    if artist_count == 0:
                        print("No artists found. Creating sample artists...")
                        cur.execute("""
                            INSERT INTO artists (name, description) VALUES
                            ('John Doe', 'Famous rock artist'),
                            ('Jane Smith', 'Popular pop singer'),
                            ('The Band', 'Indie rock band')
                        """)
                    
                    # Get first artist ID
                    cur.execute("SELECT id FROM artists LIMIT 1")
                    artist_id = cur.fetchone()[0]
                    
                    # Insert sample events
                    cur.execute("""
                        INSERT INTO events (name, description, date, venue, price, available_tickets, artist_id, status) VALUES
                        ('Summer Concert', 'Annual summer concert with great music', '2024-07-15', 'Venue A', 50.00, 200, %s, 'active'),
                        ('Rock Festival', 'The biggest rock festival of the year', '2024-08-20', 'Venue B', 75.00, 500, %s, 'active'),
                        ('Acoustic Night', 'A night of acoustic performances', '2024-06-10', 'Venue C', 30.00, 100, %s, 'active'),
                        ('Jazz Evening', 'Enjoy the best jazz music', '2024-09-05', 'Venue A', 45.00, 150, %s, 'active')
                    """, (artist_id, artist_id, artist_id, artist_id))
                    
                    conn.commit()
                    print("Sample events created successfully")
                
                # Check if contact_submissions table exists, create if not
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'contact_submissions'
                    )
                """)
                contact_table_exists = cur.fetchone()[0]
                
                if not contact_table_exists:
                    print("Creating contact_submissions table...")
                    cur.execute("""
                        CREATE TABLE contact_submissions (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            email VARCHAR(100) NOT NULL,
                            message TEXT NOT NULL,
                            submission_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            status VARCHAR(20) NOT NULL DEFAULT 'unread'
                        )
                    """)
                    conn.commit()
                    print("Contact submissions table created successfully")
                
                return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Create admin user if not exists
def ensure_admin_exists():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database for admin creation")
        return False
    
    try:
        with conn.cursor() as cur:
            # Check if admin exists
            cur.execute("SELECT id FROM users WHERE email = %s", ("admin@example.com",))
            if cur.fetchone():
                print("Admin user already exists")
                return True
            
            # Create admin user
            hashed_password = generate_password_hash("admin123")
            cur.execute("""
                INSERT INTO users (
                    first_name, last_name, email, password, is_admin
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                "Admin", "User", "admin@example.com", hashed_password, True
            ))
            
            conn.commit()
            print("Admin user created successfully")
            return True
    except Exception as e:
        print(f"Error creating admin user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact', methods=['POST'])
def contact_submit():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    
    if not all([name, email, message]):
        flash("Please fill all required fields", "error")
        return redirect(url_for('index', _anchor='contact'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return redirect(url_for('index', _anchor='contact'))
    
    try:
        with conn.cursor() as cur:
            # Insert contact submission
            cur.execute("""
                INSERT INTO contact_submissions (name, email, message)
                VALUES (%s, %s, %s)
            """, (name, email, message))
            
            conn.commit()
            return redirect(url_for('contact_success'))
    except Exception as e:
        conn.rollback()
        flash(f"Error submitting form: {e}", "error")
        return redirect(url_for('index', _anchor='contact'))
    finally:
        conn.close()

@app.route('/contact/success')
def contact_success():
    return render_template('contact_success.html')

@app.route('/events')
def events():
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return render_template('events.html', events=[])
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT e.id, e.name as eventname, e.available_tickets, e.price, 
                       a.name as artistname, e.venue, e.status as eventstatus, e.date
                FROM events e
                JOIN artists a ON e.artist_id = a.id
                ORDER BY e.date
            """)
            events = cur.fetchall()
            return render_template('events.html', events=events)
    except Exception as e:
        flash(f"Error fetching events: {e}", "error")
        return render_template('events.html', events=[])
    finally:
        conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([first_name, last_name, email, password]):
            flash("Please fill all required fields", "error")
            return render_template('register.html')
        
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template('register.html')
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection error", "error")
            return render_template('register.html')
        
        try:
            with conn.cursor() as cur:
                # Check if email already exists
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    flash("Email already registered", "error")
                    return render_template('register.html')
                
                # Insert new user
                hashed_password = generate_password_hash(password)
                cur.execute("""
                    INSERT INTO users (first_name, last_name, email, phone, password, is_admin)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """, (first_name, last_name, email, phone, hashed_password, False))
                
                user_id = cur.fetchone()[0]
                conn.commit()
                
                print(f"User registered successfully with ID: {user_id}")
                
                flash("Registration successful! Please login.", "success")
                return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            flash(f"Registration error: {e}", "error")
            return render_template('register.html')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'user')
        
        if not email or not password:
            flash("Please enter both email and password", "error")
            return render_template('login.html')
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection error", "error")
            return render_template('login.html')
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, first_name, last_name, email, password, is_admin
                    FROM users WHERE email = %s
                """, (email,))
                
                user = cur.fetchone()
                if not user:
                    flash("Invalid email or password", "error")
                    return render_template('login.html')
                
                # Verify password
                if not check_password_hash(user['password'], password):
                    flash("Invalid email or password", "error")
                    return render_template('login.html')
                
                # Check user type
                if (user_type == 'admin' and not user['is_admin']) or (user_type == 'user' and user['is_admin']):
                    flash("Invalid account type", "error")
                    return render_template('login.html')
                
                # Set session
                session['user_id'] = user['id']
                session['user_name'] = f"{user['first_name']} {user['last_name']}"
                session['is_admin'] = user['is_admin']
                
                if user['is_admin']:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
        except Exception as e:
            flash(f"Login error: {e}", "error")
            return render_template('login.html')
        finally:
            conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return redirect(url_for('index'))
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get user info
            cur.execute("""
                SELECT id, first_name, last_name, email, phone
                FROM users WHERE id = %s
            """, (session['user_id'],))
            
            user = cur.fetchone()
            
            # Get user bookings
            cur.execute("""
                SELECT b.id, e.name as event_name, b.num_tickets, b.total_price,
                       b.booking_date, e.date as event_date, e.venue as event_venue
                FROM bookings b
                JOIN events e ON b.event_id = e.id
                WHERE b.user_id = %s AND b.status = 'active'
                ORDER BY b.booking_date DESC
            """, (session['user_id'],))
            
            bookings = cur.fetchall()
            
            return render_template('user_dashboard.html', 
                                  user=user, 
                                  user_name=session['user_name'],
                                  bookings=bookings)
    except Exception as e:
        flash(f"Error loading dashboard: {e}", "error")
        return redirect(url_for('index'))
    finally:
        conn.close()

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return redirect(url_for('index'))
    
    try:
        print("Fetching admin dashboard data...")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get admin info
            cur.execute("""
                SELECT id, first_name, last_name, email
                FROM users WHERE id = %s
            """, (session['user_id'],))
            
            admin = cur.fetchone()
            
            # Get all events
            cur.execute("""
                SELECT e.id, e.name, e.date, e.venue, e.price, e.available_tickets,
                       e.status, e.description, a.name as artistname
                FROM events e
                JOIN artists a ON e.artist_id = a.id
                ORDER BY e.date DESC
            """)
            
            events = cur.fetchall()
            print(f"Found {len(events) if events else 0} events for admin dashboard")
            
            # Get all users
            cur.execute("""
                SELECT id, first_name, last_name, email, phone
                FROM users
                WHERE is_admin = FALSE OR is_admin IS NULL
                ORDER BY id
            """)
            
            users = cur.fetchall()
            print(f"Found {len(users) if users else 0} non-admin users")
            
            # Get all bookings
            cur.execute("""
                SELECT b.id, u.first_name || ' ' || u.last_name as user_name,
                       e.name as event_name, b.num_tickets, b.total_price,
                       b.status, b.booking_date, u.id as user_id
                FROM bookings b
                JOIN events e ON b.event_id = e.id
                JOIN users u ON b.user_id = u.id
                ORDER BY b.booking_date DESC
            """)
            
            bookings = cur.fetchall()
            
            # Get all contact submissions
            cur.execute("""
                SELECT id, name, email, message, submission_date, status
                FROM contact_submissions
                ORDER BY submission_date DESC
            """)
            
            contact_submissions = cur.fetchall()
            print(f"Found {len(contact_submissions) if contact_submissions else 0} contact submissions")
            
            return render_template('admin_dashboard.html', 
                                  admin=admin,
                                  events=events,
                                  users=users,
                                  bookings=bookings,
                                  contact_submissions=contact_submissions)
    except Exception as e:
        flash(f"Error loading admin dashboard: {e}", "error")
        return redirect(url_for('index'))
    finally:
        conn.close()

@app.route('/mark_contact_read/<int:submission_id>', methods=['POST'])
def mark_contact_read(submission_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return redirect(url_for('admin_dashboard'))
    
    try:
        with conn.cursor() as cur:
            # Update submission status
            cur.execute("""
                UPDATE contact_submissions
                SET status = 'read'
                WHERE id = %s
            """, (submission_id,))
            
            conn.commit()
            flash("Contact submission marked as read", "success")
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        conn.rollback()
        flash(f"Error updating contact submission: {e}", "error")
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()

@app.route('/delete_contact/<int:submission_id>', methods=['POST'])
def delete_contact(submission_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return redirect(url_for('admin_dashboard'))
    
    try:
        with conn.cursor() as cur:
            # Delete submission
            cur.execute("""
                DELETE FROM contact_submissions
                WHERE id = %s
            """, (submission_id,))
            
            conn.commit()
            flash("Contact submission deleted", "success")
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting contact submission: {e}", "error")
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'user_id' not in session:
        flash("Please login to book tickets", "error")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        event_id = request.form.get('event')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        num_tickets = int(request.form.get('tickets', 1))
        payment_method = request.form.get('payment_method')
        
        if not all([event_id, name, email, phone, payment_method]):
            flash("Please fill all required fields", "error")
            return redirect(url_for('booking'))
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection error", "error")
            return redirect(url_for('booking'))
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get event details
                cur.execute("""
                    SELECT id, name, price, available_tickets
                    FROM events WHERE id = %s
                """, (event_id,))
                
                event = cur.fetchone()
                if not event:
                    flash("Event not found", "error")
                    return redirect(url_for('booking'))
                
                # Check ticket availability
                if event['available_tickets'] < num_tickets:
                    flash(f"Only {event['available_tickets']} tickets available", "error")
                    return redirect(url_for('booking'))
                
                # Calculate total price
                total_price = event['price'] * num_tickets
                
                # Create booking
                cur.execute("""
                    INSERT INTO bookings (
                        user_id, event_id, num_tickets, total_price, 
                        status, booking_date, payment_method
                    )
                    VALUES (%s, %s, %s, %s, %s, CURRENT_DATE, %s)
                    RETURNING id
                """, (
                    session['user_id'], event_id, num_tickets, 
                    total_price, 'active', payment_method
                ))
                
                booking_id = cur.fetchone()['id']
                
                # Update available tickets
                cur.execute("""
                    UPDATE events
                    SET available_tickets = available_tickets - %s
                    WHERE id = %s
                """, (num_tickets, event_id))
                
                conn.commit()
                flash("Booking successful!", "success")
                return redirect(url_for('user_dashboard'))
        except Exception as e:
            conn.rollback()
            flash(f"Booking error: {e}", "error")
            return redirect(url_for('booking'))
        finally:
            conn.close()
    
    # GET request - show booking form
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return render_template('booking.html', events=[], user=None)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get user info
            cur.execute("""
                SELECT id, first_name, last_name, email, phone
                FROM users WHERE id = %s
            """, (session['user_id'],))
            
            user = cur.fetchone()
            
            # Get available events
            cur.execute("""
                SELECT id, name, date, venue, price, available_tickets
                FROM events
                WHERE date >= CURRENT_DATE AND status = 'active' AND available_tickets > 0
                ORDER BY date
            """)
            
            events = cur.fetchall()
            print(f"Found {len(events) if events else 0} available events for booking")
            
            if not events:
                flash("No upcoming events available for booking at this time.", "info")
            
            return render_template('booking.html', events=events, user=user)
    except Exception as e:
        flash(f"Error loading booking page: {e}", "error")
        return render_template('booking.html', events=[], user=None)
    finally:
        conn.close()

@app.route('/cancel_ticket/<int:booking_id>', methods=['POST'])
def cancel_ticket(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return redirect(url_for('user_dashboard'))
    
    try:
        with conn.cursor() as cur:
            # Check if booking belongs to user
            cur.execute("""
                SELECT event_id, num_tickets, user_id
                FROM bookings
                WHERE id = %s
            """, (booking_id,))
            
            booking = cur.fetchone()
            if not booking or booking[2] != session['user_id']:
                flash("Invalid booking", "error")
                return redirect(url_for('user_dashboard'))
            
            # Update booking status
            cur.execute("""
                UPDATE bookings
                SET status = 'cancelled'
                WHERE id = %s
            """, (booking_id,))
            
            # Return tickets to event
            cur.execute("""
                UPDATE events
                SET available_tickets = available_tickets + %s
                WHERE id = %s
            """, (booking[1], booking[0]))
            
            conn.commit()
            flash("Booking cancelled successfully", "success")
            return redirect(url_for('user_dashboard'))
    except Exception as e:
        conn.rollback()
        flash(f"Error cancelling booking: {e}", "error")
        return redirect(url_for('user_dashboard'))
    finally:
        conn.close()

@app.route('/add_event', methods=['POST'])
def add_event():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    name = request.form.get('name')
    date = request.form.get('date')
    venue = request.form.get('venue')
    price = request.form.get('price')
    available_tickets = request.form.get('available_tickets')
    description = request.form.get('description')
    
    print(f"Received form data: {name}, {date}, {venue}, {price}, {available_tickets}")
    
    if not all([name, date, venue, price, available_tickets]):
        flash("Please fill all required fields", "error")
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return redirect(url_for('admin_dashboard'))
    
    try:
        print(f"Adding new event: {name} on {date} at {venue}")
        with conn.cursor() as cur:
            # Get first artist (simplified)
            cur.execute("SELECT id FROM artists LIMIT 1")
            artist_result = cur.fetchone()
            if not artist_result:
                print("No artists found in database")
                flash("No artists found", "error")
                return redirect(url_for('admin_dashboard'))
            
            artist_id = artist_result[0]
            print(f"Using artist ID: {artist_id}")
            
            # Insert event
            cur.execute("""
                INSERT INTO events (
                    name, date, venue, price, available_tickets,
                    description, artist_id, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                name, date, venue, price, available_tickets,
                description, artist_id, 'active'
            ))
            
            new_event_id = cur.fetchone()[0]
            conn.commit()
            print(f"Event added successfully with ID: {new_event_id}")
            flash("Event added successfully", "success")
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        conn.rollback()
        print(f"Error adding event: {e}")
        flash(f"Error adding event: {e}", "error")
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()

@app.route('/edit_event/<int:event_id>', methods=['POST'])
def edit_event(event_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    name = request.form.get('name')
    date = request.form.get('date')
    venue = request.form.get('venue')
    price = request.form.get('price')
    available_tickets = request.form.get('available_tickets')
    description = request.form.get('description')
    
    if not all([name, date, venue, price, available_tickets]):
        flash("Please fill all required fields", "error")
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return redirect(url_for('admin_dashboard'))
    
    try:
        with conn.cursor() as cur:
            # Update event
            cur.execute("""
                UPDATE events
                SET name = %s, date = %s, venue = %s, price = %s,
                    available_tickets = %s, description = %s
                WHERE id = %s
            """, (
                name, date, venue, price, available_tickets,
                description, event_id
            ))
            
            conn.commit()
            flash("Event updated successfully", "success")
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        conn.rollback()
        flash(f"Error updating event: {e}", "error")
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()

@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return redirect(url_for('admin_dashboard'))
    
    try:
        with conn.cursor() as cur:
            # Update event status to cancelled
            cur.execute("""
                UPDATE events
                SET status = 'cancelled'
                WHERE id = %s
            """, (event_id,))
            
            conn.commit()
            flash("Event cancelled successfully", "success")
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        conn.rollback()
        flash(f"Error cancelling event: {e}", "error")
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return redirect(url_for('admin_dashboard'))
    
    try:
        with conn.cursor() as cur:
            # Check if user has active bookings
            cur.execute("""
                SELECT COUNT(*) FROM bookings
                WHERE user_id = %s AND status = 'active'
            """, (user_id,))
            
            active_bookings = cur.fetchone()[0]
            if active_bookings > 0:
                flash("Cannot delete user with active bookings", "error")
                return redirect(url_for('admin_dashboard'))
            
            # Delete all cancelled bookings for this user
            cur.execute("""
                DELETE FROM bookings
                WHERE user_id = %s AND status = 'cancelled'
            """, (user_id,))
            
            # Delete user
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            conn.commit()
            flash("User deleted successfully", "success")
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting user: {e}", "error")
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([first_name, last_name, email]):
        flash("Please fill all required fields", "error")
        return redirect(url_for('user_dashboard'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection error", "error")
        return redirect(url_for('user_dashboard'))
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get current user data
            cur.execute("""
                SELECT password
                FROM users WHERE id = %s
            """, (session['user_id'],))
            
            user = cur.fetchone()
            
            # Update basic info
            cur.execute("""
                UPDATE users
                SET first_name = %s, last_name = %s, email = %s, phone = %s
                WHERE id = %s
            """, (
                first_name, last_name, email, phone, session['user_id']
            ))
            
            # Update password if provided
            if current_password and new_password and confirm_password:
                if new_password != confirm_password:
                    flash("New passwords do not match", "error")
                    return redirect(url_for('user_dashboard'))
                
                if not check_password_hash(user['password'], current_password):
                    flash("Current password is incorrect", "error")
                    return redirect(url_for('user_dashboard'))
                
                hashed_password = generate_password_hash(new_password)
                cur.execute("""
                    UPDATE users
                    SET password = %s
                    WHERE id = %s
                """, (hashed_password, session['user_id']))
            
            conn.commit()
            
            # Update session name
            session['user_name'] = f"{first_name} {last_name}"
            
            flash("Profile updated successfully", "success")
            return redirect(url_for('user_dashboard'))
    except Exception as e:
        conn.rollback()
        flash(f"Error updating profile: {e}", "error")
        return redirect(url_for('user_dashboard'))
    finally:
        conn.close()

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Create admin user
    ensure_admin_exists()
    
    # Run the app
    app.run(debug=True)
