

## pip install -r Requirements.txt
import os
import json
import base64
import re
from pathlib import Path
from email.mime.text import MIMEText
from email.utils import parseaddr
import email.utils

from google import genai
from google.genai import types
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv


#=========================================================
# 1. Configuration
#=========================================================
# Load Gemini Key
load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

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




def get_unread_emails(service):
    """
    Fetch unread emails from inbox
    ---
    Searches for messages with both 'INBOX' and 'UNREAD' labels
    Retrieves full message details for each email
    Extracts subject and sender from email headers
    Returns a list of dictionaries containing email ID, subject, sender, and body preview
    """
    results = service.users().messages().list(
        userId='me', 
        labelIds=['INBOX', 'UNREAD'],
        maxResults=10
    ).execute()
    messages = results.get('messages', [])
    
    emails = []
    for message in messages:
        msg = service.users().messages().get(
            userId='me', 
            id=message['id'],
            format='full'
        ).execute()
        
        # Extract headers
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        message_id = next((h['value'] for h in headers if h['name'] == 'Message-ID'), '')
        references = next((h['value'] for h in headers if h['name'] == 'References'), '')
        thread_id = msg.get('threadId', '')  # Gmail's thread ID
        
        # Extract body
        body = ''
        # Check if it's a simple message (no parts)
        if msg['payload'].get('body', {}).get('data'):
            try:
                body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
            except:
                pass
        
        # Check multipart messages
        elif 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain' and part.get('body', {}).get('data'):
                    try:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                    except:
                        continue
        
        # Debug print to see what we're getting
        print(f"Debug: Email from {sender[:30]}... has {len(body)} characters")
        
        
        emails.append({
            'id': message['id'],
            'subject': subject,
            'sender': sender,
            'body': body, # body[:500]  # Truncates body to first 500 characters
            'message_id': message_id,         # Original Message-ID header
            'references': references,         # References header
            'thread_id': thread_id           # Gmail thread ID
        })
    return emails









def send_reply(service, to, subject, body, original_message_id, gmail_message_id, original_references=None): # thread_id
    """
    Send email reply
    ---
    Builds a MIME email with the specified body content
    Sets recipient and adds "Re: " prefix to subject
    Adds threading headers (In-Reply-To and References) to maintain conversation thread
    """
    message = MIMEText(body)
    message['to'] = to
    # Fix double "Re:" issue
    if not subject.startswith('Re: '):
        message['subject'] = f"Re: {subject}"
    else:
        message['subject'] = subject
    if original_references and original_message_id:
        message['References'] = f"{original_references} {original_message_id}"
    elif original_message_id:
        message['References'] = original_message_id
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

    # Mark original email as read
        service.users().messages().modify(
            userId='me',
            id=gmail_message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

        return sent_message
    except Exception as e:
        print(f"Error sending email: {e}")
        return None


def extract_email_address(sender):
    """Extract clean email address from sender string"""
    return parseaddr(sender)[1]






def main():
    try:
        # Initialize services
        gmail_service = get_gmail_service()
        
        # Get unread emails
        emails = get_unread_emails(gmail_service)
        if not emails:
            print("No unread emails found")
            return
        
        print(f"\nFound {len(emails)} unread emails. Processing one by one...\n")
        
        # Process each email individually
        for i, email in enumerate(emails, 1):
            print("=" * 60)
            print(f"EMAIL {i} of {len(emails)}")
            print("=" * 60)
            print(f"From: {email['sender']}")
            print(f"Subject: {email['subject']}")
            print(f"Content:\n{email['body']}")
            print("=" * 60)
            
            # Ask user what to do with this email
            while True:
                action = input(f"\nWhat would you like to do with this email?\n"
                              f"1. Reply\n"
                              f"2. Skip\n"
                              f"3. Quit\n"
                              f"Choice (1/2/3): ").strip()
                
                if action == '1':
                    # Get user's reply instruction
                    user_prompt = input("\nHow should I reply to this email?\n> ")
                    
                    # Create prompt for this specific email
                    prompt = f"""
                    User instruction: {user_prompt}
                    
                    Email to respond to:
                    From: {email['sender']}
                    Subject: {email['subject']}
                    Content: {email['body']}
                    
                    Instructions:
                    1. Write a helpful, professional, and contextually appropriate response to this email
                    2. Address the specific content and any questions in the original email
                    3. Follow the user's instruction: "{user_prompt}"
                    4. Keep it concise but substantive
                    5. Output ONLY the email response content (no extra formatting or labels)
                    
                    Important: Base your response entirely on the email content and user instruction.
                    """
                    
                    # Generate response with Gemini
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction='You are a helpful assistant who writes professional email replies.',
                            max_output_tokens=1000,
                            temperature=0.6,
                        ),
                    )
                    
                    reply_text = response.text.strip()
                    
                    # Show the proposed reply
                    print("\nPROPOSED REPLY:")
                    print("-" * 40)
                    print(f"To: {email['sender']}")
                    print(f"Subject: Re: {email['subject']}")
                    print(f"Content:\n{reply_text}")
                    print("-" * 40)
                    
                    # Confirm sending
                    confirm = input("\nSend this reply? (y/n): ").lower().strip()
                    if confirm == 'y':
                        result = send_reply(
                            service=gmail_service,
                            to=email['sender'],
                            subject=email['subject'],
                            body=reply_text,
                            original_message_id=email.get('message_id', ''),
                            gmail_message_id=email['id'],
                            original_references=email.get('references', '')
                        )
                        
                        if result:
                            print(f"✓ Reply sent successfully!")
                        else:
                            print("✗ Failed to send reply")
                    else:
                        print("Reply cancelled.")
                    
                    break  # Move to next email
                    
                elif action == '2':
                    print("Skipping this email...")
                    break  # Move to next email
                    
                elif action == '3':
                    print("Exiting...")
                    return
                    
                else:
                    print("Please enter 1, 2, or 3")
            
            print("\n")  # Space between emails
        
        print("All emails processed!")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()