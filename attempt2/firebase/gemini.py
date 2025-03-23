from google import genai

client = genai.Client(api_key="AIzaSyAATMva5buJTHF2tMjGRkTx5rz8SClKmV4")

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain how AI works in a few words"
)
print(response.text)