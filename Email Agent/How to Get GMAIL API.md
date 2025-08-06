
# 1. Go to Google Cloud Console
🔗 https://console.cloud.google.com/

# 2. Create a New Project

- Click the project dropdown (top bar near Google Cloud logo)
- Click "Create or Select a project" -> “NEW PROJECT”
- Give it a name, e.g., GeminiEmailAgent
- Click “CREATE”
- After creation, make sure it is selected

# 3. Enable Gmail API
- In the left sidebar, go to: APIs & Services > Library
- Search for Gmail API
- Click on Gmail API → Click Enable

# 4. Configure OAuth Consent Screen
- In the left sidebar, go to: APIs & Services > OAuth consent screen
- Choose "External" → Click Create
- Fill basic info:
  - App Name: Gemini Email Agent
  - User Support Email: your Google email
  - Click "Next"
  - Audience -> "External"
- Developer Contact: your email
- Click Save and Continue (keep default scopes and users)
- Under Test Users, add your Gmail address → Click Save and Continue

# 5. Create OAuth 2.0 Credentials
- Go to: APIs & Services > Credentials
- Click “+ CREATE CREDENTIALS” → OAuth Client ID
- Choose Application type: ✅ Desktop App
- Name it: Local Email Sender
- Click Create

- Download the client_secret.json File
- After creation:
  - Click the Download icon 📥
- Save the file as client_secret.json in your Python project directory.

# 6. Add yourself as Test User
- Go to Google Cloud Console
- Navigate to APIs & Services > OAuth consent screen
- Click on Audience.
- Under "Test users", add the Gmail address you're using to test.
- Save and retry authorization.