
import os, re, json, base64
from pathlib import Path
from email.mime.text import MIMEText

from google import genai
from google.genai import types
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

#=========================================================
# 1. Configuration
#=========================================================
# Load Gemini Key
load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

# Load GMAIL API crednetials with the right scopes and authentication for OAuth2
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.readonly'] # modify, send, readonly
CLIENT_SECRET_FILE = Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'client_secret.json' # 'G:\My Drive\KEYS\client_secret.json' 
#==========================================================

def get_gmail_service():
    """Authenticate and return Gmail API service"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

#=========================================================
# 2. Email Sorting + Question Detection + Draft Reply
#=========================================================

def analyze_email(email_body):
    user_prompt = f"""
    Analyze the following email:

    "{email_body}"

    1. Classify it into one of these categories: "Urgent", "Not urgent".
    2. Determine if it contains a question (Yes/No).
    3. Generate a draft reply suggesting next steps or answering the query if applicable.

    Respond in JSON format with keys: category, has_question, draft_reply.
    """

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction='You are a helpful assistant who answers emails.',
                    max_output_tokens= 1000,
                    temperature= 0.6,  # range(0,1), higher value mean more creative/random
                    safety_settings= [types.SafetySetting(
                            category='HARM_CATEGORY_HATE_SPEECH',
                            threshold='BLOCK_ONLY_HIGH'),]
                    ),
                )
    
    # Extract JSON from response
    match = re.search(r'\{[\s\S]*\}', response.text)
    if not match:
        raise ValueError("No JSON found in Gemini response.")
    
    try:
        result = json.loads(match.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")

    required_keys = {"category", "has_question", "draft_reply"}
    if not isinstance(result, dict) or not required_keys.issubset(result.keys()):
        raise ValueError("Invalid response format from Gemini.")

    return result

#=========================================================
# 3. Gmail Authentication (OAuth2)
#=========================================================

def authenticate_gmail():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    service = build('gmail', 'v1', credentials=creds)
    return service

#=========================================================
# 4. Read & Label Emails
#=========================================================

LABEL_MAP = {
    'Urgent': 'Label_1935202856905512437', 
    'Not urgent': 'Label_8853844692182591357'
}

def get_unread_emails(service):
    results = service.users().messages().list(userId='me', q='is:unread').execute()
    messages = results.get('messages', [])
    return messages

def get_message_body(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    payload = msg['payload']
    parts = payload.get('parts', [])
    data = ''
    if parts:
        for part in parts:
            if part['mimeType'] == 'text/plain':
                data = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                break
    return data, msg

def add_label(service, msg_id, label_id):
    service.users().messages().modify(
        userId='me',
        id=msg_id,
        body={'addLabelIds': [label_id]}
    ).execute()


#=========================================================
# 5. Save Draft Reply to Gmail
#=========================================================

def create_draft_message(to, subject, body):
    """
    Creates a MIME message for draft
    """
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    # Add a prefix to indicate it's a draft
    if not subject.startswith("[Draft]"):
        message['subject'] = f"[Draft] {subject}"
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'message': {'raw': raw}}



def save_draft(service, to, subject, body):
    """
    Saves a draft email in Gmail
    """
    try:
        draft_message = create_draft_message(to, subject, body)
        draft = service.users().drafts().create(userId="me", body=draft_message).execute()
        print(f"💾 Draft saved with ID: {draft['id']}")
        return draft
    except Exception as e:
        print(f"❌ Failed to save draft: {str(e)}")
        return None



def extract_sender_email(full_msg):
    """
    Extract sender email from the full message object
    """
    headers = full_msg['payload']['headers']
    for header in headers:
        if header['name'] == 'From':
            # Simple extraction - you might want to use email.utils for better parsing
            sender = header['value']
            # Extract email address from format: "Name <email@domain.com>"
            import re
            email_match = re.search(r'<([^>]+)>', sender)
            if email_match:
                return email_match.group(1)
            else:
                return sender.strip()
    return "unknown@example.com"

#=========================================================
# 6. Main Agent Loop
#=========================================================

def run_email_agent():
    print("📧 Starting Email Agent...")

    # Authenticate Gmail
    gmail_service = authenticate_gmail()

    # Get unread emails
    emails = get_unread_emails(gmail_service)

    if not emails:
        print("📭 No unread emails.")
        return

    for email in emails:
        msg_id = email['id']
        body, full_msg = get_message_body(gmail_service, msg_id)

        print(f"\n🔍 Processing Email ID: {msg_id}")
        # print(f"📩 Body Preview: {body[:100]}...")

        try:
            analysis = analyze_email(body)
            # print("🧠 Analysis Result:", analysis)

            # Apply label based on category
            category = analysis["category"]
            label_id = LABEL_MAP.get(category)
            if label_id:
                add_label(gmail_service, msg_id, label_id)
                print(f"📁 Labeled as '{category}'")

            # Mark as read
            # gmail_service.users().messages().modify(
            #     userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}
            # ).execute()

            # If there's a question, generate draft reply
            if analysis["has_question"]:
                print("❓ Email contains a question. Generating draft reply...")
                # print("📝 Draft Reply:\n", analysis["draft_reply"])

                # Extract sender email
                sender_email = extract_sender_email(full_msg)
                # print(f"📧 Sender: {sender_email}")
                
                # Get original subject
                headers = full_msg['payload']['headers']
                subject = ""
                for header in headers:
                    if header['name'] == 'Subject':
                        subject = header['value']
                        break
                
                # Save draft reply
                save_draft(
                    service=gmail_service,
                    to=sender_email,
                    subject=f"Re: {subject}",
                    body=analysis["draft_reply"])

        except Exception as e:
            print(f"⚠️ Error processing email {msg_id}: {str(e)}")

    print("\n✅ Email Agent finished.")

#=========================================================
# Run the agent
#=========================================================

if __name__ == "__main__":
    run_email_agent()