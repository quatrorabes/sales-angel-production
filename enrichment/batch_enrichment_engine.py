#!/usr/bin/env python3

# batch_enrichment_engine.py - Scale enrichment intelligently

import sqlite3
import os
import time
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

load_dotenv()

class BatchEnrichmentEngine:
		"""Intelligent batch enrichment with cost control and prioritization"""
	
		def __init__(self, db_path='sales_angel.db'):
				self.db_path = db_path
				self.api_key = os.getenv('PERPLEXITY_API_KEY')
				self.base_url = "https://api.perplexity.ai/chat/completions"
				self.model = "sonar-pro"
			
				# Cost tracking
				self.cost_per_enrichment = 0.15  # $0.15 per contact
				self.max_budget = 10.00  # Max $10 per batch
			
		def get_top_unenriched(self, limit=50):
				"""Get highest-priority unenriched contacts"""
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				contacts = conn.execute("""
						SELECT id, firstname, lastname, company, jobtitle, email, phone,
										score, tier, linkedin_url
						FROM contacts 
						WHERE enriched = 0 
							AND score IS NOT NULL
							AND score > 40
						ORDER BY score DESC, tier ASC
						LIMIT ?
				""", (limit,)).fetchall()
			
				conn.close()
				return [dict(c) for c in contacts]
	
		def enrich_contact(self, contact):
				"""Enrich a single contact using Perplexity"""
			
				name = f"{contact['firstname']} {contact['lastname']}"
				company = contact['company']
				title = contact['jobtitle']
			
				prompt = f"""Research {name}, {title} at {company}.

Provide:
1. Professional background (2-3 sentences)
2. Company overview (2-3 sentences)
3. Key talking points for outreach (3-4 bullets)
4. Communication style (formal/casual, data-driven/relationship-focused)

Be concise. Focus on sales-relevant information."""
			
				try:
						response = requests.post(
								self.base_url,
								headers={"Authorization": f"Bearer {self.api_key}"},
								json={
										"model": self.model,
										"messages": [{"role": "user", "content": prompt}],
										"max_tokens": 500,
										"temperature": 0.7
								},
								timeout=30
						)
						response.raise_for_status()
					
						content = response.json()['choices'][0]['message']['content']
					
						# Store in database
						conn = sqlite3.connect(self.db_path)
						conn.execute("""
								UPDATE contacts 
								SET profile_content = ?,
										enriched = 1,
										enriched_at = ?,
										model_used = ?
								WHERE id = ?
						""", (content, datetime.now(timezone.utc).isoformat(), self.model, contact['id']))
						conn.commit()
						conn.close()
					
						return True
			
				except Exception as e:
						print(f"  ❌ Error enriching {name}: {str(e)}")
						return False
			
		def batch_enrich(self, count=10, auto_generate=True):
				"""Enrich multiple contacts in batch"""
			
				# Calculate budget
				estimated_cost = count * self.cost_per_enrichment
				if estimated_cost > self.max_budget:
						print(f"⚠️  Estimated cost ${estimated_cost:.2f} exceeds budget ${self.max_budget:.2f}")
						count = int(self.max_budget / self.cost_per_enrichment)
						print(f"   Reducing to {count} contacts (${count * self.cost_per_enrichment:.2f})")
					
				# Get contacts
				contacts = self.get_top_unenriched(count)
			
				if not contacts:
						print("❌ No unenriched contacts with score > 40")
						return
			
				print(f"\n🚀 BATCH ENRICHMENT")
				print(f"={'='*70}")
				print(f"Contacts: {len(contacts)}")
				print(f"Estimated Cost: ${len(contacts) * self.cost_per_enrichment:.2f}")
				print(f"Auto-generate content: {auto_generate}")
				print(f"={'='*70}\n")
			
				enriched = 0
				failed = 0
			
				for i, contact in enumerate(contacts, 1):
						name = f"{contact['firstname']} {contact['lastname']}"
						print(f"[{i}/{len(contacts)}] {name} ({contact['company']}) - Score: {contact['score']}")
					
						if self.enrich_contact(contact):
								enriched += 1
								print(f"  ✅ Enriched")
							
								# Auto-generate content if requested
								if auto_generate:
										print(f"  📧 Generating email variants...")
										os.system(f"python email_variant_generator.py {contact['id']} > /dev/null 2>&1")
										print(f"  📞 Generating call scripts...")
										os.system(f"python call_script_generator.py {contact['id']} > /dev/null 2>&1")
										print(f"  ✅ Content generated")
									
								# Rate limiting
								time.sleep(2)
						else:
								failed += 1
							
						print()
					
				print(f"\n{'='*70}")
				print(f"✅ Batch Complete")
				print(f"{'='*70}")
				print(f"Enriched: {enriched}/{len(contacts)}")
				print(f"Failed: {failed}/{len(contacts)}")
				print(f"Actual Cost: ${enriched * self.cost_per_enrichment:.2f}")
				print(f"New Total Enriched: {self.get_enriched_count()}")
				print(f"{'='*70}\n")
			
		def get_enriched_count(self):
				"""Get total enriched contact count"""
				conn = sqlite3.connect(self.db_path)
				count = conn.execute("SELECT COUNT(*) FROM contacts WHERE enriched = 1").fetchone()[0]
				conn.close()
				return count
	
		def get_stats(self):
				"""Get enrichment statistics"""
				conn = sqlite3.connect(self.db_path)
			
				stats = {
						'total': conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0],
						'enriched': conn.execute("SELECT COUNT(*) FROM contacts WHERE enriched = 1").fetchone()[0],
						'with_score': conn.execute("SELECT COUNT(*) FROM contacts WHERE score IS NOT NULL").fetchone()[0],
						'high_score': conn.execute("SELECT COUNT(*) FROM contacts WHERE score > 60").fetchone()[0],
						'with_content': conn.execute("SELECT COUNT(*) FROM contacts WHERE email_1_subject IS NOT NULL").fetchone()[0]
				}
			
				conn.close()
				return stats
	
	
