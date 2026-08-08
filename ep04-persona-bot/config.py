import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY= os.getenv("OPENAI_API_KEY")
# Optional: sets the default --provider so you don't have to pass it every time
PROVIDER=anthropic
