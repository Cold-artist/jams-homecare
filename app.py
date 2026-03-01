from flask import Flask, render_template, request, flash, redirect, url_for, session, abort, jsonify
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
import urllib.request
import urllib.error # CRITICAL: Required for catching HTTPError
import hmac
import hashlib
from sqlalchemy import func, inspect, text # Critical for db_recovery

# Cloudinary Storage
import cloudinary
import cloudinary.uploader
import cloudinary.api


app = Flask(__name__)
# Security Key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = 1800
app.config['PROPAGATE_EXCEPTIONS'] = True # CRITICAL: Show 500 errors, don't hide them
print("DEBUG: App Loading...", flush=True)

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

# --- CLOUDINARY CONFIGURATION ---
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')
# If URL is provided, Cloudinary SDK automatically picks it up from the environment
# But we explicitly configure it for safety in case it's not set globally
if CLOUDINARY_URL:
    try:
        cloudinary.config(
            secure=True
        )
        app.logger.info("Cloudinary configured successfully via CLOUDINARY_URL")
    except Exception as e:
        app.logger.error(f"Failed to configure Cloudinary: {e}")
else:
     app.logger.warning("CLOUDINARY_URL environment variable is MISSING. Image uploads will fail.")

# --- RAZORPAY CONFIGURATION ---
# Using Test Credentials for Development (Replace with Env Vars in Prod)
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
if RAZORPAY_KEY_ID: RAZORPAY_KEY_ID = RAZORPAY_KEY_ID.strip()

RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
if RAZORPAY_KEY_SECRET: RAZORPAY_KEY_SECRET = RAZORPAY_KEY_SECRET.strip()

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Email Configuration
# Email Configuration (Ultra-Robust for Render)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587  # TLS (Standard) prevents timeouts
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))  # TLS (Standard) prevents timeouts
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USE_TLS'] = True # Enable TLS for 587
app.config['MAIL_TIMEOUT'] = 10 # Force Timeout in 10s (prevents hanging)

# Robust Env Loader (Case-Insensitive Scan)
def get_env_robust(key_fragment):
    for k, v in os.environ.items():
        if key_fragment.lower() == k.lower():
            return v.strip().strip("'").strip('"')
    return None

app.config['MAIL_USERNAME'] = get_env_robust('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = get_env_robust('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

# SendGrid Configuration (Robust Fallback)
app.config['SENDGRID_API_KEY'] = os.environ.get('SENDGRID_API_KEY', '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')

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
    password_hash = db.Column(db.String(256)) # Increased for scrypt hash
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
    amount = db.Column(db.Integer, default=499) # Store agreed price
    staff_id = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # Added for Admin tracking
    
    # Relationship to Items
    items = db.relationship('BookingItem', backref='booking', lazy=True, cascade="all, delete-orphan")

class BookingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    item_type = db.Column(db.String(50), nullable=False) # 'medicine' or 'lab_test'
    item_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Integer, nullable=False) # Price at time of booking
    
    def __repr__(self):
        return f"<Item {self.item_name} x{self.quantity}>" 

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

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), default='OTC') # Prescription, OTC, Supplement
    price = db.Column(db.Integer, nullable=False)
    original_price = db.Column(db.Integer)
    image_url = db.Column(db.String(500)) # External URL (e.g., Imgur/Cloudinary)
    description = db.Column(db.String(300))
    is_active = db.Column(db.Boolean, default=True)

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
# Helper: Send Email (SendGrid API V3 - Render Firewall Bypass)
def send_async_email(app, subject, body, recipients):
    with app.app_context():
        # Priority 1: SendGrid API (Port 80/443 - Firewall Safe)
        sg_key = app.config.get('SENDGRID_API_KEY')
        sender = "jamshomecare@gmail.com" # Verified User
        
        if sg_key and sg_key.startswith("SG."):
            try:
                url = "https://api.sendgrid.com/v3/mail/send"
                
                # Payload construction remains same
                to_emails = [{"email": r} for r in recipients]
                payload = {
                    "personalizations": [{"to": to_emails}],
                    "from": {"email": sender, "name": "Jams Homecare"},
                    "subject": subject,
                    "content": [{"type": "text/plain", "value": body}]
                }
                
                # URLLIB Implementation (dependency-free)
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(url, data=data, method='POST')
                req.add_header('Authorization', f'Bearer {sg_key}')
                req.add_header('Content-Type', 'application/json')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                     if 200 <= response.status < 300:
                         app.logger.info(f"SendGrid Success (urllib): {response.status} to {recipients}")
                         return True
            except urllib.error.HTTPError as e:
                app.logger.error(f"SendGrid API Error: {e.code} - {e.read().decode('utf-8')}")
            except Exception as e:
                app.logger.error(f"SendGrid Exception (urllib): {e}")

        # Priority 2: Standard SMTP (Flask-Mail) - Fallback for LocalDev or if Key missing
        try:
            msg = Message(subject, recipients=recipients)
            msg.body = body
            mail.send(msg)
            app.logger.info(f"SMTP Success (Fallback) to {recipients}")
            return True
        except Exception as e:
            app.logger.error(f"SMTP Fallback Failed: {e}")
            return False

