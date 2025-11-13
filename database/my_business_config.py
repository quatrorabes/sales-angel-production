#!/usr/bin/env python3

"""
YOUR BUSINESS CONFIGURATION
Edit this file with YOUR real information - OpenAI will use this to generate emails
"""

# YOUR COMPANY INFO
MY_COMPANY = {
	'name': 'Your Company Name',
	'your_name': 'Chris Rabenold',  # or whoever is sending
	'your_title': 'Founder',  # or your actual title
	'website': 'yourwebsite.com'
}

# WHAT YOU ACTUALLY DO (in your own words)
MY_VALUE_PROPOSITION = """
I help commercial lenders and CDCs streamline their SBA loan processing through automation and AI. 

Specifically, I build custom workflows that:
- Automate document collection and verification
- Reduce manual data entry into ETRAN
- Flag compliance issues before they become problems
- Cut loan processing time by 40-60%

I work hands-on with each client to understand their specific bottlenecks and build solutions that fit their existing processes.
"""

# YOUR REAL CASE STUDIES (use actual examples or remove if you don't have any yet)
MY_CASE_STUDIES = [
	{
		'company_type': 'Community Bank',
		'company_name': 'Example Bank',  # Can be anonymous like "a 50-person community bank in Ohio"
		'problem': 'Taking 45+ days to process 504 loans, losing deals to faster competitors',
		'solution': 'Built automated document workflow and ETRAN integration',
		'results': '25-day average processing, closed 40% more loans in Q4'
	},
	# Add more or leave empty list if you don't have case studies yet
]

# YOUR SPECIFIC OFFERINGS/SERVICES
MY_SERVICES = {
	'SBA Workflow Automation': {
		'description': 'Custom automation for 504 and 7(a) loan processing',
		'ideal_for': ['CDCs', 'SBA Preferred Lenders', 'Community Banks'],
		'key_benefit': 'Cut processing time in half'
	},
	'ETRAN Integration': {
		'description': 'Direct integration with SBA ETRAN system to eliminate manual data entry',
		'ideal_for': ['High-volume SBA lenders', 'PLP lenders'],
		'key_benefit': 'Eliminate data entry errors'
	},
	'Compliance Automation': {
		'description': 'Automated compliance checking and documentation',
		'ideal_for': ['All SBA lenders', 'Credit Unions'],
		'key_benefit': 'Reduce compliance risk'
	}
}

# INDUSTRIES/PERSONAS YOU TARGET
MY_TARGET_PERSONAS = {
	'CDC_LENDER': {
		'pain_points': [
			'Environmental reviews taking weeks',
			'504 processing averaging 45+ days',
			'Small staff handling growing loan volume',
			'Manual tracking of multiple moving parts'
		],
		'your_unique_approach': 'I specialize in CDC workflow automation - built systems for 3 CDCs processing 100+ loans/year',
	},
	'COMMERCIAL_BANK': {
		'pain_points': [
			'SBA processing delays losing deals',
			'Tight credit underwriting',
			'Keeping a relationship after declining a loan',
			'Unwilling to listen to the borrowers story'
		],
		'your_unique_approach': 'I help banks add SBA without adding headcount - automation handles the paperwork',
	},
	'COMMUNITY_BANK': {
		'pain_points': [
			'Limited SBA expertise on staff',
			'Competing with big banks on speed',
			'Small margins on SBA loans',
			'Time-consuming paperwork'
		],
		'your_unique_approach': 'Turn-key SBA solutions that don\'t require hiring SBA experts',
	},
	'SBA_LENDER': {
		'pain_points': [
			'PLP ranking pressure',
			'Processing time affecting volume',
			'Staff burnout from manual work',
			'Scaling bottlenecks'
		],
		'your_unique_approach': 'I focus on high-volume lenders - automation that handles 50+ loans/month',
	}
}

# YOUR WRITING STYLE/VOICE
MY_WRITING_STYLE = """
Keep it:
- Direct and professional, not salesy
- Focused on their specific pain points
- No buzzwords or corporate jargon
- Short (under 80 words)
- Personal - write like I'm reaching out 1-on-1
- No fake urgency or pressure tactics
- Reference specific details when available
"""

# WHAT NOT TO SAY
AVOID_PHRASES = [
	"We recently helped 3 companies",
	"Results: 40% faster processing",
	"Quick question",
	"Worth a quick call?",
	"I thought you'd find this interesting",
	"Just checking in",
	"Hope you're doing well",
	"Per my last email"
]
