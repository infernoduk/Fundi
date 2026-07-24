import os
import sys

# Add project root to sys.path to allow imports from models, etc.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from datetime import datetime
import bcrypt
import uuid
from bson import ObjectId

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='../public', static_url_path='', template_folder='../templates')
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
    get_verified_workers, search_verified_workers, update_worker_verification,
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

@login_manager.user_loader
def load_user(user_id):
    user_data = find_user_by_id(user_id)
    if user_data:
        return User(user_data)
    return None
# Create admin user at startup
with app.app_context():
    admin = mongo.db.users.find_one({"phone": "254700000000"})
    if not admin:
        create_user("254700000000", "Admin", "admin123", "admin")
        print("Admin user created: phone=254700000000, password=admin123")

# ---------- PUBLIC ROUTES ----------

@app.route('/')
def index():
    """Home page - show verified workers or worker dashboard feed"""
    # 1. Handle Worker Personalized Feed
    if current_user.is_authenticated and current_user.role == 'worker':
        worker_profile = find_worker_by_user_id(current_user.id)
        if worker_profile:
            # Fetch available jobs for their trade
            jobs = find_open_jobs_by_trade(worker_profile.get('trade'))
            
            # Enrich jobs with customer data
            for job in jobs:
                customer = mongo.db.users.find_one({"_id": job['customer_id']})
                job['customer'] = customer
                
            return render_template('index.html', 
                                   is_worker_view=True, 
                                   worker_profile=worker_profile, 
                                   jobs=jobs)
                                   
    # 2. Handle Public/Customer View with Search
    search_query = request.args.get('q')
    if search_query:
        workers = search_verified_workers(search_query)
    else:
        workers = get_verified_workers()
        
    # Enrich workers with user data
    for worker in workers:
        user = mongo.db.users.find_one({"_id": worker['user_id']})
        worker['user'] = user
        
    return render_template('index.html', 
                           is_worker_view=False, 
                           workers=workers,
                           search_query=search_query)

@app.route('/register', methods=['GET', 'POST'])
def register():
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
        
        # Create user
        user_id = create_user(phone, name, password, role)
        
        # If worker, create worker profile with trade + location
        if role == 'worker':
            trade = request.form.get('trade')
            location_area = request.form.get('location_area')
            
            if not trade or not location_area:
                flash('Trade and location are required for workers')
                return redirect(url_for('register'))
            
            create_worker(str(user_id.inserted_id), trade, location_area, False)
        
        # Log the user in
        user_data = mongo.db.users.find_one({"_id": user_id.inserted_id})
        login_user(User(user_data))
        
        if role == 'worker':
            flash('Registration successful! Please verify your identity.')
            return redirect(url_for('verify_identity', user_id=str(user_id.inserted_id)))
        else:
            flash('Welcome to Fundi!')
            return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/verification/<user_id>')
def old_verification_redirect(user_id):
    # Redirect aggressively-cached browsers to the new route
    return redirect(url_for('verify_identity', user_id=user_id))