def send_email_notification(subject, body, recipients, sync=False):
    # Check credentials before spawning thread
    if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
        app.logger.warning("Skipping email: No MAIL_USERNAME or MAIL_PASSWORD configured.")
        return False
        
    if sync:
        # Blocking Send (For Critical Flows to catch errors)
        try:
             success = send_async_email(app, subject, body, recipients)
             if success:
                 app.logger.info(f"Sync Email sent successfully to {recipients}")
                 return True
             else:
                 app.logger.error("Sync Email Failed inside send_async_email")
                 return False
        except Exception as e:
             app.logger.error(f"Sync Email Failed: {e}")
             return False

    # Start Thread with actual app instance (passed to thread)
    # Note: We pass 'app' (the Flask object) directly. 
    # This works because 'app' is global here, but passing it is safer for clarity.
    email_thread = threading.Thread(target=send_async_email, args=(app, subject, body, recipients))
    email_thread.start()
    app.logger.info(f"Email thread started for {recipients}")
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

        # Calculate Price based on Service/Test (Robust Lookup)
        # Default to 499 unless overridden by Cart or Lab Test
        booking_price = 499 
        
        # 1. CHECK FOR CART TOTAL (Passed via URL from /cart/checkout)
        cart_total = request.args.get('price')
        if cart_total:
            try:
                booking_price = int(float(cart_total))
                app.logger.info(f"Booking Price Set from Cart: {booking_price}")
            except ValueError:
                app.logger.warning(f"Invalid Cart Price '{cart_total}', defaulting to 499")

        service_type = form.service_type.data
        test_name = form.test_name.data

        # 2. CHECK FOR LAB TEST PRICE (Overrides Cart if specific test selected manually)
        if service_type == 'sample_collection' and test_name:
            # Case-insensitive match for robustness
            cleaned_name = test_name.strip()
            lab_test = LabTest.query.filter(func.lower(LabTest.name) == func.lower(cleaned_name)).first()
            
            if lab_test:
                booking_price = lab_test.price
                app.logger.info(f"Price Found from Lab Test Update: {booking_price} for {test_name}")
            else:
                app.logger.warning(f"Price Lookup Failed for: {test_name}")

        # Create booking (Unified)
        booking = Booking(
            user_id=current_user.id if current_user.is_authenticated else None,
            patient_name=form.patient_name.data,
            age=form.age.data,
            mobile=form.mobile.data,
            email=form.email.data,
            address=form.address.data,
            area=form.area.data,
            landmark=form.landmark.data,
            service_type=service_type,
            test_name=test_name, # Kept for single manual test booking
            prescription_path=prescription_path,
            preferred_date=form.preferred_date.data,
            preferred_time=form.preferred_time.data,
            amount=booking_price,
            payment_method=request.form.get('payment_method', 'cod'),
            status='pending' # Default status
        )
        db.session.add(booking)
        db.session.flush() # Get ID before committing items

        # --- UNIFIED BOOKING LOGIC: SAVE ITEMS ---
        cart = session.get('cart', [])
        
        # 1. Add Cart Items
        for item in cart:
            booking_item = BookingItem(
                booking_id=booking.id,
                item_type=item.get('type', 'medicine'),
                item_name=item.get('name'),
                quantity=item.get('qty', 1),
                price=item.get('price', 0)
            )
            db.session.add(booking_item)
            
        # 2. Add Single Lab Test (if booked directly via form, not cart)
        if service_type == 'sample_collection' and test_name:
             # Check if this was already in cart to avoid duplicates? 
             # For now, we assume form-based booking is separate or additive
             # If cart is empty, this ensures the test is recorded as an item
            if not cart: 
                 booking_item = BookingItem(
                    booking_id=booking.id,
                    item_type='lab_test',
                    item_name=test_name,
                    quantity=1,
                    price=booking_price
                )
                 db.session.add(booking_item)

        db.session.commit()
        
        # Clear Cart after successful booking
        session.pop('cart', None)
        
        # Payment Message
        payment_text = "Pay on Collection"
        if booking.payment_method == 'online':
             payment_text = "Pay Online"
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
    # Ensure amount is an integer (default 499 if missing)
    booking_amount = booking.amount if booking.amount else 499
    amount = booking_amount * 100 # Convert to Paise
    
    try:
        data = { "amount": amount, "currency": "INR", "receipt": f"HHC{booking.id}" }
        order = razorpay_client.order.create(data=data)
        app.logger.info(f"Created Razorpay Order: {order['id']} for Booking {booking.id}")
    except Exception as e:
        app.logger.error(f"Razorpay Order Creation Failed: {e}")
        
        # MOCK MODE Fallback
        order = {
            "id": f"order_mock_{int(datetime.now().timestamp())}",
            "amount": amount,
            "currency": "INR"
        }
        
        if not RAZORPAY_KEY_ID:
            flash("Setup Error: RAZORPAY_KEY_ID not found in Render settings.", "danger")
        else:
             flash(f"Payment Gateway Error: {str(e)}", "warning")

    return render_template('payment.html', 
                         booking=booking, 
                         order=order,
                         key_id=RAZORPAY_KEY_ID)

@app.route('/payment/verify', methods=['POST'])
def payment_verify():
    # Strict Safe Mode: No Global Handler, Simple Print, Async Email
    import sys
    print("DEBUG: ENTERED payment_verify", flush=True)
    
    try:
        data = request.form
        booking_id = request.args.get('booking_id')
        
        if not booking_id:
            msg = "Error: Missing booking_id query parameter"
            print(msg, flush=True)
            return msg, 400

        print(f"DEBUG: Processing Booking ID: {booking_id}", flush=True)
        booking = Booking.query.get_or_404(booking_id)

        # Lazy Init Razorpay Local
        key_id = os.environ.get('RAZORPAY_KEY_ID', '').strip()
        key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '').strip()
        client = razorpay.Client(auth=(key_id, key_secret))

        # Handle MOCK/SIMULATION Mode
        is_simulation = data.get('razorpay_order_id', '').startswith('order_mock_')
        
        if not is_simulation:
            # Verify Signature (Real Mode)
            params_dict = {
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            }
            client.utility.verify_payment_signature(params_dict)
        
        # --- SUCCESS PATH ---
        booking.status = 'confirmed'
        booking.payment_method = 'online_paid'
        db.session.commit()
        print(f"SUCCESS: Booking {booking.id} Confirmed", flush=True)

        # --- PREPARE EMAIL CONTENT ---
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
Amount: ₹{booking.amount}.00
Booking ID: #HHC{booking.id:04d}
Service: {service_display}
Date: {booking.preferred_date.strftime('%d/%m/%Y')} {booking.preferred_time.strftime('%I:%M %p')}

