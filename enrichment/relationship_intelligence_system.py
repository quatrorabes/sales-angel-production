#!/usr/bin/env python3

#!/usr/bin/env python3
"""
RELATIONSHIP INTELLIGENCE & OUTREACH ORCHESTRATOR
Complete system for multi-channel outreach, signal monitoring, and relationship nurturing
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests

class RelationshipIntelligenceSystem:
	"""
	Complete relationship tracking and outreach system
	"""
	
	def __init__(self):
		self.config = self.load_config()
		
		# OUTREACH CADENCES (based on relationship stage)
		self.OUTREACH_CADENCES = {
			"new_referral_partner": {
				"name": "New Referral Partner Onboarding",
				"sequence": [
					{"day": 0, "channel": "linkedin", "action": "connect"},
					{"day": 1, "channel": "email", "action": "welcome"},
					{"day": 3, "channel": "phone", "action": "intro_call"},
					{"day": 7, "channel": "email", "action": "value_add"},
					{"day": 14, "channel": "linkedin", "action": "share_content"},
					{"day": 21, "channel": "email", "action": "case_study"},
					{"day": 30, "channel": "phone", "action": "partnership_call"},
					{"day": 45, "channel": "letter", "action": "handwritten_note"},
					{"day": 60, "channel": "email", "action": "quarterly_update"}
				]
			},
			"dormant_relationship": {
				"name": "Re-engage Dormant Contact (18+ months)",
				"sequence": [
					{"day": 0, "channel": "linkedin", "action": "view_profile"},
					{"day": 1, "channel": "linkedin", "action": "react_to_post"},
					{"day": 3, "channel": "email", "action": "reconnect"},
					{"day": 7, "channel": "linkedin", "action": "message"},
					{"day": 14, "channel": "phone", "action": "catch_up_call"},
					{"day": 30, "channel": "email", "action": "value_share"}
				]
			},
			"active_referrer": {
				"name": "Active Referral Source Maintenance",
				"sequence": [
					{"day": 0, "channel": "email", "action": "monthly_update"},
					{"day": 30, "channel": "phone", "action": "check_in"},
					{"day": 60, "channel": "linkedin", "action": "celebrate_win"},
					{"day": 90, "channel": "letter", "action": "quarterly_gift"},
					{"day": 120, "channel": "in_person", "action": "lunch_meeting"}
				]
			},
			"potential_borrower": {
				"name": "Direct Borrower Nurture",
				"sequence": [
					{"day": 0, "channel": "email", "action": "market_update"},
					{"day": 7, "channel": "linkedin", "action": "share_rates"},
					{"day": 14, "channel": "phone", "action": "needs_assessment"},
					{"day": 30, "channel": "email", "action": "case_study"},
					{"day": 45, "channel": "text", "action": "quick_check"},
					{"day": 60, "channel": "email", "action": "market_opportunity"}
				]
			}
		}
		
		# LINKEDIN TRIGGER EVENTS TO MONITOR
		self.LINKEDIN_TRIGGERS = {
			"job_change": {
				"priority": "HIGH",
				"action": "congratulate_new_role",
				"message": "Congrats on the new role at {company}! If you need financing for expansion, let's talk."
			},
			"promotion": {
				"priority": "HIGH", 
				"action": "celebrate_promotion",
				"message": "Huge congrats on the promotion to {title}! Well deserved."
			},
			"company_expansion": {
				"priority": "CRITICAL",
				"action": "offer_expansion_financing",
				"message": "Saw {company} is expanding! We specialize in expansion financing. Coffee?"
			},
			"posted_about_real_estate": {
				"priority": "HIGH",
				"action": "engage_re_content",
				"message": "Great insights on the CRE market! I help with owner-user financing if useful."
			},
			"work_anniversary": {
				"priority": "MEDIUM",
				"action": "celebrate_milestone",
				"message": "{years} years at {company} - impressive! Time to buy the building? 😊"
			},
			"shared_article": {
				"priority": "LOW",
				"action": "thoughtful_comment",
				"message": "Interesting perspective on {topic}. Have you seen {related_article}?"
			}
		}
		
		# COMPANY NEWS TRIGGERS
		self.COMPANY_TRIGGERS = {
			"funding_round": {
				"priority": "CRITICAL",
				"action": "offer_real_estate_solution",
				"message": "Congrats on the {funding_amount} raise! Ready to own your office space?"
			},
			"new_location": {
				"priority": "CRITICAL",
				"action": "expansion_financing",
				"message": "Saw you're opening in {location}. We do 90% financing for owner-users."
			},
			"acquisition": {
				"priority": "HIGH",
				"action": "consolidation_opportunity",
				"message": "Congrats on acquiring {company}! Need to consolidate real estate?"
			},
			"award_recognition": {
				"priority": "MEDIUM",
				"action": "celebrate_success",
				"message": "Well-deserved recognition! Growing companies often need real estate financing."
			}
		}
		
		# PERSONAL INTERESTS & HOBBIES (from LinkedIn/Facebook)
		self.PERSONAL_TRIGGERS = {
			"marathon_running": {
				"touchpoint": "Saw you ran the {race} - incredible time! I'm training for {my_race}.",
				"gift_idea": "Running gear or race entry"
			},
			"golf": {
				"touchpoint": "Want to play 18 at {course}? I'll bring the financing talk to the 19th hole.",
				"gift_idea": "ProV1s with company logo"
			},
			"wine_enthusiast": {
				"touchpoint": "Have you tried the new {winery}? My treat if you're interested.",
				"gift_idea": "Wine club membership"
			},
			"kids_sports": {
				"touchpoint": "How's {child} soccer season going? My kid plays too!",
				"gift_idea": "Team sponsorship"
			},
			"charity_involvement": {
				"touchpoint": "Love that you support {charity}. Can I sponsor your next event?",
				"gift_idea": "Charity donation in their name"
			}
		}
		
	def load_config(self):
		with open('config.json') as f:
			return json.load(f)
		
	def calculate_optimal_frequency(self, contact: Dict) -> Dict:
		"""
		Calculate optimal outreach frequency based on relationship
		"""
		relationship_age_days = contact.get('relationship_age_days', 0)
		last_interaction_days = contact.get('days_since_contact', 999)
		contact_type = contact.get('type', 'unknown')
		lifetime_value = contact.get('lifetime_referral_value', 0)
		
		# BASE FREQUENCIES BY TYPE
		if contact_type == "active_referrer":
			if lifetime_value > 100000:
				return {
					"phone": "monthly",
					"email": "bi-weekly", 
					"linkedin": "weekly",
					"in_person": "quarterly",
					"gift": "quarterly"
				}
			else:
				return {
					"phone": "quarterly",
					"email": "monthly",
					"linkedin": "bi-weekly",
					"in_person": "bi-annual"
				}
			
		elif contact_type == "potential_referrer":
			return {
				"phone": "quarterly",
				"email": "monthly",
				"linkedin": "weekly",
				"in_person": "annual"
			}
		
		elif contact_type == "dormant_valuable":
			# Known for 10+ years, haven't talked in 1.5 years
			return {
				"phone": "immediate",
				"email": "immediate_soft",
				"linkedin": "immediate_engage",
				"letter": "immediate_handwritten"
			}
		
		else:  # potential_borrower
			return {
				"phone": "bi-monthly",
				"email": "monthly",
				"linkedin": "bi-weekly",
				"text": "quarterly"
			}
	
	def generate_outreach_script(self, contact: Dict, channel: str, trigger: Optional[Dict] = None) -> Dict:
		"""
		Generate personalized outreach script based on context
		"""
		name = contact.get('first_name', 'there')
		company = contact.get('company', '')
		years_known = contact.get('years_known', 0)
		last_interaction = contact.get('last_interaction', {})
		
		scripts = {}
		
		# SCENARIO: Haven't talked in 1.5+ years but known for 10 years
		if years_known >= 10 and contact.get('days_since_contact', 0) > 540:
			scripts['email'] = {
				'subject': f"Too long, {name}!",
				'body': f"""Hi {name},

