#!/usr/bin/env python3

# meeting_scheduler.py - Calendar integration

from datetime import datetime, timedelta
import sqlite3

class MeetingScheduler:
	"""Smart meeting scheduling"""
	
	def __init__(self, db_path='sales_angel.db'):
		self.db_path = db_path
		self._init_tables()
		
	def _init_tables(self):
		conn = sqlite3.connect(self.db_path)
		conn.execute("""
			CREATE TABLE IF NOT EXISTS meetings (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				contact_id INTEGER NOT NULL,
				title TEXT NOT NULL,
				scheduled_at TEXT NOT NULL,
				duration_minutes INTEGER DEFAULT 30,
				location TEXT,
				meeting_link TEXT,
				notes TEXT,
				status TEXT DEFAULT 'scheduled',
				created_at TEXT NOT NULL,
				FOREIGN KEY (contact_id) REFERENCES contacts(id)
			)
		""")
		conn.commit()
		conn.close()
		
	def propose_times(self, contact_id, num_options=3):
		"""Propose meeting times based on best practices"""
		
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		
		contact = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
		conn.close()
		
		if not contact:
			return []
		
		# Smart time selection based on tier
		base_time = datetime.now() + timedelta(days=1)
		
		# HOT contacts: Next day, early slots
		# WARM: 2-3 days out
		# Others: Next week
		
		if contact['tier'] == 'HOT':
			days_out = [1, 2, 2]
			hours = [10, 14, 16]  # 10am, 2pm, 4pm
		elif contact['tier'] == 'WARM':
			days_out = [2, 3, 4]
			hours = [10, 14, 15]
		else:
			days_out = [5, 7, 7]
			hours = [11, 14, 15]
			
		options = []
		for i in range(num_options):
			time = base_time + timedelta(days=days_out[i])
			time = time.replace(hour=hours[i], minute=0, second=0, microsecond=0)
			
			# Skip weekends
			while time.weekday() >= 5:
				time += timedelta(days=1)
				
			options.append({
				'datetime': time,
				'formatted': time.strftime('%A, %B %d at %I:%M %p'),
				'priority': i + 1
			})
			
		return options
	
	def book_meeting(self, contact_id, scheduled_at, title=None, duration=30, location='Video Call'):
		"""Book a meeting"""
		
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		
		contact = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
		
		if not contact:
			conn.close()
			return None
		
		if not title:
			title = f"Sales Meeting - {contact['firstname']} {contact['lastname']}"
			
		# Generate Zoom/Gmeet link (placeholder)
		meeting_link = f"https://zoom.us/j/{contact_id}{int(datetime.now().timestamp())}"
		
		conn.execute("""
			INSERT INTO meetings 
			(contact_id, title, scheduled_at, duration_minutes, location, meeting_link, created_at)
			VALUES (?, ?, ?, ?, ?, ?, ?)
		""", (contact_id, title, scheduled_at, duration, location, meeting_link, 
				datetime.now().isoformat()))
		
		meeting_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
		conn.commit()
		conn.close()
		
		return {
			'id': meeting_id,
			'title': title,
			'scheduled_at': scheduled_at,
			'meeting_link': meeting_link,
			'contact_name': f"{contact['firstname']} {contact['lastname']}"
		}
	
	def get_upcoming(self, days=7):
		"""Get upcoming meetings"""
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		
		cutoff = (datetime.now() + timedelta(days=days)).isoformat()
		
		meetings = conn.execute("""
			SELECT m.*, c.firstname, c.lastname, c.company
			FROM meetings m
			JOIN contacts c ON m.contact_id = c.id
			WHERE m.scheduled_at <= ? AND m.status = 'scheduled'
			ORDER BY m.scheduled_at ASC
		""", (cutoff,)).fetchall()
		
		conn.close()
		return [dict(m) for m in meetings]
	
	def generate_calendar_invite(self, meeting_id):
		"""Generate .ics calendar file"""
		
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		
		meeting = conn.execute("""
			SELECT m.*, c.firstname, c.lastname, c.email
			FROM meetings m
			JOIN contacts c ON m.contact_id = c.id
			WHERE m.id = ?
		""", (meeting_id,)).fetchone()
		
		conn.close()
		
		if not meeting:
			return None
		
		# Simple ICS format
		ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Sales Angel//Meeting//EN
BEGIN:VEVENT
UID:{meeting_id}@salesangel.local
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{meeting['scheduled_at'].replace('-','').replace(':','')[:15]}
DURATION:PT{meeting['duration_minutes']}M
SUMMARY:{meeting['title']}
DESCRIPTION:Meeting with {meeting['firstname']} {meeting['lastname']}\\n{meeting['meeting_link']}
LOCATION:{meeting['location']}
ATTENDEE:mailto:{meeting['email']}
END:VEVENT
END:VCALENDAR"""
		
		filename = f"meeting_{meeting_id}.ics"
		with open(filename, 'w') as f:
			f.write(ics)
			
		return filename
	
# CLI
if __name__ == "__main__":
	import sys
	
	scheduler = MeetingScheduler()
	
	if len(sys.argv) < 2:
		print("Usage: python meeting_scheduler.py <command>")
		print("Commands: propose <contact_id>, book <contact_id> <datetime>, upcoming")
		sys.exit(1)
		
	command = sys.argv[1]
	
	if command == 'propose':
		contact_id = int(sys.argv[2])
		options = scheduler.propose_times(contact_id)
		
		print(f"\n🗓️  Proposed Meeting Times for Contact {contact_id}:\n")
		for i, opt in enumerate(options, 1):
			print(f"{i}. {opt['formatted']}")
		print()
		
	elif command == 'upcoming':
		meetings = scheduler.get_upcoming()
		print(f"\n📅 Upcoming Meetings ({len(meetings)}):\n")
		for m in meetings:
			print(f"• {m['title']}")
			print(f"  {m['scheduled_at']} with {m['firstname']} {m['lastname']}")
			print(f"  Link: {m['meeting_link']}\n")
			