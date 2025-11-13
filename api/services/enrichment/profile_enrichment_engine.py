#!/usr/bin/env python3
"""
Sales Angel - Profile Enrichment Engine
Uses Perplexity API for intelligence gathering with structured prompts
Location: ~/projects/sales-angel/engines/profile_enrichment_engine.py
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional

class ProfileEnrichmentEngine:
    """
    Handles person and company enrichment using Perplexity AI
    with structured 11-step (person) and 5-step (company) frameworks
    """
    
    def __init__(self):
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
        
        self.base_url = 'https://api.perplexity.ai/chat/completions'
        self.model = 'llama-3.1-sonar-large-128k-online'
        
        # System prompt for profile building
        self.system_prompt = """You are an AI profile-building assistant. When given the name of a person or company, generate a comprehensive and up-to-date profile using both public web sources and any available uploaded internal files. Use sources such as LinkedIn, company websites, and the broader Internet. Once the profile is created, update the relevant contact in Hubspot and add a new note documenting any changes or new information found."""
    
    def enrich_person(self, name: str, company: Optional[str] = None, additional_context: str = "") -> Dict:
        """
        Enriches a person profile using your 11-step structured format
        
        Args:
            name: Full name of the person
            company: Company name (optional but recommended)
            additional_context: Any additional information to help the search
            
        Returns:
            Dictionary containing enriched profile data and citations
        """
        
        # Construct person-specific prompt with your exact structure
        user_prompt = f"""
Generate a comprehensive profile for: {name}
{f"Company: {company}" if company else ""}
{f"Additional Context: {additional_context}" if additional_context else ""}

For a PERSON, structure the profile as follows:

1. Overview: Report current title and organization.

2. Background: Summarize work history and notable achievements.

3. Education: List degrees and institutions.

4. Recent Mentions: Provide any news, public appearances, LinkedIn posts, or recent online presence.

5. Social Profiles: Find and list Instagram, Facebook, and Twitter profiles.

6. Personality Detail: Estimate Myers-Briggs personality type based on available data.

7. Assessment: Write and interpret a Myers-Briggs assessment summary.

8. Sales Opportunities: Identify potential talking points regarding sales opportunities.

9. Deal History: Search deals database for any past or current deals connected to the person.

10. Profile Accuracy: Update all fields with any new or corrected information found.

11. Additional Insights: Find relevant company news or fun facts; add these to "talking points" and the relevant company page.

Be thorough, accurate, and concise in your reporting.

Return the profile in a structured format with clear section headers.
"""
        
        return self._call_perplexity_api(user_prompt, profile_type='person')
    
    def enrich_company(self, company_name: str, additional_context: str = "") -> Dict:
        """
        Enriches a company profile using your 5-step structured format
        
        Args:
            company_name: Name of the company
            additional_context: Any additional information to help the search
            
        Returns:
            Dictionary containing enriched profile data and citations
        """
        
        # Construct company-specific prompt with your exact structure
        user_prompt = f"""
Generate a comprehensive profile for company: {company_name}
{f"Additional Context: {additional_context}" if additional_context else ""}

For a COMPANY, structure the profile as follows:

1. Overview: Include company description, mission, founding details, and headquarters location.

2. Products & Services: Summarize key offerings and markets served.

3. Leadership: List key executives and founders.

4. Market & Competitors: State industry, market position, and key competitors.

5. Recent News: Highlight major announcements, deals, or product launches.

Be thorough, accurate, and concise in your reporting.

