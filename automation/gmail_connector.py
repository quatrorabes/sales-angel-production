#!/usr/bin/env python3

# gmail_connector.py - One-click Gmail sending

import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailConnector:
	"""Send emails directly through Gmail API"""
	
	def __init__(self):
		self.service = self._get_service()
		
	def _get_service(self):
		"""Authenticate and get Gmail service"""
		creds = None
		
		if os.path.exists('token.json'):
			creds = Credentials.from_authorized_user_file('token.json', SCOPES)
			
		if not creds or not creds.valid:
			if creds and creds.expired and creds.refresh_token:
				creds.refresh(Request())
			else:
				if not os.path.exists('credentials.json'):
					print("⚠️  Gmail integration not configured")
					print("See: https://developers.google.com/gmail/api/quickstart/python")
					return None
				
				flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
				creds = flow.run_local_server(port=0)
				
			with open('token.json', 'w') as token:
				token.write(creds.to_json())
				
		return build('gmail', 'v1', credentials=creds) if creds else None
	
	def send_email(self, to, subject, body, sender='me'):
		"""Send email via Gmail"""
		
		if not self.service:
			return {'status': 'error', 'message': 'Gmail not configured'}
		
		try:
			message = MIMEText(body)
			message['to'] = to
			message['subject'] = subject
			
			raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
			
			result = self.service.users().messages().send(
				userId=sender,
				body={'raw': raw}
			).execute()
			
			return {
				'status': 'success',
				'message_id': result['id'],
				'message': f'Email sent to {to}'
			}
		
		except Exception as e:
			return {'status': 'error', 'message': str(e)}
		
	def is_configured(self):
		"""Check if Gmail is configured"""
		return self.service is not None
	
# Quick setup guide
def print_setup_guide():
	print("""
╔══════════════════════════════════════════════════════════════╗
║              GMAIL INTEGRATION SETUP                          ║
╚══════════════════════════════════════════════════════════════╝

1. Go to: https://console.cloud.google.com/
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials.json to this directory
6. Run: python gmail_connector.py

First run will open browser for authentication.
""")
	
if __name__ == "__main__":
	if not os.path.exists('credentials.json'):
		print_setup_guide()
	else:
		gmail = GmailConnector()
		if gmail.is_configured():
			print("✅ Gmail configured and ready!")
			
			# Test send
			test = input("\nSend test email? (y/n): ")
			if test.lower() == 'y':
				to = input("To: ")
				result = gmail.send_email(to, "Test from Sales Angel", "This is a test email!")
				print(f"\n{result['message']}")
				