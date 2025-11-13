#!/usr/bin/env python3

import sqlite3
from datetime import datetime, timezone, timedelta
import time
try:
	from notification_engine import NotificationEngine
except:
	NotificationEngine = None
	
try:
	from gmail_connector import GmailConnector
except:
	GmailConnector = None# auto_sequence_engine.py - STANDALONE VERSION
	
import sqlite3
from datetime import datetime, timezone, timedelta
import time

class AutoSequenceEngine:
	"""Automated multi-touch sales sequences - standalone"""
	
	SEQUENCES = {
		'aggressive': {
			'name': 'Aggressive Outreach (7 days)',
			'touches': [
				{'day': 0, 'type': 'email', 'variant': 1},
				{'day': 1, 'type': 'call', 'variant': 1},
				{'day': 3, 'type': 'email', 'variant': 2},
				{'day': 5, 'type': 'call', 'variant': 2},
				{'day': 7, 'type': 'email', 'variant': 3},
			]
		},
		'standard': {
			'name': 'Standard Follow-Up (14 days)',
			'touches': [
				{'day': 0, 'type': 'email', 'variant': 1},
				{'day': 3, 'type': 'email', 'variant': 2},
				{'day': 7, 'type': 'call', 'variant': 1},
				{'day': 10, 'type': 'email', 'variant': 3},
				{'day': 14, 'type': 'call', 'variant': 2},
			]
		},
		'nurture': {
			'name': 'Long-Term Nurture (30 days)',
			'touches': [
				{'day': 0, 'type': 'email', 'variant': 1},
				{'day': 7, 'type': 'email', 'variant': 2},
				{'day': 14, 'type': 'call', 'variant': 1},
				{'day': 21, 'type': 'email', 'variant': 3},
				{'day': 30, 'type': 'call', 'variant': 2},
			]
		}
	}
	
	def __init__(self, db_path='sales_angel.db'):
		self.db_path = db_path
		self._init_tables()
		
	def _init_tables(self):
		conn = sqlite3.connect(self.db_path)
		conn.execute("""
			CREATE TABLE IF NOT EXISTS sequences (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				contact_id INTEGER NOT NULL,
				sequence_type TEXT NOT NULL,
				status TEXT DEFAULT 'active',
				started_at TEXT NOT NULL,
				current_touch INTEGER DEFAULT 0,
				last_touch_at TEXT,
				completed_at TEXT,
				FOREIGN KEY (contact_id) REFERENCES contacts(id)
			)
		""")
		
		conn.execute("""
			CREATE TABLE IF NOT EXISTS sequence_touches (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				sequence_id INTEGER NOT NULL,
				touch_number INTEGER NOT NULL,
				touch_type TEXT NOT NULL,
				variant_number INTEGER,
				scheduled_for TEXT NOT NULL,
				executed_at TEXT,
				status TEXT DEFAULT 'pending',
				response_received INTEGER DEFAULT 0,
				FOREIGN KEY (sequence_id) REFERENCES sequences(id)
			)
		""")
		
		conn.commit()
		conn.close()
		
	def start_sequence(self, contact_id, sequence_type='standard'):
		"""Start automated sequence for a contact"""
		
		if sequence_type not in self.SEQUENCES:
			return {'error': f'Invalid sequence type: {sequence_type}'}
		
		conn = sqlite3.connect(self.db_path)
		
		# Check if already in sequence
		existing = conn.execute("""
			SELECT id FROM sequences 
			WHERE contact_id = ? AND status = 'active'
		""", (contact_id,)).fetchone()
		
		if existing:
			conn.close()
			return {'error': 'Contact already in active sequence'}
		
		# Create sequence
		now = datetime.now(timezone.utc).isoformat()
		cursor = conn.execute("""
			INSERT INTO sequences (contact_id, sequence_type, started_at)
			VALUES (?, ?, ?)
		""", (contact_id, sequence_type, now))
		
		sequence_id = cursor.lastrowid
		
		# Schedule touches
		sequence = self.SEQUENCES[sequence_type]
		start_date = datetime.now(timezone.utc)
		
		for i, touch in enumerate(sequence['touches'], 1):
			scheduled = start_date + timedelta(days=touch['day'])
			
			conn.execute("""
				INSERT INTO sequence_touches 
				(sequence_id, touch_number, touch_type, variant_number, scheduled_for)
				VALUES (?, ?, ?, ?, ?)
			""", (sequence_id, i, touch['type'], touch.get('variant'), scheduled.isoformat()))
			
		conn.commit()
		conn.close()
		
		return {
	'sequence_id': sequence_id,
	'type': sequence_type,
	'touches_scheduled': len(sequence['touches'])
	}
	
	def get_pending_touches(self):
		"""Get all pending touches"""
		
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		
		now = datetime.now(timezone.utc).isoformat()
		
		pending = conn.execute("""
			SELECT t.*, s.contact_id, s.sequence_type,
					c.firstname, c.lastname, c.company, c.email
			FROM sequence_touches t
			JOIN sequences s ON t.sequence_id = s.id
			JOIN contacts c ON s.contact_id = c.id
			WHERE t.status = 'pending'
				AND t.scheduled_for <= ?
				AND s.status = 'active'
			ORDER BY t.scheduled_for ASC
		""", (now,)).fetchall()
		
		conn.close()
		return [dict(p) for p in pending]
	
	def mark_touch_complete(self, touch_id, status='completed'):
		"""Mark a touch as complete"""
		
		conn = sqlite3.connect(self.db_path)
		
		conn.execute("""
			UPDATE sequence_touches
			SET status = ?, executed_at = ?
			WHERE id = ?
		""", (status, datetime.now(timezone.utc).isoformat(), touch_id))
		
		conn.commit()
		conn.close()
		
	def get_active_sequences(self):
		"""Get all active sequences"""
		
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		
		sequences = conn.execute("""
			SELECT s.*, c.firstname, c.lastname, c.company,
					COUNT(t.id) as total_touches,
					SUM(CASE WHEN t.status != 'pending' THEN 1 ELSE 0 END) as completed_touches
			FROM sequences s
			JOIN contacts c ON s.contact_id = c.id
			LEFT JOIN sequence_touches t ON s.id = t.sequence_id
			WHERE s.status = 'active'
			GROUP BY s.id
		""").fetchall()
		
		conn.close()
		return [dict(s) for s in sequences]
	
	
	# CLI