Return the profile in a structured format with clear section headers.
"""
        
        return self._call_perplexity_api(user_prompt, profile_type='company')
    
    def _call_perplexity_api(self, user_prompt: str, profile_type: str) -> Dict:
        """
        Internal method to call Perplexity API
        
        Args:
            user_prompt: The formatted prompt for person or company
            profile_type: 'person' or 'company'
            
        Returns:
            Structured response with profile data and metadata
        """
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': self.system_prompt
                },
                {
                    'role': 'user',
                    'content': user_prompt
                }
            ],
            'return_citations': True,
            'search_recency_filter': 'month',  # Focus on recent data
            'temperature': 0.2,  # Low temperature for factual accuracy
            'max_tokens': 4000  # Allow comprehensive responses
        }
        
        try:
            print(f"🔍 Calling Perplexity API for {profile_type} enrichment...")
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            
            data = response.json()
            
            # Extract profile content and citations
            profile_content = data['choices'][0]['message']['content']
            citations = data.get('citations', [])
            
            # Structure the response
            enriched_profile = {
                'profile_type': profile_type,
                'raw_content': profile_content,
                'citations': citations,
                'citation_count': len(citations),
                'model_used': data.get('model', self.model),
                'generated_at': datetime.now().isoformat(),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Parse structured sections from content
            enriched_profile['parsed_sections'] = self._parse_sections(profile_content, profile_type)
            
            print(f"✅ Enrichment complete! Found {len(citations)} sources")
            
            return enriched_profile
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Perplexity API request failed: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                'profile_type': profile_type,
                'error': error_msg,
                'raw_content': None,
                'citations': [],
                'generated_at': datetime.now().isoformat(),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _parse_sections(self, content: str, profile_type: str) -> Dict:
        """
        Parses the Perplexity response into structured sections
        
        Args:
            content: Raw profile content from Perplexity
            profile_type: 'person' or 'company'
            
        Returns:
            Dictionary with parsed sections
        """
        
        sections = {}
        
        if profile_type == 'person':
            # Person sections: Overview, Background, Education, Recent Mentions, 
            # Social Profiles, Personality Detail, Assessment, Sales Opportunities,
            # Deal History, Profile Accuracy, Additional Insights
            section_headers = [
                'Overview', 'Background', 'Education', 'Recent Mentions',
                'Social Profiles', 'Personality Detail', 'Assessment',
                'Sales Opportunities', 'Deal History', 'Profile Accuracy',
                'Additional Insights'
            ]
        else:
            # Company sections: Overview, Products & Services, Leadership,
            # Market & Competitors, Recent News
            section_headers = [
                'Overview', 'Products & Services', 'Products and Services',
                'Leadership', 'Market & Competitors', 'Recent News'
            ]
        
        # Simple section parsing (can be enhanced with more sophisticated NLP)
        lines = content.split('\n')
        current_section = 'raw'
        current_content = []
        
        for line in lines:
            # Check if line is a section header
            is_header = False
            for header in section_headers:
                if header.lower() in line.lower() and (line.startswith('#') or line.endswith(':') or '**' in line):
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    
                    # Start new section
                    current_section = header.lower().replace(' ', '_').replace('&', 'and')
                    current_content = []
                    is_header = True
                    break
            
            if not is_header and line.strip():
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def save_profile(self, profile_data: Dict, output_dir: str = './profiles') -> str:
        """
        Saves enriched profile to JSON file
        
        Args:
            profile_data: Enriched profile dictionary
            output_dir: Directory to save profiles
            
        Returns:
            Path to saved file
        """
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        profile_type = profile_data.get('profile_type', 'unknown')
        filename = f"{profile_type}_profile_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Profile saved to: {filepath}")
        
        return filepath


# Convenience function for quick testing
def quick_enrich(name: str, company: str = None, profile_type: str = 'person'):
    """
    Quick enrichment function for testing
    
    Usage:
        quick_enrich('James Ritter', 'Example Company', 'person')
        quick_enrich('Apple Inc', profile_type='company')
    """
    
    engine = ProfileEnrichmentEngine()
    
    if profile_type == 'person':
        result = engine.enrich_person(name, company)
    else:
        result = engine.enrich_company(name)
    
    # Save profile
    filepath = engine.save_profile(result)
    
    # Print summary
    print("\n" + "="*80)
    print(f"📊 ENRICHMENT SUMMARY")
    print("="*80)
    print(f"Profile Type: {result['profile_type'].upper()}")
    print(f"Generated: {result['timestamp']}")
    print(f"Citations: {result['citation_count']}")
    print(f"Model: {result.get('model_used', 'N/A')}")
    print(f"Saved to: {filepath}")
    
    if result.get('error'):
        print(f"\n⚠️  ERROR: {result['error']}")
    else:
        print(f"\n✅ SUCCESS: Profile enrichment complete!")
        
        # Show first 500 chars of content
        content_preview = result['raw_content'][:500] + "..." if len(result['raw_content']) > 500 else result['raw_content']
        print(f"\nContent Preview:\n{content_preview}")
    
    return result


if __name__ == "__main__":
    """
    Test the enrichment engine directly
    """
    print("🚀 Sales Angel - Profile Enrichment Engine")
    print("="*80)
    
    # Test with example
    test_name = input("\nEnter person name (or press Enter for 'John Smith'): ").strip()
    if not test_name:
        test_name = "John Smith"
    
    test_company = input("Enter company name (optional, press Enter to skip): ").strip()
    
    result = quick_enrich(
        name=test_name,
        company=test_company if test_company else None,
        profile_type='person'
    )
    
    print("\n✅ Test complete!")
