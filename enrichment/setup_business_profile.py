#!/usr/bin/env python3

#!/usr/bin/env python3
"""
SALES ANGEL - Interactive Business Profile Setup
Guides users through configuring their business info for personalized AI emails
"""

import json
import os
from typing import Dict, List

class BusinessProfileWizard:
		"""Interactive wizard to create business configuration"""
	
		def __init__(self):
				self.profile = {}
				self.config_file = 'my_business_config.py'
			
		def run(self):
				"""Run the complete setup wizard"""
				print("""
╔══════════════════════════════════════════════════════════════╗
║          SALES ANGEL - BUSINESS PROFILE SETUP                 ║
║                                                               ║
║  This wizard will help configure your business information   ║
║  for AI-powered personalized emails.                         ║
║                                                               ║
║  Takes about 5-10 minutes.                                   ║
╚══════════════════════════════════════════════════════════════╝
""")
			
				input("\nPress ENTER to begin...")
			
				# Step 1: Company Info
				print("\n" + "="*70)
				print("STEP 1/6: Your Company Information")
				print("="*70)
				self.profile['company'] = self._get_company_info()
			
				# Step 2: Value Proposition
				print("\n" + "="*70)
				print("STEP 2/6: Your Value Proposition")
				print("="*70)
				self.profile['value_prop'] = self._get_value_proposition()
			
				# Step 3: Target Personas
				print("\n" + "="*70)
				print("STEP 3/6: Who You Sell To")
				print("="*70)
				self.profile['personas'] = self._get_target_personas()
			
				# Step 4: Services/Products
				print("\n" + "="*70)
				print("STEP 4/6: Your Services/Products")
				print("="*70)
				self.profile['services'] = self._get_services()
			
				# Step 5: Case Studies (Optional)
				print("\n" + "="*70)
				print("STEP 5/6: Success Stories (Optional)")
				print("="*70)
				self.profile['case_studies'] = self._get_case_studies()
			
				# Step 6: Writing Style
				print("\n" + "="*70)
				print("STEP 6/6: Your Writing Style")
				print("="*70)
				self.profile['style'] = self._get_writing_style()
			
				# Generate config file
				self._generate_config_file()
			
				# Show summary
				self._show_summary()
			
		def _get_company_info(self) -> Dict:
				"""Collect company information"""
				print("\nTell us about your company:\n")
			
				company = {
						'name': self._ask("Company name", "Acme Inc"),
						'your_name': self._ask("Your name (for emails)", "John Smith"),
						'your_title': self._ask("Your title", "Founder"),
						'website': self._ask("Website (optional)", "", required=False),
						'phone': self._ask("Phone (optional)", "", required=False)
				}
			
				return company
	
		def _get_value_proposition(self) -> str:
				"""Get value proposition through guided questions"""
				print("\nLet's define what you do and how you help:\n")
			
				print("Answer these questions in your own words (be specific):\n")
			
				who_you_help = self._ask(
						"1. Who do you primarily help?",
						"commercial banks and CDCs"
				)
			
				what_problem = self._ask(
						"2. What's the main problem they have?",
						"slow, manual SBA loan processing"
				)
			
				how_you_help = self._ask(
						"3. How do you solve it?",
						"automation and AI to streamline workflows"
				)
			
				key_outcomes = self._ask(
						"4. What results do they get?",
						"40-60% faster processing, fewer errors"
				)
			
				your_approach = self._ask(
						"5. What makes your approach unique?",
						"hands-on implementation, not just software"
				)
			
				# Build value prop
				value_prop = f"""I help {who_you_help} solve {what_problem}.

Specifically, I {how_you_help}.

Results: {key_outcomes}.

What makes me different: {your_approach}."""
			
				print("\n✅ Here's your value proposition:")
				print(f"\n{value_prop}\n")
			
				if self._ask_yes_no("Does this sound right?"):
						return value_prop
				else:
						print("\nNo problem! Let's write it yourself:")
						return self._ask_multiline("Enter your value proposition (press Ctrl+D when done)")
			
		def _get_target_personas(self) -> Dict:
				"""Define target personas and their pain points"""
				print("\nLet's define who you sell to and their pain points.\n")
			
				personas = {}
			
				# Pre-defined persona types
				persona_types = [
						'Commercial Banks',
						'Community Banks',
						'Credit Unions',
						'CDCs (Certified Development Companies)',
						'SBA Preferred Lenders',
						'CRE Firms',
						'Other'
				]
			
				print("Which of these do you sell to? (enter numbers separated by commas)")
				for i, persona in enumerate(persona_types, 1):
						print(f"  {i}. {persona}")
					
				selected = input("\nYour selection (e.g., 1,2,4): ").strip()
				selected_indices = [int(x.strip()) - 1 for x in selected.split(',') if x.strip()]
			
				for idx in selected_indices:
						if 0 <= idx < len(persona_types):
								persona_name = persona_types[idx]
								print(f"\n--- {persona_name} ---")
							
								personas[persona_name.upper().replace(' ', '_')] = {
										'pain_points': self._get_pain_points(persona_name),
										'your_unique_approach': self._ask(
												f"How you help {persona_name} specifically",
												"custom automation for their workflow"
										)
								}
							
				return personas
	
		def _get_pain_points(self, persona_name: str) -> List[str]:
				"""Get pain points for a persona"""
				print(f"\nWhat are the top 3-5 pain points {persona_name} typically have?")
				print("(Enter one per line, press ENTER twice when done)\n")
			
				pain_points = []
				while True:
						pain = input(f"  Pain point #{len(pain_points)+1}: ").strip()
						if not pain:
								if len(pain_points) >= 3:
										break
								else:
										print("Please enter at least 3 pain points")
										continue
						pain_points.append(pain)
						if len(pain_points) >= 8:  # Max 8
								break
			
				return pain_points
	
		def _get_services(self) -> Dict:
				"""Get services/products"""
				print("\nWhat services or products do you offer?\n")
			
				services = {}
			
				while True:
						service_name = input(f"\nService/Product #{len(services)+1} (or ENTER to finish): ").strip()
						if not service_name:
								if len(services) >= 1:
										break
								else:
										print("Please enter at least one service")
										continue
							
						services[service_name] = {
								'description': self._ask(
										f"  Brief description of {service_name}",
										"automation solution"
								),
								'ideal_for': self._ask(
										f"  Who is this ideal for?",
										"mid-size lenders"
								),
								'key_benefit': self._ask(
										f"  Main benefit",
										"saves time"
								)
						}
					
						if len(services) >= 5:  # Max 5
								break
			
				return services
	
		def _get_case_studies(self) -> List[Dict]:
				"""Get case studies (optional)"""
				print("\nDo you have success stories or case studies to share?")
				print("(These make emails much more credible - but optional)\n")
			
				if not self._ask_yes_no("Add case studies?", default=False):
						return []
			
				case_studies = []
			
				while True:
						print(f"\n--- Case Study #{len(case_studies)+1} ---")
					
						cs = {
								'company_type': self._ask(
										"Type of company (e.g., 'Community Bank')",
										"Community Bank"
								),
								'company_name': self._ask(
										"Company name (or 'Anonymous' if confidential)",
										"Anonymous"
								),
								'problem': self._ask(
										"What problem did they have?",
										"slow loan processing"
								),
								'solution': self._ask(
										"What did you do for them?",
										"implemented automation"
								),
								'results': self._ask(
										"What results did they achieve?",
										"50% faster processing"
								)
						}
					
						case_studies.append(cs)
					
						if not self._ask_yes_no(f"\nAdd another case study?", default=False):
								break
					
						if len(case_studies) >= 5:  # Max 5
								break
			
				return case_studies
	
		def _get_writing_style(self) -> Dict:
				"""Define writing style preferences"""
				print("\nLet's define your email writing style:\n")
			
				style = {
						'tone': self._ask_choice(
								"Email tone",
								['Professional & Direct', 'Casual & Friendly', 'Consultative', 'Executive/Brief'],
								default=0
						),
						'length': self._ask_choice(
								"Preferred email length",
								['Short (under 60 words)', 'Medium (60-100 words)', 'Longer (100+ words)'],
								default=0
						),
						'personalization': self._ask_choice(
								"Personalization level",
								['Highly personalized (reference their details)', 'Moderately personalized', 'Keep it general'],
								default=0
						)
				}
			
				# Phrases to avoid
				print("\nWhat phrases or words do you want to AVOID in emails?")
				print("(Common ones: 'quick question', 'just checking in', 'hope you're doing well')")
				print("Enter phrases to avoid (one per line, ENTER twice when done):\n")
			
				avoid_phrases = []
				while True:
						phrase = input(f"  Avoid: ").strip()
						if not phrase:
								break
						avoid_phrases.append(phrase)
						if len(avoid_phrases) >= 10:
								break
					
				style['avoid_phrases'] = avoid_phrases if avoid_phrases else [
						"quick question",
						"just checking in",
						"hope you're doing well",
						"per my last email"
				]
			
				return style
	
		def _generate_config_file(self):
				"""Generate the Python config file"""
				print("\n" + "="*70)
				print("Generating configuration file...")
				print("="*70)
			
				# Build the Python file content
				content = f'''"""
SALES ANGEL - YOUR BUSINESS CONFIGURATION
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

This file contains your business information for AI-powered email generation.
Edit this file anytime to update your configuration.
"""

# YOUR COMPANY INFO
MY_COMPANY = {{
		'name': {repr(self.profile['company']['name'])},
		'your_name': {repr(self.profile['company']['your_name'])},
		'your_title': {repr(self.profile['company']['your_title'])},
		'website': {repr(self.profile['company'].get('website', ''))},
		'phone': {repr(self.profile['company'].get('phone', ''))}
}}

# WHAT YOU DO (Value Proposition)
MY_VALUE_PROPOSITION = """{self.profile['value_prop']}"""

# WHO YOU SELL TO & THEIR PAIN POINTS
MY_TARGET_PERSONAS = {self._format_dict(self.profile['personas'], indent=0)}

# YOUR SERVICES/PRODUCTS
MY_SERVICES = {self._format_dict(self.profile['services'], indent=0)}

# SUCCESS STORIES (Case Studies)
MY_CASE_STUDIES = {self._format_list(self.profile['case_studies'])}

# YOUR WRITING STYLE
MY_WRITING_STYLE = """
Tone: {self.profile['style']['tone']}
Length: {self.profile['style']['length']}
Personalization: {self.profile['style']['personalization']}

Keep emails natural and conversational. Reference specific details about the prospect when available.
Avoid sounding scripted or using sales cliches.
"""

# PHRASES TO AVOID
AVOID_PHRASES = {repr(self.profile['style']['avoid_phrases'])}
'''

				# Write file
				with open(self.config_file, 'w') as f:
						f.write(content)
					
				print(f"✅ Configuration saved to: {self.config_file}")
				
		def _show_summary(self):
				"""Show setup summary"""
				print("\n" + "="*70)
				print("🎉 SETUP COMPLETE!")
				print("="*70)
			
				print(f"""
✅ Business Profile Created: {self.config_file}

Your Configuration:
	Company: {self.profile['company']['name']}
	Your Name: {self.profile['company']['your_name']}
	Target Personas: {len(self.profile['personas'])}
	Services: {len(self.profile['services'])}
	Case Studies: {len(self.profile['case_studies'])}

Next Steps:
	1. Review/edit {self.config_file} if needed
	2. Run: python sales_angel_PREMIUM.py generate <contact_id>
	3. AI will now use YOUR business info for personalized emails!

To update your profile later, run this wizard again or edit {self.config_file} directly.
""")
			
		# Helper methods
		def _ask(self, question: str, example: str = "", required: bool = True) -> str:
				"""Ask a question with optional example"""
				prompt = f"{question}"
				if example:
						prompt += f" (e.g., '{example}')"
				prompt += ": "
			
				while True:
						answer = input(prompt).strip()
						if answer or not required:
								return answer
						print("  This field is required. Please enter a value.")
					
		def _ask_multiline(self, prompt: str) -> str:
				"""Ask for multiline input"""
				print(f"\n{prompt}:")
				lines = []
				try:
						while True:
								line = input()
								lines.append(line)
				except EOFError:
						pass
				return '\n'.join(lines)

		def _ask_yes_no(self, question: str, default: bool = True) -> bool:
				"""Ask yes/no question"""
				suffix = " (Y/n)" if default else " (y/N)"
				while True:
						answer = input(f"{question}{suffix}: ").strip().lower()
						if not answer:
								return default
						if answer in ['y', 'yes']:
								return True
						if answer in ['n', 'no']:
								return False
						print("  Please answer 'y' or 'n'")
					
		def _ask_choice(self, question: str, choices: List[str], default: int = 0) -> str:
				"""Ask multiple choice question"""
				print(f"\n{question}:")
				for i, choice in enumerate(choices, 1):
						marker = " (default)" if i-1 == default else ""
						print(f"  {i}. {choice}{marker}")
					
				while True:
						answer = input(f"\nYour choice (1-{len(choices)}): ").strip()
						if not answer:
								return choices[default]
						try:
								idx = int(answer) - 1
								if 0 <= idx < len(choices):
										return choices[idx]
						except:
								pass
						print(f"  Please enter a number 1-{len(choices)}")
					
		def _format_dict(self, d: Dict, indent: int = 0) -> str:
				"""Format dictionary for Python file"""
				import pprint
				return pprint.pformat(d, indent=4, width=100)

		def _format_list(self, lst: List) -> str:
				"""Format list for Python file"""
				import pprint
				return pprint.pformat(lst, indent=4, width=100)


# Run wizard
if __name__ == "__main__":
		from datetime import datetime
	
		wizard = BusinessProfileWizard()
	
		# Check if config already exists
		if os.path.exists(wizard.config_file):
				print(f"\n⚠️  Configuration file already exists: {wizard.config_file}")
				if input("\nOverwrite existing configuration? (y/N): ").strip().lower() != 'y':
						print("Setup cancelled.")
						exit(0)
				print()
			
		wizard.run()
	