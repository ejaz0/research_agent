import requests
from bs4 import BeautifulSoup
from config import CLAUDE_API_KEY, SERPAPI_KEY
import anthropic
from serpapi import GoogleSearch

# Initialize Claude client
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
model = "claude-haiku-4-5"
# Tool 1: Search Web using SerpAPI
def search_web(query, num_results=2):
    search = GoogleSearch({"q": query, "api_key": SERPAPI_KEY, "num": num_results})
    results = search.get_dict()
    urls = []
    if "organic_results" in results:
        for r in results["organic_results"]:
            if "link" in r:
                urls.append(r["link"])
    return urls

# Tool 2: Fetch URL and extract text
def fetch_url(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # Get main text
            texts = soup.stripped_strings
            return " ".join(texts)
        else:
            return f"Error: Status {r.status_code}"
    except Exception as e:
        return f"Error: {e}"

# Tool 3: Summarize using Claude
def summarize(text):
    prompt = f"Summarize the following text concisely:\n{text}"
    response = client.messages.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )
    # response.content may be a list; take the first string
    if isinstance(response.content, list):
        return response.content[0]["content"] if "content" in response.content[0] else str(response.content[0])
    return str(response.content)