I was going through my contacts and realized we haven't connected in way too long! 

Last we spoke, you were at {company} - still there? I've been {self.config.get('your_update', 'growing the lending business')}.

Would love to catch up over coffee or a quick call. How's next week looking?

Best,
{self.config.get('your_name', 'Your Name')}

P.S. Remember that {last_interaction.get('memorable_moment', 'deal we talked about')}? Still makes me laugh."""
			}
			
			scripts['phone'] = {
				'opening': f"Hi {name}, it's {self.config.get('your_name')} - I know it's been forever, but I was just thinking about you!",
				'bridge': "I was looking at my CRM and realized we haven't talked since [specific date/event]. How have you been?",
				'value': "I've been working with a lot of [their industry] companies lately on owner-user financing...",
				'close': "We should grab coffee and properly catch up. What's your calendar like next week?"
			}
			
			scripts['linkedin'] = {
				'message': f"Hi {name} - Can't believe it's been {contact.get('months_since_contact', 18)} months! Was just thinking about that time we {last_interaction.get('memorable_moment', 'connected at that event')}. Would love to reconnect - coffee on me?"
			}
			
			scripts['handwritten_letter'] = {
				'message': f"""Dear {name},

In our digital world, I wanted to send a real note to say I've been thinking about you.

It's been far too long since we connected. I miss our conversations about [shared interest].

