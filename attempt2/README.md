# NextGen Marketplace

A modern marketplace application built with Streamlit and Firebase.

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your API keys and other sensitive information to `.env`
   - Never commit the `.env` file to version control

4. Set up Firebase:
   - Create a Firebase project
   - Download your service account key
   - Place it in the `firebase` directory as `serviceAccountKey.json`

5. Run the application:
   ```bash
   streamlit run app.py
   ```

## Environment Variables

The following environment variables are required:

- `GEMINI_API_KEY`: Your Google Gemini API key

## Security Notes

- Never commit API keys or sensitive credentials to version control
- Keep your `.env` file secure and never share it
- Regularly rotate your API keys and credentials
- Use environment variables for all sensitive information 