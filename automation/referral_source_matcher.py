#!/usr/bin/env python3
"""
REFERRAL SOURCE MATCHING AI
Matches lenders with their ideal referral partners from their contact database
"""

import json
import requests
from datetime import datetime
from typing import List, Dict, Tuple

class ReferralSourceMatcher:
    def __init__(self):
        with open('config.json') as f:
            self.config = json.load(f)
        
        # Lender profiles with their ideal referral sources
        self.LENDER_PROFILES = {
            "nationwide_direct": {
                "name": "Nationwide Direct Lender",
                "products": ["Conventional CRE", "SBA 7(a)", "SBA 504"],
                "ideal_referrals": {
                    "commercial_bankers": {
                        "titles": ["commercial banker", "relationship manager", "vp commercial", "commercial lending"],
                        "companies": ["bank", "credit union", "financial"],
                        "score": 100
                    },
                    "sba_bankers": {
                        "titles": ["sba", "small business banker", "business banking"],
                        "companies": ["bank", "credit union"],
                        "score": 95
                    },
                    "cre_brokers": {
                        "titles": ["broker", "agent", "advisor", "associate"],
                        "companies": ["colliers", "cbre", "jll", "cushman", "lee & associates", "marcus & millichap"],
                        "score": 90
                    },
                    "mortgage_brokers": {
                        "titles": ["mortgage broker", "loan broker", "financing advisor"],
                        "companies": ["mortgage", "capital", "funding", "finance"],
                        "score": 85
                    }
                }
            },
            "community_bank": {
                "name": "Community Bank",
                "products": ["Local CRE", "Lines of Credit", "Term Loans"],
                "ideal_referrals": {
                    "local_brokers": {
                        "titles": ["broker", "agent", "realtor"],
                        "companies": ["realty", "properties", "real estate"],
                        "score": 95
                    },
                    "accountants": {
                        "titles": ["cpa", "accountant", "cfo", "controller"],
                        "companies": ["accounting", "cpa", "tax"],
                        "score": 90
                    },
                    "attorneys": {
                        "titles": ["attorney", "lawyer", "counsel"],
                        "companies": ["law", "legal", "llp"],
                        "score": 85
                    }
                }
            },
            "credit_union": {
                "name": "Credit Union",
                "products": ["Member Business Loans", "CRE Loans"],
                "ideal_referrals": {
                    "member_businesses": {
                        "titles": ["owner", "president", "ceo"],
                        "companies": ["*"],  # Any company
                        "score": 100
                    },
                    "local_associations": {
                        "titles": ["director", "president", "board"],
                        "companies": ["association", "chamber", "council"],
                        "score": 90
                    }
                }
            }
        }
    
    def analyze_contact_for_referral(self, contact: Dict, lender_type: str) -> Dict:
        """Analyze a single contact for referral potential"""
        props = contact.get('properties', {})
        
        # Get contact details
        name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
        company = (props.get('company', '') or '').lower()
        title = (props.get('jobtitle', '') or '').lower()
        phone = props.get('phone', '')
        email = props.get('email', '')
        
        # Get lender profile
        profile = self.LENDER_PROFILES.get(lender_type, self.LENDER_PROFILES['nationwide_direct'])
        
        # Score the contact
        match_score = 0
        match_reasons = []
        matched_category = None
        
        for category, criteria in profile['ideal_referrals'].items():
            category_match = False
            
            # Check title match
            title_match = any(keyword in title for keyword in criteria['titles'])
            
            # Check company match
            company_match = False
            if criteria['companies'] == ["*"]:
                company_match = True
            else:
                company_match = any(keyword in company for keyword in criteria['companies'])
            
            # Calculate match
            if title_match and company_match:
                match_score = criteria['score']
                matched_category = category
                category_match = True
                
                # Add specific reasons
                if 'bank' in company and 'commercial' in title:
                    match_reasons.append("Commercial banker at major bank - can refer declined deals")
                elif 'sba' in title:
                    match_reasons.append("SBA specialist - perfect for 504/7a referrals")
                elif any(broker in company for broker in ['colliers', 'cbre', 'jll']):
                    match_reasons.append("Major CRE broker - handles large transactions")
                elif 'mortgage' in title or 'broker' in title:
                    match_reasons.append("Mortgage broker - steady referral source")
                elif 'owner' in title or 'president' in title:
                    match_reasons.append("Business owner - potential direct borrower")
                else:
                    match_reasons.append(f"Matches {category.replace('_', ' ').title()} profile")
            
            elif title_match:
                match_score = max(match_score, criteria['score'] * 0.6)
                match_reasons.append(f"Title matches {category.replace('_', ' ')}")
            elif company_match:
                match_score = max(match_score, criteria['score'] * 0.4)
                match_reasons.append(f"Company type matches {category.replace('_', ' ')}")
        
        # Bonus scoring factors
        if props.get('hs_linkedin_url'):
            match_score += 5
            match_reasons.append("LinkedIn connected")
        
        if int(props.get('num_contacted_notes', 0) or 0) > 0:
            match_score += 10
            match_reasons.append("Previous interaction history")
        
        if props.get('hs_lead_status') == 'open':
            match_score += 5
            match_reasons.append("Active lead status")
        
        return {
            'contact': contact,
            'name': name or 'Unknown',
            'title': props.get('jobtitle', 'Unknown'),
            'company': props.get('company', 'Unknown'),
            'phone': phone,
            'email': email,
            'match_score': min(match_score, 100),
            'match_category': matched_category,
            'match_reasons': match_reasons,
            'referral_potential': self.calculate_referral_potential(match_score)
        }
    
    def calculate_referral_potential(self, score: int) -> str:
        """Calculate referral potential tier"""
        if score >= 90:
            return "🔥 TIER 1 - Top Priority"
        elif score >= 75:
            return "⭐ TIER 2 - High Value"
        elif score >= 60:
            return "✅ TIER 3 - Good Potential"
        elif score >= 40:
            return "📊 TIER 4 - Worth Exploring"
        else:
            return "🔍 TIER 5 - Low Priority"
    
    def get_contacts(self, limit: int = 200) -> List[Dict]:
        """Get contacts from HubSpot"""
        url = "https://api.hubapi.com/crm/v3/objects/contacts"
        headers = {'Authorization': f'Bearer {self.config["HUBSPOT_API_KEY"]}'}
        
        all_contacts = []
        after = None
        
        while len(all_contacts) < limit:
            params = {
                'limit': min(100, limit - len(all_contacts)),
                'properties': 'firstname,lastname,company,phone,email,jobtitle,hs_lead_status,lifecyclestage,hs_linkedin_url,num_contacted_notes'
            }
            if after:
                params['after'] = after
                
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                for contact in results:
                    props = contact.get('properties', {})
                    lead_status = (props.get('hs_lead_status') or '').lower()
                    
                    # Skip unqualified
                    if lead_status not in ['unqualified', 'do not contact', 'disqualified']:
                        all_contacts.append(contact)
                        if len(all_contacts) >= limit:
                            break
                
                if data.get('paging', {}).get('next'):
                    after = data['paging']['next']['after']
                else:
                    break
            else:
                break
        
        return all_contacts
    
    def match_referral_sources(self, lender_type: str = "nationwide_direct", limit: int = 200):
        """Main matching function"""
        print("\n" + "="*80)
        print("🎯 REFERRAL SOURCE MATCHING AI")
        print("="*80)
        
        # Display lender profile
        profile = self.LENDER_PROFILES.get(lender_type, self.LENDER_PROFILES['nationwide_direct'])
        print(f"\n📊 YOUR LENDER PROFILE:")
        print(f"Type: {profile['name']}")
        print(f"Products: {', '.join(profile['products'])}")
        print(f"\n🎯 Your Ideal Referral Sources:")
        for category, criteria in profile['ideal_referrals'].items():
            print(f"  • {category.replace('_', ' ').title()}")
        
        print(f"\n🔍 Analyzing your {limit} contacts...")
        
        # Get and analyze contacts
        contacts = self.get_contacts(limit)
        analyzed_contacts = []
        
        for contact in contacts:
            analysis = self.analyze_contact_for_referral(contact, lender_type)
            if analysis['match_score'] > 0:
                analyzed_contacts.append(analysis)
        
        # Sort by match score
        analyzed_contacts.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Display results
        print("\n" + "="*80)
        print("🏆 TOP 15 REFERRAL SOURCE MATCHES:")
        print("="*80 + "\n")
        
        for i, match in enumerate(analyzed_contacts[:15], 1):
            print(f"{i}. {match['name']}")
            print(f"   📍 {match['title']} at {match['company']}")
            print(f"   📞 {match['phone'] or 'No phone'}")
            print(f"   📊 Match Score: {match['match_score']}/100 - {match['referral_potential']}")
            print(f"   🎯 Why: {match['match_reasons'][0] if match['match_reasons'] else 'Potential referral source'}")
            
            # Generate personalized approach
            approach = self.generate_referral_approach(match, profile)
            print(f"   💬 Approach: \"{approach}\"")
            print()
        
        # Show category breakdown
        print("="*80)
        print("📈 REFERRAL SOURCE BREAKDOWN:")
        print("-"*40)
        
        categories = {}
        for match in analyzed_contacts:
            cat = match['match_category'] or 'other'
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {cat.replace('_', ' ').title()}: {count} contacts")
        
        print(f"\nTotal qualified referral sources: {len(analyzed_contacts)}")
        print("="*80)
        
        return analyzed_contacts
    
    def generate_referral_approach(self, match: Dict, profile: Dict) -> str:
        """Generate personalized approach for referral partner"""
        name = match['name'].split()[0] if match['name'] != 'Unknown' else 'there'
        
        if match['match_category'] == 'commercial_bankers':
            return f"Hi {name}, I specialize in CRE deals your bank declines. Let's set up a referral partnership - I pay 1% on closed deals."
        elif match['match_category'] == 'sba_bankers':
            return f"Hi {name}, I handle SBA 504/7a loans nationwide. Happy to be your overflow partner when you're at capacity."
        elif match['match_category'] == 'cre_brokers':
            return f"Hi {name}, I close CRE loans in 30 days with 90% LTV. Want to add me to your preferred lender list?"
        elif match['match_category'] == 'mortgage_brokers':
            return f"Hi {name}, I do CRE loans from $500K-$20M. Let's discuss how we can work together on deals."
        else:
            return f"Hi {name}, I provide {profile['products'][0]} financing. Let's explore how we can refer business to each other."

def main():
    """Interactive lender profile selection"""
    matcher = ReferralSourceMatcher()
    
    print("\n🏦 SELECT YOUR LENDER TYPE:")
    print("1. Nationwide Direct Lender (CRE/SBA specialist)")
    print("2. Community Bank (local relationships)")
    print("3. Credit Union (member-focused)")
    
    choice = input("\nEnter choice (1-3, default=1): ").strip() or "1"
    
    lender_map = {
        "1": "nationwide_direct",
        "2": "community_bank",
        "3": "credit_union"
    }
    
    lender_type = lender_map.get(choice, "nationwide_direct")
    
    # Run the matching
    matcher.match_referral_sources(lender_type)

if __name__ == "__main__":
    main()
