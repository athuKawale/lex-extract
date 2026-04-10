import os
from langchain_classic.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()

# Universal Model Initialization
# Supports providers like "openai", "anthropic", "google_genai", "ollama", etc.
# Requirements:
# - For OpenAI: pip install langchain-openai, set OPENAI_API_KEY
# - For Anthropic: pip install langchain-anthropic, set ANTHROPIC_API_KEY
# - For Ollama: pip install langchain-ollama, ensure OLLAMA_BASE_URL is set
llm = init_chat_model(
    model=os.getenv("MODEL_NAME", "gemma4:31b-cloud"),
    model_provider=os.getenv("MODEL_PROVIDER", "ollama"),
    temperature=0,
    # Provider-specific kwargs (passed to underlying model class)
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
)