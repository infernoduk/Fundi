# Fundi Service Marketplace Platform 🛠️

Fundi is a premium marketplace platform designed to connect trusted, identity-verified professionals (plumbers, electricians, painters, etc.) with customers who need reliable services done right.

## Features ✨

*   **Public Directory & Search:** Customers can search for verified workers by trade or location directly from the beautifully designed landing page.
*   **Worker Personalized Feed:** When workers log in, their homepage transforms into a personalized job board showing available gigs matching their specific trade and area.
*   **Automated ID Verification:** Workers are required to upload a selfie and their Kenyan National ID. The system uses **Tesseract OCR** to extract the ID number and verify it against a database instantly.
*   **Cloudinary Integration:** Profile photos and ID images are securely uploaded and served via Cloudinary.
*   **Premium UI:** Built with Bootstrap 5 and a custom design system inspired by modern corporate aesthetics (Amber and Deep Teal color palette).

## Tech Stack 💻

*   **Backend:** Python, Flask, Flask-Login
*   **Database:** MongoDB (via PyMongo)
*   **Frontend:** HTML5, Bootstrap 5, Custom CSS, Vanilla JavaScript
*   **Integrations:** Cloudinary API, Pytesseract (OCR)

## Prerequisites ⚙️

Before running the project, ensure you have the following installed:
1.  Python 3.8+
2.  MongoDB (Running locally on `mongodb://localhost:27017` or via MongoDB Atlas)
3.  Tesseract OCR Engine installed on your system.

## Environment Variables 🔐

Create a `.env` file in the root directory of the project and add the following keys:

```ini
# Flask Config
SECRET_KEY=your_super_secret_flask_key_here
MONGO_URI=mongodb://localhost:27017/fundi

# Cloudinary Credentials (Required for image uploads)
CLOUDINARY_CLOUD_NAME=your_cloud_name
API_KEY=your_api_key
API_SECRET=your_api_secret
```

## Setup & Installation 🚀

1.  **Clone the repository**
    ```bash
    git clone https://github.com/infernoduk/Fundi.git
    cd Fundi
    ```

2.  **Install dependencies**
    It is recommended to use a virtual environment:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**
    ```bash
    python api/index.py
    ```

4.  **Access the application**
    Open your browser and navigate to `http://127.0.0.1:5000/`.

## Demo Users 👤

If you are using the mock ID verification database, the following ID number is pre-approved for successful verification testing:
*   `15248301`

*(Other mock IDs can be found in `verification.py`)*

## License
&copy; 2026 Fundi Marketplace. All rights reserved.
