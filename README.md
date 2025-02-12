# AI Voice Agent for Google Calendar

This project demonstrates a voice AI agent that can manage Google Calendar events through natural conversation. It combines several cutting-edge technologies to create a seamless voice interaction experience.

## Features

- Natural voice conversations for calendar management
- Schedule, update, and cancel calendar events
- Check calendar availability
- Real-time voice processing with WebRTC
- Integration with Google Calendar API

## Technology Stack

- **Voice Processing**
  - Daily.co for WebRTC audio calls
  - Cartesia for Text-to-Speech
  - Silero VAD for voice activity detection
- **AI & Language Processing**
  - OpenAI GPT-4 for natural language understanding
  - Custom calendar management tools
- **Backend**
  - Python 3.12
  - FastAPI
  - Google Calendar API
- **Infrastructure**
  - Docker containerization
  - Poetry for dependency management

## Requirements

- Python 3.12
- Poetry package manager
- Docker (optional)
- API Keys:
  - [Cartesia API key](https://cartesia.ai/sonic) for TTS
  - [Daily API key](https://daily.co/developers) for WebRTC
  - [OpenAI API key](https://platform.openai.com/api-keys)
  - Google Calendar API credentials:
    - Client ID
    - Client Secret
    - Refresh Token

## Setup & Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Configure environment variables in `.env`:
   ```
   CARTESIA_API_KEY=your_key
   DAILY_API_KEY=your_key
   OPENAI_API_KEY=your_key
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_secret
   GOOGLE_REFRESH_TOKEN=your_token
   ```

## Running the Application

### Local Development
```bash
poetry run python server.py
```

### Docker Deployment
```bash
docker build -t calendar-assistant .
docker run -p 7860:7860 calendar-assistant
```

Access the application at [http://localhost:7860](http://localhost:7860)

## Architecture

The application uses a pipeline architecture that processes:
1. Audio input through Daily's WebRTC
2. Voice activity detection with Silero
3. Natural language processing with GPT-4
4. Calendar operations through Google Calendar API
5. Text-to-speech conversion with Cartesia
6. Audio output back to the user

## Calendar Features

The assistant can:
- Create new calendar events (30-minute duration by default)
- Check free time slots between 9 AM and 5 PM
- Update existing calendar events (title, description, or time)
- Cancel/delete calendar events
- Handle multiple attendees for events

## Voice Interface

The voice interface provides:
- Real-time voice activity detection
- Natural conversation flow
- Interruption handling
- High-quality text-to-speech responses
- WebRTC-based audio streaming

## Development

The project uses:
- Poetry for dependency management
- Environment variables for configuration
- Async/await patterns for efficient I/O
- Logging with loguru
- Docker for containerization

## Google Calendar Setup

### 1. Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

### 2. Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type
3. Fill in the required information:
   - App name
   - User support email
   - Developer contact information
4. Add scopes:
   - Select "Google Calendar API"
   - Add "./auth/calendar" and "./auth/calendar.events"
5. Add test users (your Google email)

### 3. Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application" as application type
4. Name your client
5. Add Authorized redirect URIs:
   - http://localhost:3000/callback
   - http://localhost:3000/oauth/callback
6. Click "Create"
7. Save your Client ID and Client Secret

### 4. Get Authorization Code
1. Create an authorization URL with these parameters:
   ```
   https://accounts.google.com/o/oauth2/v2/auth
   ?client_id=YOUR_CLIENT_ID
   &redirect_uri=http://localhost:3000/callback
   &response_type=code
   &scope=https://www.googleapis.com/auth/calendar
   &access_type=offline
   &prompt=consent
   ```
2. Open this URL in a browser
3. Sign in with your Google account
4. Approve the permissions
5. You'll be redirected to your redirect URI with a code parameter

### 5. Exchange Code for Refresh Token
1. Make a POST request to Google's token endpoint:
   ```bash
   curl -X POST https://oauth2.googleapis.com/token \
   -d "client_id=YOUR_CLIENT_ID" \
   -d "client_secret=YOUR_CLIENT_SECRET" \
   -d "code=YOUR_AUTH_CODE" \
   -d "grant_type=authorization_code" \
   -d "redirect_uri=http://localhost:3000/callback"
   ```
2. The response will include your refresh token:
   ```json
   {
     "access_token": "...",
     "refresh_token": "...",
     "scope": "https://www.googleapis.com/auth/calendar",
     "token_type": "Bearer",
     "expires_in": 3599
   }
   ```

### 6. Update Environment Variables
Add the credentials to your `.env` file:
```
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token
```

### Important Notes
- The `access_type=offline` parameter is required to receive a refresh token
- The `prompt=consent` parameter ensures you get a refresh token even if you've authenticated before
- Refresh tokens don't expire unless explicitly revoked
- Store your refresh token securely - it grants long-term access to your calendar

### Troubleshooting
- If you don't receive a refresh token:
  - Ensure `access_type=offline` and `prompt=consent` are included in the authorization URL
  - Revoke the application's access in Google Account settings and try again
- If you get authentication errors:
  - Verify your redirect URI exactly matches what's configured in Google Cloud Console
  - Check that all required scopes are included
  - Ensure your client ID and secret are correct
  - Verify your credentials are properly set in your `.env` file

## License

This project is licensed under the MIT License - see the LICENSE file for details.