Our team will call you shortly to confirm staff details.

Regards,
Jams Homecare
"""

        # --- SEND EMAIL (Async Safe) ---
        if booking.email:
            # Revert to Async (sync=False) to prevent 500 crashes due to network
            # If email fails, it logs but doesn't stop payment
            send_email_notification(f"Payment Received - #HHC{booking.id:04d}", paid_body, [booking.email], sync=False)

        if is_simulation:
            flash('Payment Successful! (Simulation Mode)', 'success')
        else:
            flash('Payment Successful!', 'success')
            
        return redirect(url_for('payment_success', booking_id=booking.id))
        
    except razorpay.errors.SignatureVerificationError:
        print("ERROR: Signature Verification Failed", flush=True)
        flash('Payment Failed. Signature Invalid.', 'danger')
        return redirect(url_for('dashboard'))
    except Exception as e:
        # ABSOLUTE SAFETIES
        err_msg = f"FATAL ERROR: {str(e)}"
        print(err_msg, flush=True)
        # Return 200 OK with Error Text to bypass Server 500 Page
        return f"<h1>Diagnostic Error (200 OK)</h1><p>{str(e)}</p>", 200

@app.route('/payment/success/<int:booking_id>')
def payment_success(booking_id):
    import traceback
    try:
        booking = Booking.query.get_or_404(booking_id)
        # Security: Only show if confirmed (prevent peeking)
        if booking.status != 'confirmed':
            flash("This booking is not confirmed.", "warning")
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
    except Exception as e:
        print(f"FATAL SUCCESS PAGE ERROR: {e}")
        return f"<h1>Fatal Success Page Error (Diagnostic)</h1><pre>{traceback.format_exc()}</pre>", 200

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

# --- PHARMACY & CART ROUTES ---
@app.route('/pharmacy')
def pharmacy():
    medicines = Medicine.query.filter_by(is_active=True).all()
    return render_template('pharmacy.html', medicines=medicines)

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    try:
        item_id = request.form.get('item_id')
        item_type = request.form.get('item_type') # 'medicine' or 'test'
        item_name = request.form.get('item_name')
        item_price = int(request.form.get('item_price'))
        
        # Initialize Cart in Session if not exists
        if 'cart' not in session:
            session['cart'] = []
            
        cart = session['cart']
        
        # Check if item already in cart
        for item in cart:
            if item['id'] == item_id and item['type'] == item_type:
                item['qty'] += 1
                session.modified = True
                return jsonify({'status': 'success', 'msg': 'Quantity updated', 'cart_count': len(cart)})
                
        # Add new item
        cart.append({
            'id': item_id,
            'type': item_type,
            'name': item_name,
            'price': item_price,
            'qty': 1
        })
        session.modified = True
        
        return jsonify({'status': 'success', 'msg': 'Added to cart', 'cart_count': len(cart)})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': str(e)})

@app.route('/cart')
def view_cart():
    cart = session.get('cart', [])
    total = sum(item['price'] * item['qty'] for item in cart)
    return render_template('cart.html', cart=cart, total=total)

@app.route('/cart/remove/<int:index>')
def remove_from_cart(index):
    if 'cart' in session:
        cart = session['cart']
        if 0 <= index < len(cart):
            cart.pop(index)
            session.modified = True
    return redirect(url_for('view_cart'))

@app.route('/cart/checkout', methods=['GET', 'POST'])
def checkout_cart():
    cart = session.get('cart', [])
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('pharmacy'))
        
    total = sum(item['price'] * item['qty'] for item in cart)
    
    # Create a summary string for the "Service Type" field
    order_summary = ", ".join([f"{item['name']} x{item['qty']}" for item in cart])
    
    # Determine Service Type based on cart content
    has_lab_test = any(item['type'] == 'lab_test' for item in cart)
    service_type = 'Lab & Pharmacy Order' if has_lab_test else 'Pharmacy Delivery'
    
    # Redirect to Booking Form with context
    # We pass 'details' as the order summary so the form knows what's being booked
    return redirect(url_for('book_home_visit', service=service_type, details=order_summary, price=total))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            # 1. Check for duplicates
            if User.query.filter_by(email=form.email.data).first():
                flash('Email already registered.', 'danger')
                return redirect(url_for('register'))
            
            # 2. Create User
            user = User(
                name=form.name.data,
                email=form.email.data,
                mobile=form.mobile.data
            )
            user.set_password(form.password.data)
            
            # 3. Commit to DB
            db.session.add(user)
            db.session.commit()
            
            # 4. Login
            login_user(user, remember=True)
            session.permanent = True
            
            flash('Account created successfully! Welcome to Jams Homecare.', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback() # Important: Rollback on error
            app.logger.error(f"Signup Error: {e}")
            flash(f"Signup Failed (Internal Error): {str(e)}", 'danger')

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
            login_user(user, remember=True)
            session.permanent = True
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

@app.route('/admin/seed-medicines')
def trigger_seed_medicines():
    # Check for Admin Session (Not Patient Login)
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        from seed_medicines import seed_medicines
        seed_medicines()
        return "Medicines Seeded Successfully! <a href='/pharmacy'>Go to Pharmacy</a>"
    except Exception as e:
        return f"Seeding Failed: {e}"

    except Exception as e:
        return f"Seeding Failed: {e}"

@app.route('/debug-images')
def debug_images():
    import os
    try:
        # Check File System
        static_path = os.path.join(app.root_path, 'static', 'images', 'medicines')
        if os.path.exists(static_path):
            files = os.listdir(static_path)
        else:
            files = ["Directory Not Found"]
            
        # Check Database
        med = Medicine.query.filter_by(name="Glucon-D Regular 250g").first()
        db_url = med.image_url if med else "Medicine Not Found"
        
        return f"""
        <h1>Debug Info</h1>
        <h3>Directory: {static_path}</h3>
        <pre>{files}</pre>
        <h3>DB URL for Glucon-D Regular 250g:</h3>
        <pre>{db_url}</pre>
        """
    except Exception as e:
        return f"Error: {e}"

@app.route('/debug-config')
def debug_config():
    """Safe route to check if environment variables are loaded."""
    def mask(s):
        return f"{s[:2]}...{s[-2:]}" if s and len(s) > 4 else "MISSING"

    # Capture ALL MAIL related keys
    mail_keys = {k: mask(v) for k, v in os.environ.items() if 'MAIL' in k.upper()}

    return f"""
    <h1>Configuration Check (v3 - Robust)</h1>
    <h3>Keys Found in Environment:</h3>
    <pre>{json.dumps(mail_keys, indent=4)}</pre>
    <hr>
    <p><strong>App Config (MAIL_USERNAME):</strong> {mask(app.config.get('MAIL_USERNAME'))}</p>
    <p><strong>App Config (MAIL_PASSWORD):</strong> {'SET' if app.config.get('MAIL_PASSWORD') else 'MISSING'}</p>
    <p><strong>RAZORPAY_KEY_ID:</strong> {mask(RAZORPAY_KEY_ID)}</p>
    <hr>
    <p><small>If "Keys Found" is empty, Render has NOT loaded any variables. Try Manual Deploy or Restart.</small></p>
    """

    return status

@app.route('/health_check')
def health_check():
    """Debug route to expose production errors."""
    status = {"status": "ok", "version": "v6.0-DEBUG", "db": "unknown", "env": "unknown"}
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

@app.route('/reset_db_force')
def reset_db_force():
    """Nuclear option to fix schema mismatches on Render."""
    try:
        db.drop_all()
        db.create_all()
        seed_production_data()
        return "<h1>Database Reset Successful</h1><p>All tables dropped and recreated. New Schema applied. <a href='/'>Go Home</a></p>"
    except Exception as e:
        return f"Reset Failed: {e}"

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
    try:
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        
        # Unified Booking Query with Sorting
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
        
        # --- REVENUE CALCULATION ---
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        
        # 1. Monthly Revenue (Paid or Completed bookings in current month)
        monthly_revenue = db.session.query(func.sum(Booking.amount)).filter(
            Booking.created_at >= current_month_start,
            Booking.status.in_(['completed', 'paid', 'confirmed']) # Adjust based on business logic
        ).scalar() or 0
        
        # 2. Total Revenue (Lifetime)
        total_revenue = db.session.query(func.sum(Booking.amount)).filter(
            Booking.status.in_(['completed', 'paid', 'confirmed'])
        ).scalar() or 0
        
        # 3. Pending Count
        pending_count = Booking.query.filter_by(status='pending').count()
        
        # Check for SQLite (Ephemeral DB Risk)
        is_sqlite = app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('sqlite:')
        
        return render_template('admin.html', 
                            bookings=bookings, 
                            inquiries=inquiries, 
                            is_sqlite=is_sqlite,
                            monthly_revenue=int(monthly_revenue),
                            total_revenue=int(total_revenue),
                            pending_count=pending_count)
    except Exception as e:
        app.logger.error(f"Admin Dashboard Error: {e}")
        return f"<h1>Admin Dashboard Error</h1><pre>{str(e)}</pre>"

@app.route('/admin/medicines')
def admin_medicines():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    medicines = Medicine.query.all()
    return render_template('admin_medicines.html', medicines=medicines)

@app.route('/admin/medicines/add', methods=['POST'])
def admin_add_medicine():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        new_med = Medicine(
            name=request.form['name'],
            price=int(request.form['price']),
            original_price=int(request.form['original_price']) if request.form['original_price'] else None,
            category=request.form['category'],
            image_url=request.form['image_url'],
            description=request.form['description']
        )
        db.session.add(new_med)
        db.session.commit()
        flash('Medicine added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding medicine: {e}', 'danger')
        
    return redirect(url_for('admin_medicines'))

@app.route('/admin/medicines/delete/<int:id>', methods=['POST'])
def admin_delete_medicine(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
        
    med = Medicine.query.get_or_404(id)
    db.session.delete(med)
    db.session.commit()
    flash('Medicine deleted.', 'success')
    return redirect(url_for('admin_medicines'))

@app.route('/admin/booking/<int:booking_id>/status/<string:new_status>')
def admin_update_booking_status(booking_id, new_status):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    valid_statuses = ['pending', 'confirmed', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        flash('Invalid Status Update', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    booking = Booking.query.get_or_404(booking_id)
        
    flash(f"Booking #{booking.id} marked as {new_status.title()}", 'success')
    return redirect(url_for('admin_dashboard'))

# --- PHARMACY IMAGE MANAGER SECURE ROUTES ---

@app.route('/admin/manage-images')
@login_required
def manage_images():
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('home'))
        
    medicines = Medicine.query.order_by(Medicine.name).all()
    return render_template('manage_images.html', medicines=medicines)

@app.route('/admin/upload-image/<int:med_id>', methods=['POST'])
@login_required
def upload_medicine_image(med_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    medicine = Medicine.query.get_or_404(med_id)
    
    if 'image' not in request.files:
        flash('No image file selected', 'danger')
        return redirect(url_for('manage_images'))
        
    file = request.files['image']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('manage_images'))
        
    try:
        # Upload directly to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file, 
            folder="homecare/medicines/", 
            public_id=f"med_{medicine.id}",
            overwrite=True
        )
        # Save secure URL to DB
        medicine.image_url = upload_result.get('secure_url')
        db.session.commit()
        flash(f'Image uploaded successfully for {medicine.name}!', 'success')
    except Exception as e:
        app.logger.error(f"Cloudinary Upload Error: {e}")
        flash('Failed to upload image to Cloud. Please try again or check connection.', 'danger')
        
    return redirect(url_for('manage_images'))

@app.route('/admin/link-image/<int:med_id>', methods=['POST'])
@login_required
def link_medicine_image(med_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    medicine = Medicine.query.get_or_404(med_id)
    image_url = request.form.get('image_url')
    
    if image_url:
        image_url = image_url.strip()
        
        # 1. Check if it's a base64 encoded data string (which is huge and not a real URL)
        if image_url.startswith('data:'):
            flash('You copied a thumbnail instead of the real image link. Please click "Upload Photo" instead or click the image on Google first before copying its address.', 'warning')
            return redirect(url_for('manage_images'))
            
        # 2. Check column length limit (500 chars)
        if len(image_url) > 500:
            flash('The image link is too long to save directly. Please download the image and use the "Upload" button.', 'warning')
            return redirect(url_for('manage_images'))
            
        try:
            medicine.image_url = image_url
            db.session.commit()
            flash(f'Image link saved successfully for {medicine.name}!', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"DB Error saving image link: {e}")
            flash('Error saving the link to the database. Please try another image or upload it.', 'danger')
    else:
        flash('Please provide a valid image URL', 'danger')
        
    return redirect(url_for('manage_images'))

@app.route('/admin/bulk-link-images', methods=['POST'])
@login_required
def bulk_link_images():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    if not data or 'links' not in data:
        return jsonify({'error': 'No data provided'}), 400
        
    links = data['links']
    success_count = 0
    error_count = 0
    
    for item in links:
        try:
            med_id = item.get('med_id')
            url = item.get('image_url', '').strip()
            
            if not med_id or not url:
                error_count += 1
                continue
                
            if url.startswith('data:') or len(url) > 500:
                error_count += 1
                continue
                
            medicine = Medicine.query.get(med_id)
            if medicine:
                medicine.image_url = url
                success_count += 1
        except Exception as e:
            app.logger.error(f"Bulk Link Error for med {med_id}: {e}")
            error_count += 1
            
    try:
        db.session.commit()
        if success_count > 0:
            flash(f"Successfully saved {success_count} image link(s).", "success")
            if error_count > 0:
                flash(f"Note: {error_count} link(s) failed (e.g. invalid thumbnails or too long).", "warning")
        else:
            flash("No valid links were saved.", "danger")
        return jsonify({"success": True, "saved": success_count, "failed": error_count})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Bulk Link Commit Error: {e}")
        return jsonify({"error": "Database error"}), 500


# --- STARTUP DATA SEEDING (V6.0 PRODUCTION) ---
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
                # Single Tests (Updated with 37 User Provided Tests)
                single_tests = [
                    # Blood Sugar Tests
                    {"name": "Fasting Blood Sugar", "category": "Diabetes", "price": 50, "description": "Measures blood glucose after fasting.", "components": "Glucose (Fasting)", "significance": "Diabetes screening."},
                    {"name": "Post Prandial Blood Sugar (2 Hours)", "category": "Diabetes", "price": 50, "description": "Measures blood glucose 2 hours after a meal.", "components": "Glucose (PP)", "significance": "Diabetes management."},
                    {"name": "Random Blood Sugar", "category": "Diabetes", "price": 50, "description": "Measures blood glucose at any time.", "components": "Glucose (Random)", "significance": "Quick diabetes check."},
                    {"name": "HbA1c", "category": "Diabetes", "price": 450, "description": "Average blood sugar 3 months.", "components": "Glycosylated Haemoglobin", "significance": "Long-term diabetes control."},

                    # Liver Function Related
                    {"name": "Bilirubin (Total / Direct / Indirect)", "category": "Liver", "price": 170, "description": "Checks for jaundice and liver issues.", "components": "Total, Direct, Indirect Bilirubin", "significance": "Liver health."},
                    {"name": "SGOT (AST)", "category": "Liver", "price": 120, "description": "Liver enzyme test.", "components": "Aspartate Aminotransferase", "significance": "Liver damage."},
                    {"name": "SGPT (ALT)", "category": "Liver", "price": 120, "description": "Liver enzyme test.", "components": "Alanine Aminotransferase", "significance": "Liver damage."},
                    {"name": "Liver Function Test (LFT)", "category": "Liver", "price": 650, "description": "Complete liver health check.", "components": "Bilirubin, SGOT, SGPT, ALP, Protein, Albumin", "significance": "Comprehensive liver assessment."},
                    {"name": "Total Protein Test", "category": "Liver", "price": 170, "description": "Measures proteins in blood.", "components": "Total Protein, Albumin, Globulin", "significance": "Nutritional status."},

                    # Kidney Function Related
                    {"name": "Urea Test", "category": "Kidney", "price": 140, "description": "Measures waste product in blood.", "components": "Blood Urea Nitrogen", "significance": "Kidney function."},
                    {"name": "Creatinine Test", "category": "Kidney", "price": 110, "description": "Key marker for kidney health.", "components": "Serum Creatinine", "significance": "Kidney function."},
                    {"name": "Kidney Function Test (KFT)", "category": "Kidney", "price": 750, "description": "Complete kidney health check.", "components": "Urea, Creatinine, Uric Acid, Electrolytes", "significance": "Kidney assessment."},
                    {"name": "PCR (Protein Creatinine Ratio)", "category": "Kidney", "price": 500, "description": "Urine test for protein.", "components": "Protein, Creatinine Ratio", "significance": "Kidney damage."},

                    # Urine Tests
                    {"name": "Urine Routine & Microscopy", "category": "Urine", "price": 100, "description": "Basic urine examination.", "components": "Physical, Chemical, Microscopic analysis", "significance": "UTI, kidney disease."},
                    {"name": "Urine Culture", "category": "Urine", "price": 450, "description": "Detects bacteria in urine.", "components": "Bacterial Culture & Sensitivity", "significance": "Urinary Tract Infection."},

                    # Complete Blood & Basic Tests
                    {"name": "Complete Blood Count (CBC)", "category": "Routine", "price": 200, "description": "Overall health check.", "components": "Hb, TLC, DLC, Platelets, RBC indices", "significance": "Anemia, infection."},
                    {"name": "Haemoglobin", "category": "Routine", "price": 70, "description": "Measures oxygen-carrying protein.", "components": "Hb", "significance": "Anemia."},
                    {"name": "Platelet Count", "category": "Routine", "price": 100, "description": "Essential for blood clotting.", "components": "Platelet Count", "significance": "Dengue, bleeding disorders."},
                    {"name": "ESR", "category": "Routine", "price": 70, "description": "Inflammation marker.", "components": "ESR", "significance": "Infection, inflammation."},
                    {"name": "Blood Group", "category": "Routine", "price": 80, "description": "Identifies blood type.", "components": "ABO & Rh Typing", "significance": "Emergency, pregnancy."},

                    # Thyroid Tests
                    {"name": "Thyroid Function Test (TFT)", "category": "Thyroid", "price": 490, "description": "Complete thyroid check.", "components": "Total T3, Total T4, TSH", "significance": "Thyroid disorders."},
                    {"name": "TSH", "category": "Thyroid", "price": 220, "description": "Thyroid Stimulating Hormone.", "components": "TSH", "significance": "Thyroid screening."},

                    # Lipid & Cholesterol
                    {"name": "Lipid Profile", "category": "Heart", "price": 400, "description": "Cholesterol and fat levels.", "components": "Cholesterol, Triglycerides, HDL, LDL, VLDL", "significance": "Heart disease risk."},
                    {"name": "Total Cholesterol", "category": "Heart", "price": 110, "description": "Total measuring of cholesterol.", "components": "Total Cholesterol", "significance": "Heart health."},

                    # Electrolytes
                    {"name": "Sodium Test", "category": "Electrolytes", "price": 170, "description": "Electrolyte balance.", "components": "Serum Sodium", "significance": "Dehydration. "},
                    {"name": "Potassium Test", "category": "Electrolytes", "price": 170, "description": "Electrolyte balance.", "components": "Serum Potassium", "significance": "Heart function."},

                    # Infection & Inflammation
                    {"name": "CRP (C-Reactive Protein)", "category": "Infection", "price": 420, "description": "Inflammation marker.", "components": "CRP Quantitative", "significance": "Infection."},
                    {"name": "Widal", "category": "Fever", "price": 130, "description": "Typhoid screening.", "components": "Salmonella Antibodies", "significance": "Typhoid fever."},
                    {"name": "Typhi Dot (IgM / IgG)", "category": "Fever", "price": 800, "description": "Rapid typhoid test.", "components": "IgM & IgG Antibodies", "significance": "Typhoid fever."},

                    # Male Health
                    {"name": "PSA Test", "category": "Male Health", "price": 800, "description": "Prostate screening.", "components": "Prostate Specific Antigen", "significance": "Prostate health."},

                    # Pancreas Tests
                    {"name": "Amylase Test", "category": "Pancreas", "price": 390, "description": "Pancreatic enzyme.", "components": "Serum Amylase", "significance": "Pancreatitis."},
                    {"name": "Lipase Test", "category": "Pancreas", "price": 350, "description": "Pancreatic enzyme.", "components": "Serum Lipase", "significance": "Pancreatitis."},

                    # Vitamins & Minerals
                    {"name": "Vitamin B12", "category": "Vitamins", "price": 1200, "description": "Nerve health vitamin.", "components": "Cyanocobalamin", "significance": "Nerve health."},
                    {"name": "Vitamin D", "category": "Vitamins", "price": 1200, "description": "Bone health vitamin.", "components": "25-OH Vitamin D", "significance": "Bone health."},
                    {"name": "Iron", "category": "Vitamins", "price": 500, "description": "Iron levels.", "components": "Serum Iron", "significance": "Anemia."},
                    {"name": "Calcium", "category": "Vitamins", "price": 130, "description": "Bone mineral.", "components": "Serum Calcium", "significance": "Bone health."},
                    {"name": "Uric Acid Test", "category": "Kidney", "price": 110, "description": "Joint health / Kidney.", "components": "Serum Uric Acid", "significance": "Gout, kidney stones."}
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
                app.logger.info("Lab Tests already populated.")

            # --- Medicine Seeding ---
            if not Medicine.query.first():
                app.logger.info("Seeding Medicines...")
                
                # Simplified Seeding (User Request: Remove Image Logic)
                medicines_data = [
                    # Energy
                    {"name": "Glucon-D Regular 125g", "price": 40, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
                    {"name": "Glucon-D Regular 250g", "price": 79, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
                    {"name": "Glucon-D Regular 500g", "price": 140, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
                    {"name": "Glucon-D Regular 1kg", "price": 255, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
                    {"name": "Glucon-D Orange 125g", "price": 56, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
                    {"name": "Glucon-D Orange 200g", "price": 89, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
                    {"name": "Glucon-D Orange 450g", "price": 219, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
                    {"name": "Glucon-D Orange 1kg", "price": 415, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
                    {"name": "Glucon-D Nimbu Pani 125g", "price": 56, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
                    {"name": "Glucon-D Nimbu Pani 450g", "price": 219, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
                    {"name": "Glucon-D Nimbu Pani 1kg", "price": 415, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
                    # Honey
                    {"name": "Dabur Honey 100g", "price": 70, "cat": "Honey", "type": "Healthy Food", "brand": "Dabur"},
                    {"name": "Dabur Honey 200g", "price": 125, "cat": "Honey", "type": "Healthy Food", "brand": "Dabur"},
                    {"name": "Dabur Honey 600g", "price": 250, "cat": "Honey", "type": "Healthy Food", "brand": "Dabur"},
                    # Digestion
                    {"name": "Sat Isabgol 50g", "price": 90, "cat": "Digestion", "type": "OTC", "brand": "Dabur"},
                    {"name": "Sat Isabgol 100g", "price": 175, "cat": "Digestion", "type": "OTC", "brand": "Dabur"},
                    {"name": "Sat Isabgol 200g", "price": 345, "cat": "Digestion", "type": "OTC", "brand": "Dabur"},
                    # Baby
                    {"name": "Little Baby Wipes (30 Wipes)", "price": 49, "cat": "Baby", "type": "Personal Care", "brand": "Little"},
                    {"name": "Little Baby Wipes (72 Wipes)", "price": 99, "cat": "Baby", "type": "Personal Care", "brand": "Little"},
                    {"name": "Lactogen Pro 1", "price": 450, "cat": "Nutrition", "type": "Baby Food", "brand": "Nestle"},
                    {"name": "Lactogen Pro 2", "price": 450, "cat": "Nutrition", "type": "Baby Food", "brand": "Nestle"},
                    {"name": "Lactogen Pro 3", "price": 435, "cat": "Nutrition", "type": "Baby Food", "brand": "Nestle"},
                    {"name": "Lactogen Pro 4", "price": 435, "cat": "Nutrition", "type": "Baby Food", "brand": "Nestle"},
                    # Immunity
                    {"name": "Zandu Chyawanprash 450g", "price": 215, "cat": "Immunity", "type": "Ayurveda", "brand": "Zandu"},
                    {"name": "Zandu Chyawanprash 900g", "price": 350, "cat": "Immunity", "type": "Ayurveda", "brand": "Zandu"},
                    {"name": "Dabur Chyawanprash 250g", "price": 99, "cat": "Immunity", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Dabur Chyawanprash 500g", "price": 240, "cat": "Immunity", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Dabur Chyawanprash 1kg", "price": 430, "cat": "Immunity", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Dabur Chyawanprash Sugar Free 500g", "price": 255, "cat": "Immunity", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Dabur Chyawanprash Sugar Free 900g", "price": 440, "cat": "Immunity", "type": "Ayurveda", "brand": "Dabur"},
                    # Syrups
                    {"name": "Dabur Dashmularishta 450ml", "price": 215, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Dabur Dashmularishta 680ml", "price": 268, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Dabur Ashokarishta 450ml", "price": 155, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Dabur Ashokarishta 680ml", "price": 200, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Dabur Punarnavarishta 450ml", "price": 210, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Dabur Ashwagandharishta 680ml", "price": 300, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Dabur Pathyadiarishta 450ml", "price": 192, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Dabur Lohasava 450ml", "price": 195, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Dabur Lohasava 680ml", "price": 245, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
                    {"name": "Baidyanath Dashmularishta 680ml", "price": 275, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Baidyanath"},
                    {"name": "Baidyanath Abhayarishta 680ml", "price": 255, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Baidyanath"},
                    {"name": "Baidyanath Ashokarishta 680ml", "price": 200, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Baidyanath"},
                    {"name": "Baidyanath Lohasav 450ml", "price": 198, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Baidyanath"},
                    {"name": "Baidyanath Arjunarishta 680ml", "price": 281, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Baidyanath"},
                    # Liver & Condition Specific
                    {"name": "Liv 52 Tablet", "price": 215, "cat": "Liver", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Liv 52 DS Tablet", "price": 300, "cat": "Liver", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Liv 52 Syrup 100ml", "price": 140, "cat": "Liver", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Liv 52 Syrup 200ml", "price": 250, "cat": "Liver", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Liv 52 DS Syrup 100ml", "price": 220, "cat": "Liver", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Liv 52 DS Syrup 200ml", "price": 351, "cat": "Liver", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Septiline Tablet", "price": 275, "cat": "Tablet", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Septiline Syrup 200ml", "price": 200, "cat": "Syrup", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Pilex Tablet", "price": 250, "cat": "Tablet", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Pilex Forte Ointment 30g", "price": 160, "cat": "Ointment", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Cystone Tablet", "price": 260, "cat": "Tablet", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Cystone Syrup 200ml", "price": 225, "cat": "Syrup", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Evecare Syrup 200ml", "price": 190, "cat": "Syrup", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Gasex Tablet", "price": 200, "cat": "Tablet", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Neeri Syrup 100ml", "price": 164, "cat": "Syrup", "type": "Prescription", "brand": "Himalaya"},
                    {"name": "Neeri Syrup 200ml", "price": 313, "cat": "Syrup", "type": "Prescription", "brand": "Himalaya"},
                    # Ointments & Hygiene
                    {"name": "Anovate Ointment 20g", "price": 145, "cat": "Ointment", "type": "OTC", "brand": "Generic"},
                    {"name": "Abzorb Powder", "price": 175, "cat": "Hygiene", "type": "Personal Care", "brand": "Generic"},
                    {"name": "Candid Powder 60g", "price": 104, "cat": "Hygiene", "type": "Personal Care", "brand": "Glenmark"},
                    {"name": "Candid Powder 120g", "price": 174, "cat": "Hygiene", "type": "Personal Care", "brand": "Glenmark"},
                    {"name": "Clocip Powder 75g", "price": 93, "cat": "Hygiene", "type": "Personal Care", "brand": "Cipla"},
                    {"name": "Clocip Powder 120g", "price": 168, "cat": "Hygiene", "type": "Personal Care", "brand": "Cipla"},
                    {"name": "Dettol Liquid 60ml", "price": 41, "cat": "Hygiene", "type": "Personal Care", "brand": "Dettol"},
                    {"name": "Dettol Liquid 125ml", "price": 83, "cat": "Hygiene", "type": "Personal Care", "brand": "Dettol"},
                    {"name": "Dettol Liquid 250ml", "price": 159, "cat": "Hygiene", "type": "Personal Care", "brand": "Dettol"},
                    {"name": "Dettol Liquid 550ml", "price": 267, "cat": "Hygiene", "type": "Personal Care", "brand": "Dettol"},
                    {"name": "Dettol Liquid 1L", "price": 485, "cat": "Hygiene", "type": "Personal Care", "brand": "Dettol"},
                    {"name": "Maxirich (10 Tablets)", "price": 129, "cat": "Supplement", "type": "Supplements", "brand": "Cipla"}
                ]

                # Clean Up: Simple Seeding without Image Logic
                for m in medicines_data:
                    med = Medicine(
                        name=m['name'],
                        category=m['type'], 
                        price=m['price'],
                        original_price=int(m['price'] * 1.15),
                        description=f"Genuine {m['name']} for {m['cat']} care.",
                        image_url="https://i.imgur.com/7X5Xy9C.png", # Default Placeholder for all
                        is_active=True
                    )
                    db.session.add(med)
                
                db.session.commit()
                app.logger.info("Medicines Seeded Successfully!")
            else:
                 app.logger.info("Medicines already populated.")
    except Exception as e:
        app.logger.error(f"Seeding Failed: {e}")

@app.route('/init-data')
def init_data():
    """Manually trigger seeding without dropping tables."""
    try:
        seed_production_data()
        return "<h1>Data Initialized!</h1><p>Medicines and Lab Tests checked/added.</p><a href='/pharmacy'>Go to Pharmacy</a>"
    except Exception as e:
        return f"Error: {e}"

# Run Seeding on Module Import (Gunicorn loads this)
# DISABLED: Preventing Timeout on Render. 
# Use /init-data to seed manually.
# try:
#     seed_production_data()
# except Exception as e:
#     app.logger.error(f"CRITICAL: Startup Seeding Failed: {e}")
#     print(f"CRITICAL: Startup Seeding Failed: {e}") # Ensure it hits stdout

# --- DEPLOYMENT SUCCESS CHECK ---
@app.route('/debug-mail')
@app.route('/test-email')
def cleanup_redirect():
    return f"<h1>✅ System Active</h1><p>Debug tools have been removed for security.</p><p><a href='/'>Go to Homepage</a></p>"

@app.route('/debug-db')
def debug_db():
    """Diagnose DB Connection Errors on Render (Restored)."""
    import os
    try:
        # 1. Check Config
        uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'MISSING')
        masked_uri = uri.split('@')[1] if '@' in uri else uri[:10] + "..."
        
        info = [f"<h1>Database Diagnostic (V6.1-SAFE)</h1>"]
        info.append(f"<p><strong>URI Configured:</strong> {masked_uri}</p>")
        
        # 2. Test Connection
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            info.append(f"<p style='color:green'>✅ Connection Successful (SELECT 1 returns {result.fetchone()})</p>")
            
        # 3. Check Tables
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        info.append(f"<p><strong>Tables Found:</strong> {tables}</p>")
        
        # 4. Check Tables Existence logic
        if 'user' in tables or 'User' in tables:
             count = User.query.count()
             info.append(f"<p style='color:green'>✅ User Table Accessible (Count: {count})</p>")
        else:
             info.append(f"<p style='color:red'>❌ User Table MISSING (Should auto-create)</p>")
             
        return "".join(info)
        
    except Exception as e:
        return f"<h1>❌ Database Error (V6.1)</h1><pre>{str(e)}</pre>"



# --- SELF-HEALING DATABASE ---
# Critical for Render ephemeral storage: Ensure DB exists on first request
db_initialized = False

@app.before_request
def initialize_database():
    global db_initialized
    if not db_initialized:
        try:
             # Robust Check for Empty DB (Works on Postgres & SQLite)
             try:
                 db.session.query(User).first()
             except Exception:
                 app.logger.info("Database Not Found/Empty. Creating Tables...")
                 db.create_all()
                 # seed_production_data() # DISABLED: Prevent Startup Timeout
                 app.logger.info("Database Created. Visit /init-data to seed.")
            
             db_initialized = True
        except Exception as e:
             app.logger.error(f"Critical DB Init Error: {e}")
             # Do NOT swallow the error, let it print so we can debug if it persists
             print(f"CRITICAL DB ERROR: {e}")
        pass

@app.route('/update-schema')
def update_schema_v2():
    try:
        from sqlalchemy import text
        with db.engine.connect() as connection:
             # 1. Create BookingItem Table (if not exists)
             # We rely on db.create_all() for new tables, but explicit SQL is safer for migrations
             connection.execute(text('''
                CREATE TABLE IF NOT EXISTS booking_item (
                    id SERIAL PRIMARY KEY,
                    booking_id INTEGER NOT NULL REFERENCES booking(id),
                    item_type VARCHAR(50) NOT NULL,
                    item_name VARCHAR(200) NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    price INTEGER NOT NULL
                );
             '''))
             
             # 2. Add updated_at column to Booking (if not exists)
             try:
                 connection.execute(text('ALTER TABLE booking ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;'))
             except Exception:
                 pass # Column likely exists
                 
             connection.commit()
             
        app.logger.info("Schema Update: Created BookingItem & Added updated_at.")
        return "<h1>Schema Updated!</h1><p>Booking System Upgrade Applied.</p><a href='/admin/login'>Go to Admin</a>"
    except Exception as e:
        app.logger.error(f"Schema Update Failed: {e}")
        return f"<h1>Update Failed</h1><p>{e}</p>"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
