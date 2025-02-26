import os
from dotenv import load_dotenv
from pathlib import Path

base_dir = Path(__file__).resolve().parent
env_file = base_dir / '.env'
load_dotenv(env_file)


class Config:
    FLASK_APP = os.environ.get('FLASK_APP')
    FLASK_DEBUG = os.environ.get('FLASK_APP')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_USE_TLS = os.environ.get('AIL_USE_TLS')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    FB_CLIENT_ID = os.environ.get('FB_CLIENT_ID')
    FB_CLIENT_SECRET = os.environ.get('FB_CLIENT_SECRET')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_PROJECT_ID = os.environ.get('GOOGLE_PROJECT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

    STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
    STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
    CRON_KEY = os.environ.get('CRON_KEY')
    MAILERLITE_TOKEN = os.environ.get('MAILERLITE_TOKEN')
    DAYS_TO_ADD_ACTIVITY = 10