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
import hmac
import hashlib
from sqlalchemy import func, inspect # Critical for db_recovery


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
    amount = db.Column(db.Integer, default=499) # Store agreed price
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
def send_async_email(app, subject, body, recipients):
    with app.app_context():
        try:
            # Create Message using Flask-Mail
            msg = Message(subject, recipients=recipients)
            msg.body = body
            # HTML body support if needed in future
            # msg.html = body 
            
            mail.send(msg)
            app.logger.info(f"Background Thread: Email sent successfully to {recipients}")
            return True
        except Exception as e:
            app.logger.error(f"BACKGROUND EMAIL ERROR: {e}")
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

        # Create booking
        booking = Booking(
            user_id=current_user.id if current_user.is_authenticated else None,
            patient_name=form.patient_name.data,
            age=form.age.data,
            mobile=form.mobile.data,
            email=form.email.data, # Save customer email
            address=form.address.data,
            area=form.area.data,
            landmark=form.landmark.data,
            service_type=service_type,
            test_name=test_name,
            prescription_path=prescription_path,
            preferred_date=form.preferred_date.data,
            preferred_time=form.preferred_time.data,
            amount=booking_price, # CRITICAL: Save calculated price
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

@app.route('/test-email')
def test_email():
    """Fail-Safe Diagnostic for Render (Prevents Timeout/Blank Page)."""
    import smtplib, socket, ssl
    
    # 2-Second Timeout: Forces page to load even if network is blocked
    TIMEOUT = 2 
    
    username = app.config.get('MAIL_USERNAME', 'MISSING')
    password_status = 'SET' if app.config.get('MAIL_PASSWORD') else 'MISSING'
    
    report = [
        "<html><head><title>Email Diagnostic</title></head><body style='font-family:sans-serif; padding:2rem;'>",
        "<h1>🚀 Email Diagnostic Report</h1>",
        f"<p><strong>Config:</strong> User={username}, Password={password_status}</p>",
        "<hr>"
    ]

    # Test 1: DNS Resolution (Is Google reachable?)
    try:
        ip = socket.gethostbyname('smtp.gmail.com')
        report.append(f"<p>✅ <strong>DNS Resolved:</strong> {ip}</p>")
    except Exception as e:
        report.append(f"<p>❌ <strong>DNS Failed:</strong> {str(e)}</p>")

    # Test 2: Port 587 (TLS)
    try:
        report.append(f"<p>Attempting Port 587 (Standard TLS)...</p>")
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=TIMEOUT) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(username, app.config.get('MAIL_PASSWORD'))
            s.sendmail(username, username, f"Subject: Test 587\n\nSuccess")
        report.append("<h3 style='color:green'>✅ Port 587 SUCCESS! (Email Sent)</h3>")
    except Exception as e:
        err = str(e)
        if "Authentication" in err or "(535" in err:
             report.append(f"<h3 style='color:red'>❌ Authentication Failed (Check App Password)</h3>")
        else:
             report.append(f"<p style='color:orange'>⚠️ Port 587 Failed: {err}</p>")

    # Test 3: Port 465 (SSL)
    try:
        report.append(f"<p>Attempting Port 465 (Secure SSL)...</p>")
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=TIMEOUT) as s:
            s.login(username, app.config.get('MAIL_PASSWORD'))
            s.sendmail(username, username, f"Subject: Test 465\n\nSuccess")
        report.append("<h3 style='color:green'>✅ Port 465 SUCCESS! (Email Sent)</h3>")
    except Exception as e:
        err = str(e)
        if "Authentication" in err or "(535" in err:
             report.append(f"<h3 style='color:red'>❌ Authentication Failed (Check App Password)</h3>")
        else:
             report.append(f"<p style='color:orange'>⚠️ Port 465 Failed: {err}</p>")

    report.append("</body></html>")
    return "".join(report)

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
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template('admin.html', bookings=bookings, inquiries=inquiries)

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
                
                # Category Images
                # High-Quality Official Brand Logos (Real Images via Clearbit)
                images = {
                    "Glucon-D": "https://logo.clearbit.com/glucond.com", 
                    "Dabur": "https://logo.clearbit.com/dabur.com",
                    "Himalaya": "https://logo.clearbit.com/himalayawellness.in",
                    "Dettol": "https://logo.clearbit.com/reckitt.com", 
                    "Zandu": "https://logo.clearbit.com/zanducare.com",
                    "Little": "https://logo.clearbit.com/piramal.com", 
                    "Nestle": "https://logo.clearbit.com/nestle.in", 
                }

                # Fallback Category Icons
                cat_images = {
                    "Energy": "https://i.imgur.com/8J5s2e6.png",
                    "Honey": "https://logo.clearbit.com/dabur.com",
                    "Digestion": "https://i.imgur.com/3q5Xy9C.png",
                    "Baby": "https://logo.clearbit.com/piramal.com",
                    "Immunity": "https://logo.clearbit.com/zanducare.com",
                    "Syrup": "https://i.imgur.com/4q5Xy9C.png",
                    "Ayurveda": "https://logo.clearbit.com/dabur.com",
                    "Nutrition": "https://logo.clearbit.com/nestle.in",
                    "Liver": "https://logo.clearbit.com/himalayawellness.in",
                    "Tablet": "https://logo.clearbit.com/himalayawellness.in",
                    "Ointment": "https://i.imgur.com/0X5Xy9C.png",
                    "Hygiene": "https://logo.clearbit.com/reckitt.com",
                    "Supplement": "https://i.imgur.com/bX5Xy9C.png"
                }

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

                # Bulk Add
                for m in medicines_data:
                    # 1. Try Specific Manual Image (User Uploaded)
                    img = None
                    if m['name'] == "Glucon-D Regular 125g":
                        img = "/static/images/medicines/glucond_reg125gm.jpg"
                    elif m['name'] == "Dabur Honey 100g":
                        img = "/static/images/medicines/honey100gm.jpg"

                    # 2. Try Specific Brand Logo
                    if not img:
                        img = images.get(m.get('brand'), None)
                    
                    # 3. Key Mapping Overrides
                    if not img:
                        if "Baidyanath" in m['name']: img = "https://logo.clearbit.com/baidyanath.co.in"
                        elif "Cipla" in m.get('brand', ''): img = "https://logo.clearbit.com/cipla.com"
                        elif "Glenmark" in m.get('brand', ''): img = "https://logo.clearbit.com/glenmarkpharma.com"
                        elif "Glucon-D" in m['brand']: img = "https://logo.clearbit.com/glucond.com"
                    
                    # 4. Fallback Category Icon
                    if not img:
                        img = cat_images.get(m['cat'], "https://i.imgur.com/7X5Xy9C.png")
                    
                    med = Medicine(
                        name=m['name'],
                        category=m['type'], 
                        price=m['price'],
                        original_price=int(m['price'] * 1.15),
                        description=f"Genuine {m['name']} for {m['cat']} care.",
                        image_url=img,
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

# --- EMAIL DIAGNOSTIC TOOL (V2) ---
# DISABLED: Causing Startup Crash on Render.
# @app.route('/test-email')
# def test_email_route():
#     import smtplib
#     import socket
#     import ssl
#     
#     user = app.config.get('MAIL_USERNAME')
#     pwd = app.config.get('MAIL_PASSWORD')
#     TIMEOUT = 5
#
#     results = []
#     results.append("<h1>🚀 Email Diagnostic Report v2</h1>")
#     results.append(f"Config: User={user}, Password={'SET' if pwd else 'MISSING'}")
#     
#     # 1. DNS Resolution
#     try:
#         ip = socket.gethostbyname('smtp.gmail.com')
#         results.append(f"✅ DNS Resolved: {ip}")
#     except Exception as e:
#         results.append(f"❌ DNS Failed: {e}")
#         return "<br>".join(results)
#
#     # 2. Try Port 587 (TLS)
#     results.append("<br>Attempting Port 587 (Standard TLS)...")
#     try:
#         with smtplib.SMTP('smtp.gmail.com', 587, timeout=TIMEOUT) as s:
#             s.starttls()
#             s.login(user, pwd)
#             results.append("✅ Port 587 Success! (Authentication OK)")
#     except Exception as e:
#         err = str(e)
#         if "Network is unreachable" in err:
#              results.append(f"⚠️ Port 587 BLOCKED by Firewall (Network Unreachable)")
#         else:
#              results.append(f"⚠️ Port 587 Failed: {err}")
#
#     # 3. Try Port 465 (SSL)
#     results.append("<br>Attempting Port 465 (Secure SSL)...")
#     try:
#         context = ssl.create_default_context()
#         with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=TIMEOUT) as s:
#             s.login(user, pwd)
#             results.append("✅ Port 465 Success! (Authentication OK)")
#     except Exception as e:
#         err = str(e)
#         if "Network is unreachable" in err:
#              results.append(f"⚠️ Port 465 BLOCKED by Firewall (Network Unreachable)")
#         else:
#              results.append(f"⚠️ Port 465 Failed: {err}")
#
#     # 4. Try Port 2525 (Alternative TLS)
#     results.append("<br>Attempting Port 2525 (Alternative TLS)...")
#     try:
#         with smtplib.SMTP('smtp.gmail.com', 2525, timeout=TIMEOUT) as s:
#             s.starttls()
#             s.login(user, pwd)
#             results.append("✅ Port 2525 Success! (Use THIS Port!)")
#     except Exception as e:
#         results.append(f"⚠️ Port 2525 Failed: {e}")
#
#     return "<br>".join(results)


# --- SELF-HEALING DATABASE ---
# Critical for Render ephemeral storage: Ensure DB exists on first request
db_initialized = False

@app.before_request
def initialize_database():
    global db_initialized
    if not db_initialized:
        try:
            # Check if tables exist by inspecting the engine
            inspector = inspect(db.engine)
            if not inspector.has_table("lab_test"):
                app.logger.info("First Request: Database empty. Seeding data...")
                db.create_all()
                seed_production_data()
                
                # CRITICAL: Run External Medicine Seeder (Overwrites default medicines with correct local images)
                try:
                    from seed_medicines import seed_medicines
                    seed_medicines()
                    app.logger.info("External Medicine Seeder: Success")
                except Exception as e:
                    app.logger.error(f"External Medicine Seeder Failed: {e}")

                app.logger.info("Database Seeding Completed.")
            db_initialized = True
        except Exception as e:
            app.logger.error(f"Database Initialization Failed: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
