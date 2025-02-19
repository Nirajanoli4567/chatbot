import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = 'your-secret-key-here'
    SESSION_TYPE = 'filesystem'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') 