from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
from dotenv import load_dotenv
import openai
import psycopg2
import logging
import sys
from sqlalchemy import text
from flask_session import Session
from data.faq_data import FAQ_DATA

# Enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"],  # Vite's default port
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

load_dotenv()

# Add this before database configuration
logger.info("Starting application...")

# Configure Flask app
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
Session(app)

# Configure OpenAI
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    logger.error("OpenAI API key not found in environment variables")
    raise ValueError("OPENAI_API_KEY not set in environment")

openai.api_key = openai_api_key
logger.info("OpenAI API key configured successfully")

# Database configuration
def get_database_url():
    try:
        url = os.getenv('DATABASE_URL')
        logger.info(f"Database URL configured: {url}")
        return url
    except Exception as e:
        logger.error(f"Error getting database URL: {e}")
        return None

# Configure database
try:
    db_url = get_database_url()
    if not db_url:
        raise ValueError("DATABASE_URL not set in environment")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    
    # Test connection
    with app.app_context():
        db.session.execute(text('SELECT 1'))
        logger.info("✅ Database connection successful!")
except Exception as e:
    logger.error(f"❌ Database connection failed: {e}")
    raise

# Define FAQ model
class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize TF-IDF vectorizer
vectorizer = TfidfVectorizer()

# Basic greeting responses
GREETINGS = {
    'hi': [
        "Hi there! I'm Jessi from SkillUp Teaching Consultancy. How can I help you today?",
        "Hello! I'd be happy to help you learn about our courses and services. What would you like to know?"
    ],
    'hello': [
        "Hello! I'm Jessi, your AI assistant. I can help you with information about our courses, admissions, and more.",
        "Hi there! Welcome to SkillUp Teaching Consultancy. What can I help you with today?"
    ],
    'hey': [
        "Hey! Thanks for reaching out. I'm here to help you with any questions about our educational programs.",
        "Hi! I'm Jessi, your AI guide to SkillUp Teaching Consultancy. What would you like to know?"
    ],
    'good morning': [
        "Good morning! I'm Jessi, your AI guide to SkillUp Teaching Consultancy. What would you like to know?",
        "Hi! I'm Jessi, your AI guide to SkillUp Teaching Consultancy. What would you like to know?"
    ],
    'good evening': [
        "Good evening! I'm Jessi, your AI guide to SkillUp Teaching Consultancy. What would you like to know?",
        "Hi! I'm Jessi, your AI guide to SkillUp Teaching Consultancy. What would you like to know?"
    ],
    'good afternoon': [
        "Good afternoon! I'm Jessi, your AI guide to SkillUp Teaching Consultancy. What would you like to know?",
        "Hi! I'm Jessi, your AI guide to SkillUp Teaching Consultancy. What would you like to know?"
    ],
    'good night': [
        "Good night! I'm Jessi, your AI guide to SkillUp Teaching Consultancy. What would you like to know?",
        "Hi! I'm Jessi, your AI guide to SkillUp Teaching Consultancy. What would you like to know?"
    ],


}

def get_greeting_response(message):
    message = message.lower().strip()
    for greeting in GREETINGS:
        if message.startswith(greeting):
            return np.random.choice(GREETINGS[greeting])
    return None

