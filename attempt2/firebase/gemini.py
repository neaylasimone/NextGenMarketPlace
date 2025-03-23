from google import genai

# Initialize Gemini client
client = genai.Client(api_key="AIzaSyAATMva5buJTHF2tMjGRkTx5rz8SClKmV4")

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