if __name__ == "__main__":
	import sys
	
	engine = AutoSequenceEngine()
	
	if len(sys.argv) < 2:
		print("Usage: python auto_sequence_engine.py [start|list|pending] ...")
		sys.exit(1)
		
	command = sys.argv[1]
	
	if command == 'start':
		contact_id = int(sys.argv[2])
		seq_type = sys.argv[3] if len(sys.argv) > 3 else 'standard'
		
		result = engine.start_sequence(contact_id, seq_type)
		
		if 'error' in result:
			print(f"❌ {result['error']}")
		else:
			print(f"✅ Sequence started for contact {contact_id}!")
			print(f"   Type: {seq_type}")
			print(f"   Touches: {result['touches_scheduled']}")
			
	elif command == 'pending':
		touches = engine.get_pending_touches()
		
		print(f"\n📋 Pending Touches ({len(touches)}):\n")
		for t in touches:
			print(f"  {t['touch_type'].upper()}: {t['firstname']} {t['lastname']} ({t['company']})")
			print(f"    Scheduled: {t['scheduled_for'][:10]}")
			print(f"    Variant: {t['variant_number']}")
			print()
			
	elif command == 'list':
		sequences = engine.get_active_sequences()
		
		print(f"\n📊 Active Sequences ({len(sequences)}):\n")
		for s in sequences:
			progress = f"{s['completed_touches']}/{s['total_touches']}"
			print(f"  {s['firstname']} {s['lastname']} - {s['sequence_type']}")
			print(f"    Progress: {progress}")
			print()


