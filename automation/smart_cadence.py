#!/usr/bin/env python3

# smart_cadence.py - Automated outreach cadences

import sqlite3
from datetime import datetime, timezone, timedelta
from activity_tracker import ActivityTracker

class SmartCadence:
		"""Automated sales cadences with intelligent scheduling"""
	
		CADENCES = {
				'quick': {
						'name': 'Quick Follow-up',
						'steps': [
								{'day': 0, 'action': 'email', 'variant': 1},
								{'day': 2, 'action': 'email', 'variant': 2},
								{'day': 5, 'action': 'call', 'variant': 1},
								{'day': 7, 'action': 'email', 'variant': 3}
						]
				},
				'standard': {
						'name': 'Standard Nurture',
						'steps': [
								{'day': 0, 'action': 'email', 'variant': 1},
								{'day': 3, 'action': 'email', 'variant': 2},
								{'day': 7, 'action': 'call', 'variant': 1},
								{'day': 10, 'action': 'email', 'variant': 3},
								{'day': 14, 'action': 'call', 'variant': 2}
						]
				},
				'aggressive': {
						'name': 'Aggressive Outreach',
						'steps': [
								{'day': 0, 'action': 'email', 'variant': 1},
								{'day': 1, 'action': 'call', 'variant': 1},
								{'day': 3, 'action': 'email', 'variant': 2},
								{'day': 5, 'action': 'call', 'variant': 2},
								{'day': 7, 'action': 'email', 'variant': 3},
								{'day': 10, 'action': 'call', 'variant': 3}
						]
				}
		}
	
		def __init__(self, db_path='sales_angel.db'):
				self.db_path = db_path
				self.tracker = ActivityTracker(db_path)
				self._init_tables()
			
		def _init_tables(self):
				"""Create cadence tracking table"""
				conn = sqlite3.connect(self.db_path)
				conn.execute("""
						CREATE TABLE IF NOT EXISTS cadences (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								contact_id INTEGER NOT NULL,
								cadence_type TEXT NOT NULL,
								current_step INTEGER DEFAULT 0,
								status TEXT DEFAULT 'active',
								started_at TEXT NOT NULL,
								last_action_at TEXT,
								completed_at TEXT,
								FOREIGN KEY (contact_id) REFERENCES contacts(id)
						)
				""")
				conn.commit()
				conn.close()
			
		def start(self, contact_id: int, cadence_type: str = 'standard'):
				"""Start a cadence for a contact"""
			
				if cadence_type not in self.CADENCES:
						print(f"❌ Unknown cadence type: {cadence_type}")
						return False
			
				conn = sqlite3.connect(self.db_path)
			
				# Check if already in a cadence
				existing = conn.execute("""
						SELECT id FROM cadences 
						WHERE contact_id = ? AND status = 'active'
				""", (contact_id,)).fetchone()
			
				if existing:
						print(f"⚠️  Contact {contact_id} already in active cadence")
						conn.close()
						return False
			
				# Start new cadence
				conn.execute("""
						INSERT INTO cadences (contact_id, cadence_type, started_at)
						VALUES (?, ?, ?)
				""", (contact_id, cadence_type, datetime.now(timezone.utc).isoformat()))
			
				conn.commit()
				conn.close()
			
				print(f"✅ Started {self.CADENCES[cadence_type]['name']} for contact {contact_id}")
			
				# Execute first step immediately
				self.execute_next_step(contact_id)
				return True
	
		def execute_next_step(self, contact_id: int):
				"""Execute the next cadence step for a contact"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				cadence = conn.execute("""
						SELECT * FROM cadences 
						WHERE contact_id = ? AND status = 'active'
				""", (contact_id,)).fetchone()
			
				if not cadence:
						conn.close()
						return
			
				cadence_config = self.CADENCES[cadence['cadence_type']]
				current_step = cadence['current_step']
			
				if current_step >= len(cadence_config['steps']):
						# Cadence complete
						conn.execute("""
								UPDATE cadences 
								SET status = 'completed', completed_at = ?
								WHERE id = ?
						""", (datetime.now(timezone.utc).isoformat(), cadence['id']))
						conn.commit()
						conn.close()
						print(f"✅ Cadence completed for contact {contact_id}")
						return
			
				step = cadence_config['steps'][current_step]
			
				# Log the action
				action_type = f"{step['action']}_{'sent' if step['action'] == 'email' else 'attempted'}"
				self.tracker.log(
						contact_id, 
						action_type,
						variant=step['variant'],
						channel=step['action'],
						message=f"Cadence step {current_step + 1}"
				)
			
				# Update cadence
				conn.execute("""
						UPDATE cadences 
						SET current_step = ?, last_action_at = ?
						WHERE id = ?
				""", (current_step + 1, datetime.now(timezone.utc).isoformat(), cadence['id']))
			
				conn.commit()
				conn.close()
			
				print(f"✅ Executed step {current_step + 1}: {step['action']} (variant {step['variant']})")
			
		def check_due_actions(self):
				"""Check for and execute any due cadence actions"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				active_cadences = conn.execute("""
						SELECT * FROM cadences WHERE status = 'active'
				""").fetchall()
			
				conn.close()
			
				executed = 0
				for cadence in active_cadences:
						cadence_config = self.CADENCES[cadence['cadence_type']]
						current_step = cadence['current_step']
					
						if current_step >= len(cadence_config['steps']):
								continue
					
						step = cadence_config['steps'][current_step]
						started = datetime.fromisoformat(cadence['started_at'])
						last_action = datetime.fromisoformat(cadence['last_action_at']) if cadence['last_action_at'] else started
					
						days_since_last = (datetime.now(timezone.utc) - last_action).days
					
						if days_since_last >= step['day']:
								self.execute_next_step(cadence['contact_id'])
								executed += 1
							
				return executed
	
		def stop(self, contact_id: int, reason: str = 'manual_stop'):
				"""Stop an active cadence"""
			
				conn = sqlite3.connect(self.db_path)
				conn.execute("""
						UPDATE cadences 
						SET status = ?, completed_at = ?
						WHERE contact_id = ? AND status = 'active'
				""", (reason, datetime.now(timezone.utc).isoformat(), contact_id))
				conn.commit()
				conn.close()
			
				print(f"✅ Stopped cadence for contact {contact_id} (reason: {reason})")
			
			
# CLI Interface
if __name__ == "__main__":
		import sys
	
		cadence = SmartCadence()
	
		if len(sys.argv) < 2:
				print("""
