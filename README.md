# Jams Homecare - Full-Stack Healthcare Platform

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue.svg)
![Cloudinary](https://img.shields.io/badge/Cloudinary-Media%20API-orange.svg)
![Razorpay](https://img.shields.io/badge/Razorpay-Payment%20Gateway-lightgrey.svg)

**Jams Homecare** is a production-ready, full-stack web application designed to bring clinical healthcare services directly to patients' homes. Built with Python and Flask, the platform serves as a modern e-commerce and booking engine for nursing services, home lab sample collections, and pharmacy deliveries.

## 🚀 Key Features

* **Advanced Admin Dashboard:** Secure, role-based access control (RBAC) panel allowing clinical staff to manage inventory, track active bookings, and dynamically update lab test pricing.
* **E-Commerce Pharmacy:** fully-functional shopping cart system with state-management for adding/removing medicines and calculating totals.
* **Bulk Media Management Engine:** Integrated directly with the **Cloudinary API**. Allows admins to perform asynchronous bulk uploads of product images and prescriptions directly to cloud storage, bypassing slow server processing.
* **Secure Checkout Flow:** Integrated with the **Razorpay API** to process secure online payments, handling checkout flows, order verification, and digital receipt generation.
* **Intelligent Database Auto-Seeding:** Automated Python migration scripts that seed the production PostgreSQL database with hundreds of initial medicinal products and lab tests upon zero-downtime deployment.
* **Mobile-First Responsive UI:** Designed using modern vanilla CSS Grid and Flexbox (without bloated external frameworks) to maintain lightning-fast performance across all mobile devices.

## 🛠️ Technology Stack

* **Backend:** Python, Flask, Jinja2
* **Database & ORM:** PostgreSQL (Neon), SQLite (Local Dev), SQLAlchemy, Flask-Migrate (Alembic)
* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **Authentication:** Flask-Login (Session management), Werkzeug (Password Hashing), CSRF Protection (Flask-WTF)
* **Cloud Infrastructure:** Render (PaaS Deployment), Gunicorn (WSGI HTTP Server)
* **3rd Party APIs:** Razorpay (Payments), Cloudinary (Image Hosting), SendGrid (Email Notifications)

## 💻 Local Installation

To run this project locally for testing or contribution:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Cold-artist/jams-homecare.git
   cd jams-homecare
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the local database:**
   ```bash
   flask db upgrade
   python seed_lab_tests.py
   ```

5. **Run the application:**
   ```bash
   python wsgi.py
   ```
   *The application will be available at `http://127.0.0.1:8000`*

## 🔒 Security
This repository strictly utilizes environment variables (`os.environ`) for all sensitive API keys and database URIs. No actual production passwords or cryptographic secret keys are stored in the source code.

---
*Built with professional clinical supervision protocols in mind.*
