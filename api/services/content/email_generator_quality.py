#!/usr/bin/env python3
"""
EMAIL GENERATOR - AI-POWERED QUALITY CONTENT
Generates 3 personalized email variants using OpenAI GPT-4
Replaces template-based emails with research-backed AI content
"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
try:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env file")
        print("Make sure you have:")
        print("  OPENAI_API_KEY=sk-...")
        sys.exit(1)
    client = OpenAI(api_key=api_key)
except Exception as e:
    print(f"❌ ERROR initializing OpenAI: {e}")
    sys.exit(1)

def generate_email_variants(contact_data, enrichment_data=None, business_profile=None):
    """
    Generate 3 high-quality, personalized email variants

    Args:
        contact_data (dict): Contact info
            - firstname (str): First name
            - lastname (str): Last name
            - company (str): Company name
            - jobtitle (str): Job title
            - email (str): Email address

        enrichment_data (dict, optional): Enrichment data
            - linkedin_summary (str): What they do
            - recent_news (str): Recent company news
            - signals (str): Buying signals found
            - industry (str): Industry

        business_profile (dict, optional): Your business info
            - what_you_do (str): Your value prop
            - target (str): Who you serve
            - value_prop (str): Key benefit
            - case_study (str): Success story

    Returns:
        list: 3 dicts with keys: subject, body, style
    """

    # Build prospect context
    prospect_context = f"""
PROSPECT:
Name: {contact_data.get('firstname', 'Unknown')} {contact_data.get('lastname', '')}
Company: {contact_data.get('company', 'Unknown')}
Title: {contact_data.get('jobtitle', 'Unknown')}
Email: {contact_data.get('email', 'Unknown')}
"""

    # Add enrichment if available
    if enrichment_data:
        if enrichment_data.get('linkedin_summary'):
            prospect_context += f"\nBackgroundRoleBackground: {enrichment_data['linkedin_summary']}"
        if enrichment_data.get('recent_news'):
            prospect_context += f"\nRecent News: {enrichment_data['recent_news']}"
        if enrichment_data.get('signals'):
            prospect_context += f"\nBuying Signals: {enrichment_data['signals']}"
        if enrichment_data.get('industry'):
            prospect_context += f"\nIndustry: {enrichment_data['industry']}"

    # Build sender/business context
    business_context = ""
    if business_profile:
        business_context = f"""
YOUR BUSINESS:
What you do: {business_profile.get('what_you_do', '')}
Who you serve: {business_profile.get('target', '')}
Value proposition: {business_profile.get('value_prop', '')}
Proof point: {business_profile.get('case_study', '')}
"""

    # Define 3 distinct email approaches
    email_approaches = [
        {
            "style": "Problem-Agitate-Solve",
            "description": "Lead with relevant problem, acknowledge impact, present solution",
            "instructions": f"""Write a short, highly personalized B2B sales email using the Problem-Agitate-Solve framework.

{prospect_context}

{business_context}

REQUIREMENTS:
- Reference something SPECIFIC about their company, role, or recent news
- Lead with a problem they LIKELY face in their industry/role
- Acknowledge the impact/cost of that problem
- Briefly mention how similar companies solved it
- Keep it under 80 words
- Natural, conversational tone - sounds like a real person
- NO generic openers like "I hope this email finds you well" or "I wanted to reach out"
- End with a simple, low-pressure question or observation

FORMAT:
Subject: [compelling subject line - no clickbait]
Body: [email body in conversational tone]

Generate NOW:"""
        },
        {
            "style": "Social Proof",
            "description": "Reference similar success, build credibility, invite conversation",
            "instructions": f"""Write a short, highly personalized B2B sales email using social proof.

{prospect_context}

{business_context}

REQUIREMENTS:
- Reference a similar company or recent success story (make it relevant to THEIR situation)
- Connect that proof point to something specific about THEM
- Show that you understand their world
- Keep it under 80 words
- Natural, conversational tone
- NO generic openers
- End with offering to share more details if relevant

FORMAT:
Subject: [compelling subject line]
Body: [email body]

Generate NOW:"""
        },
        {
            "style": "Value-First Consultative",
            "description": "Offer genuine value with no pitch, build rapport, then explore fit",
            "instructions": f"""Write a short, highly personalized B2B sales email offering value first.

{prospect_context}

{business_context}

REQUIREMENTS:
- Reference something specific about their company/role/industry
- Offer something useful (insight, benchmark data, relevant article, intro to someone) with NO strings attached
- Show you did research and understand their situation
- Keep it under 80 words
- Natural, conversational tone - helpful, not salesy
- NO generic openers
- Signature question: "Would this be valuable?"

FORMAT:
Subject: [compelling subject line]
Body: [email body]

