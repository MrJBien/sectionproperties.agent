import google.genai as genai
from google.genai import types
from dotenv import load_dotenv
import os

# Configure your API key (replace with your actual key or environment variable)
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY","xxx")
client = genai.Client(api_key=api_key)

# Define the grounding tool
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# Configure generation settings to include the tool
config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

# Make the request
response = client.models.generate_content(
    model="gemini-2.5-flash", # Or "gemini-2.5-pro", etc.
    contents="What are the current news headlines regarding the global economy?",
    config=config,
)

print(response.text)

# # You can inspect the grounding metadata to see if a search was performed
# if response.candidates[0].grounding_metadata:
#     print("\n--- Grounding Metadata ---")
#     if response.candidates[0].grounding_metadata.web_search_queries:
#         print("Search Queries:", response.candidates[0].grounding_metadata.web_search_queries)
#     if response.candidates[0].grounding_metadata.search_results:
#         for result in response.candidates[0].grounding_metadata.search_results:
#             print(f"  - Source: {result.title} ({result.uri})")
#             print(f"    Snippet: {result.snippet}")