@app.route('/verify-identity/<user_id>', methods=['GET', 'POST'])
def verify_identity(user_id):
    """Verify worker identity"""
    if current_user.id != user_id:
        flash('Unauthorized')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        id_file = request.files.get('id_image')
        selfie_file = request.files.get('selfie')
        if not selfie_file or selfie_file.filename == '':
            selfie_file = request.files.get('selfie_upload')
            
        selfie_base64 = request.form.get('selfie_base64')
            
        if not id_file or id_file.filename == '':
            flash('Please upload your ID photo')
            return redirect(request.url)
            
        if (not selfie_file or selfie_file.filename == '') and not selfie_base64:
            flash('Please upload your selfie')
            return redirect(request.url)
        
        # Save files locally for verification
        os.makedirs('uploads', exist_ok=True)
        id_path = os.path.join('uploads', f'id_{user_id}_{uuid.uuid4().hex[:8]}.jpg')
        selfie_path = os.path.join('uploads', f'selfie_{user_id}_{uuid.uuid4().hex[:8]}.jpg')
        id_file.save(id_path)
        
        if selfie_file and selfie_file.filename != '':
            selfie_file.save(selfie_path)
        elif selfie_base64:
            import base64
            # Handle the "data:image/jpeg;base64,..." prefix
            if ',' in selfie_base64:
                header, encoded = selfie_base64.split(',', 1)
            else:
                encoded = selfie_base64
            with open(selfie_path, 'wb') as f:
                f.write(base64.b64decode(encoded))
        # Run verification using OCR and Mock Database
        from verification import verify_worker
        result = verify_worker(id_path, selfie_path)
        
        #Update worker 
        worker = find_worker_by_user_id(user_id)
        if worker:
            update_worker_verification(worker['_id'], result['verified'])
            
            # Upload images to Cloudinary
            from cloudinary_uploader import upload_image
            selfie_url = upload_image(selfie_path, folder_name=f"fundi/workers/{worker['_id']}/selfie")
            id_url = upload_image(id_path, folder_name=f"fundi/workers/{worker['_id']}/id")
            
            from models import update_worker_images
            update_worker_images(worker['_id'], selfie_url, id_url)
        
        # Clean up local files
        try:
            os.remove(id_path)
            os.remove(selfie_path)
        except:
            pass
        
        if result['verified']:
            flash('✅ Verification passed! You are now a verified Fundi worker.')
        else:
            error_msg = result.get('error', 'Please ensure your ID photo is clear and readable.')
            flash(f'❌ Verification failed: {error_msg}')
            return redirect(request.url)
        
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

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded images locally if not using Cloudinary or during local fallback."""
    public_uploads = os.path.join(app.root_path, '../public/uploads')
    if os.path.exists(os.path.join(public_uploads, filename)):
        return send_from_directory(public_uploads, filename)
    uploads_dir = os.path.join(app.root_path, '../uploads')
    return send_from_directory(uploads_dir, filename)

@app.route('/worker/dashboard')
@login_required
def worker_dashboard():
    """Worker dashboard with open and accepted jobs."""
    if current_user.role != 'worker':
        flash('Access denied')
        return redirect(url_for('index'))
    
    worker = find_worker_by_user_id(current_user.id)
    if not worker:
        flash('Worker profile not found. Please contact support.')
        return redirect(url_for('index'))
    
    # Get open jobs for this worker's trade
    open_jobs = find_open_jobs_by_trade(worker.get('trade'))
    for job in open_jobs:
        if 'area' not in job:
            job['area'] = job.get('location_area', '')
    
    # Get accepted jobs for this worker
    accepted_jobs = []
    quotes = list(mongo.db.quotes.find({"worker_id": worker['_id'], "status": "accepted"}))
    for q in quotes:
        job = mongo.db.job_requests.find_one({"_id": q['job_request_id']})
        booking = mongo.db.bookings.find_one({"quote_id": q['_id']})
        customer = mongo.db.users.find_one({"_id": job['customer_id']}) if job else None
        accepted_jobs.append({
            'quote_id': str(q['_id']),
            'job_id': str(job['_id']) if job else None,
            'customer_name': customer['name'] if customer else 'Customer',
            'customer_phone': customer['phone'] if customer else '',
            'full_address': job.get('full_address', '') if job else '',
            'amount': q['amount'],
            'payment_status': booking['payment_status'] if booking else 'pending_escrow',
            'photo_url': job.get('photo_url') if job else None
        })
    
    return render_template('worker_dashboard.html', worker=worker, open_jobs=open_jobs, accepted_jobs=accepted_jobs)

@app.route('/submit_quote/<job_id>', methods=['POST'])
@login_required
def submit_quote(job_id):
    if current_user.role != 'worker':
        flash('Only workers can submit quotes')
        return redirect(url_for('index'))
    
    worker = find_worker_by_user_id(current_user.id)
    if not worker or not worker.get('is_verified'):
        flash('You must be verified to submit quotes')
        return redirect(url_for('worker_dashboard'))
        
    amount = request.form.get('amount')
    message = request.form.get('message')
    
    if not amount:
        flash('Amount is required')
        return redirect(url_for('worker_dashboard'))
        
    create_quote(job_id, str(worker['_id']), float(amount), message)
    flash('Quote submitted successfully!')
    return redirect(url_for('worker_dashboard'))

@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    """Customer dashboard with posted jobs and quotes."""
    if current_user.role != 'customer':
        flash('Access denied')
        return redirect(url_for('index'))
    
    my_jobs = find_jobs_by_customer(current_user.id)
    for job in my_jobs:
        if 'area' not in job:
            job['area'] = job.get('location_area', '')
            
    job_ids = [j['_id'] for j in my_jobs]
    
    # Get pending quotes for customer's jobs
    pending_quotes = []
    quotes = list(mongo.db.quotes.find({"job_request_id": {"$in": job_ids}, "status": "pending"}))
    for q in quotes:
        w = mongo.db.workers.find_one({"_id": q['worker_id']})
        w_user = mongo.db.users.find_one({"_id": w['user_id']}) if w else None
        pending_quotes.append({
            'id': str(q['_id']),
            'worker_id': str(w['_id']) if w else '',
            'worker_name': w_user['name'] if w_user else 'Worker',
            'worker_rating': w.get('rating', 0.0) if w else 0.0,
            'amount': q['amount'],
            'message': q.get('message', '')
        })
        
    # Get accepted jobs for customer
    accepted_jobs = []
    acc_quotes = list(mongo.db.quotes.find({"job_request_id": {"$in": job_ids}, "status": "accepted"}))
    for q in acc_quotes:
        w = mongo.db.workers.find_one({"_id": q['worker_id']})
        w_user = mongo.db.users.find_one({"_id": w['user_id']}) if w else None
        job = mongo.db.job_requests.find_one({"_id": q['job_request_id']})
        booking = mongo.db.bookings.find_one({"quote_id": q['_id']})
        accepted_jobs.append({
            'quote_id': str(q['_id']),
            'worker_id': str(w['_id']) if w else '',
            'worker_name': w_user['name'] if w_user else 'Worker',
            'worker_phone': w_user['phone'] if w_user else '',
            'full_address': job.get('full_address', '') if job else '',
            'amount': q['amount'],
            'payment_status': booking['payment_status'] if booking else 'pending_escrow',
            'photo_url': job.get('photo_url') if job else None
        })

    return render_template('customer_dashboard.html', my_jobs=my_jobs, pending_quotes=pending_quotes, accepted_jobs=accepted_jobs)

@app.route('/worker/profile/<worker_id>')
def view_worker_profile(worker_id):
    """View detailed worker profile and reviews."""
    try:
        worker = find_worker_by_id(worker_id)
    except Exception:
        worker = None
        
    if not worker:
        flash('Worker profile not found.', 'danger')
        return redirect(url_for('index'))
        
    worker_user = find_user_by_id(worker['user_id'])
    reviews = find_reviews_by_worker(worker_id)
    
    for r in reviews:
        c = find_user_by_id(r['customer_id'])
        r['customer_name'] = c['name'] if c else 'Customer'

    return render_template('worker_profile.html', worker=worker, worker_user=worker_user, reviews=reviews)

@app.route('/accept_quote/<quote_id>')
@login_required
def accept_quote(quote_id):
    if current_user.role != 'customer':
        flash('Unauthorized')
        return redirect(url_for('index'))
    
    quote = find_quote_by_id(quote_id)
    if quote:
        update_quote_status(quote_id, 'accepted')
        update_job_status(quote['job_request_id'], 'booked')
        create_booking(quote_id)
        flash('Quote accepted!')
    return redirect(url_for('customer_dashboard'))

@app.route('/reject_quote/<quote_id>')
@login_required
def reject_quote(quote_id):
    if current_user.role != 'customer':
        flash('Unauthorized')
        return redirect(url_for('index'))
    
    quote = find_quote_by_id(quote_id)
    if quote:
        update_quote_status(quote_id, 'rejected')
        flash('Quote rejected.')
    return redirect(url_for('customer_dashboard'))

@app.route('/delete_job/<job_id>')
@login_required
def delete_job_route(job_id):
    if current_user.role != 'customer':
        flash('Unauthorized')
        return redirect(url_for('index'))
    
    job = find_job_by_id(job_id)
    if job and str(job['customer_id']) == current_user.id:
        delete_job(job_id)
        flash('Job request deleted.')
    return redirect(url_for('customer_dashboard'))

@app.route('/mark_job_completed/<quote_id>', methods=['POST'])
@login_required
def mark_job_completed(quote_id):
    if current_user.role != 'worker':
        flash('Unauthorized')
        return redirect(url_for('index'))
    
    booking = find_booking_by_quote(quote_id)
    if booking:
        update_booking_payment(str(booking['_id']), 'released')
        quote = find_quote_by_id(quote_id)
        if quote:
            update_job_status(quote['job_request_id'], 'completed')
            worker = find_worker_by_user_id(current_user.id)
            if worker:
                increment_worker_jobs(str(worker['_id']))
        flash('Job marked as complete!')
    return redirect(url_for('worker_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin():
        flash('Access denied')
        return redirect(url_for('index'))
    
    stats = get_stats()
    images = get_all_images()
    return render_template('admin_dashboard.html', stats=stats, images=images)

@app.route('/post_job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'customer':
        flash('Only customers can post jobs')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        trade = request.form.get('trade')
        description = request.form.get('description')
        area = request.form.get('area')
        full_address = request.form.get('full_address')
        
        preferred_date = request.form.get('preferred_date', '').strip() or None
        budget_min = request.form.get('budget_min', '').strip() or None
        budget_max = request.form.get('budget_max', '').strip() or None

        photo_file = request.files.get('photo')
        photo_url = None
        if photo_file and photo_file.filename != '':
            uploads_dir = os.path.join(app.root_path, '../public/uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            filename = f"job_{current_user.id}_{uuid.uuid4().hex[:8]}.jpg"
            local_photo_path = os.path.join(uploads_dir, filename)
            photo_file.save(local_photo_path)
            
            try:
                from cloudinary_uploader import upload_image
                uploaded_url = upload_image(local_photo_path, folder_name=f"fundi/jobs/{current_user.id}")
                if uploaded_url:
                    photo_url = uploaded_url
                else:
                    photo_url = f"/uploads/{filename}"
            except Exception as e:
                print(f"Cloudinary upload failed: {e}")
                photo_url = f"/uploads/{filename}"
        
        if not all([trade, description, area, full_address]):
            flash('All required fields must be filled.', 'danger')
            return render_template('post_job.html')
        
        job_id = create_job_request(
            customer_id=current_user.id,
            trade=trade,
            description=description,
            location_area=area,
            full_address=full_address,
            photo_url=photo_url,
            preferred_date=preferred_date,
            budget_min=budget_min,
            budget_max=budget_max
        )
        flash('Job posted successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
    
    return render_template('post_job.html')

if __name__ == '__main__':
    app.run(debug=True)

    