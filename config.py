import os
from dotenv import load_dotenv

load_dotenv()
# OpenAI settings
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your-openai-api-key")
OPENAI_MODEL = "gpt-4o"  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.

# Document processing settings
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}
MAX_TOKEN_LIMIT = 5000  # Maximum number of tokens to use in context

# ChromaDB settings
CHROMA_PERSIST_DIRECTORY = os.path.join(os.getcwd(), 'chroma_db')

# Make sure upload and ChromaDB directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHROMA_PERSIST_DIRECTORY, exist_ok=True)
