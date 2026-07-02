import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from datetime import datetime
import bcrypt
import uuid
from bson import ObjectId

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='../public', static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/fundi')

# Initialize MongoDB
from models import mongo, UserMixin
mongo.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models helpers
from models import (
    create_user, find_user_by_phone, find_user_by_id,
    create_worker, find_worker_by_user_id, find_worker_by_id,
    get_verified_workers, update_worker_verification,
    update_worker_rating, increment_worker_jobs,
    create_job_request, find_job_by_id, find_jobs_by_customer,
    find_open_jobs_by_trade, update_job_status, delete_job,
    create_quote, find_quote_by_id, update_quote_status,
    create_booking, find_booking_by_id, find_booking_by_quote,
    update_booking_payment, create_review, find_reviews_by_worker,
    find_review_by_booking, get_all_images, get_stats
)

# User class for Flask-Login with MongoDB
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.phone = user_data['phone']
        self.name = user_data['name']
        self.role = user_data['role']
#Check if user is admin
    def is_admin(self):
        return self.role == 'admin'
#Create admin user at startup
with app.app_context():
    admin = mongo.db.users.find_one({"phone": "254700000000"})
    if not admin:
        create_user("254700000000", "Admin", "admin123", "admin")
        print("✅ Admin user created: phone=254700000000, password=admin123")

# ---------- PUBLIC ROUTES ----------

@app.route('/')
def index():
    """Home page - show verified workers"""
    workers = get_verified_workers()
    # Enrich workers with user data
    for worker in workers:
        user = mongo.db.users.find_one({"_id": worker['user_id']})
        worker['user'] = user
    return render_template('index.html', workers=workers)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if not all([name, phone, password, role]):
            flash('All fields are required')
            return redirect(url_for('register'))
        
        if mongo.db.users.find_one({"phone": phone}):
            flash('Phone number already registered')
            return redirect(url_for('register'))
        
        user_id = create_user(phone, name, password, role)
        
        flash('Registration successful! Please log in.')
        if role == 'worker':
            return redirect(url_for('complete_worker_profile', user_id=str(user_id.inserted_id)))
        else:
            user_data = mongo.db.users.find_one({"_id": user_id.inserted_id})
            login_user(User(user_data))
            flash('Welcome to Fundi!')
            return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/complete_worker_profile/<user_id>', methods=['GET', 'POST'])
def complete_worker_profile(user_id):
    """Complete worker profile(tradeu, location)"""
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        flash('User not found')
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        trade = request.form.get('trade')
        location_area = request.form.get('location_area')
        
        if not trade or not location_area:
            flash('All fields are required')
            return redirect(request.url)
        
        create_worker(user_id, trade, location_area, False)
        flash('Worker profile created! Please verify your identity.')
        return redirect(url_for('verification', user_id=user_id))
    
    return render_template('worker_profile_complete.html', user=user)

@app.route('/verification/<user_id>', methods=['GET', 'POST'])
def verification(user_id):
    """Verify worker identity"""
    if current_user.id != user_id:
        flash('Unauthorized')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        id_file = request.files.get('id_image')
        selfie_file = request.files.get('selfie')
        
        if not id_file or not selfie_file:
            flash('Please upload both ID photo and selfie')
            return redirect(request.url)
        
        # Save files locally for verification
        os.makedirs('uploads', exist_ok=True)
        id_path = os.path.join('uploads', f'id_{user_id}_{uuid.uuid4().hex[:8]}.jpg')
        selfie_path = os.path.join('uploads', f'selfie_{user_id}_{uuid.uuid4().hex[:8]}.jpg')
        id_file.save(id_path)
        selfie_file.save(selfie_path)
        #Run verification (placeholder - will be implemented in Week 10)
        # For now, always pass
        result = {'verified': True}
        #Update worker 
        worker = find_worker_by_user_id(user_id)
        if worker:
            update_worker_verification(worker['_id'], result['verified'])
        
        # Clean up local files
        try:
            os.remove(id_path)
            os.remove(selfie_path)
        except:
            pass
        
        if result['verified']:
            flash('✅ Verification passed! You are now a verified Fundi worker.')
        else:
            flash('❌ Verification failed. Please try again with clearer images.')
        
        if current_user.role == 'worker':
            return redirect(url_for('worker_dashboard'))
        else:
            return redirect(url_for('index'))
    
    return render_template('verification.html', user_id=user_id)
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        user_data = mongo.db.users.find_one({"phone": phone})
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
            login_user(User(user_data))
            flash(f'Welcome back, {user_data["name"]}!')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        flash('Invalid phone number or password')
    
    return render_template('login.html')
@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))
@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    if current_user.role == 'worker':
        return redirect(url_for('worker_dashboard'))
    elif current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('customer_dashboard'))
# ---------- PLACEHOLDER DASHBOARD ROUTES ----------

@app.route('/worker/dashboard')
@login_required
def worker_dashboard():
    """Worker dashboard - placeholder"""
    if current_user.role != 'worker':
        flash('Access denied')
        return redirect(url_for('index'))
    
    worker = find_worker_by_user_id(current_user.id)
    if not worker:
        flash('Complete your worker profile first')
        return redirect(url_for('complete_worker_profile', user_id=current_user.id))
    
    return render_template('worker_dashboard.html', worker=worker)
@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    """Customer dashboard - placeholder"""
    if current_user.role != 'customer':
        flash('Access denied')
        return redirect(url_for('index'))
    
    return render_template('customer_dashboard.html')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard - placeholder"""
    if not current_user.is_admin():
        flash('Access denied')
        return redirect(url_for('index'))
    
    return render_template('admin_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
    