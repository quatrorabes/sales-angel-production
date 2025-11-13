#!/usr/bin/env python3

# linkedin_automation.py - LinkedIn outreach automation

import sqlite3
from datetime import datetime, timezone, timedelta
import time
import os
import requests

class LinkedInAutomation:
		"""Automated LinkedIn outreach - SAFE & COMPLIANT"""
	
		def __init__(self, db_path='sales_angel.db'):
				self.db_path = db_path
				self._init_tables()
			
				# LinkedIn limits (stay under radar)
				self.DAILY_LIMITS = {
						'connection_requests': 20,  # Safe: 20/day
						'messages': 30,              # Safe: 30/day
						'profile_views': 100,        # Safe: 100/day
						'inmails': 10                # Safe: 10/day (if premium)
				}
			
		def _init_tables(self):
				conn = sqlite3.connect(self.db_path)
			
				conn.execute("""
						CREATE TABLE IF NOT EXISTS linkedin_prospects (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								contact_id INTEGER,
								linkedin_url TEXT UNIQUE NOT NULL,
								profile_name TEXT,
								headline TEXT,
								company TEXT,
								connection_status TEXT DEFAULT 'not_connected',
								connection_request_sent TEXT,
								connection_accepted TEXT,
								last_message_sent TEXT,
								last_engaged TEXT,
								engagement_score INTEGER DEFAULT 0,
								notes TEXT,
								FOREIGN KEY (contact_id) REFERENCES contacts(id)
						)
				""")
			
				conn.execute("""
						CREATE TABLE IF NOT EXISTS linkedin_activities (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								prospect_id INTEGER NOT NULL,
								activity_type TEXT NOT NULL,
								activity_data TEXT,
								performed_at TEXT NOT NULL,
								result TEXT,
								FOREIGN KEY (prospect_id) REFERENCES linkedin_prospects(id)
						)
				""")
			
				conn.execute("""
						CREATE TABLE IF NOT EXISTS linkedin_message_templates (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								template_name TEXT UNIQUE NOT NULL,
								template_type TEXT NOT NULL,
								subject TEXT,
								message_body TEXT NOT NULL,
								variables TEXT,
								performance_score REAL DEFAULT 0.0,
								uses_count INTEGER DEFAULT 0
						)
				""")
			
				conn.commit()
				conn.close()
			
				# Add default templates
				self._add_default_templates()
			
		def _add_default_templates(self):
				"""Add default message templates"""
			
				templates = [
						{
								'name': 'connection_request_1',
								'type': 'connection_request',
								'message': "Hi {firstname}, I noticed we're both in {industry}. I'd love to connect and potentially explore synergies between our work. Looking forward to connecting!"
						},
						{
								'name': 'connection_request_2',
								'type': 'connection_request',
								'message': "Hi {firstname}, Really impressed by your work at {company}. Would love to connect and learn more about what you're building. Best regards!"
						},
						{
								'name': 'follow_up_1',
								'type': 'follow_up',
								'subject': 'Quick question about {company}',
								'message': "Hi {firstname},\n\nHope you're doing well! I've been following {company}'s recent growth and wanted to reach out.\n\nI work with similar companies in {industry} helping them {value_prop}. Would you be open to a quick 15-min call to explore if there's mutual value?\n\nBest,\n{sender_name}"
						},
						{
								'name': 'value_add_1',
								'type': 'value_add',
								'subject': 'Thought this might interest you',
								'message': "Hi {firstname},\n\nSaw your recent post about {topic} and thought you might find this interesting:\n\n{insight_or_resource}\n\nWould love to hear your thoughts!\n\nBest,\n{sender_name}"
						}
				]
			
				conn = sqlite3.connect(self.db_path)
			
				for template in templates:
						try:
								conn.execute("""
										INSERT OR IGNORE INTO linkedin_message_templates 
										(template_name, template_type, subject, message_body)
										VALUES (?, ?, ?, ?)
								""", (template['name'], template['type'], 
											template.get('subject'), template['message']))
						except:
								pass
							
				conn.commit()
				conn.close()
			
		def add_prospect(self, linkedin_url, contact_id=None, profile_data=None):
				"""Add a LinkedIn prospect"""
			
				conn = sqlite3.connect(self.db_path)
			
				try:
						conn.execute("""
								INSERT INTO linkedin_prospects 
								(linkedin_url, contact_id, profile_name, headline, company)
								VALUES (?, ?, ?, ?, ?)
						""", (linkedin_url, contact_id, 
									profile_data.get('name') if profile_data else None,
									profile_data.get('headline') if profile_data else None,
									profile_data.get('company') if profile_data else None))
					
						prospect_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
						conn.commit()
					
						return {'success': True, 'prospect_id': prospect_id}
			
				except sqlite3.IntegrityError:
						return {'success': False, 'error': 'Prospect already exists'}
				finally:
						conn.close()
					
		def generate_connection_message(self, prospect_id, template_name='connection_request_1'):
				"""Generate personalized connection request"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				prospect = conn.execute("""
						SELECT p.*, c.firstname, c.company as contact_company, c.industry
						FROM linkedin_prospects p
						LEFT JOIN contacts c ON p.contact_id = c.id
						WHERE p.id = ?
				""", (prospect_id,)).fetchone()
			
				template = conn.execute("""
						SELECT message_body FROM linkedin_message_templates
						WHERE template_name = ?
				""", (template_name,)).fetchone()
			
				conn.close()
			
				if not prospect or not template:
						return None
			
				# Personalize message
				message = template['message_body']
				replacements = {
						'{firstname}': prospect['firstname'] or prospect['profile_name'] or 'there',
						'{company}': prospect['company'] or prospect['contact_company'] or 'your company',
						'{industry}': prospect['industry'] or 'the industry'
				}
			
				for key, value in replacements.items():
						message = message.replace(key, value)
					
				return message
	
		def get_daily_quota_status(self):
				"""Check today's activity against limits"""
			
				conn = sqlite3.connect(self.db_path)
			
				today = datetime.now().strftime('%Y-%m-%d')
			
				quota = {}
				for activity_type, limit in self.DAILY_LIMITS.items():
						count = conn.execute("""
								SELECT COUNT(*) FROM linkedin_activities
								WHERE activity_type = ? 
									AND performed_at LIKE ?
						""", (activity_type, today + '%')).fetchone()[0]
					
					
						quota[activity_type] = {
								'used': count,
								'limit': limit,
								'remaining': max(0, limit - count),
								'percentage': (count / limit * 100) if limit > 0 else 0
						}
					
				conn.close()
				return quota
	
		def schedule_outreach_campaign(self, prospect_ids, campaign_type='standard'):
				"""Schedule automated outreach campaign"""
			
				campaigns = {
						'standard': [
								{'day': 0, 'action': 'connection_request'},
								{'day': 3, 'action': 'follow_up_if_accepted'},
								{'day': 7, 'action': 'value_add_message'},
								{'day': 14, 'action': 'final_touch'}
						],
						'aggressive': [
								{'day': 0, 'action': 'connection_request'},
								{'day': 1, 'action': 'follow_up_if_accepted'},
								{'day': 3, 'action': 'value_add_message'},
								{'day': 7, 'action': 'final_touch'}
						],
						'nurture': [
								{'day': 0, 'action': 'connection_request'},
								{'day': 7, 'action': 'follow_up_if_accepted'},
								{'day': 21, 'action': 'value_add_message'},
								{'day': 45, 'action': 'final_touch'}
						]
				}
			
				campaign = campaigns.get(campaign_type, campaigns['standard'])
			
				conn = sqlite3.connect(self.db_path)
				scheduled = []
			
				for prospect_id in prospect_ids:
						for touch in campaign:
								scheduled_date = datetime.now() + timedelta(days=touch['day'])
							
								# Store in database (you'd implement a scheduler table)
								scheduled.append({
										'prospect_id': prospect_id,
										'action': touch['action'],
										'scheduled_for': scheduled_date.isoformat()
								})
							
				conn.close()
				return scheduled
	
		def get_analytics(self):
				"""Get LinkedIn outreach analytics"""
			
				conn = sqlite3.connect(self.db_path)
			
				stats = {
						'total_prospects': conn.execute("SELECT COUNT(*) FROM linkedin_prospects").fetchone()[0],
						'connection_requests_sent': conn.execute("""
								SELECT COUNT(*) FROM linkedin_prospects 
								WHERE connection_request_sent IS NOT NULL
						""").fetchone()[0],
						'connections_accepted': conn.execute("""
								SELECT COUNT(*) FROM linkedin_prospects 
								WHERE connection_status = 'connected'
						""").fetchone()[0],
						'messages_sent': conn.execute("""
								SELECT COUNT(*) FROM linkedin_activities 
								WHERE activity_type = 'messages'
						""").fetchone()[0],
						'responses_received': conn.execute("""
								SELECT COUNT(*) FROM linkedin_prospects 
								WHERE last_engaged IS NOT NULL
						""").fetchone()[0]
				}
			
				# Calculate rates
				if stats['connection_requests_sent'] > 0:
						stats['acceptance_rate'] = (stats['connections_accepted'] / stats['connection_requests_sent'] * 100)
				else:
						stats['acceptance_rate'] = 0
					
				if stats['messages_sent'] > 0:
						stats['response_rate'] = (stats['responses_received'] / stats['messages_sent'] * 100)
				else:
						stats['response_rate'] = 0
					
				conn.close()
				return stats
	
		def get_pending_actions(self):
				"""Get today's pending LinkedIn actions"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				# Get prospects ready for connection requests
				quota = self.get_daily_quota_status()
			
				pending = {
						'connection_requests': [],
						'follow_ups': [],
						'value_adds': []
				}
			
				if quota['connection_requests']['remaining'] > 0:
						prospects = conn.execute("""
								SELECT * FROM linkedin_prospects
								WHERE connection_request_sent IS NULL
									AND connection_status = 'not_connected'
								LIMIT ?
						""", (quota['connection_requests']['remaining'],)).fetchall()
					
						pending['connection_requests'] = [dict(p) for p in prospects]
					
				conn.close()
				return pending
	
	
# CLI
if __name__ == "__main__":
		import sys
	
		linkedin = LinkedInAutomation()
	
		if len(sys.argv) < 2:
				print("""
