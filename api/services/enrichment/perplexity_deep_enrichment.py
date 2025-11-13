#!/usr/bin/env python3
"""
Automated version of your manual Perplexity enrichment process
Uses YOUR exact prompts that generate the amazing data
"""

import os
import json
import requests
from datetime import datetime
from hubspot import HubSpot
from notion_client import Client
import time

# Your API keys
PERPLEXITY_KEY = os.getenv("PERPLEXITY_API_KEY")
HUBSPOT_KEY = os.getenv("HUBSPOT_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Initialize clients
hubspot = HubSpot(access_token=HUBSPOT_KEY)
notion = Client(auth=NOTION_TOKEN)

def perplexity_enrich(contact_name, company, linkedin_url):
    """
    Uses YOUR EXACT PROMPT that generates the incredible enrichment
    """
    
    # Your magic prompt
    prompt = f"""You are a professional profile-building assistant. Generate up-to-date profile using both public web sources for {contact_name} at {company}. Use sources such as LinkedIn ({linkedin_url}) & Internet.

For a company ({company}), structure the profile as:
1. Overview – Description, mission, founding details, and HQ
2. Products & Services – Key offerings and markets served
3. Leadership – Key executives and founders
4. Market & Competitors – Industry, position, key competitors
5. Recent News – Major announcements, deals, or product launches

For a person ({contact_name}), structure the profile as:
1. Overview – Current title and organization
2. Background – Work history, notable achievements
3. Education – Degrees and institutions
4. Recent Mentions – Any news, public appearances, LinkedIn posts, or online presence
5. Find instagram, facebook, and twitter user profiles.
6. Personality Detail - perform a Myers briggs assessment.
7. Compose and interpret Myers-Briggs Personality assessment summary.
8. Evaluate potential talking points regarding sales opportunities.
9. Search deals database for any past or current "deal"
10. Update all fields with new or inaccurate information
11. Find any relevant company news or fun facts. Populate results in "talking points" tab and on relevant company page.
12. Trigger Events - Identify any recent events that create sales opportunities (new funding, expansion, leadership changes)
13. Competitive Intelligence - What solutions are they currently using that we could replace?
14. Warm Introduction Paths - Find mutual connections or shared affiliations
15. Engagement Preferences - Best time to reach, preferred communication channels
16. Decision Making Style - How they evaluate vendors and make purchasing decisions
17. Budget Authority - Signs of budget availability or fiscal year timing
18. Success Metrics - What KPIs they care about based on their role

Additionally, provide:
- AI Score Reasoning: Why this is a high-value contact (100+ words)
- Relationship Tips: Based on their personality type
- Pain Points: Specific to their role and industry
- Outreach Approach: Multi-paragraph personalized approach"""
    
    # Call Perplexity API
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {PERPLEXITY_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional profile-building assistant. Generate comprehensive, actionable intelligence."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,
            "max_tokens": 4000
        }
    )
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        print(f"Error: {response.status_code}")
        return None

def parse_enrichment_response(enrichment_text, contact):
    """
    Parse the Perplexity response into structured fields
    """
    # Initialize all fields
    enriched_data = {
        "name": contact.get("firstname", "") + " " + contact.get("lastname", ""),
        "company": contact.get("company", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "linkedin": contact.get("linkedin", ""),
        "enrichment_date": datetime.now().isoformat(),
    }
    
    # Parse sections (this is simplified - you might want more sophisticated parsing)
    sections = enrichment_text.split("\n\n")
    
    for section in sections:
        if "Overview" in section:
            enriched_data["overview"] = section
        elif "Background" in section:
            enriched_data["background"] = section
        elif "Education" in section:
            enriched_data["education"] = section
        elif "Recent" in section and "News" in section:
            enriched_data["recent_news"] = section
        elif "Recent Mentions" in section:
            enriched_data["recent_mentions"] = section
        elif "Myers" in section or "MBTI" in section:
            enriched_data["myers_briggs"] = section
            # Extract MBTI type (ENTJ, INTJ, etc.)
            for mbti_type in ["ENTJ", "INTJ", "ENTP", "INTP", "ENFJ", "INFJ", "ENFP", "INFP",
                             "ESTJ", "ISTJ", "ESTP", "ISTP", "ESFJ", "ISFJ", "ESFP", "ISFP"]:
                if mbti_type in section:
                    enriched_data["mbti_type"] = mbti_type
                    break
        elif "Pain Points" in section:
            enriched_data["pain_points"] = section
        elif "Relationship Tips" in section:
            enriched_data["relationship_tips"] = section
        elif "Outreach Approach" in section:
            enriched_data["outreach_approach"] = section
        elif "Talking Points" in section or "talking points" in section:
            enriched_data["talking_points"] = section
        elif "AI Score Reasoning" in section:
            enriched_data["ai_score_reasoning"] = section
    
    # Add the full response as perplexity_insights
    enriched_data["perplexity_insights"] = enrichment_text
    
    return enriched_data

def update_hubspot(contact_id, enriched_data):
    """
    Update HubSpot with the enriched data
    """
    # Prepare HubSpot properties
    properties = {
        "perplexity_insights": enriched_data.get("perplexity_insights", "")[:65000],  # HubSpot limit
        "myers_briggs_type": enriched_data.get("mbti_type", ""),
        "pain_points": enriched_data.get("pain_points", "")[:5000],
        "relationship_tips": enriched_data.get("relationship_tips", "")[:5000],
        "outreach_approach": enriched_data.get("outreach_approach", "")[:5000],
        "talking_points": enriched_data.get("talking_points", "")[:5000],
        "ai_score_reasoning": enriched_data.get("ai_score_reasoning", "")[:5000],
        "enrichment_date": enriched_data.get("enrichment_date", ""),
        "recent_news": enriched_data.get("recent_news", "")[:5000],
    }
    
    # Update contact
    hubspot.crm.contacts.basic_api.update(
        contact_id=contact_id,
        simple_public_object_input={"properties": properties}
    )
    
    # Add note about the update
    note = f"✅ Enriched with Perplexity AI on {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    note += f"Key Insights:\n{enriched_data.get('ai_score_reasoning', '')[:500]}"
    
    # Create engagement note
    hubspot.crm.objects.notes.basic_api.create(
        simple_public_object_input={
            "properties": {
                "hs_note_body": note
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 10}]
                }
            ]
        }
    )