class AutoSequenceEngine:
		"""Automated multi-touch sales sequences"""
	
		SEQUENCES = {
				'aggressive': {
						'name': 'Aggressive Outreach (7 days)',
						'touches': [
								{'day': 0, 'type': 'email', 'variant': 1},
								{'day': 1, 'type': 'call', 'variant': 1},
								{'day': 3, 'type': 'email', 'variant': 2},
								{'day': 5, 'type': 'call', 'variant': 2},
								{'day': 7, 'type': 'email', 'variant': 3},
						]
				},
				'standard': {
						'name': 'Standard Follow-Up (14 days)',
						'touches': [
								{'day': 0, 'type': 'email', 'variant': 1},
								{'day': 3, 'type': 'email', 'variant': 2},
								{'day': 7, 'type': 'call', 'variant': 1},
								{'day': 10, 'type': 'email', 'variant': 3},
								{'day': 14, 'type': 'call', 'variant': 2},
						]
				},
				'nurture': {
						'name': 'Long-Term Nurture (30 days)',
						'touches': [
								{'day': 0, 'type': 'email', 'variant': 1},
								{'day': 7, 'type': 'email', 'variant': 2},
								{'day': 14, 'type': 'call', 'variant': 1},
								{'day': 21, 'type': 'email', 'variant': 3},
								{'day': 30, 'type': 'call', 'variant': 2},
						]
				}
		}
	
		def __init__(self, db_path='sales_angel.db'):
				self.db_path = db_path
				self.notif = NotificationEngine() if NotificationEngine else None if NotificationEngine else None
				self._init_tables()
			
		def _init_tables(self):
				conn = sqlite3.connect(self.db_path)
				conn.execute("""
						CREATE TABLE IF NOT EXISTS sequences (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								contact_id INTEGER NOT NULL,
								sequence_type TEXT NOT NULL,
								status TEXT DEFAULT 'active',
								started_at TEXT NOT NULL,
								current_touch INTEGER DEFAULT 0,
								last_touch_at TEXT,
								completed_at TEXT,
								FOREIGN KEY (contact_id) REFERENCES contacts(id)
						)
				""")
			
				conn.execute("""
						CREATE TABLE IF NOT EXISTS sequence_touches (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								sequence_id INTEGER NOT NULL,
								touch_number INTEGER NOT NULL,
								touch_type TEXT NOT NULL,
								variant_number INTEGER,
								scheduled_for TEXT NOT NULL,
								executed_at TEXT,
								status TEXT DEFAULT 'pending',
								response_received INTEGER DEFAULT 0,
								FOREIGN KEY (sequence_id) REFERENCES sequences(id)
						)
				""")
			
				conn.commit()
				conn.close()
			
		def start_sequence(self, contact_id, sequence_type='standard'):
				"""Start automated sequence for a contact"""
			
				if sequence_type not in self.SEQUENCES:
						return {'error': f'Invalid sequence type: {sequence_type}'}
			
				conn = sqlite3.connect(self.db_path)
			
				# Check if already in sequence
				existing = conn.execute("""
						SELECT id FROM sequences 
						WHERE contact_id = ? AND status = 'active'
				""", (contact_id,)).fetchone()
			
				if existing:
						conn.close()
						return {'error': 'Contact already in active sequence'}
			
				# Create sequence
				now = datetime.now(timezone.utc).isoformat()
				cursor = conn.execute("""
						INSERT INTO sequences (contact_id, sequence_type, started_at)
						VALUES (?, ?, ?)
				""", (contact_id, sequence_type, now))
			
				sequence_id = cursor.lastrowid
			
				# Schedule touches
				sequence = self.SEQUENCES[sequence_type]
				start_date = datetime.now(timezone.utc)
			
				for i, touch in enumerate(sequence['touches'], 1):
						scheduled = start_date + timedelta(days=touch['day'])
					
						conn.execute("""
								INSERT INTO sequence_touches 
								(sequence_id, touch_number, touch_type, variant_number, scheduled_for)
								VALUES (?, ?, ?, ?, ?)
						""", (sequence_id, i, touch['type'], touch.get('variant'), scheduled.isoformat()))
					
				conn.commit()
				conn.close()
			
				# Notification
				self.notif.create_notification(
						'sequence',
						f"🎯 Sequence Started",
						f"Contact {contact_id} added to {sequence['name']}",
						contact_id,
						'normal'
				)
			
				return {
						'sequence_id': sequence_id,
						'type': sequence_type,
						'touches_scheduled': len(sequence['touches'])
				}
	
		def execute_pending_touches(self, auto_send=False):
				"""Execute all pending touches that are due"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				# Get pending touches due now
				now = datetime.now(timezone.utc).isoformat()
			
				pending = conn.execute("""
						SELECT t.*, s.contact_id, s.sequence_type
						FROM sequence_touches t
						JOIN sequences s ON t.sequence_id = s.id
						WHERE t.status = 'pending'
							AND t.scheduled_for <= ?
							AND s.status = 'active'
						ORDER BY t.scheduled_for ASC
				""", (now,)).fetchall()
			
				executed = []
			
				for touch in pending:
						# Get contact info
						contact = conn.execute("""
								SELECT * FROM contacts WHERE id = ?
						""", (touch['contact_id'],)).fetchone()
					
						if not contact:
								continue
					
						if touch['touch_type'] == 'email':
								result = self._execute_email_touch(touch, contact, auto_send)
						elif touch['touch_type'] == 'call':
								result = self._execute_call_touch(touch, contact)
						else:
								result = {'status': 'skipped'}
							
						# Mark as executed
						conn.execute("""
								UPDATE sequence_touches
								SET status = ?, executed_at = ?
								WHERE id = ?
						""", (result['status'], datetime.now(timezone.utc).isoformat(), touch['id']))
					
						# Update sequence
						conn.execute("""
								UPDATE sequences
								SET current_touch = ?, last_touch_at = ?
								WHERE id = ?
						""", (touch['touch_number'], datetime.now(timezone.utc).isoformat(), touch['sequence_id']))
					
						executed.append({
								'touch_id': touch['id'],
								'contact_id': touch['contact_id'],
								'type': touch['touch_type'],
								'result': result
						})
					
				conn.commit()
				conn.close()
			
				return executed
	
		def _execute_email_touch(self, touch, contact, auto_send=False):
				"""Execute an email touch"""
			
				variant = touch['variant_number'] or 1
				subject = contact[f'email_{variant}_subject']
				body = contact[f'email_{variant}_body']
			
				if not subject or not body:
						return {'status': 'failed', 'reason': 'No email content'}
			
				if auto_send:
						# Actually send via Gmail
						try:
								gmail = GmailConnector()
								result = gmail.send_email(contact['email'], subject, body)
							
								if result['status'] == 'success':
										self.notif.create_notification(
												'sequence_sent',
												f"📧 Auto-Sent: {contact['firstname']} {contact['lastname']}",
												f"Sent email variant {variant}",
												contact['id'],
												'normal'
										)
										return {'status': 'sent', 'method': 'gmail'}
								else:
										return {'status': 'failed', 'reason': result['message']}
						except:
								return {'status': 'failed', 'reason': 'Gmail not configured'}
				else:
						# Just notify - manual send required
						self.notif.create_notification(
								'sequence_ready',
								f"📧 Ready to Send: {contact['firstname']} {contact['lastname']}",
								f"Email variant {variant} ready - send manually",
								contact['id'],
								'high'
						)
						return {'status': 'ready', 'method': 'manual'}
			
		def _execute_call_touch(self, touch, contact):
				"""Execute a call touch"""
			
				variant = touch['variant_number'] or 1
			
				# Create high-priority notification
				self.notif.create_notification(
						'sequence_call',
						f"📞 Call Due: {contact['firstname']} {contact['lastname']}",
						f"Use call script {variant} - python call_assistant.py {contact['id']} {variant}",
						contact['id'],
						'high'
				)
			
				return {'status': 'notified', 'method': 'manual'}
	
		def get_active_sequences(self):
				"""Get all active sequences"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				sequences = conn.execute("""
						SELECT s.*, c.firstname, c.lastname, c.company,
										COUNT(t.id) as total_touches,
										SUM(CASE WHEN t.status = 'sent' THEN 1 ELSE 0 END) as completed_touches
						FROM sequences s
						JOIN contacts c ON s.contact_id = c.id
						LEFT JOIN sequence_touches t ON s.id = t.sequence_id
						WHERE s.status = 'active'
						GROUP BY s.id
				""").fetchall()
			
				conn.close()
				return [dict(s) for s in sequences]
	
		def check_responses(self):
				"""Check for responses and pause sequences"""
			
				# This would integrate with email tracking/Gmail API
				# For now, manual marking
				pass
			
		def get_dashboard_summary(self):
				"""Get summary for dashboard"""
			
				conn = sqlite3.connect(self.db_path)
			
				summary = {
						'active_sequences': conn.execute("SELECT COUNT(*) FROM sequences WHERE status = 'active'").fetchone()[0],
						'pending_touches': conn.execute("SELECT COUNT(*) FROM sequence_touches WHERE status = 'pending'").fetchone()[0],
						'touches_today': conn.execute("""
								SELECT COUNT(*) FROM sequence_touches 
								WHERE DATE(scheduled_for) = DATE('now')
									AND status = 'pending'
						""").fetchone()[0]
				}
			
				conn.close()
				return summary
	
	
# CLI
if __name__ == "__main__":
		import sys
	
		engine = AutoSequenceEngine()
	
		if len(sys.argv) < 2:
				print("""
