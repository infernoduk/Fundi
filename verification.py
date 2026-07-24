# verification.py
import pytesseract
from PIL import Image
import re
import os

# Point to the actual Tesseract executable on Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Mock database of valid IDs for demonstration purposes
MOCK_VALID_IDS = [
    "12345678", 
    "87654321", 
    "11223344",
    "98765432",
    "510790496",
    "25561552",
    "15248301",
    "21419626",
    "92917210",
    "80392154"

]

def extract_id_text(image_path):
    """Extract ID number and name from Kenyan National ID photo."""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        
        # Search for 8-digit ID number (Kenyan ID format)
        id_match = re.search(r'\b\d{8}\b', text)
        id_number = id_match.group() if id_match else None
        
        # Search for name (letters only, >5 characters)
        lines = text.split('\n')
        name = None
        for line in lines:
            cleaned = line.strip()
            if re.match(r'^[A-Za-z\s]+$', cleaned) and len(cleaned) > 5:
                name = cleaned
                break
        
        return id_number, name
    except Exception as e:
        print(f"OCR error: {e}")
        return None, None

def verify_worker(id_image_path, selfie_image_path):
    """Full verification pipeline using Mock Database and OCR."""
    id_number, name = extract_id_text(id_image_path)
    
    # Check if the extracted ID is in our mock database
    id_verified = id_number in MOCK_VALID_IDS
    
    # Skip actual face matching to keep the app lightweight,
    # but we still require the selfie to be passed to simulate the flow
    face_match = True 
    
    verified = id_verified and face_match
    
    return {
        'verified': verified,
        'id_number': id_number,
        'name': name,
        'face_match': face_match,
        'error': "ID number not found in government database." if not id_verified else None
    }