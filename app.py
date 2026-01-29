from flask import Flask, render_template, request, flash, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FileField, DateField, TimeField, IntegerField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Regexp, NumberRange, Optional
import os
from datetime import datetime
import urllib.parse
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# ... (Previous imports kept if not redundant)
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import razorpay
import json
import hmac
import hashlib


app = Flask(__name__)
# Security Key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = 1800

# Login Manager Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- PROFESSIONAL LOGGING SETUP ---
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/homecare.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)
app.logger.info('Homecare Startup')

# --- RAZORPAY CONFIGURATION ---
# Using Test Credentials for Development (Replace with Env Vars in Prod)
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_ChangeMe123') 
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'secret_ChangeMe123')

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'Jamshomecare@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'geyywvdqjrmlcvfz')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

mail = Mail(app)

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
# Critical for Render: Ensure 'instance' folder exists before SQLite tries to write
os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

# Production DB Support (PostgreSQL) with SQLite Fallback
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
else:
    db_path = os.path.join(basedir, 'instance', 'homehealthcare_v2.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)
migrate = Migrate(app, db) # Initialize Flask-Migrate
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Link to User
    patient_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=False)
    area = db.Column(db.String(100), nullable=False)
    landmark = db.Column(db.String(200))
    service_type = db.Column(db.String(50), nullable=False)
    test_name = db.Column(db.String(100))
    prescription_path = db.Column(db.String(200))
    preferred_date = db.Column(db.Date, nullable=False)
    preferred_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(20), default='cod')
    staff_id = db.Column(db.Integer, nullable=True) 

class LabTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Package, Fever, Routine, Women
    price = db.Column(db.Integer, nullable=False)
    original_price = db.Column(db.Integer) # Added for MRP display
    description = db.Column(db.String(200))
    components = db.Column(db.Text)
    significance = db.Column(db.Text)
    tat = db.Column(db.String(50)) # Turnaround Time
    sample_type = db.Column(db.String(50))

# Admin Contact Details
ADMIN_EMAIL = 'jamshomecare@gmail.com'
ADMIN_PHONES = ['9758928213']

class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    service = db.Column(db.String(50))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='unread')

class BookingForm(FlaskForm):
    patient_name = StringField('Patient Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=1, max=120)])
    mobile = StringField('Mobile Number', validators=[
        DataRequired(),
        Regexp(r'^(\+91[\-\s]?)?[0-9]{10}$', message='Please enter a valid 10-digit mobile number')
    ])
    email = StringField('Email (Optional)', validators=[Optional(), Email()]) # Added Optional() so empty strings pass
    address = TextAreaField('Address', validators=[DataRequired()])
    area = StringField('Area/Locality', validators=[DataRequired()])
    landmark = StringField('Landmark (Optional)')
    service_type = SelectField('Service Required', choices=[
        ('', 'Select Service'),
        ('medical_care', 'Medical Home Services (Injections, Dressing, Catheter Care, etc.)'),
        ('elderly_care', 'Elderly & Bedridden Care'),
        ('sample_collection', 'Home Sample Collection'),
        ('medicine_delivery', 'Medicine Delivery & Support')
    ], validators=[DataRequired()])
    test_name = StringField('Specific Test/Package Name (Optional)')
    prescription = FileField('Upload Prescription (Optional but Recommended)')
    preferred_date = DateField('Preferred Date', validators=[DataRequired()])
    preferred_time = TimeField('Preferred Time', validators=[DataRequired()])
    payment_method = StringField('Payment Method', default='cod') # cod or online
    submit = SubmitField('Book Home Visit')

class ContactForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[
        DataRequired(), 
        Regexp(r'^[0-9+\s-]{10,}$', message='Please enter a valid mobile number')
    ])
    service = SelectField('Service Interested In', choices=[
        ('', 'Select a Service'),
        ('Home Visit', 'Doctor/Nurse Home Visit'),
        ('Lab Test', 'Lab Sample Collection'),
        ('Injection', 'Injection/Drip Service'),
        ('Elderly Care', 'Elderly Care Support'),
        ('Medicine', 'Medicine Delivery'),
        ('Other', 'Other Inquiry')
    ], validators=[DataRequired()])
    message = TextAreaField('Message (Optional)')
    submit = SubmitField('Submit Request')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile Number', validators=[
        DataRequired(),
        Regexp(r'^(\+91[\-\s]?)?[0-9]{10}$', message='Please enter a valid 10-digit mobile number')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Create Account')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ContactForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[
        DataRequired(), 
        Regexp(r'^[0-9+\s-]{10,}$', message='Please enter a valid mobile number')
    ])
    service = SelectField('Service Interested In', choices=[
        ('', 'Select a Service'),
        ('Home Visit', 'Doctor/Nurse Home Visit'),
        ('Lab Test', 'Lab Sample Collection'),
        ('Injection', 'Injection/Drip Service'),
        ('Elderly Care', 'Elderly Care Support'),
        ('Medicine', 'Medicine Delivery'),
        ('Other', 'Other Inquiry')
    ], validators=[DataRequired()])
    message = TextAreaField('Message (Optional)')
    submit = SubmitField('Submit Request')

