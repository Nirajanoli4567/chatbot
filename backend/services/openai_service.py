import openai
import logging
from config.settings import Config

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        openai.api_key = self.api_key

    def generate_response(self, message, context=""):
        try:
            if not self.api_key:
                logger.error("OpenAI API key is not set")
                return {
                    'content': "I'm having trouble connecting to my AI service. Please try asking about our courses or services directly.",
                    'source': 'error'
                }

            completion = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are Jessi, an AI assistant for SkillUp Teaching Consultancy.
                        Provide helpful, accurate responses based on the context and your knowledge.
                        Always respond in a friendly, professional tone and keep responses concise."""
                    },
                    {
                        "role": "user",
                        "content": f"Context: {context}\n\nQuestion: {message}"
                    }
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            response = completion.choices[0].message.content.strip()
            return {
                'content': response,
                'source': 'ai'
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                'content': "I apologize, but I'm having trouble processing your request. Let me provide you with direct information from our FAQ.",
                'source': 'error'
            } 