I'd love to catch up properly - coffee, lunch, or even just a phone call.

Hope you and [family members if known] are well.

Warmly,
{self.config.get('your_name')}

P.S. - I'm still in lending, now focusing on helping businesses buy their buildings. If you know anyone, I'd appreciate the intro!"""
			}
			
		# SCENARIO: Job change trigger
		elif trigger and trigger.get('type') == 'job_change':
			scripts['linkedin'] = {
				'message': f"Congrats on joining {trigger.get('new_company')}! If you need financing for office/warehouse space, I'm your guy. Coffee to celebrate?"
			}
			
			scripts['email'] = {
				'subject': f"Congrats on {trigger.get('new_company')}!",
				'body': f"""Hi {name},

Just saw you joined {trigger.get('new_company')} as {trigger.get('new_title')} - fantastic news!

If you're looking at real estate for the new role, I specialize in owner-user financing (90% LTV, 30-year terms).

Would love to catch up and hear about the new role.

Best,
{self.config.get('your_name')}"""
			}
			
		# SCENARIO: Company expansion news
		elif trigger and trigger.get('type') == 'company_expansion':
			scripts['phone'] = {
				'opening': f"Hi {name}, saw the news about {company} expanding to {trigger.get('new_location')} - congrats!",
				'value': "I specialize in expansion financing for growing companies. We can do 90% financing on owner-occupied properties.",
				'close': "Worth a quick coffee to explore if we can help with the real estate side?"
			}
			
		return scripts.get(channel, scripts)
	
	def monitor_linkedin_activity(self, contact: Dict) -> List[Dict]:
		"""
		Monitor LinkedIn for trigger events
		"""
		triggers_found = []
		
		# This would integrate with LinkedIn API or scraping tool
		# For now, returning example triggers
		
		linkedin_data = self.get_linkedin_data(contact)
		
		# Check for job changes
		if linkedin_data.get('job_changed'):
			triggers_found.append({
				'type': 'job_change',
				'priority': 'HIGH',
				'new_company': linkedin_data.get('new_company'),
				'new_title': linkedin_data.get('new_title'),
				'action': 'congratulate_and_offer',
				'suggested_outreach': self.LINKEDIN_TRIGGERS['job_change']
			})
			
		# Check recent posts
		for post in linkedin_data.get('recent_posts', []):
			if 'real estate' in post.get('content', '').lower():
				triggers_found.append({
					'type': 'posted_about_real_estate',
					'priority': 'HIGH',
					'post_url': post.get('url'),
					'action': 'engage_immediately'
				})
				
		return triggers_found
	
	def get_linkedin_data(self, contact: Dict) -> Dict:
		"""
		Placeholder for LinkedIn data fetching
		Would integrate with LinkedIn API or scraping service
		"""
		# This would actually fetch from LinkedIn
		return {
			'job_changed': False,
			'recent_posts': [],
			'recent_likes': [],
			'connections': []
		}
	
	def track_company_news(self, company: str) -> List[Dict]:
		"""
		Track company news and expansion signals
		"""
		news_triggers = []
		
		# This would integrate with news APIs (Google News, Crunchbase, etc.)
		# For demonstration:
		news_items = self.fetch_company_news(company)
		
		for item in news_items:
			if 'funding' in item.get('title', '').lower():
				news_triggers.append({
					'type': 'funding_round',
					'priority': 'CRITICAL',
					'amount': item.get('funding_amount'),
					'action': 'immediate_outreach',
					'message': self.COMPANY_TRIGGERS['funding_round']['message']
				})
				
			elif 'expand' in item.get('title', '').lower() or 'new location' in item.get('title', '').lower():
				news_triggers.append({
					'type': 'expansion',
					'priority': 'CRITICAL',
					'location': item.get('location'),
					'action': 'immediate_outreach'
				})
				
		return news_triggers
	
	def fetch_company_news(self, company: str) -> List[Dict]:
		"""
		Fetch company news from various sources
		"""
		# Placeholder - would integrate with:
		# - Google News API
		# - Crunchbase API
		# - LinkedIn Company Pages
		# - Industry publications
		return []
	
	def create_touchpoint_calendar(self, contact: Dict) -> List[Dict]:
		"""
		Create a calendar of touchpoints for the next 90 days
		"""
		calendar = []
		today = datetime.now()
		
		# Get optimal frequency
		frequency = self.calculate_optimal_frequency(contact)
		
		# Get any triggers
		triggers = self.monitor_linkedin_activity(contact)
		company_news = self.track_company_news(contact.get('company', ''))
		
		# Priority 1: Immediate triggers
		for trigger in triggers + company_news:
			if trigger.get('priority') == 'CRITICAL':
				calendar.append({
					'date': today,
					'channel': 'phone',
					'action': trigger.get('action'),
					'script': self.generate_outreach_script(contact, 'phone', trigger),
					'reason': f"TRIGGER: {trigger.get('type')}"
				})
				
		# Priority 2: Scheduled touchpoints based on frequency
		if frequency.get('phone') == 'immediate':
			calendar.append({
				'date': today + timedelta(days=1),
				'channel': 'phone',
				'action': 'reconnect_call',
				'script': self.generate_outreach_script(contact, 'phone'),
				'reason': 'Dormant high-value relationship'
			})
			
		# Add regular cadence
		next_email = today + timedelta(days=7)
		next_phone = today + timedelta(days=30)
		next_linkedin = today + timedelta(days=3)
		
		for i in range(90):
			current_date = today + timedelta(days=i)
			
			# Email cadence
			if frequency.get('email') == 'bi-weekly' and i % 14 == 0 and i > 0:
				calendar.append({
					'date': current_date,
					'channel': 'email',
					'action': 'value_add_email',
					'reason': 'Regular nurture'
				})
				
			# Phone cadence
			if frequency.get('phone') == 'monthly' and i % 30 == 0 and i > 0:
				calendar.append({
					'date': current_date,
					'channel': 'phone',
					'action': 'check_in_call',
					'reason': 'Monthly touchpoint'
				})
				
			# LinkedIn cadence
			if frequency.get('linkedin') == 'weekly' and i % 7 == 0:
				calendar.append({
					'date': current_date,
					'channel': 'linkedin',
					'action': 'engage_content',
					'reason': 'Stay visible'
				})
				
		# Add special dates
		if contact.get('birthday'):
			birthday = datetime.strptime(contact['birthday'], '%m-%d')
			birthday = birthday.replace(year=today.year)
			if birthday > today and birthday < today + timedelta(days=90):
				calendar.append({
					'date': birthday,
					'channel': 'phone',
					'action': 'birthday_call',
					'reason': 'Birthday',
					'gift': 'Send favorite wine/whiskey'
				})
				
		return sorted(calendar, key=lambda x: x['date'])
	
	def generate_relationship_report(self, contacts: List[Dict]) -> str:
		"""
		Generate comprehensive relationship intelligence report
		"""
		report = []
		report.append("="*80)
		report.append("RELATIONSHIP INTELLIGENCE & OUTREACH REPORT")
		report.append("="*80)
		report.append(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
		
		# Segment contacts
		dormant_valuable = [c for c in contacts if c.get('years_known', 0) >= 5 and c.get('days_since_contact', 0) > 365]
		active_referrers = [c for c in contacts if c.get('lifetime_referral_value', 0) > 0]
		trigger_opportunities = []
		
		for contact in contacts:
			triggers = self.monitor_linkedin_activity(contact)
			if triggers:
				trigger_opportunities.append((contact, triggers))
				
		# Section 1: Immediate Actions
		report.append("\n🚨 IMMEDIATE ACTIONS REQUIRED:")
		report.append("-" * 40)
		
		if dormant_valuable:
			report.append(f"\n{len(dormant_valuable)} Dormant Valuable Relationships to Reactivate:")
			for contact in dormant_valuable[:5]:
				report.append(f"\n• {contact.get('name')} - Known {contact.get('years_known')} years")
				report.append(f"  Last contact: {contact.get('days_since_contact')} days ago")
				report.append(f"  Action: Send handwritten note + follow-up call")
				script = self.generate_outreach_script(contact, 'email')
				if script:
					report.append(f"  Script: \"{script.get('email', {}).get('subject', '')}\"")
					
		# Section 2: Trigger Opportunities
		if trigger_opportunities:
			report.append(f"\n\n💡 {len(trigger_opportunities)} TRIGGER OPPORTUNITIES:")
			report.append("-" * 40)
			for contact, triggers in trigger_opportunities[:5]:
				report.append(f"\n• {contact.get('name')} at {contact.get('company')}")
				for trigger in triggers:
					report.append(f"  → {trigger.get('type')}: {trigger.get('suggested_outreach', {}).get('message', '')}")
					
		# Section 3: Outreach Calendar
		report.append("\n\n📅 NEXT 7 DAYS OUTREACH CALENDAR:")
		report.append("-" * 40)
		
		all_touchpoints = []
		for contact in contacts[:20]:  # Top 20 contacts
			touchpoints = self.create_touchpoint_calendar(contact)
			for tp in touchpoints:
				if tp['date'] < datetime.now() + timedelta(days=7):
					all_touchpoints.append({
						'contact': contact.get('name'),
						'date': tp['date'],
						'channel': tp['channel'],
						'action': tp['action']
					})
					
		all_touchpoints.sort(key=lambda x: x['date'])
		
		for tp in all_touchpoints[:10]:
			report.append(f"\n{tp['date'].strftime('%a %m/%d')}: {tp['contact']}")
			report.append(f"  → {tp['channel'].upper()}: {tp['action']}")
			
		# Section 4: Relationship Health Summary
		report.append("\n\n📊 RELATIONSHIP HEALTH METRICS:")
		report.append("-" * 40)
		report.append(f"Total Relationships: {len(contacts)}")
		report.append(f"Dormant (>1 year): {len([c for c in contacts if c.get('days_since_contact', 0) > 365])}")
		report.append(f"At Risk (>90 days): {len([c for c in contacts if 90 < c.get('days_since_contact', 0) < 365])}")
		report.append(f"Active (<30 days): {len([c for c in contacts if c.get('days_since_contact', 0) < 30])}")
		
		# Section 5: Channel Recommendations
		report.append("\n\n📱 OPTIMAL CHANNEL MIX:")
		report.append("-" * 40)
		report.append("• HIGH-VALUE REFERRERS: Phone monthly, LinkedIn weekly, Gifts quarterly")
		report.append("• DORMANT RELATIONSHIPS: Handwritten note → Phone → Coffee")
		report.append("• NEW CONNECTIONS: LinkedIn → Email → Phone within 30 days")
		report.append("• ACTIVE BORROWERS: Email bi-weekly with market updates")
		
		report.append("\n" + "="*80)
		
		return '\n'.join(report)
	
# Example usage
if __name__ == "__main__":
	system = RelationshipIntelligenceSystem()
	
	# Example contact who we've known for 10 years but haven't talked to in 1.5 years
	example_contact = {
		'name': 'John Smith',
		'first_name': 'John',
		'company': 'ABC Properties',
		'type': 'dormant_valuable',
		'years_known': 10,
		'days_since_contact': 548,  # 1.5 years
		'lifetime_referral_value': 250000,
		'last_interaction': {
			'memorable_moment': 'that deal at the golf tournament'
		},
		'birthday': '03-15',
		'interests': ['golf', 'wine'],
		'email': 'john@abcproperties.com'
	}
	
	# Generate outreach scripts
	scripts = system.generate_outreach_script(example_contact, 'email')
	print("EMAIL SCRIPT:")
	print(json.dumps(scripts.get('email', {}), indent=2))
	
	# Create touchpoint calendar
	calendar = system.create_touchpoint_calendar(example_contact)
	print("\nTOUCHPOINT CALENDAR (Next 30 days):")
	for touchpoint in calendar[:10]:
		print(f"{touchpoint['date'].strftime('%m/%d')}: {touchpoint['channel']} - {touchpoint['action']}")
		
	# Generate full report
	contacts = [example_contact]  # Would be your full contact list
	report = system.generate_relationship_report(contacts)
	print(report)
	