def update_notion(enriched_data):
    """
    Update or create Notion page with enriched data
    """
    # Create rich text for long fields
    def make_rich_text(text):
        return [{"text": {"content": text[:2000]}}] if text else []
    
    properties = {
        "Name": {"title": [{"text": {"content": enriched_data.get("name", "")}}]},
        "Company": {"rich_text": make_rich_text(enriched_data.get("company", ""))},
        "Email": {"email": enriched_data.get("email")} if enriched_data.get("email") else {"email": None},
        "Phone": {"phone_number": enriched_data.get("phone")} if enriched_data.get("phone") else {"phone_number": None},
        "LinkedIn": {"url": enriched_data.get("linkedin")} if enriched_data.get("linkedin") else {"url": None},
        "Myers-Briggs Type": {"select": {"name": enriched_data.get("mbti_type", "Unknown")}},
        "AI Insights": {"rich_text": make_rich_text(enriched_data.get("ai_score_reasoning", ""))},
        "Perplexity Insights": {"rich_text": make_rich_text(enriched_data.get("perplexity_insights", ""))},
        "Pain Points": {"rich_text": make_rich_text(enriched_data.get("pain_points", ""))},
        "Relationship Tips": {"rich_text": make_rich_text(enriched_data.get("relationship_tips", ""))},
        "Outreach Approach": {"rich_text": make_rich_text(enriched_data.get("outreach_approach", ""))},
        "Talking Points": {"rich_text": make_rich_text(enriched_data.get("talking_points", ""))},
        "Enrichment Date": {"date": {"start": enriched_data.get("enrichment_date", datetime.now().isoformat())}},
    }
    
    # Create the page
    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties=properties
    )

def main():
    """
    Main enrichment pipeline
    """
    print("🚀 Starting Perplexity Deep Enrichment Pipeline")
    print("=" * 60)
    
    # Get contacts from HubSpot
    contacts = hubspot.crm.contacts.basic_api.get_page(limit=10, properties=["firstname", "lastname", "company", "email", "phone", "linkedin"])
    
    enriched_count = 0
    
    for contact in contacts.results:
        props = contact.properties
        name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
        company = props.get('company', '')
        linkedin = props.get('linkedin', '')
        
        if not name or not company:
            continue
        
        print(f"\n📊 Enriching: {name} at {company}")
        
        # Get enrichment from Perplexity
        enrichment_text = perplexity_enrich(name, company, linkedin)
        
        if enrichment_text:
            # Parse the response
            enriched_data = parse_enrichment_response(enrichment_text, props)
            
            # Update HubSpot
            update_hubspot(contact.id, enriched_data)
            print(f"  ✅ Updated HubSpot")
            
            # Update Notion
            update_notion(enriched_data)
            print(f"  ✅ Created Notion page")
            
            enriched_count += 1
            
            # Rate limit
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print(f"✨ Enrichment Complete! Processed {enriched_count} contacts")
    print(f"📊 Check your Notion database for the rich profiles")

if __name__ == "__main__":
    main()
    