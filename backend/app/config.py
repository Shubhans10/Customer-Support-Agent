import os
from dotenv import load_dotenv

load_dotenv()

# ---- LLM Provider ----
# Set LLM_PROVIDER to "azure" to use Azure OpenAI, or "openai" (default)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

# ---- OpenAI Settings ----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))

# ---- Azure OpenAI Settings ----
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
