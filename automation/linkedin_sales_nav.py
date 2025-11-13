#!/usr/bin/env python3

# linkedin_sales_nav.py - Sales Navigator Power Features

import sqlite3
from datetime import datetime, timezone
import json
import os

class SalesNavigatorIntegration:
		"""LinkedIn Sales Navigator premium features"""
	
		def __init__(self, db_path='sales_angel.db'):
				self.db_path = db_path
				self._init_tables()
			
		def _init_tables(self):
				conn = sqlite3.connect(self.db_path)
			
				conn.execute("""
						CREATE TABLE IF NOT EXISTS sales_nav_leads (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								contact_id INTEGER,
								linkedin_prospect_id INTEGER,
								sales_nav_lead_id TEXT UNIQUE,
								lead_data JSON,
								last_synced TEXT,
								notes TEXT,
								saved_to_list TEXT,
								FOREIGN KEY (contact_id) REFERENCES contacts(id),
								FOREIGN KEY (linkedin_prospect_id) REFERENCES linkedin_prospects(id)
						)
				""")
			
				conn.execute("""
						CREATE TABLE IF NOT EXISTS sales_nav_insights (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								lead_id INTEGER NOT NULL,
								insight_type TEXT NOT NULL,
								insight_data JSON NOT NULL,
								discovered_at TEXT NOT NULL,
								relevance_score REAL,
								FOREIGN KEY (lead_id) REFERENCES sales_nav_leads(id)
						)
				""")
			
				conn.execute("""
						CREATE TABLE IF NOT EXISTS sales_nav_saved_searches (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								search_name TEXT UNIQUE NOT NULL,
								search_criteria JSON NOT NULL,
								auto_import INTEGER DEFAULT 0,
								last_run TEXT,
								total_results INTEGER DEFAULT 0
						)
				""")
			
				conn.commit()
				conn.close()
			
		def import_sales_nav_lead(self, lead_data, contact_id=None):
				"""Import a lead from Sales Navigator"""
			
				conn = sqlite3.connect(self.db_path)
			
				try:
						conn.execute("""
								INSERT INTO sales_nav_leads 
								(contact_id, sales_nav_lead_id, lead_data, last_synced)
								VALUES (?, ?, ?, ?)
						""", (contact_id, lead_data.get('id'), 
									json.dumps(lead_data), 
									datetime.now(timezone.utc).isoformat()))
					
						lead_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
						conn.commit()
					
						# Extract insights
						self._extract_insights(lead_id, lead_data)
					
						return {'success': True, 'lead_id': lead_id}
			
				except sqlite3.IntegrityError:
						return {'success': False, 'error': 'Lead already imported'}
				finally:
						conn.close()
					
		def _extract_insights(self, lead_id, lead_data):
				"""Extract actionable insights from Sales Nav data"""
			
				insights = []
			
				# Job change insight
				if lead_data.get('tenure_at_current_company'):
						tenure_months = lead_data['tenure_at_current_company']
						if tenure_months <= 6:
								insights.append({
										'type': 'job_change',
										'data': {
												'message': f"New to role - been at {lead_data.get('company')} for {tenure_months} months",
												'relevance': 'HIGH',
												'action': 'Perfect timing for outreach - building new relationships'
										},
										'score': 0.9
								})
							
				# Company growth
				if lead_data.get('company_employee_growth'):
						growth = lead_data['company_employee_growth']
						if growth > 20:
								insights.append({
										'type': 'company_growth',
										'data': {
												'message': f"Company growing rapidly: {growth}% employee growth",
												'relevance': 'HIGH',
												'action': 'Growth = budget = opportunity'
										},
										'score': 0.85
								})
							
				# Recent activity
				if lead_data.get('recent_posts'):
						insights.append({
								'type': 'recent_activity',
								'data': {
										'message': f"Active on LinkedIn - {len(lead_data['recent_posts'])} posts recently",
										'relevance': 'MEDIUM',
										'action': 'Engage with recent content before outreach'
								},
								'score': 0.7
						})
					
				# Shared connections
				if lead_data.get('shared_connections_count', 0) > 0:
						insights.append({
								'type': 'shared_network',
								'data': {
										'message': f"{lead_data['shared_connections_count']} shared connections",
										'relevance': 'MEDIUM',
										'action': 'Request intro or mention shared connection'
								},
								'score': 0.75
						})
					
				# Save insights
				conn = sqlite3.connect(self.db_path)
				for insight in insights:
						conn.execute("""
								INSERT INTO sales_nav_insights 
								(lead_id, insight_type, insight_data, discovered_at, relevance_score)
								VALUES (?, ?, ?, ?, ?)
						""", (lead_id, insight['type'], json.dumps(insight['data']),
									datetime.now(timezone.utc).isoformat(), insight['score']))
					
				conn.commit()
				conn.close()
			
		def create_saved_search(self, search_name, criteria, auto_import=False):
				"""Save a Sales Navigator search for recurring use"""
			
				conn = sqlite3.connect(self.db_path)
			
				try:
						conn.execute("""
								INSERT INTO sales_nav_saved_searches 
								(search_name, search_criteria, auto_import)
								VALUES (?, ?, ?)
						""", (search_name, json.dumps(criteria), 1 if auto_import else 0))
					
						conn.commit()
						return {'success': True}
			
				except sqlite3.IntegrityError:
						return {'success': False, 'error': 'Search name already exists'}
				finally:
						conn.close()
					
		def get_lead_insights(self, lead_id):
				"""Get all insights for a lead"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				insights = conn.execute("""
						SELECT * FROM sales_nav_insights
						WHERE lead_id = ?
						ORDER BY relevance_score DESC
				""", (lead_id,)).fetchall()
			
				conn.close()
			
				return [
						{
								'type': i['insight_type'],
								'data': json.loads(i['insight_data']),
								'score': i['relevance_score']
						}
						for i in insights
				]
	
		def generate_outreach_strategy(self, lead_id):
				"""Generate personalized outreach strategy based on Sales Nav data"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				lead = conn.execute("""
						SELECT lead_data FROM sales_nav_leads WHERE id = ?
				""", (lead_id,)).fetchone()
			
				if not lead:
						conn.close()
						return None
			
				lead_data = json.loads(lead['lead_data'])
				insights = self.get_lead_insights(lead_id)
				conn.close()
			
				# Build strategy
				strategy = {
						'priority_level': 'MEDIUM',
						'best_approach': 'connection_request',
						'timing': 'next_3_days',
						'talking_points': [],
						'personalization_hooks': []
				}
			
				# Analyze insights to determine strategy
				high_score_insights = [i for i in insights if i['score'] >= 0.8]
			
				if high_score_insights:
						strategy['priority_level'] = 'HIGH'
						strategy['timing'] = 'today'
					
				# Add talking points from insights
				for insight in insights[:3]:  # Top 3
						if insight['type'] == 'job_change':
								strategy['talking_points'].append("Congrats on the new role!")
								strategy['personalization_hooks'].append(insight['data']['action'])
						elif insight['type'] == 'company_growth':
								strategy['talking_points'].append("Impressive company growth")
								strategy['personalization_hooks'].append("Perfect time to discuss scaling solutions")
						elif insight['type'] == 'shared_network':
								strategy['personalization_hooks'].append("Mention shared connections")
							
				# Determine best channel
				if lead_data.get('accepts_inmails'):
						strategy['best_approach'] = 'inmail'
				elif lead_data.get('open_link_enabled'):
						strategy['best_approach'] = 'connection_request'
					
				return strategy
	
		def get_premium_analytics(self):
				"""Get Sales Navigator specific analytics"""
			
				conn = sqlite3.connect(self.db_path)
			
				stats = {
						'total_leads': conn.execute("SELECT COUNT(*) FROM sales_nav_leads").fetchone()[0],
						'high_priority_leads': conn.execute("""
								SELECT COUNT(DISTINCT lead_id) FROM sales_nav_insights
								WHERE relevance_score >= 0.8
						""").fetchone()[0],
						'insights_discovered': conn.execute("SELECT COUNT(*) FROM sales_nav_insights").fetchone()[0],
						'saved_searches': conn.execute("SELECT COUNT(*) FROM sales_nav_saved_searches").fetchone()[0]
				}
			
				# Top insight types
				top_insights = conn.execute("""
						SELECT insight_type, COUNT(*) as count
						FROM sales_nav_insights
						GROUP BY insight_type
						ORDER BY count DESC
						LIMIT 5
				""").fetchall()
			
				stats['top_insights'] = [
						{'type': i[0], 'count': i[1]} 
						for i in top_insights
				]
			
				conn.close()
				return stats
	
	
# LINKMATCH PRO INTEGRATION
class LinkMatchProIntegration:
		"""LinkMatch Pro warmup and inbox management"""
	
		def __init__(self, db_path='sales_angel.db'):
				self.db_path = db_path
			
		def suggest_warmup_sequence(self, prospect_id):
				"""Suggest LinkMatch Pro warmup before cold outreach"""
			
				return {
						'day_1-3': [
								'View profile (does not connect yet)',
								'Like 1-2 recent posts',
								'View their company page'
						],
						'day_4_7': [
								'Like another post',
								'View profile again',
								'Comment thoughtfully on a post (optional)'
						],
						'day_8': [
								'Send personalized connection request',
								'Reference something from their content'
						]
				}
	
		def generate_inbox_management_rules(self):
				"""Smart inbox rules for LinkMatch Pro"""
			
				rules = [
						{
								'name': 'Hot Leads - Instant Alert',
								'condition': 'message_contains: "interested" OR "let\'s talk" OR "meeting"',
								'action': 'notify_immediately + tag:hot_lead'
						},
						{
								'name': 'Auto-respond Busy',
								'condition': 'message_contains: "busy" OR "not now" OR "later"',
								'action': 'tag:follow_up_3_months + auto_response'
						},
						{
								'name': 'Positive Signal',
								'condition': 'message_contains: "thanks" OR "appreciate" OR "interesting"',
								'action': 'tag:warm + schedule_follow_up:3_days'
						}
				]
			
				return rules
	
	
# CLI
if __name__ == "__main__":
		import sys
	
		sales_nav = SalesNavigatorIntegration()
		linkmatch = LinkMatchProIntegration()
	
		if len(sys.argv) < 2:
				print("""