╔══════════════════════════════════════════════════════════════╗
║            AUTO-SEQUENCE ENGINE                               ║
║     Set It and Forget It Sales Automation                     ║
╚══════════════════════════════════════════════════════════════╝

Usage:
	python auto_sequence_engine.py start <contact_id> <type>
	python auto_sequence_engine.py execute [--auto-send]
	python auto_sequence_engine.py list
	python auto_sequence_engine.py summary

Sequence Types:
	aggressive  - 7-day,  5 touches (best for hot leads)
	standard    - 14-day, 5 touches (balanced approach)
	nurture     - 30-day, 5 touches (long-term relationships)

Examples:
	python auto_sequence_engine.py start 157153 aggressive
	python auto_sequence_engine.py execute
	python auto_sequence_engine.py execute --auto-send  # Gmail configured
""")
				sys.exit(1)
			
		command = sys.argv[1]
	
		if command == 'start':
				contact_id = int(sys.argv[2])
				seq_type = sys.argv[3] if len(sys.argv) > 3 else 'standard'
			
				result = engine.start_sequence(contact_id, seq_type)
			
				if 'error' in result:
						print(f"❌ {result['error']}")
				else:
						print(f"✅ Sequence started!")
						print(f"   Type: {seq_type}")
						print(f"   Touches scheduled: {result['touches_scheduled']}")
					
		elif command == 'execute':
				auto_send = '--auto-send' in sys.argv
			
				print("\n🤖 Executing pending touches...\n")
				executed = engine.execute_pending_touches(auto_send=auto_send)
			
				print(f"✅ Executed {len(executed)} touches\n")
				for touch in executed:
						print(f"  • Contact {touch['contact_id']}: {touch['type']} - {touch['result']['status']}")
					
		elif command == 'list':
				sequences = engine.get_active_sequences()
			
				print(f"\n📋 Active Sequences ({len(sequences)}):\n")
				for seq in sequences:
						progress = f"{seq['completed_touches']}/{seq['total_touches']}"
						print(f"  {seq['firstname']} {seq['lastname']} ({seq['company']})")
						print(f"    Type: {seq['sequence_type']} | Progress: {progress}")
						print()
					
		elif command == 'summary':
				summary = engine.get_dashboard_summary()
			
				print("\n📊 Sequence Summary\n")
				print(f"  Active Sequences: {summary['active_sequences']}")
				print(f"  Pending Touches:  {summary['pending_touches']}")
				print(f"  Due Today:        {summary['touches_today']}")
				print()