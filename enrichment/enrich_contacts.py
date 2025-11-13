#!/usr/bin/env python3
"""
SALES ANGEL - PERPLEXITY ENRICHMENT ENGINE
Enriches contacts with 68-citation intelligence profiles using Perplexity AI
"""

import os
import sys
import sqlite3
from dotenv import load_dotenv
import requests
from typing import Dict, Optional

# Load environment variables
load_dotenv()

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
if not PERPLEXITY_API_KEY:
    print("❌ ERROR: PERPLEXITY_API_KEY not found in .env")
    print("   Get one at: https://www.perplexity.ai/")
    sys.exit(1)

print("=" * 70)
print("🧠 SALES ANGEL - CONTACT ENRICHMENT ENGINE")
print("=" * 70)
print()

class PerplexityEnricher:
    """Enriches contacts with intelligence using Perplexity AI"""
    
    def __init__(self):
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar-pro"
        self.total_enriched = 0
        self.total_skipped = 0
        self.total_failed = 0
        self.total_cost = 0
    
    def enrich_contact(self, contact: Dict) -> Optional[Dict]:
        """Enrich a single contact with Perplexity intelligence"""
        
        firstname = contact.get('firstname', '')
        lastname = contact.get('lastname', '')
        company = contact.get('company', '')
        jobtitle = contact.get('jobtitle', '')
        email = contact.get('email', '')
        
        if not email or not firstname:
            return None
        
        # Build search query
        query = f"""
        Find professional intelligence on {firstname} {lastname} at {company}.
        
        Research:
        1. Current role and exact job title
        2. LinkedIn profile URL and recent posts
        3. Company size, revenue, and market position
        4. Specific achievements or deals they've led
        5. Industry trends affecting their business
        6. Pain points for their company/role
        7. Communication style and personality
        8. Recent news about company or individual
        
        Format:
        - Find EXACT LinkedIn URL (linkedin.com/in/...)
        - List complete work history with dates
        - Include specific metrics/achievements
        - Reference recent company news
        - List 3-5 key pain points
        - Identify 2-3 industry opportunities
        """
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 12000,
            "temperature": 0.7
        }
        
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            print(f"   🔍 Enriching: {firstname} {lastname} ({email})", end=" ... ")
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"❌ API Error {response.status_code}")
                return None
            
            data = response.json()
            
            if 'choices' not in data or not data['choices']:
                print("❌ No response")
                return None
            
            content = data['choices'][0]['message']['content']
            
            # Extract usage for cost calculation
            usage = data.get('usage', {})
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            cost = (input_tokens * 0.003 + output_tokens * 0.012) / 1000
            
            print(f"✅ ({input_tokens + output_tokens} tokens, ${cost:.4f})")
            
            return {
                'profile': content,
                'tokens': input_tokens + output_tokens,
                'cost': cost
            }
            
        except requests.exceptions.Timeout:
            print("❌ Timeout")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def update_database(self, contact_id: int, enrichment: Dict) -> bool:
        """Save enrichment to database"""
        try:
            conn = sqlite3.connect("sales_angel.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE contacts 
                SET enriched_profile = ?, 
                    enriched_at = datetime('now'),
                    enrichment_cost = ?
                WHERE id = ?
            """, (
                enrichment['profile'],
                enrichment['cost'],
                contact_id
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"   ❌ Database error: {e}")
            return False
    
    def enrich_batch(self, limit: int = 10, skip_enriched: bool = True) -> Dict:
        """Enrich a batch of contacts"""
        
        try:
            conn = sqlite3.connect("sales_angel.db")
            cursor = conn.cursor()
            
            # Build query
            if skip_enriched:
                cursor.execute("""
                    SELECT id, firstname, lastname, email, company, jobtitle
                    FROM contacts
                    WHERE enriched_profile IS NULL
                    LIMIT ?
                """, (limit,))
            else:
                cursor.execute("""
                    SELECT id, firstname, lastname, email, company, jobtitle
                    FROM contacts
                    LIMIT ?
                """, (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                print("ℹ️  No contacts to enrich")
                return {
                    'enriched': 0,
                    'skipped': 0,
                    'failed': 0,
                    'cost': 0
                }
            
            print(f"📋 Found {len(results)} contacts to enrich")
            print()
            
            for row in results:
                contact_id, firstname, lastname, email, company, jobtitle = row
                
                contact = {
                    'id': contact_id,
                    'firstname': firstname,
                    'lastname': lastname,
                    'email': email,
                    'company': company,
                    'jobtitle': jobtitle
                }
                
                enrichment = self.enrich_contact(contact)
                
                if enrichment:
                    if self.update_database(contact_id, enrichment):
                        self.total_enriched += 1
                        self.total_cost += enrichment['cost']
                    else:
                        self.total_failed += 1
                else:
                    self.total_failed += 1
            
            return {
                'enriched': self.total_enriched,
                'skipped': self.total_skipped,
                'failed': self.total_failed,
                'cost': self.total_cost
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                'enriched': 0,
                'skipped': 0,
                'failed': 0,
                'cost': 0
            }


def main():
    """Main enrichment flow"""
    
    print("🔌 Checking Perplexity connection...")
    
    try:
        test_payload = {
            "model": "sonar",
            "messages": [{"role": "user", "content": "Say 'Connected'"}],
            "max_tokens": 10
        }
        test_headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            json=test_payload,
            headers=test_headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Connection failed: {response.status_code}")
            print(f"   {response.text}")
            sys.exit(1)
        
        print("✅ Perplexity connection successful!")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)
    
    print()
    print("=" * 70)
    print()
    
    # Ask how many
    try:
        limit_input = input("How many contacts to enrich? (default 5, max 50): ").strip()
        limit = int(limit_input) if limit_input else 5
        limit = min(limit, 50)
    except ValueError:
        limit = 5
    
    print()
    
    # Run enrichment
    enricher = PerplexityEnricher()
    results = enricher.enrich_batch(limit=limit)
    
    print()
    print("=" * 70)
    print("📊 ENRICHMENT SUMMARY")
    print("=" * 70)
    print(f"Successfully Enriched: {results['enriched']}")
    print(f"Failed:     {results['failed']}")
    print(f"Cost:       ${results['cost']:.2f}")
    print()
    
    if results['enriched'] > 0:
        print("✅ Enrichment complete!")
        print()
        print("Next steps:")
        print("  1. Launch dashboard: streamlit run dashboard.py")
        print("  2. Go to Generate tab")
        print("  3. Select enriched contact")
        print("  4. Generate AI emails and call scripts")
        print("  5. Content will reference enriched intelligence")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