# CLI Interface
if __name__ == "__main__":
		import sys
	
		engine = BatchEnrichmentEngine()
	
		if len(sys.argv) < 2:
				print("""
╔══════════════════════════════════════════════════════════════╗
║        BATCH ENRICHMENT ENGINE                                ║
║        Scale to 50+ Enriched Contacts                         ║
╚══════════════════════════════════════════════════════════════╝

Usage:
	python batch_enrichment_engine.py enrich <count> [--no-content]
	python batch_enrichment_engine.py stats
	python batch_enrichment_engine.py preview <count>

Examples:
	python batch_enrichment_engine.py enrich 10         # Enrich top 10, generate content
	python batch_enrichment_engine.py enrich 25 --no-content  # Enrich only
	python batch_enrichment_engine.py preview 50        # See who would be enriched
	python batch_enrichment_engine.py stats             # View current stats
""")
				sys.exit(1)
			
		command = sys.argv[1]
	
		if command == 'enrich':
				count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
				auto_generate = '--no-content' not in sys.argv
				engine.batch_enrich(count, auto_generate)
			
		elif command == 'stats':
				stats = engine.get_stats()
				print(f"\n📊 ENRICHMENT STATS")
				print(f"={'='*70}")
				print(f"Total Contacts: {stats['total']}")
				print(f"Enriched: {stats['enriched']} ({stats['enriched']/stats['total']*100:.1f}%)")
				print(f"With Scores: {stats['with_score']}")
				print(f"High Score (>60): {stats['high_score']}")
				print(f"With Content Generated: {stats['with_content']}")
				print(f"={'='*70}\n")
			
		elif command == 'preview':
				count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
				contacts = engine.get_top_unenriched(count)
			
				print(f"\n🔍 TOP {count} UNENRICHED CONTACTS")
				print(f"={'='*70}")
				for i, c in enumerate(contacts, 1):
						print(f"{i:2d}. {c['firstname']} {c['lastname']:20s} | {c['company']:30s} | Score: {c['score']}")
				print(f"={'='*70}")
				print(f"Estimated cost: ${len(contacts) * 0.15:.2f}\n")
			