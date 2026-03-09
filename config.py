from dotenv import load_dotenv
import os

load_dotenv()  # must be called first

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

