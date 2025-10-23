import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# University Portal Configuration
PORTAL_URL = os.getenv('PORTAL_URL', 'http://212.0.143.242/portal/students')
DEFAULT_PASSWORD = os.getenv('DEFAULT_PASSWORD', '123456')

# Validate required environment variables
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is required. Please set it in .env file or environment variables.")