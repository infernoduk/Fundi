import os
import cloudinary
import cloudinary.uploader

from dotenv import load_dotenv

# Force load environment variables in case the server hasn't been completely restarted
load_dotenv()

# We securely load the discrete keys from the .env file instead of hardcoding them
import cloudinary.api
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)
def upload_image(file_path, folder_name="fundi"):
    """
    Uploads a local image file to Cloudinary and returns the secure URL.
    """
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
            
        print(f"Uploading {file_path} to Cloudinary folder {folder_name}...")
        
        # Upload the image and let Cloudinary automatically assign a public ID
        response = cloudinary.uploader.upload(
            file_path,
            folder=folder_name
        )
        
        secure_url = response.get('secure_url')
        print(f"Successfully uploaded: {secure_url}")
        return secure_url
        
    except Exception as e:
        print(f"Cloudinary upload failed: {e}")
        return None