def get_openai_response(message, context=""):
    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": """You are Jessi, an AI assistant for SkillUp Teaching Consultancy. 
                    Use the provided FAQ context to give accurate, friendly responses. 
                    If the question isn't covered in the FAQ, use your knowledge to provide helpful information.
                    Always maintain a professional, educational tone."""
                },
                {
                    "role": "user", 
                    "content": f"Context: {context}\n\nUser Question: {message}"
                }
            ],
            temperature=0.7,
            max_tokens=200
        )
        return {
            'content': completion.choices[0].message.content.strip(),
            'source': 'ai'
        }
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return None

def find_relevant_faqs(user_question, faqs, threshold=0.3):
    if not faqs:
        return []
    
    # Prepare questions for vectorization
    questions = [faq.question for faq in faqs]
    questions.append(user_question)
    
    # Calculate TF-IDF vectors
    tfidf_matrix = vectorizer.fit_transform(questions)
    
    # Calculate similarities
    similarities = cosine_similarity(
        tfidf_matrix[-1:], tfidf_matrix[:-1]
    )[0]
    
    # Get all relevant FAQs above threshold
    relevant_faqs = []
    for idx, similarity in enumerate(similarities):
        if similarity > threshold:
            relevant_faqs.append({
                'faq': faqs[idx],
                'similarity': similarity
            })
    
    return sorted(relevant_faqs, key=lambda x: x['similarity'], reverse=True)

@app.route('/')
def home():
    return "Server is running!"

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Get user message
        user_message = request.json.get('message', '').strip()
        
        # Step 1: Check for greetings first
        greeting_response = get_greeting_response(user_message.lower())
        if greeting_response:
            return jsonify({
                'content': greeting_response,
                'source': 'greeting'
            })

        # Step 2: Check FAQ Database
        faqs = FAQ.query.all()
        relevant_faqs = find_relevant_faqs(user_message, faqs, threshold=0.3)
        
        if relevant_faqs:
            # If very close match found (similarity > 0.7)
            if relevant_faqs[0]['similarity'] > 0.7:
                return jsonify({
                    'content': relevant_faqs[0]['faq'].answer,
                    'source': 'faq'
                })
            else:
                # Step 3: Use OpenAI with FAQ context for similar but not exact matches
                context = "\n".join([
                    f"Q: {faq['faq'].question}\nA: {faq['faq'].answer}"
                    for faq in relevant_faqs[:3]
                ])
                response_data = get_openai_response(user_message, context)
                if response_data:
                    return jsonify(response_data)
        
        # Step 4: If no FAQ matches, use OpenAI for dynamic response
        response_data = get_openai_response(user_message)
        if response_data:
            return jsonify(response_data)

        # Fallback response if all else fails
        return jsonify({
            'content': "I understand you're asking about our services. Could you please rephrase your question?",
            'source': 'fallback'
        })

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({
            'content': "I apologize, but I encountered an error. Please try again.",
            'source': 'error'
        }), 500

@app.route('/api/chat-history', methods=['GET'])
def get_chat_history():
    return jsonify({'history': session.get('chat_history', [])})

# Route to add new FAQs
@app.route('/api/faq', methods=['POST'])
def add_faq():
    data = request.json
    question = data.get('question')
    answer = data.get('answer')
    
    if not question or not answer:
        return jsonify({'error': 'Question and answer are required'}), 400
    
    new_faq = FAQ(question=question, answer=answer)
    db.session.add(new_faq)
    db.session.commit()
    
    return jsonify({'message': 'FAQ added successfully'}), 201

def initialize_faq_data():
    # Add FAQ data if table is empty
    if not FAQ.query.first():
        for faq in FAQ_DATA:
            new_faq = FAQ(
                question=faq["question"],
                answer=faq["answer"]
            )
            db.session.add(new_faq)
        db.session.commit()
        logger.info("✅ FAQ data initialized successfully!")

# Modified health check
@app.route('/api/health', methods=['GET'])
def health_check():
    logger.info("Health check endpoint called")
    try:
        with app.app_context():
            db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'message': 'System is running normally'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Add a route to get all FAQs
@app.route('/api/faqs', methods=['GET'])
def get_faqs():
    try:
        faqs = FAQ.query.all()
        return jsonify({
            'faqs': [
                {
                    'id': faq.id,
                    'question': faq.question,
                    'answer': faq.answer,
                    'created_at': faq.created_at.isoformat()
                }
                for faq in faqs
            ]
        })
    except Exception as e:
        logger.error(f"Error fetching FAQs: {str(e)}")
        return jsonify({'error': 'Failed to fetch FAQs'}), 500

if __name__ == '__main__':
    try:
        with app.app_context():
            # Create tables
            db.create_all()
            logger.info("✅ Tables created successfully!")
            
            # Initialize FAQ data
            initialize_faq_data()
            
        # Run the app
        logger.info("🚀 Starting Flask server...")
        app.run(
            host='0.0.0.0',  # Allow external connections
            port=5003,       # Use port 5003
            debug=True,
            use_reloader=True
        )
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1) 