╔══════════════════════════════════════════════════════════════╗
║         SALES NAVIGATOR + LINKMATCH PRO                       ║
║         Premium LinkedIn Intelligence                          ║
╚══════════════════════════════════════════════════════════════╝

Sales Navigator Commands:
	python linkedin_sales_nav.py import <lead_json_file>
	python linkedin_sales_nav.py insights <lead_id>
	python linkedin_sales_nav.py strategy <lead_id>
	python linkedin_sales_nav.py analytics

LinkMatch Pro:
	python linkedin_sales_nav.py warmup <prospect_id>
	python linkedin_sales_nav.py inbox_rules
""")
				sys.exit(1)
			
		command = sys.argv[1]
	
		if command == 'analytics':
				stats = sales_nav.get_premium_analytics()
			
				print("\n📊 Sales Navigator Analytics:\n")
				print(f"Total Leads: {stats['total_leads']}")
				print(f"High Priority: {stats['high_priority_leads']}")
				print(f"Insights: {stats['insights_discovered']}")
				print(f"Saved Searches: {stats['saved_searches']}")
			
				if stats['top_insights']:
						print("\nTop Insights:")
						for insight in stats['top_insights']:
								print(f"  • {insight['type']}: {insight['count']}")
				print()
			
		elif command == 'warmup':
				prospect_id = int(sys.argv[2])
				sequence = linkmatch.suggest_warmup_sequence(prospect_id)
			
				print("\n🔥 LinkMatch Pro Warmup Sequence:\n")
				for phase, actions in sequence.items():
						print(f"{phase.replace('_', ' ').title()}:")
						for action in actions:
								print(f"  ✓ {action}")
						print()
					
		elif command == 'inbox_rules':
				rules = linkmatch.generate_inbox_management_rules()
			
				print("\n📥 Smart Inbox Rules:\n")
				for rule in rules:
						print(f"Rule: {rule['name']}")
						print(f"  When: {rule['condition']}")
						print(f"  Then: {rule['action']}")
						print()
					