Smart Cadence CLI

Usage:
	python smart_cadence.py start <contact_id> [type]
	python smart_cadence.py stop <contact_id>
	python smart_cadence.py check
	python smart_cadence.py list

Cadence Types:
	quick      - 4 touches over 7 days
	standard   - 5 touches over 14 days (default)
	aggressive - 6 touches over 10 days

Examples:
	python smart_cadence.py start 157153 standard
	python smart_cadence.py check
	python smart_cadence.py stop 157153
""")
				sys.exit(1)
			
		command = sys.argv[1]
	
		if command == 'start':
				contact_id = int(sys.argv[2])
				cadence_type = sys.argv[3] if len(sys.argv) > 3 else 'standard'
				cadence.start(contact_id, cadence_type)
			
		elif command == 'stop':
				contact_id = int(sys.argv[2])
				cadence.stop(contact_id)
			
		elif command == 'check':
				executed = cadence.check_due_actions()
				print(f"\n✅ Executed {executed} pending cadence actions")
			
		elif command == 'list':
				conn = sqlite3.connect('sales_angel.db')
				conn.row_factory = sqlite3.Row
				active = conn.execute("""
						SELECT c.*, con.firstname, con.lastname 
						FROM cadences c
						JOIN contacts con ON c.contact_id = con.id
						WHERE c.status = 'active'
				""").fetchall()
				conn.close()
			
				print(f"\n📊 Active Cadences: {len(active)}")
				for row in active:
						print(f"  {row['firstname']} {row['lastname']} - {row['cadence_type']} (step {row['current_step']})")
					