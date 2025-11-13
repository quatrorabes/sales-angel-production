#!/usr/bin/env python3

#!/usr/bin/env python3
"""
Conversion Metrics Dashboard
Generates weekly performance report from Notion data
Tracks: Lifecycle progression, Lead status funnel, Persona performance
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime, timedelta
from collections import defaultdict
from notion_client import Client as NotionClient

class ConversionReport:
	def __init__(self):
		self.load_config()
		self.notion = NotionClient(auth=self.config["NOTION_API_KEY"])
		
		self.db_id = (
			self.config.get("NOTION_DB_ID") or 
			self.config.get("NOTION_DATABASE_ID") or
			self.config.get("NOTION_CONTACTS_DATABASE_ID")
		)
		
	def load_config(self):
		"""Load configuration"""
		config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
		with open(config_path, 'r') as f:
			self.config = json.load(f)
			
	def get_all_contacts(self):
		"""Get all contacts from Notion"""
		print("📊 Fetching contacts from Notion...")
		
		contacts = []
		has_more = True
		start_cursor = None
		
		while has_more:
			query_params = {
				"database_id": self.db_id,
				"page_size": 100
			}
			
			if start_cursor:
				query_params["start_cursor"] = start_cursor
				
			response = self.notion.databases.query(**query_params)
			contacts.extend(response["results"])
			
			has_more = response["has_more"]
			start_cursor = response.get("next_cursor")
			
		print(f"✅ Loaded {len(contacts)} contacts")
		return contacts
	
	def analyze_contacts(self, contacts):
		"""Analyze contacts and group by various metrics"""
		by_lifecycle = defaultdict(list)
		by_lead_status = defaultdict(list)
		by_persona = defaultdict(list)
		by_conversion_stage = defaultdict(list)
		
		total_outreach = 0
		with_activities = 0
		
		for page in contacts:
			props = page["properties"]
			
			# Lifecycle Stage
			lifecycle = props.get("Lifecycle Stage", {}).get("select")
			if lifecycle:
				by_lifecycle[lifecycle.get("name", "Unknown")].append(page)
				
			# Lead Status
			lead_status = props.get("Lead Status", {}).get("select")
			if lead_status:
				by_lead_status[lead_status.get("name", "Unknown")].append(page)
				
			# Primary Persona
			persona = props.get("Primary Persona Tier", {}).get("select")
			if persona:
				by_persona[persona.get("name", "Unknown")].append(page)
				
			# Conversion Stage
			conversion = props.get("Conversion Stage", {}).get("select")
			if conversion:
				by_conversion_stage[conversion.get("name", "Unknown")].append(page)
				
			# Count outreach sent
			outreach_date = props.get("Last Outreach Generated", {}).get("date")
			if outreach_date:
				total_outreach += 1
				
			# Count contacts with activities
			activities = props.get("Total Touchpoints", {}).get("number")
			if activities and activities > 0:
				with_activities += 1
				
		return {
			"lifecycle": by_lifecycle,
			"lead_status": by_lead_status,
			"persona": by_persona,
			"conversion_stage": by_conversion_stage,
			"total": len(contacts),
			"total_outreach": total_outreach,
			"with_activities": with_activities
		}
	
	def calculate_conversion_rates(self, data):
		"""Calculate conversion rates between stages"""
		lifecycle = data["lifecycle"]
		lead_status = data["lead_status"]
		
		# Lifecycle funnel
		total = data["total"]
		subscriber = len(lifecycle.get("Subscriber", []))
		lead = len(lifecycle.get("Lead", []))
		mql = len(lifecycle.get("Mql", []))
		sql = len(lifecycle.get("Sql", []))
		opportunity = len(lifecycle.get("Opportunity", []))
		customer = len(lifecycle.get("Customer", []))
		
		# Lead status funnel
		new_leads = len(lead_status.get("New", []))
		open_leads = len(lead_status.get("Open", []))
		contacted = len(lead_status.get("Contacted", []))
		engaged = len(lead_status.get("Engaged", []))
		qualified = len(lead_status.get("Qualified", []))
		
		# Total leads (any status)
		total_leads = lead + mql + sql
		
		return {
			"lifecycle": {
				"total_contacts": total,
				"subscriber": subscriber,
				"lead": lead,
				"mql": mql,
				"sql": sql,
				"opportunity": opportunity,
				"customer": customer,
				"lead_rate": (total_leads / total * 100) if total > 0 else 0,
				"opp_rate": (opportunity / total_leads * 100) if total_leads > 0 else 0,
				"close_rate": (customer / opportunity * 100) if opportunity > 0 else 0
			},
			"lead_status": {
				"new": new_leads,
				"open": open_leads,
				"contacted": contacted,
				"engaged": engaged,
				"qualified": qualified,
				"contact_rate": (contacted / (new_leads + open_leads) * 100) if (new_leads + open_leads) > 0 else 0,
				"engage_rate": (engaged / contacted * 100) if contacted > 0 else 0,
				"qualify_rate": (qualified / engaged * 100) if engaged > 0 else 0
			}
		}
	
	def generate_report(self, days=7):
		"""Generate conversion report"""
		print(f"\n" + "=" * 70)
		print(f"📊 CONVERSION METRICS REPORT")
		print(f"Period: All Time (Last sync: {datetime.now().strftime('%B %d, %Y')})")
		print("=" * 70)
		
		# Get data
		contacts = self.get_all_contacts()
		data = self.analyze_contacts(contacts)
		metrics = self.calculate_conversion_rates(data)
		
		# Overview
		print(f"\n### Overview\n")
		print(f"Total Contacts: {data['total']}")
		print(f"Outreach Sent: {data['total_outreach']}")
		print(f"With Activities: {data['with_activities']}")
		print(f"Activity Rate: {(data['with_activities'] / data['total'] * 100):.1f}%")
		
		# Lifecycle Stage Funnel
		print(f"\n### Lifecycle Stage Funnel\n")
		lc = metrics["lifecycle"]
		print(f"Subscriber: {lc['subscriber']}")
		print(f"Lead: {lc['lead']}")
		print(f"MQL: {lc['mql']}")
		print(f"SQL: {lc['sql']}")
		print(f"Opportunity: {lc['opportunity']} ({lc['opp_rate']:.1f}% conversion from leads)")
		print(f"Customer: {lc['customer']} ({lc['close_rate']:.1f}% close rate)")
		
		# Lead Status Funnel
		print(f"\n### Lead Status Progression\n")
		ls = metrics["lead_status"]
		print(f"New: {ls['new']}")
		print(f"Open: {ls['open']}")
		print(f"Contacted: {ls['contacted']} ({ls['contact_rate']:.1f}% of new)")
		print(f"Engaged: {ls['engaged']} ({ls['engage_rate']:.1f}% of contacted)")
		print(f"Qualified: {ls['qualified']} ({ls['qualify_rate']:.1f}% of engaged)")
		
		# Persona Breakdown
		print(f"\n### Performance by Persona\n")
		for persona, contacts in sorted(data["persona"].items(), key=lambda x: len(x[1]), reverse=True):
			if persona != "Unknown" and len(contacts) > 0:
				print(f"{persona}: {len(contacts)} contacts")
				
		# Conversion Stage Distribution
		print(f"\n### Conversion Stage Distribution\n")
		for stage, contacts in sorted(data["conversion_stage"].items(), key=lambda x: len(x[1]), reverse=True):
			if stage != "Unknown" and len(contacts) > 0:
				pct = (len(contacts) / data['total'] * 100)
				print(f"{stage}: {len(contacts)} ({pct:.1f}%)")
				
		# Export to markdown
		self.export_markdown_report(metrics, data)
		
		print(f"\n" + "=" * 70)
		print(f"✅ Report exported: data/conversion_report_{datetime.now().strftime('%Y-%m-%d')}.md")
		print("=" * 70)
		
	def export_markdown_report(self, metrics, data):
		"""Export report to markdown file"""
		filepath = f"data/conversion_report_{datetime.now().strftime('%Y-%m-%d')}.md"
		
		with open(filepath, 'w') as f:
			f.write(f"# Conversion Metrics Report\n\n")
			f.write(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  \n")
			f.write(f"**Total Contacts:** {data['total']}  \n")
			f.write(f"**Outreach Sent:** {data['total_outreach']}  \n\n")
			
			f.write("---\n\n")
			
			# Lifecycle funnel
			f.write("## Lifecycle Stage Funnel\n\n")
			lc = metrics["lifecycle"]
			f.write(f"- **Subscriber:** {lc['subscriber']}\n")
			f.write(f"- **Lead:** {lc['lead']}\n")
			f.write(f"- **MQL:** {lc['mql']}\n")
			f.write(f"- **SQL:** {lc['sql']}\n")
			f.write(f"- **Opportunity:** {lc['opportunity']} ({lc['opp_rate']:.1f}% conversion)\n")
			f.write(f"- **Customer:** {lc['customer']} ({lc['close_rate']:.1f}% close rate)\n\n")
			
			# Lead status
			f.write("## Lead Status Progression\n\n")
			ls = metrics["lead_status"]
			f.write(f"- **New:** {ls['new']}\n")
			f.write(f"- **Open:** {ls['open']}\n")
			f.write(f"- **Contacted:** {ls['contacted']} ({ls['contact_rate']:.1f}% of new)\n")
			f.write(f"- **Engaged:** {ls['engaged']} ({ls['engage_rate']:.1f}% of contacted)\n")
			f.write(f"- **Qualified:** {ls['qualified']} ({ls['qualify_rate']:.1f}% of engaged)\n\n")
			
			# Persona breakdown
			f.write("## Performance by Persona\n\n")
			for persona, contacts in sorted(data["persona"].items(), key=lambda x: len(x[1]), reverse=True):
				if persona != "Unknown" and len(contacts) > 0:
					f.write(f"- **{persona}:** {len(contacts)} contacts\n")
					
			f.write("\n")
			
			# Conversion stages
			f.write("## Conversion Stage Distribution\n\n")
			for stage, contacts in sorted(data["conversion_stage"].items(), key=lambda x: len(x[1]), reverse=True):
				if stage != "Unknown" and len(contacts) > 0:
					pct = (len(contacts) / data['total'] * 100)
					f.write(f"- **{stage}:** {len(contacts)} ({pct:.1f}%)\n")
					
			f.write("\n---\n\n")
			f.write("*Generated automatically by Phase 2: Response Tracking System*\n")
			
			
def main():
	import argparse
	parser = argparse.ArgumentParser(description="Generate conversion metrics report")
	parser.add_argument("--days", type=int, default=7, help="Report period in days (not used currently)")
	
	args = parser.parse_args()
	
	reporter = ConversionReport()
	reporter.generate_report(args.days)
	
	
if __name__ == "__main__":
	main()
	