╔══════════════════════════════════════════════════════════════╗
║            LINKEDIN AUTOMATION ENGINE                         ║
║     Safe, Compliant Outreach at Scale                         ║
╚══════════════════════════════════════════════════════════════╝

Usage:
	python linkedin_automation.py add <linkedin_url> [contact_id]
	python linkedin_automation.py quota
	python linkedin_automation.py pending
	python linkedin_automation.py analytics
	python linkedin_automation.py message <prospect_id>

Examples:
	python linkedin_automation.py add "https://linkedin.com/in/johnsmith"
	python linkedin_automation.py quota
	python linkedin_automation.py pending
""")
				sys.exit(1)
			
		command = sys.argv[1]
	
		if command == 'add':
				url = sys.argv[2]
				contact_id = int(sys.argv[3]) if len(sys.argv) > 3 else None
			
				result = linkedin.add_prospect(url, contact_id)
				if result['success']:
						print(f"✅ Prospect added! ID: {result['prospect_id']}")
				else:
						print(f"❌ {result['error']}")
					
		elif command == 'quota':
				quota = linkedin.get_daily_quota_status()
			
				print("\n📊 Today's LinkedIn Quota:\n")
				for activity, stats in quota.items():
						print(f"{activity.replace('_', ' ').title()}: {stats['used']}/{stats['limit']} ({stats['remaining']} remaining)")
				print()
			
		elif command == 'pending':
				pending = linkedin.get_pending_actions()
			
				print("\n📋 Pending LinkedIn Actions:\n")
				print(f"Connection Requests: {len(pending['connection_requests'])}")
				print(f"Follow-ups: {len(pending['follow_ups'])}")
				print(f"Value-Add Messages: {len(pending['value_adds'])}")
				print()
			
		elif command == 'analytics':
				stats = linkedin.get_analytics()
			
				print("\n📈 LinkedIn Analytics:\n")
				print(f"Total Prospects: {stats['total_prospects']}")
				print(f"Connection Requests Sent: {stats['connection_requests_sent']}")
				print(f"Connections Accepted: {stats['connections_accepted']}")
				print(f"Acceptance Rate: {stats['acceptance_rate']:.1f}%")
				print(f"Messages Sent: {stats['messages_sent']}")
				print(f"Responses: {stats['responses_received']}")
				print(f"Response Rate: {stats['response_rate']:.1f}%")
				print()
			
		elif command == 'message':
				prospect_id = int(sys.argv[2])
				message = linkedin.generate_connection_message(prospect_id)
			
				if message:
						print("\n📝 Generated Message:\n")
						print(message)
						print()
				else:
						print("❌ Could not generate message")
					