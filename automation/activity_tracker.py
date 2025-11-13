#!/usr/bin/env python3

# activity_tracker.py - Complete activity logging system

import sqlite3
from datetime import datetime, timezone
from typing import Optional

class ActivityTracker:
		"""Track all sales activities and engagement"""
	
		def __init__(self, db_path='sales_angel.db'):
				self.db_path = db_path
				self._init_tables()
			
		def _init_tables(self):
				"""Create activities table if it doesn't exist"""
				conn = sqlite3.connect(self.db_path)
				conn.execute("""
						CREATE TABLE IF NOT EXISTS activities (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								contact_id INTEGER NOT NULL,
								activity_type TEXT NOT NULL,
								variant_used INTEGER,
								channel TEXT,
								status TEXT,
								message TEXT,
								metadata TEXT,
								created_at TEXT NOT NULL,
								FOREIGN KEY (contact_id) REFERENCES contacts(id)
						)
				""")
			
				# Create index for fast queries
				conn.execute("""
						CREATE INDEX IF NOT EXISTS idx_activities_contact 
						ON activities(contact_id, created_at DESC)
				""")
				conn.commit()
				conn.close()
			
		def log(self, contact_id: int, activity_type: str, 
						variant: Optional[int] = None, channel: str = 'email',
						status: str = 'completed', message: str = '', metadata: str = ''):
				"""Log a sales activity"""
			
				conn = sqlite3.connect(self.db_path)
				conn.execute("""
						INSERT INTO activities 
						(contact_id, activity_type, variant_used, channel, status, message, metadata, created_at)
						VALUES (?, ?, ?, ?, ?, ?, ?, ?)
				""", (contact_id, activity_type, variant, channel, status, message, metadata,
							datetime.now(timezone.utc).isoformat()))
				conn.commit()
				conn.close()
			
				print(f"✅ Logged {activity_type} for contact {contact_id}")
			
		def get_activities(self, contact_id: int, limit: int = 50):
				"""Get recent activities for a contact"""
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				activities = conn.execute("""
						SELECT * FROM activities 
						WHERE contact_id = ? 
						ORDER BY created_at DESC 
						LIMIT ?
				""", (contact_id, limit)).fetchall()
			
				conn.close()
				return [dict(a) for a in activities]
	
		def get_stats(self):
				"""Get overall activity statistics"""
				conn = sqlite3.connect(self.db_path)
			
				stats = {
						'total_activities': conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0],
						'by_type': dict(conn.execute("""
								SELECT activity_type, COUNT(*) 
								FROM activities 
								GROUP BY activity_type
						""").fetchall()),
						'by_channel': dict(conn.execute("""
								SELECT channel, COUNT(*) 
								FROM activities 
								GROUP BY channel
						""").fetchall()),
						'by_status': dict(conn.execute("""
								SELECT status, COUNT(*) 
								FROM activities 
								GROUP BY status
						""").fetchall())
				}
			
				conn.close()
				return stats
	
		def get_response_rate(self):
				"""Calculate email response rate"""
				conn = sqlite3.connect(self.db_path)
			
				sent = conn.execute("""
						SELECT COUNT(DISTINCT contact_id) 
						FROM activities 
						WHERE activity_type = 'email_sent'
				""").fetchone()[0]
			
				replied = conn.execute("""
						SELECT COUNT(DISTINCT contact_id) 
						FROM activities 
						WHERE activity_type IN ('reply_received', 'meeting_booked')
				""").fetchone()[0]
			
				conn.close()
			
				return {
						'sent': sent,
						'replied': replied,
						'rate': (replied / sent * 100) if sent > 0 else 0
				}
	
	
# CLI Interface
if __name__ == "__main__":
		import sys
	
		tracker = ActivityTracker()
	
		if len(sys.argv) < 3:
				print("""
Activity Tracker CLI

Usage:
	python activity_tracker.py log <contact_id> <type> [variant] [message]
	python activity_tracker.py view <contact_id>
	python activity_tracker.py stats

Examples:
	python activity_tracker.py log 157153 email_sent 1 "Sent variant 1"
	python activity_tracker.py log 157153 reply_received 0 "Positive response"
	python activity_tracker.py view 157153
	python activity_tracker.py stats
""")
				sys.exit(1)
			
		command = sys.argv[1]
	
		if command == 'log':
				contact_id = int(sys.argv[2])
				activity_type = sys.argv[3]
				variant = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else None
				message = ' '.join(sys.argv[5:]) if len(sys.argv) > 5 else ''
			
				tracker.log(contact_id, activity_type, variant=variant, message=message)
			
		elif command == 'view':
				contact_id = int(sys.argv[2])
				activities = tracker.get_activities(contact_id)
			
				print(f"\n📊 Activity History for Contact {contact_id}")
				print("="*70)
				for a in activities:
						print(f"{a['created_at'][:19]} | {a['activity_type']:20s} | {a['message']}")
					
		elif command == 'stats':
				stats = tracker.get_stats()
				response = tracker.get_response_rate()
			
				print("\n📊 ACTIVITY STATISTICS")
				print("="*70)
				print(f"\nTotal Activities: {stats['total_activities']}")
			
				print("\nBy Type:")
				for type, count in stats['by_type'].items():
						print(f"  {type}: {count}")
					
				print("\nBy Channel:")
				for channel, count in stats['by_channel'].items():
						print(f"  {channel}: {count}")
					
				print("\n📧 Response Rate:")
				print(f"  Sent: {response['sent']}")
				print(f"  Replied: {response['replied']}")
				print(f"  Rate: {response['rate']:.1f}%")
				print()
			