Generate NOW:"""
        }
    ]

    variants = []

    for i, approach in enumerate(email_approaches, 1):
        try:
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a world-class B2B sales copywriter who writes highly personalized, research-backed emails that get responses. You never use templates, generic language, or corporate-speak. Every email is unique to the prospect. You understand their world and speak their language."
                    },
                    {
                        "role": "user",
                        "content": approach["instructions"]
                    }
                ],
                temperature=0.7,
                max_tokens=400
            )

            # Extract the response
            content = response.choices[0].message.content.strip()

            # Parse subject and body
            subject = ""
            body = ""
            lines = content.split('\n')

            for line in lines:
                if line.startswith('Subject:'):
                    subject = line.replace('Subject:', '').strip()
                elif line.startswith('Body:'):
                    body = line.replace('Body:', '').strip()
                elif body:  # Continue adding to body
                    if line.strip():
                        body += "\n" + line.strip()

            # Clean up
            if not subject:
                subject = "Quick thought about your team"
            if not body:
                body = content[:200]

            variant = {
                'subject': subject,
                'body': body.strip(),
                'style': approach['style'],
                'description': approach['description']
            }

            variants.append(variant)
            print(f"✅ Generated {i}/3: {approach['style']}")

        except Exception as e:
            print(f"❌ Error generating {approach['style']}: {e}")

            # Fallback template (generic but functional)
            variants.append({
                'subject': f"Thought about {contact_data.get('company', 'your company')}",
                'body': f"Hi {contact_data.get('firstname', 'there')},\n\nI work with companies like {contact_data.get('company', 'yours')} to [your value prop]. Would be worth a conversation?",
                'style': approach['style'] + " (Fallback)",
                'description': "Template fallback due to API error"
            })

    return variants


def validate_email_quality(email):
    """
    Quality check - does this email pass basic standards?

    Args:
        email (dict): Email with subject and body

    Returns:
        tuple: (bool, str) - (pass/fail, reason)
    """

    body = (email.get('body', '') or "").lower()
    subject = (email.get('subject', '') or "").lower()

    # RED FLAGS - Generic openers that kill response rates
    bad_openers = [
        'i hope this email finds you well',
        'i hope you are doing well',
        'i am reaching out',
        'i wanted to reach out',
        'i came across your profile',
        'saw your profile',
        'we help companies',
        'world-class',
        'industry-leading',
        'best-in-class'
    ]

    for bad in bad_openers:
        if bad in body or bad in subject:
            return False, f"Generic phrase detected: '{bad}'"

    # Must be reasonably short (under 500 chars)
    if len(body) > 500:
        return False, "Too long (>500 chars) - people won't read it"

    # Must have some substance (over 50 chars)
    if len(body) < 50:
        return False, "Too short (<50 chars) - needs more context"

    # Should have clear CTA or question
    if not ('?' in body or 'worth' in body or 'thoughts' in body):
        return False, "No clear call-to-action or question"

    return True, "✓ Looks good"


def print_email_report(contact_data, variants):
    """Pretty print email variants with quality scores"""

    print()
    print("="*70)
    print(f"📧 EMAIL VARIANTS FOR: {contact_data.get('firstname', '')} {contact_data.get('lastname', '')} @ {contact_data.get('company', '')}")
    print("="*70)
    print()

    for i, variant in enumerate(variants, 1):
        print(f"VARIANT {i}: {variant['style']}")
        print(f"Description: {variant['description']}")
        print("-" * 70)
        print(f"Subject: {variant['subject']}")
        print()
        print(f"Body:\n{variant['body']}")
        print()

        # Quality check
        passed, reason = validate_email_quality(variant)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"Quality: {status} - {reason}")
        print()
        print("="*70)
        print()


# ============================================================================
# TEST/DEMO
# ============================================================================

if __name__ == "__main__":
    print()
    print("🚀 SALES ANGEL - EMAIL GENERATOR (QUALITY VERSION)")
    print()

    # Test with sample prospect
    test_contact = {
        'firstname': 'Matt',
        'lastname': 'Wilson',
        'company': 'River City Bank',
        'jobtitle': 'SVP Commercial Lending',
        'email': 'matt.wilson@rivercitybank.com'
    }

    # Test with sample enrichment
    test_enrichment = {
        'linkedin_summary': '20+ years in commercial lending, recently promoted to SVP',
        'recent_news': 'River City Bank opened Sacramento branch, hiring for operations',
        'signals': 'Likely scaling operations, posted about process inefficiency challenges',
        'industry': 'Regional Bank / Commercial Lending'
    }

    # Test with sample business profile
    test_business = {
        'what_you_do': 'SBA lending automation software',
        'target': 'Regional banks and CDCs processing SBA loans',
        'value_prop': 'Cut SBA 504/7a processing time by 50%+',
        'case_study': 'Recent bank client: went from 45-day cycle to 21 days'
    }

    print("Generating 3 email variants...")
    print("(This uses OpenAI GPT-4, so it may take 10-15 seconds)")
    print()

    # Generate variants
    variants = generate_email_variants(test_contact, test_enrichment, test_business)

    # Display with quality scoring
    print_email_report(test_contact, variants)

    print("="*70)
    print("✅ EMAIL GENERATION COMPLETE")
    print("="*70)
    print()
    print("Next steps:")
    print("1. Review the variants above")
    print("2. Choose your favorite or combine best parts")
    print("3. Send test batch to 5-10 prospects")
    print("4. Track open rates and responses")
    print()
