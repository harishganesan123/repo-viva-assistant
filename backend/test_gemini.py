from google import genai

API_KEY = "YOUR_GEMINI_API_KEY"

client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Hello"
)

print(response.text)