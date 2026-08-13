import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set production environment
os.environ["FLASK_ENV"] = "production"

from app import app
from config import ProductionConfig
from extensions import db
from waitress import serve

app.config.from_object(ProductionConfig)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))
    print(f"[*] Starting IPCMS Production WSGI Server (Waitress) on http://{host}:{port}")
    print(f"[*] Production Mode Active | DEBUG = {app.config.get('DEBUG')}")
    serve(app, host=host, port=port)
