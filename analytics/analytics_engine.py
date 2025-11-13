#!/usr/bin/env python3

# analytics_engine.py - Track performance and ROI in real-time

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

class AnalyticsEngine:
	"""Real-time analytics for sales performance"""
	
	def __init__(self, db_path='sales_angel.db'):
		self.db_path = db_path
		
	def get_conn(self):
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		return conn
	
	def funnel_metrics(self):
		"""Calculate sales funnel conversion rates"""
		conn = self.get_conn()
		
		# Read from simple CSV tracker if database tables don't exist
		try:
			import csv
			activities = []
			with open('daily_tracker.csv', 'r') as f:
				reader = csv.DictReader(f)
				activities = list(reader)
				
			metrics = {
				'total_enriched': conn.execute("SELECT COUNT(*) FROM contacts WHERE enriched = 1").fetchone()[0],
				'with_content': conn.execute("SELECT COUNT(*) FROM contacts WHERE email_1_subject IS NOT NULL").fetchone()[0],
				'emails_sent': len([a for a in activities if a.get('Channel') == 'Email']),
				'calls_made': len([a for a in activities if a.get('Channel', '').lower().startswith('call')]),
				'responses': len([a for a in activities if 'response' in a.get('Channel', '').lower()]),
				'meetings': len([a for a in activities if 'meeting' in a.get('Status', '').lower()])
			}
		except:
			# Fallback to database if CSV doesn't exist
			metrics = {
				'total_enriched': conn.execute("SELECT COUNT(*) FROM contacts WHERE enriched = 1").fetchone()[0],
				'with_content': conn.execute("SELECT COUNT(*) FROM contacts WHERE email_1_subject IS NOT NULL").fetchone()[0],
				'emails_sent': 0,
				'calls_made': 0,
				'responses': 0,
				'meetings': 0
			}
			
		# Calculate conversion rates
		metrics['email_response_rate'] = (metrics['responses'] / metrics['emails_sent'] * 100) if metrics['emails_sent'] > 0 else 0
		metrics['meeting_rate'] = (metrics['meetings'] / metrics['responses'] * 100) if metrics['responses'] > 0 else 0
		
		conn.close()
		return metrics
	
	def variant_performance(self):
		"""Track which email/call variants perform best"""
		try:
			import csv
			activities = []
			with open('daily_tracker.csv', 'r') as f:
				reader = csv.DictReader(f)
				activities = list(reader)
				
			by_variant = defaultdict(lambda: {'sent': 0, 'responses': 0})
			
			for a in activities:
				variant = a.get('Variant', '')
				if variant and a.get('Channel') == 'Email':
					by_variant[variant]['sent'] += 1
				elif 'response' in a.get('Channel', '').lower():
					# Try to match back to variant (would need better tracking)
					by_variant['1']['responses'] += 1  # Simplified
					
			performance = {}
			for variant, stats in by_variant.items():
				rate = (stats['responses'] / stats['sent'] * 100) if stats['sent'] > 0 else 0
				performance[f'Variant {variant}'] = {
					'sent': stats['sent'],
					'responses': stats['responses'],
					'rate': rate
				}
				
			return performance
		except:
			return {}
		
	def roi_calculator(self):
		"""Calculate ROI on enrichment investment"""
		conn = self.get_conn()
		
		# Costs
		enriched = conn.execute("SELECT COUNT(*) FROM contacts WHERE enriched = 1").fetchone()[0]
		with_content = conn.execute("SELECT COUNT(*) FROM contacts WHERE email_1_subject IS NOT NULL").fetchone()[0]
		
		enrichment_cost = enriched * 0.15  # $0.15 per enrichment
		content_cost = with_content * 0.05  # $0.05 per content generation
		total_cost = enrichment_cost + content_cost
		
		# Potential value (conservative estimates)
		avg_deal_low = 45000
		avg_deal_high = 450000
		close_rate = 0.10  # 10% close rate
		
		try:
			import csv
			with open('daily_tracker.csv', 'r') as f:
				reader = csv.DictReader(f)
				activities = list(reader)
			meetings = len([a for a in activities if 'meeting' in a.get('Status', '').lower()])
		except:
			meetings = 0
			
		pipeline_low = meetings * avg_deal_low * close_rate
		pipeline_high = meetings * avg_deal_high * close_rate
		
		roi_low = ((pipeline_low - total_cost) / total_cost * 100) if total_cost > 0 else 0
		roi_high = ((pipeline_high - total_cost) / total_cost * 100) if total_cost > 0 else 0
		
		conn.close()
		
		return {
			'invested': total_cost,
			'enriched': enriched,
			'with_content': with_content,
			'meetings_booked': meetings,
			'pipeline_low': pipeline_low,
			'pipeline_high': pipeline_high,
			'roi_low': roi_low,
			'roi_high': roi_high,
			'cost_per_meeting': (total_cost / meetings) if meetings > 0 else 0
		}
	
	def daily_activity_summary(self, days=7):
		"""Summarize activity over last N days"""
		try:
			import csv
			from datetime import datetime
			
			activities = []
			with open('daily_tracker.csv', 'r') as f:
				reader = csv.DictReader(f)
				activities = list(reader)
				
			cutoff = datetime.now() - timedelta(days=days)
			recent = [a for a in activities if datetime.strptime(a['Date'], '%Y-%m-%d') >= cutoff]
			
			by_day = defaultdict(lambda: {'emails': 0, 'calls': 0, 'responses': 0})
			
			for a in recent:
				date = a['Date']
				channel = a.get('Channel', '')
				if channel == 'Email':
					by_day[date]['emails'] += 1
				elif channel.lower().startswith('call'):
					by_day[date]['calls'] += 1
				elif 'response' in channel.lower():
					by_day[date]['responses'] += 1
					
			return dict(by_day)
		except:
			return {}
		
	def hot_contacts(self, limit=10):
		"""Find hottest contacts (high score, not yet reached)"""
		conn = self.get_conn()
		
		# Get enriched contacts not in daily tracker
		contacted = set()
		try:
			import csv
			with open('daily_tracker.csv', 'r') as f:
				reader = csv.DictReader(f)
				contacted = {row['Contact'] for row in reader if row.get('Contact')}
		except:
			pass
			
		hot = conn.execute("""
			SELECT firstname, lastname, company, score, tier, email
			FROM contacts
			WHERE enriched = 1
				AND email_1_subject IS NOT NULL
				AND score > 60
			ORDER BY score DESC
			LIMIT ?
		""", (limit * 2,)).fetchall()  # Get extra in case some are contacted
		
		conn.close()
		
		# Filter out already contacted
		uncontacted = []
		for c in hot:
			name = f"{c['firstname']} {c['lastname']}"
			if name not in contacted:
				uncontacted.append(dict(c))
			if len(uncontacted) >= limit:
				break
			
		return uncontacted
	
	def print_dashboard(self):
		"""Print beautiful console dashboard"""
		
		print("\n" + "="*80)
		print("📊 SALES ANGEL ANALYTICS DASHBOARD")
		print("="*80 + "\n")
		
		# Funnel
		funnel = self.funnel_metrics()
		print("🎯 SALES FUNNEL")
		print("-"*80)
		print(f"  Enriched Contacts: {funnel['total_enriched']}")
		print(f"  With Content:      {funnel['with_content']}")
		print(f"  Emails Sent:       {funnel['emails_sent']}")
		print(f"  Calls Made:        {funnel['calls_made']}")
		print(f"  Responses:         {funnel['responses']} ({funnel['email_response_rate']:.1f}%)")
		print(f"  Meetings:          {funnel['meetings']} ({funnel['meeting_rate']:.1f}%)")
		print()
		
		# ROI
		roi = self.roi_calculator()
		print("💰 ROI ANALYSIS")
		print("-"*80)
		print(f"  Invested:          ${roi['invested']:.2f}")
		print(f"  Meetings Booked:   {roi['meetings_booked']}")
		print(f"  Cost per Meeting:  ${roi['cost_per_meeting']:.2f}")
		print(f"  Pipeline (Low):    ${roi['pipeline_low']:,.0f}")
		print(f"  Pipeline (High):   ${roi['pipeline_high']:,.0f}")
		print(f"  ROI (Low):         {roi['roi_low']:,.0f}%")
		print(f"  ROI (High):        {roi['roi_high']:,.0f}%")
		print()
		
		# Variant Performance
		variants = self.variant_performance()
		if variants:
			print("📧 VARIANT PERFORMANCE")
			print("-"*80)
			for variant, stats in variants.items():
				print(f"  {variant}: {stats['sent']} sent, {stats['responses']} responses ({stats['rate']:.1f}%)")
			print()
			
		# Hot Contacts
		hot = self.hot_contacts(5)
		if hot:
			print("🔥 TOP UNAPPROACHED CONTACTS")
			print("-"*80)
			for c in hot:
				print(f"  {c['firstname']} {c['lastname']:20s} | {c['company']:30s} | Score: {c['score']}")
			print()
			
		print("="*80 + "\n")
		
		
# CLI
if __name__ == "__main__":
	import sys
	
	analytics = AnalyticsEngine()
	
	if len(sys.argv) > 1 and sys.argv[1] == 'export':
		# Export to JSON
		import json
		data = {
			'funnel': analytics.funnel_metrics(),
			'roi': analytics.roi_calculator(),
			'variants': analytics.variant_performance(),
			'hot_contacts': analytics.hot_contacts(10)
		}
		print(json.dumps(data, indent=2))
	else:
		# Print dashboard
		analytics.print_dashboard()
		