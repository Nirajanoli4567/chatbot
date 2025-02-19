from openai import OpenAI
from config.settings import Config
import logging

client = OpenAI(api_key=Config.OPENAI_API_KEY)
logger = logging.getLogger(__name__)

def get_openai_response(message, context=""):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Jessi, a helpful AI assistant."},
                {"role": "user", "content": f"Context: {context}\nQuestion: {message}"}
            ],
            max_tokens=150
        )
        return {
            'content': response.choices[0].message.content.strip(),
            'source': 'ai'
        }
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return None 