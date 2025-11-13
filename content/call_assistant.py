#!/usr/bin/env python3

# call_assistant.py - Interactive calling assistant with live script display

import sqlite3
import sys
from datetime import datetime
import os

class CallAssistant:
		"""Live call assistant - displays script as you dial"""
	
		def __init__(self, db_path='sales_angel.db'):
				self.db_path = db_path
			
		def get_contact(self, contact_id):
				"""Get contact info and scripts"""
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				contact = conn.execute("""
						SELECT id, firstname, lastname, company, jobtitle, phone,
										score, tier, profile_content,
										call_script_1, call_script_2, call_script_3
						FROM contacts WHERE id = ?
				""", (contact_id,)).fetchone()
			
				conn.close()
				return dict(contact) if contact else None
	
		def prepare_call(self, contact_id, script_num=1):
				"""Prepare for call - display contact info and script"""
			
				contact = self.get_contact(contact_id)
				if not contact:
						print(f"❌ Contact {contact_id} not found")
						return None
			
				name = f"{contact['firstname']} {contact['lastname']}"
			
				# Clear screen for focus
				os.system('clear' if os.name != 'nt' else 'cls')
			
				# Display call screen
				print("\n" + "="*80)
				print(f"📞 CALL ASSISTANT - {datetime.now().strftime('%I:%M %p')}")
				print("="*80 + "\n")
			
				# Contact header
				print(f"🎯 CALLING: {name}")
				print(f"   {contact['jobtitle']} at {contact['company']}")
				print(f"   📞 {contact['phone']}")
				print(f"   Score: {contact['score']} | Tier: {contact['tier']}")
			
				# Quick context
				if contact['profile_content']:
						context = contact['profile_content'][:200] + "..." if len(contact['profile_content']) > 200 else contact['profile_content']
						print(f"\n💡 Context: {context}")
					
				print("\n" + "="*80)
				print(f"SCRIPT {script_num} - Ready to Read")
				print("="*80 + "\n")
			
				# Display script
				script = contact[f'call_script_{script_num}']
				if script:
						print(script)
				else:
						print("⚠️  No script generated. Generating now...")
						os.system(f"python call_script_generator.py {contact_id}")
						return self.prepare_call(contact_id, script_num)
			
				print("\n" + "="*80)
				print("READY TO DIAL")
				print("="*80 + "\n")
			
				return contact
	
		def call_flow(self, contact_id, script_num=1):
				"""Interactive call workflow"""
			
				contact = self.prepare_call(contact_id, script_num)
				if not contact:
						return
			
				name = f"{contact['firstname']} {contact['lastname']}"
			
				# Prompt to dial
				print("1️⃣  Dial number manually")
				print("2️⃣  Use different script variant")
				print("3️⃣  View profile intelligence")
				print("❌ Cancel\n")
			
				choice = input("Choose action: ").strip()
			
				if choice == '1':
						input("\n✅ Ready to dial? Press ENTER when connected...")
					
						# Post-call logging
						print("\n" + "="*80)
						print("CALL COMPLETE - Log Outcome")
						print("="*80 + "\n")
					
						print("1️⃣  Connected - Good conversation")
						print("2️⃣  Voicemail left")
						print("3️⃣  No answer")
						print("4️⃣  Wrong number / Do not call")
						print("5️⃣  Meeting booked! 🎉")
					
						outcome = input("\nOutcome: ").strip()
						notes = input("Notes: ").strip()
					
						outcomes = {
								'1': 'Connected',
								'2': 'Voicemail',
								'3': 'No Answer',
								'4': 'Wrong Number',
								'5': 'Meeting Booked'
						}
					
						outcome_text = outcomes.get(outcome, 'Call Made')
					
						# Log to tracker
						with open('daily_tracker.csv', 'a', newline='') as f:
								import csv
								writer = csv.writer(f)
								writer.writerow([
										datetime.now().strftime('%Y-%m-%d'),
										name,
										contact['company'],
										'Call',
										script_num,
										outcome_text,
										notes,
										'Follow-up in 2 days' if outcome in ['2', '3'] else 'Next step planned'
								])
							
						print(f"\n✅ Call logged: {outcome_text}")
					
						if outcome == '5':
								print("\n🎉 MEETING BOOKED! Great work!")
								print("Don't forget to:")
								print("  - Send calendar invite")
								print("  - Prepare meeting agenda")
								print("  - Research their specific needs")
							
				elif choice == '2':
						new_script = input("Which script (1-3)? ").strip()
						if new_script in ['1', '2', '3']:
								self.call_flow(contact_id, int(new_script))
							
				elif choice == '3':
						print("\n" + "="*80)
						print("PROFILE INTELLIGENCE")
						print("="*80 + "\n")
						print(contact.get('profile_content', 'No intelligence available'))
						input("\nPress ENTER to return to call screen...")
						self.call_flow(contact_id, script_num)
					
		def quick_dial(self, contact_id):
				"""Quick dial - just show number and basic script"""
				contact = self.get_contact(contact_id)
				if not contact:
						print(f"❌ Contact {contact_id} not found")
						return
			
				print(f"\n📞 {contact['firstname']} {contact['lastname']}")
				print(f"   {contact['phone']}")
				print(f"   {contact['company']}\n")
			
			
# CLI
if __name__ == "__main__":
		assistant = CallAssistant()
	
		if len(sys.argv) < 2:
				print("""
╔══════════════════════════════════════════════════════════════╗
║                    CALL ASSISTANT                             ║
║             Interactive Calling with Live Scripts             ║
╚══════════════════════════════════════════════════════════════╝

Usage:
	python call_assistant.py <contact_id> [script_num]
	python call_assistant.py quick <contact_id>

Examples:
	python call_assistant.py 157153          # Full call flow
	python call_assistant.py 157153 2        # Use script variant 2
	python call_assistant.py quick 157153    # Quick dial info only
""")
				sys.exit(1)
			
		if sys.argv[1] == 'quick':
				contact_id = int(sys.argv[2])
				assistant.quick_dial(contact_id)
		else:
				contact_id = int(sys.argv[1])
				script_num = int(sys.argv[2]) if len(sys.argv) > 2 else 1
				assistant.call_flow(contact_id, script_num)
			