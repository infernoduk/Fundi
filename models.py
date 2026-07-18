from cryptography.hazmat.primitives import constant_time
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from flask_login import UserMixin
import bcrypt

mongo = PyMongo()

#------USER HELPER-------
def create_user(phone,name,password,role):
    """Create a new user."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = {
        "phone":phone,
        "name":name,
        "password":hashed,
        "role":role, #admin or user(customer or worker)
        "created_at":datetime.now()
    }
    return mongo.db.users.insert_one(user)

def find_user_by_phone(phone):
    """Find a user by phone number."""
    return mongo.db.users.find_one({"phone": phone})
def find_user_by_id(user_id):
    """Find a user by ObjectId."""
    return mongo.db.users.find_one({"_id": ObjectId(user_id)})

#--------WORKER HELPERS---------
def create_worker(user_id, trade, location_area, is_verified=False):
    """Create a worker profile."""
    worker = {
        "user_id": ObjectId(user_id),
        "trade": trade,
        "is_verified": is_verified,
        "rating": 0.0,
        "total_jobs": 0,
        "location_area": location_area,
        "id_photo_url": None,
        "selfie_url": None,
        "created_at": datetime.utcnow()
    }
    return mongo.db.workers.insert_one(worker)
def find_worker_by_user_id(user_id):
    """Find a worker by user_id."""
    return mongo.db.workers.find_one({"user_id": ObjectId(user_id)})

def find_worker_by_id(worker_id):
    """Find a worker by ObjectId."""
    return mongo.db.workers.find_one({"_id": ObjectId(worker_id)})

def get_verified_workers():
    """Get all verified workers, sorted by rating."""
    return list(mongo.db.workers.find({"is_verified": True}).sort("rating", -1))

def search_verified_workers(query):
    """Get verified workers matching a query in trade or location."""
    import re
    regex = re.compile(f".*{query}.*", re.IGNORECASE)
    return list(mongo.db.workers.find({
        "is_verified": True,
        "$or": [
            {"trade": {"$regex": regex}},
            {"location_area": {"$regex": regex}}
        ]
    }).sort("rating", -1))

def update_worker_verification(worker_id, is_verified):
    """Update worker verification status."""
    return mongo.db.workers.update_one(
        {"_id": ObjectId(worker_id)},
        {"$set": {"is_verified": is_verified}}
    )

def update_worker_images(worker_id, selfie_url=None, id_url=None):
    """Update worker profile with uploaded image URLs."""
    update_data = {}
    if selfie_url:
        update_data["selfie_url"] = selfie_url
    if id_url:
        update_data["id_url"] = id_url
        
    if update_data:
        return mongo.db.workers.update_one(
            {"_id": ObjectId(worker_id)},
            {"$set": update_data}
        )
    return None

def update_worker_rating(worker_id, rating):
    """Update worker rating."""
    return mongo.db.workers.update_one(
        {"_id": ObjectId(worker_id)},
        {"$set": {"rating": rating}}
    )

def increment_worker_jobs(worker_id):
    """Increment the total jobs completed by a worker."""
    return mongo.db.workers.update_one(
        {"_id": ObjectId(worker_id)},
        {"$inc": {"total_jobs": 1}}
    )

# -------- JOB HELPERS ---------
def create_job_request(customer_id, trade, description, location_area, full_address, photo_url=None):
    """Create a new job request."""
    job = {
        "customer_id": ObjectId(customer_id),
        "trade": trade,
        "description": description,
        "location_area": location_area,
        "full_address": full_address,
        "photo_url": photo_url,
        "status": "open", # open, quoted, booked, completed, cancelled
        "created_at": datetime.utcnow()
    }
    return mongo.db.job_requests.insert_one(job)

def find_job_by_id(job_id):
    """Find a job by ObjectId."""
    return mongo.db.job_requests.find_one({"_id": ObjectId(job_id)})

def find_jobs_by_customer(customer_id):
    """Find jobs posted by a customer."""
    return list(mongo.db.job_requests.find({"customer_id": ObjectId(customer_id)}).sort("created_at", -1))

def find_open_jobs_by_trade(trade):
    """Find open jobs for a specific trade."""
    return list(mongo.db.job_requests.find({"trade": trade, "status": "open"}).sort("created_at", -1))

def update_job_status(job_id, status):
    """Update job status."""
    return mongo.db.job_requests.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"status": status}}
    )

def delete_job(job_id):
    """Delete a job."""
    return mongo.db.job_requests.delete_one({"_id": ObjectId(job_id)})

# ------QUOTE HELPERS----------
def create_quote(job_request_id, worker_id, amount, message):
    """Create a new quote."""
    quote = {
        "job_request_id": ObjectId(job_request_id),
        "worker_id": ObjectId(worker_id),
        "amount": amount,
        "message": message,
        "status": "pending",  # pending, accepted, rejected
        "created_at": datetime.utcnow()
    }
    return mongo.db.quotes.insert_one(quote)
def find_quote_by_id(quote_id):
    """Find a quote by ObjectId."""
    return mongo.db.quotes.find_one({"_id": ObjectId(quote_id)})

def update_quote_status(quote_id, status):
    """Update quote status."""
    return mongo.db.quotes.update_one(
        {"_id": ObjectId(quote_id)},
        {"$set": {"status": status}}
    )
# ---------- BOOKING HELPERS ----------

def create_booking(quote_id):
    """Create a new booking."""
    booking = {
        "quote_id": ObjectId(quote_id),
        "payment_status": "pending_escrow",  # pending_escrow, paid_escrow, released
        "mpesa_ref": None,
        "completed_at": None,
        "created_at": datetime.utcnow()
    }
    return mongo.db.bookings.insert_one(booking)
def find_booking_by_id(booking_id):
    """Find a booking by ObjectId."""
    return mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})

def find_booking_by_quote(quote_id):
    """Find a booking by quote_id."""
    return mongo.db.bookings.find_one({"quote_id": ObjectId(quote_id)})

def update_booking_payment(booking_id, payment_status, mpesa_ref=None):
    """Update booking payment status."""
    update = {"payment_status": payment_status}
    if mpesa_ref:
        update["mpesa_ref"] = mpesa_ref
    if payment_status == "released":
        update["completed_at"] = datetime.utcnow()
    return mongo.db.bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": update}
    )

# ---------- REVIEW HELPERS ----------

def create_review(booking_id, customer_id, worker_id, rating, comment):
    """Create a new review."""
    review = {
        "booking_id": ObjectId(booking_id),
        "customer_id": ObjectId(customer_id),
        "worker_id": ObjectId(worker_id),
        "rating": rating,
        "comment": comment,
        "created_at": datetime.utcnow()
    }
    return mongo.db.reviews.insert_one(review)
def find_reviews_by_worker(worker_id):
    """Find all reviews for a worker, sorted newest first."""
    return list(mongo.db.reviews.find({"worker_id": ObjectId(worker_id)}).sort("created_at", -1))

def find_review_by_booking(booking_id):
    """Find a review by booking_id."""
    return mongo.db.reviews.find_one({"booking_id": ObjectId(booking_id)})
def get_all_images():
    """Get all image URLs from workers and jobs for admin."""
    images = []
    workers = list(mongo.db.workers.find())
    for worker in workers:
        if worker.get('id_photo_url'):
            user = mongo.db.users.find_one({"_id": worker['user_id']})
            images.append({
                'url': worker['id_photo_url'],
                'type': 'ID Photo',
                'owner': user['name'] if user else 'Unknown',
                'id': str(worker['_id']),
                'model': 'worker',
                'field': 'id_photo_url',
                'date': worker['created_at'].strftime('%Y-%m-%d') if worker.get('created_at') else 'N/A'
            })
        if worker.get('selfie_url'):
            user = mongo.db.users.find_one({"_id": worker['user_id']})
            images.append({
                'url': worker['selfie_url'],
                'type': 'Selfie',
                'owner': user['name'] if user else 'Unknown',
                'id': str(worker['_id']),
                'model': 'worker',
                'field': 'selfie_url',
                'date': worker['created_at'].strftime('%Y-%m-%d') if worker.get('created_at') else 'N/A'
            })
            
    jobs = list(mongo.db.job_requests.find())
    for job in jobs:
        if job.get('photo_url'):
            customer = mongo.db.users.find_one({"_id": job['customer_id']})
            images.append({
                'url': job['photo_url'],
                'type': 'Job Photo',
                'owner': customer['name'] if customer else 'Unknown',
                'id': str(job['_id']),
                'model': 'job',
                'field': 'photo_url',
                'date': job['created_at'].strftime('%Y-%m-%d') if job.get('created_at') else 'N/A'
            })
            
    return images

def get_stats():
    """Get admin dashboard statistics."""
    return {
        'total_users': mongo.db.users.count_documents({}),
        'total_workers': mongo.db.workers.count_documents({}),
        'verified_workers': mongo.db.workers.count_documents({"is_verified": True}),
        'total_jobs': mongo.db.job_requests.count_documents({}),
        'completed_jobs': mongo.db.job_requests.count_documents({"status": "completed"}),
        'total_bookings': mongo.db.bookings.count_documents({})
    }
