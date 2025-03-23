from google import genai
import os

# Initialize Gemini client
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set")
client = genai.Client(api_key=api_key)

def generate_content(prompt):
    """
    Generate content using Gemini AI
    
    Args:
        prompt (str): The prompt to generate content for
        
    Returns:
        str: Generated content
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Error generating content: {str(e)}")
        return "{}"  # Return empty JSON object as fallback