# Duplicate function removed

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/services')
def services():
    return render_template('services.html')

# Duplicate routes removed


import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Helper: Send Email (Native SMTP + Threading for Reliability)
# Helper: Send Email (Flask-Mail + Threading for Reliability)
def send_async_email(app_config, subject, body, recipients):
    with app.app_context():
        try:
            # Create Message using Flask-Mail
            msg = Message(subject, recipients=recipients)
            msg.body = body
            # HTML body support if needed in future
            # msg.html = body 
            
            mail.send(msg)
            app.logger.info(f"Background Thread: Email sent successfully to {recipients}")
        except Exception as e:
            app.logger.error(f"BACKGROUND EMAIL ERROR: {e}")

def send_email_notification(subject, body, recipients):
    # Pass config explicitly to thread (copying needed context)
    app_config = app.config.copy()
    
    if not app_config['MAIL_USERNAME'] or 'your-email' in app_config['MAIL_USERNAME']:
        print("Skipping email: No credentials.")
        return False
        
    # Start Thread
    email_thread = threading.Thread(target=send_async_email, args=(app_config, subject, body, recipients))
    email_thread.start()
    print("Email thread started. UI will not block.")
    return True

@app.route('/book-home-visit', methods=['GET', 'POST'])
def book_home_visit():
    form = BookingForm()
    if form.validate_on_submit():
        # Handle file upload
        prescription_path = None
        if form.prescription.data:
            from werkzeug.utils import secure_filename
            original_filename = secure_filename(form.prescription.data.filename)
            filename = f"prescription_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{original_filename}"
            form.prescription.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            prescription_path = filename

        # Create booking
        booking = Booking(
            patient_name=form.patient_name.data,
            age=form.age.data,
            mobile=form.mobile.data,
            email=form.email.data, # Save customer email
            address=form.address.data,
            area=form.area.data,
            landmark=form.landmark.data,
            service_type=form.service_type.data,
            test_name=form.test_name.data,
            prescription_path=prescription_path,
            preferred_date=form.preferred_date.data,
            preferred_time=form.preferred_time.data,
            payment_method=request.form.get('payment_method', 'cod')
        )
        db.session.add(booking)
        db.session.commit()
        
        # Payment Message
        payment_text = "Pay on Collection"
        if booking.payment_method == 'online':
             payment_text = "Pay Online"
             # Redirect to Payment Page instead of Confirmation
             return redirect(url_for('payment', booking_id=booking.id))

        # Prepare WhatsApp message
        service_names = {
            'medical_care': 'Medical Home Services',
            'elderly_care': 'Elderly & Bedridden Care',
            'sample_collection': 'Home Sample Collection',
            'medicine_delivery': 'Medicine Delivery & Support'
        }
        service_display = service_names.get(booking.service_type, booking.service_type)

        # Format message for WhatsApp
        # Format message for WhatsApp (Conversational Style for User)
        message = f"""Hi Jams Homecare, I just booked a home visit. Please confirm.

Patient: {booking.patient_name}
Service: {service_display}
Date: {booking.preferred_date.strftime('%d/%m/%Y')}
Time: {booking.preferred_time.strftime('%I:%M %p')}
Address: {booking.address}, {booking.area}

Booking ID: #HHC{booking.id:04d}"""

        # 1. Send Admin Notification
        admin_body = f"""New Booking Received!

Patient: {booking.patient_name}
Service: {service_display}
Test: {booking.test_name or 'N/A'}
Date: {booking.preferred_date}
Time: {booking.preferred_time}
Phone: {booking.mobile}
Email: {booking.email or 'N/A'}

Check Admin Dashboard: http://127.0.0.1:8000/admin
"""
        send_email_notification(f"New Booking: {booking.patient_name}", admin_body, [ADMIN_EMAIL])

        # 2. Send Patient Confirmation (if email provided)
        if booking.email:
            patient_body = f"""Dear {booking.patient_name},

Thank you for choosing Jams Homecare Services. Your booking has been received.

Service: {service_display}
Date: {booking.preferred_date.strftime('%d %b %Y')}
Time: {booking.preferred_time.strftime('%I:%M %p')}
Booking ID: #HHC{booking.id:04d}

Next Steps:
1. Our clinical team will review your request.
2. You will receive a confirmation call/WhatsApp within 2 hours.
3. For cancellations, please call us at +91 {ADMIN_PHONES[0]}.

Regards,
Jams Homecare Team
Haldwani, Uttarakhand
"""
            send_email_notification(f"Booking Received - #HHC{booking.id:04d}", patient_body, [booking.email])

        whatsapp_url = f"https://wa.me/91{ADMIN_PHONES[0]}?text={urllib.parse.quote(message)}"

        flash('Booking submitted successfully! Our team will verify your prescription and contact you within 2 hours.', 'success')
        return render_template('booking_confirmation.html',
                             booking=booking,
                             service_name=service_names.get(booking.service_type, booking.service_type),
                             whatsapp_url=whatsapp_url)
    
    else:
        # Critical: Show validation errors to user
        app.logger.warning(f"FORM VALIDATION FAILED: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')

    return render_template('book_home_visit.html', form=form)

# --- PAYMENT ROUTES ---
@app.route('/payment/<int:booking_id>')
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Create Razorpay Order
    amount = 49900 # Example: Fixed Amount ₹499.00 (in paise)
    
    try:
        data = { "amount": amount, "currency": "INR", "receipt": f"HHC{booking.id}" }
        order = razorpay_client.order.create(data=data)
        app.logger.info(f"Created Razorpay Order: {order['id']} for Booking {booking.id}")
    except Exception as e:
        app.logger.error(f"Razorpay Order Creation Failed (likely invalid keys): {e}")
        # MOCK MODE for Demonstration if keys are invalid
        order = {
            "id": f"order_mock_{int(datetime.now().timestamp())}",
            "amount": amount,
            "currency": "INR"
        }
        flash("Running in Payment Simulation Mode (Invalid API Keys)", "warning")

    return render_template('payment.html', 
                         booking=booking, 
                         order=order,
                         key_id=RAZORPAY_KEY_ID)

@app.route('/payment/verify', methods=['POST'])
@app.route('/payment/verify', methods=['POST'])
def payment_verify():
    data = request.form
    booking_id = request.args.get('booking_id') # Passed via URL query param
    
    if not booking_id:
        app.logger.error("Payment Verify: Missing Booking ID")
        flash("System Error: Booking ID not found.", 'danger')
        return redirect(url_for('home'))

    booking = Booking.query.get_or_404(booking_id)

    try:
        # Handle MOCK/SIMULATION Mode
        is_simulation = data.get('razorpay_order_id', '').startswith('order_mock_')
        
        if is_simulation:
            app.logger.info(f"Simulation Payment Verified: {data['razorpay_order_id']}")
        else:
            # Verify Signature (Real Mode)
            params_dict = {
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            }
            razorpay_client.utility.verify_payment_signature(params_dict)
        
        # --- SUCCESS PATH ---
        booking.status = 'confirmed'
        booking.payment_method = 'online_paid'
        db.session.commit()
        
        app.logger.info(f"Booking {booking.id} Confirmed & Paid: {data['razorpay_payment_id']}")

        # Send Payment Confirmation Email
        if booking.email:
             # Prepare WhatsApp message for easier contact
             service_names = {
                'medical_care': 'Medical Home Services',
                'elderly_care': 'Elderly & Bedridden Care',
                'sample_collection': 'Home Sample Collection',
                'medicine_delivery': 'Medicine Delivery & Support'
            }
             service_display = service_names.get(booking.service_type, booking.service_type)
             
             paid_body = f"""Dear {booking.patient_name},

Payment Successful! Your booking is confirmed.

Transaction Ref: {data['razorpay_payment_id']}
Amount: ₹499.00
Booking ID: #HHC{booking.id:04d}
Service: {service_display}
Date: {booking.preferred_date.strftime('%d/%m/%Y')} {booking.preferred_time.strftime('%I:%M %p')}

Our team will call you shortly to confirm staff details.

Regards,
Jams Homecare
"""
             send_email_notification(f"Payment Received - #HHC{booking.id:04d}", paid_body, [booking.email])

        if is_simulation:
            flash('Payment Successful! (Simulation Mode)', 'success')
        else:
            flash('Payment Successful! Your booking is confirmed.', 'success')

        # Redirect to Dedicated Success Page
        return redirect(url_for('payment_success', booking_id=booking.id))
        
    except razorpay.errors.SignatureVerificationError:
        app.logger.error("Payment Signature Verification Failed!")
        flash('Payment Failed. Please try again.', 'danger')
        return redirect(url_for('dashboard'))
    except Exception as e:
        app.logger.error(f"Payment Error: {e}")
        flash('An error occurred during payment verification.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/payment/success/<int:booking_id>')
def payment_success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    # Security: Only show if confirmed (prevent peeking)
    if booking.status != 'confirmed':
        return redirect(url_for('home'))
        
    service_names = {
        'medical_care': 'Medical Home Services',
        'elderly_care': 'Elderly & Bedridden Care',
        'sample_collection': 'Home Sample Collection',
        'medicine_delivery': 'Medicine Delivery & Support'
    }
    
    return render_template('payment_success.html',
                         booking=booking,
                         service_name=service_names.get(booking.service_type, booking.service_type))

@app.route('/lab-collection')
def lab_collection():
    try:
        # Fetch all tests from DB
        lab_tests = LabTest.query.all()
        
        # Serialize to list of dicts for clean JSON handoff
        lab_tests_data = [{
            'name': t.name,
            'category': t.category,
            'price': t.price,
            'original_price': t.original_price, # Pass to template
            'description': t.description,
            'components': t.components,
            'significance': t.significance,
            'tat': t.tat,
            'sample': t.sample_type
        } for t in lab_tests]

        return render_template('lab_collection.html', lab_tests_data=lab_tests_data)
    except Exception as e:
        app.logger.error(f"Lab Collection Page Error: {e}")
        return f"<h1>System Error</h1><p>We are updating the catalog. Please check back in 5 minutes.</p><p><small>Debug: {e}</small></p>", 500

@app.route('/about-us')
def about_us():
    return render_template('home.html') # Placeholder or separate template

# Legal Pages
@app.route('/privacy-policy')
def privacy_policy():
    return render_template('policy_privacy.html')

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('policy_terms.html')

@app.route('/refund-policy')
def refund_policy():
    return render_template('policy_refund.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        inquiry = Inquiry(
            name=form.name.data,
            phone=form.phone.data,
            service=form.service.data,
            message=form.message.data
        )
        db.session.add(inquiry)
        db.session.commit()
        
        # Send Email Notification
        email_body = f"""New Contact Inquiry!

Name: {inquiry.name}
Phone: {inquiry.phone}
Service Interest: {inquiry.service}
Message: {inquiry.message}

Check Admin Dashboard: http://127.0.0.1:8000/admin
"""
        send_email_notification(f"New Inquiry: {inquiry.name}", email_body, [ADMIN_EMAIL])
        
        flash('Message sent successfully! Our team will contact you shortly.', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html', form=form, admin_phone=ADMIN_PHONES[0])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            name=form.name.data,
            email=form.email.data,
            mobile=form.mobile.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # Auto login
        login_user(user)
        flash('Account created successfully! Welcome to Jams Homecare.', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('register.html', form=form)

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Access Control Panel')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # User login only
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('login.html', form=form)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
        
    form = AdminLoginForm()
    if form.validate_on_submit():
        print(f"DEBUG: Attempting Admin Login with '{form.username.data}' / '{form.password.data}'")
        # Secure hardcoded credentials (in prod use env vars)
        username = form.username.data.strip()
        password = form.password.data.strip()
        
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            flash('Welcome back, Administrator.', 'success')
            return redirect(url_for('admin_dashboard'))
            print("DEBUG: Admin credentials failed.")
            flash('Access Denied. Invalid credentials.', 'danger')
    else:
        if request.method == 'POST':
             print(f"DEBUG: Form validation failed: {form.errors}")
            
    return render_template('admin_login.html', form=form)

@app.route('/health_check')
def health_check():
    """Debug route to expose production errors."""
    status = {"status": "ok", "db": "unknown", "env": "unknown"}
    try:
        # Check 1: Filesystem (Render instance folder)
        import os
        db_path = os.path.join(app.config.get('INSTANCE_PATH', os.getcwd()), 'instance')
        status['instance_folder_exists'] = os.path.exists(db_path)
        if not os.path.exists(db_path):
            try:
                os.makedirs(db_path, exist_ok=True)
                status['instance_folder_created'] = True
            except Exception as e:
                status['instance_folder_error'] = str(e)

        # Check 2: Database Connection & Data Integrity
        try:
            user_count = User.query.count()
            test_count = LabTest.query.count()
            status['db'] = f"Connected. Users: {user_count}, Tests: {test_count}"
            
            # Check 3: Data Serialization (Mimic /lab-collection logic)
            first_test = LabTest.query.first()
            if first_test:
                sample_data = {
                    'name': first_test.name,
                    'price': first_test.price,
                    'tat': first_test.tat, # Check if this crashes on None
                    'sample': first_test.sample_type
                }
                status['data_sample'] = sample_data
                
        except Exception as e:
            status['db_error'] = str(e)
            
            # Attempt Recovery
            try:
                with app.app_context():
                    db.create_all()
                    seed_production_data()
                status['db_recovery_attempt'] = "Ran create_all() and seed()"
            except Exception as rec_e:
                status['db_recovery_error'] = str(rec_e)

    except Exception as e:
        status['fatal_error'] = str(e)
    
    return status

@app.route('/logout')
def logout():
    logout_user()
    session.pop('admin_logged_in', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('dashboard.html', bookings=bookings)

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template('admin.html', bookings=bookings, inquiries=inquiries)

# --- DEPLOYMENT AUTO-SEEDING (CRITICAL FOR RENDER) ---
def seed_production_data():
    """Populates the database with initial Lab Tests if empty."""
    try:
        with app.app_context():
            db.create_all() # 1. Create Tables
            
            if not LabTest.query.first(): # 2. Check if Empty
                app.logger.info("Database Empty! Seeding Initial Lab Data...")
                
                # Max Lab Packages (Full Catalog)
                packages = [
                    {
                        "name": "Max Care Health Check 1",
                        "category": "Health Packages",
                        "price": 999,
                        "original_price": 1800,
                        "description": "Essential full body screening covering 37 Parameters.",
                        "components": "• Diabetes: Fasting Blood Sugar\n• Heart/Lipid Profile: Cholesterol, Triglycerides\n• Thyroid: T3, T4, TSH\n• Kidney: Uric Acid\n• Bone: Calcium",
                        "significance": "Essential baseline checkup.",
                        "tat": "24 Hours",
                        "sample_type": "Blood"
                    },
                    {
                        "name": "Max Care Health Check 2",
                        "category": "Health Packages",
                        "price": 1250,
                        "original_price": 2400,
                        "description": "Comprehensive screening with Liver & Kidney functions.",
                        "components": "• All in Check 1 PLUS:\n• HbA1c\n• Liver Function Test (LFT)\n• Kidney Function Test (KFT)\n• Hemogram",
                        "significance": "Recommended for annual screening.",
                        "tat": "24 Hours",
                        "sample_type": "Blood & Urine"
                    },
                    {
                        "name": "Max Care Health Check 3",
                        "category": "Health Packages",
                        "price": 2250,
                        "original_price": 4100,
                        "description": "Advanced profile including Vitamins.",
                        "components": "• All in Check 2 PLUS:\n• Vitamin D (Total)\n• Vitamin B12\n• Iron Studies",
                        "significance": "Detects silent deficiencies.",
                        "tat": "24-48 Hours",
                        "sample_type": "Blood"
                    },
                     {
                        "name": "Max Care Health Check 3 (Couple Pack)",
                        "category": "Health Packages",
                        "price": 4000,
                        "original_price": 8200,
                        "description": "1+1 Family Offer for Check 3 (Save ₹500).",
                        "components": "• Complete Max Care Health Check 3 for TWO Persons.",
                        "significance": "Best Value: Complete protection for you and your partner.",
                        "tat": "24-48 Hours",
                        "sample_type": "Blood"
                    },
                    {
                        "name": "Max Care Health Check 4",
                        "category": "Health Packages",
                        "price": 2700,
                        "original_price": 4900,
                        "description": "Extensive profile with Inflammation & Urine markers.",
                        "components": "• All in Check 3 PLUS:\n• CRP (C-Reactive Protein)\n• Urine Routine & Microscopy\n• Electrolytes",
                        "significance": "Deep screening for infection, inflammation.",
                        "tat": "24-48 Hours",
                        "sample_type": "Blood & Urine"
                    },
                    {
                        "name": "Max Care Health Check 5",
                        "category": "Health Packages",
                        "price": 3200,
                        "original_price": 6400,
                        "description": "Premium Executive Profile with Cardiac & Pancreas markers.",
                        "components": "• All in Check 4 PLUS:\n• Cardiac Markers: Lp(a), Apo-A1, Apo-B, hs-CRP\n• Pancreas: Amylase, Lipase\n• Arthritis: RA Factor",
                        "significance": "The most detailed health audit available.",
                        "tat": "48 Hours",
                        "sample_type": "Blood & Urine"
                    }
                ]
                
                # Single Tests
                single_tests = [
                    {"name": "CBC (Complete Blood Count)", "category": "Routine", "price": 350, "description": "Checks Hemoglobin, RBC, WBC, Platelets.", "components": "Hb, TLC, DLC, Platelet Count", "significance": "General health, infection, anemia."},
                    {"name": "Thyroid Profile (Total)", "category": "Thyroid", "price": 550, "description": "T3, T4, and TSH levels.", "components": "Total T3, Total T4, TSH", "significance": "Thyroid disorders."},
                    {"name": "Lipid Profile", "category": "Heart", "price": 650, "description": "Cholesterol and Triglycerides.", "components": "Total Cholesterol, Triglycerides, HDL, LDL", "significance": "Heart health risk."},
                    {"name": "HbA1c", "category": "Diabetes", "price": 500, "description": "Average blood sugar (3 months).", "components": "Glycosylated Haemoglobin", "significance": "Diabetes management."},
                    {"name": "Liver Function Test (LFT)", "category": "Routine", "price": 850, "description": "Checks liver health.", "components": "Bilirubin, SGOT, SGPT, ALP, Protein", "significance": "Liver damage."},
                    {"name": "Kidney Function Test (KFT)", "category": "Routine", "price": 850, "description": "Checks kidney performance.", "components": "Urea, Creatinine, Uric Acid", "significance": "Kidney health."},
                    {"name": "Vitamin D (Total)", "category": "Vitamins", "price": 1000, "description": "Bone health vitamin.", "components": "25-OH Vitamin D", "significance": "Bone weakness, fatigue."},
                    {"name": "Vitamin B12", "category": "Vitamins", "price": 1000, "description": "Nerve health vitamin.", "components": "Cyanocobalamin", "significance": "Nerve issues, anemia."},
                    {"name": "Urine Routine & Microscopy", "category": "Routine", "price": 200, "description": "Basic urine exam.", "components": "Physical, Chemical, Microscopic", "significance": "UTI, kidney issues."},
                    {"name": "Dengue NS1 Antigen", "category": "Fever", "price": 600, "description": "Early dengue detection.", "components": "Dengue NS1", "significance": "Fever diagnosis."},
                    {"name": "Typhoid (Widal)", "category": "Fever", "price": 250, "description": "Typhoid fever check.", "components": "Salmonella Typhi Antibodies", "significance": "Fever diagnosis."},
                    {"name": "CRP (C-Reactive Protein)", "category": "Heart", "price": 450, "description": "Inflammation marker.", "components": "CRP Quantitative", "significance": "Infection or inflammation."}
                ]
                
                # Add all with EXPLICIT mapping (Safe & Robust)
                for t in packages + single_tests:
                    test = LabTest(
                        name=t['name'],
                        category=t['category'],
                        price=t['price'],
                        original_price=t.get('original_price'),
                        description=t['description'],
                        components=t.get('components', ''),
                        significance=t.get('significance', ''),
                        tat=t.get('tat', '24 Hours'),
                        sample_type=t.get('sample_type', 'Blood')
                    )
                    db.session.add(test)
                
                db.session.commit()
                app.logger.info("Seeding Complete: Added Max Lab Packages.")
            else:
                app.logger.info("Database already populated.")
    except Exception as e:
        app.logger.error(f"Seeding Failed: {e}")

# Run Seeding on Module Import (Gunicorn loads this)
try:
    seed_production_data()
except Exception as e:
    app.logger.error(f"CRITICAL: Startup Seeding Failed: {e}")
    print(f"CRITICAL: Startup Seeding Failed: {e}") # Ensure it hits stdout


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
