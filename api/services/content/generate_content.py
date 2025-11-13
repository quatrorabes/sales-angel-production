#!/usr/bin/env python3
"""
Sales Angel - Content Generation Engine
Takes Perplexity intelligence → Generates personalized outreach via OpenAI
"""

import os
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_FILE = "sales_angel.db"

class ContentGenerator:
    """
    Generates hyper-personalized outreach content using enriched intelligence
    3 Emails + 3 Call Scripts + LinkedIn Request + Follow-ups
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required in .env")
        self.model = "gpt-4o"  # Latest and best model

    async def generate_email_sequence(self, contact: Dict, profile: str) -> Dict:
        """Generate 3-email sequence"""

        name = f"{contact['firstname']} {contact['lastname']}"
        company = contact['company']
        title = contact.get('jobtitle', 'your role')

        prompt = f"""
You are a world-class B2B sales copywriter. Generate a 3-email outreach sequence.

**TARGET CONTACT:**
Name: {name}
Title: {title}
Company: {company}

**INTELLIGENCE PROFILE:**
{profile[:3000]}

**REQUIREMENTS:**
1. Hyper-personalized using intelligence (reference specific details)
2. Professional but conversational tone
3. Short and scannable (150-200 words each)
4. Strong value propositions
5. Clear call-to-action
6. Reference their recent work, achievements, or posts

**Generate exactly 3 emails:**

EMAIL 1: INTRODUCTION (Day 1)
- Hook with specific detail from their profile
- Establish credibility quickly
- One clear value proposition
- Soft ask for 15-min call

EMAIL 2: VALUE ADD (Day 4 - if no response)
- Share relevant insight or resource
- Reference industry challenge they face
- Reinforce value
- Another CTA

EMAIL 3: BREAKUP (Day 7 - if no response)
- Acknowledge they're busy
- Final value statement
- Leave door open
- Different CTA (resources, connection, etc.)

Format as:
---EMAIL 1---
Subject: [subject line]

[body]

---EMAIL 2---
Subject: [subject line]

[body]

---EMAIL 3---
Subject: [subject line]

[body]
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert B2B sales copywriter who writes hyper-personalized, conversion-optimized emails."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        content = response.choices[0].message.content

        # Parse the 3 emails
        emails = self._parse_emails(content)

        return {
            'email_1': emails.get('email_1', {}),
            'email_2': emails.get('email_2', {}),
            'email_3': emails.get('email_3', {}),
            'generated_at': datetime.now().isoformat()
        }

    async def generate_call_scripts(self, contact: Dict, profile: str) -> Dict:
        """Generate 3 call scripts"""

        name = f"{contact['firstname']} {contact['lastname']}"
        company = contact['company']
        title = contact.get('jobtitle', 'your role')

        prompt = f"""
You are a world-class sales trainer. Generate 3 phone call scripts.

**TARGET CONTACT:**
Name: {name}
Title: {title}
Company: {company}

**INTELLIGENCE PROFILE:**
{profile[:3000]}

**Generate 3 scripts:**

SCRIPT 1: COLD CALL (First contact)
- Permission-based opening
- Reason for call (reference specific detail)
- Value hypothesis
- Ask for meeting
- Handle objections

SCRIPT 2: FOLLOW-UP CALL (After email/voicemail)
- Reference previous touchpoint
- New insight or value
- Discovery questions
- Next steps

SCRIPT 3: EXECUTIVE BRIEFING (If you get through)
- Executive summary opener
- 3 key discovery questions based on their role
- Value alignment
- Clear next steps

Format each script with:
- Opening
- Body/Value Prop
- Discovery Questions (3-5)
- Objection Handling
- Close/Next Steps

Make them conversational, not robotic!
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert sales trainer who creates effective, natural call scripts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )

        content = response.choices[0].message.content

        return {
            'script_1_cold_call': content.split('SCRIPT 2')[0] if 'SCRIPT 2' in content else content,
            'script_2_followup': content.split('SCRIPT 2')[1].split('SCRIPT 3')[0] if 'SCRIPT 2' in content and 'SCRIPT 3' in content else '',
            'script_3_executive': content.split('SCRIPT 3')[1] if 'SCRIPT 3' in content else '',
            'generated_at': datetime.now().isoformat()
        }

    async def generate_linkedin_request(self, contact: Dict, profile: str) -> Dict:
        """Generate LinkedIn connection request + message"""

        name = f"{contact['firstname']} {contact['lastname']}"
        company = contact['company']

        prompt = f"""
Generate a LinkedIn connection request for:

Name: {name}
Company: {company}

**INTELLIGENCE:**
{profile[:1500]}

Create:
1. Connection note (300 chars max - LinkedIn limit)
2. Follow-up message (if they accept)

Be warm, professional, reference something specific from their profile.
No sales pitch in connection request!
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You write engaging LinkedIn connection requests that get accepted."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        content = response.choices[0].message.content

        parts = content.split('Follow-up')

        return {
            'connection_note': parts[0].strip(),
            'followup_message': parts[1].strip() if len(parts) > 1 else '',
            'generated_at': datetime.now().isoformat()
        }

    async def generate_all_content(self, contact_id: int) -> Dict:
        """Generate complete outreach package"""

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        row = cursor.fetchone()

        if not row:
            return {'error': 'Contact not found'}

        contact = dict(row)

        if not contact.get('profile_content'):
            return {'error': 'Contact not enriched - run enrichment first'}

        print(f"\n{'='*80}")
        print(f"✍️  GENERATING CONTENT FOR: {contact['firstname']} {contact['lastname']}")
        print(f"{'='*80}")

        profile = contact['profile_content']

        # Generate all content in parallel
        print("\n📧 Generating email sequence...")
        emails = await self.generate_email_sequence(contact, profile)

        print("📞 Generating call scripts...")
        scripts = await self.generate_call_scripts(contact, profile)

        print("💼 Generating LinkedIn request...")
        linkedin = await self.generate_linkedin_request(contact, profile)

        # Save to database
        cursor.execute("""
            UPDATE contacts 
            SET content_generated = 1,
                email_1_subject = ?,
                email_1_body = ?,
                email_2_subject = ?,
                email_2_body = ?,
                email_3_subject = ?,
                email_3_body = ?,
                call_script_1 = ?,
                call_script_2 = ?,
                call_script_3 = ?,
                linkedin_note = ?,
                linkedin_followup = ?,
                content_generated_at = ?
            WHERE id = ?
        """, (
            emails['email_1'].get('subject', ''),
            emails['email_1'].get('body', ''),
            emails['email_2'].get('subject', ''),
            emails['email_2'].get('body', ''),
            emails['email_3'].get('subject', ''),
            emails['email_3'].get('body', ''),
            scripts['script_1_cold_call'],
            scripts['script_2_followup'],
            scripts['script_3_executive'],
            linkedin['connection_note'],
            linkedin['followup_message'],
            datetime.now().isoformat(),
            contact_id
        ))

        conn.commit()
        conn.close()

        print(f"\n{'='*80}")
        print(f"✅ CONTENT PACKAGE COMPLETE")
        print(f"{'='*80}")
        print(f"\n📧 3 Email Sequence: ✓")
        print(f"📞 3 Call Scripts: ✓")
        print(f"💼 LinkedIn Request: ✓")
        print(f"\nSaved to database!")

        return {
            'contact_id': contact_id,
            'name': f"{contact['firstname']} {contact['lastname']}",
            'emails': emails,
            'scripts': scripts,
            'linkedin': linkedin
        }

    def _parse_emails(self, content: str) -> Dict:
        """Parse email content into structured format"""
        emails = {}

        parts = content.split('---EMAIL ')
        for i, part in enumerate(parts[1:], 1):  # Skip first empty part
            if f'{i}---' in part:
                email_content = part.split('---')[1].strip()

                # Extract subject and body
                lines = email_content.split('\n')
                subject = ''
                body = ''

                for line in lines:
                    if line.startswith('Subject:'):
                        subject = line.replace('Subject:', '').strip()
                    else:
                        body += line + '\n'

                emails[f'email_{i}'] = {
                    'subject': subject,
                    'body': body.strip()
                }

        return emails


async def generate_content_for_contact(contact_id: int):
    """Generate complete outreach package for one contact"""
    generator = ContentGenerator()
    result = await generator.generate_all_content(contact_id)
    return result


async def generate_content_for_hot_leads():
    """Generate content for all hot leads"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, firstname, lastname, company, enriched
        FROM contacts 
        WHERE hot_lead = 1
    """)

    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()

    print(f"\n{'='*80}")
    print(f"🎯 CONTENT GENERATION: {len(leads)} HOT LEADS")
    print(f"{'='*80}")
    print(f"\nGenerating:")
    print(f"  • 3 emails per contact ({len(leads) * 3} total)")
    print(f"  • 3 call scripts per contact ({len(leads) * 3} total)")
    print(f"  • 1 LinkedIn request per contact ({len(leads)} total)")
    print(f"\nEstimated time: ~{len(leads) * 15} seconds ({len(leads) * 0.25:.1f} minutes)")
    print(f"Estimated cost: ~${len(leads) * 0.05:.2f}")

    # Check which ones are enriched
    unenriched = [l for l in leads if not l['enriched']]
    if unenriched:
        print(f"\n⚠️  WARNING: {len(unenriched)} contacts not enriched yet:")
        for lead in unenriched[:5]:
            print(f"   • {lead['firstname']} {lead['lastname']} at {lead['company']}")
        print(f"\nRun enrichment first: python ultimate_enrichment.py hot")
        return

    print(f"\nPress Ctrl+C to cancel, or wait 5 seconds...")
    await asyncio.sleep(5)

    generator = ContentGenerator()
    results = []

    for idx, lead in enumerate(leads, 1):
        print(f"\n[{idx}/{len(leads)}] {lead['firstname']} {lead['lastname']} at {lead['company']}")

        try:
            result = await generator.generate_all_content(lead['id'])
            results.append(result)

            if idx < len(leads):
                await asyncio.sleep(2)  # Rate limiting

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

    print(f"\n{'='*80}")
    print(f"🎉 CONTENT GENERATED FOR {len(results)}/{len(leads)} LEADS!")
    print(f"{'='*80}")

    return results


async def main():
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "hot":
            results = await generate_content_for_hot_leads()
        elif command.isdigit():
            result = await generate_content_for_contact(int(command))

            # Display the content
            print(f"\n{'='*80}")
            print(f"📧 EMAIL 1")
            print(f"{'='*80}")
            print(f"Subject: {result['emails']['email_1'].get('subject', '')}")
            print(f"\n{result['emails']['email_1'].get('body', '')}")
        else:
            print("Usage: python generate_content.py <contact_id>")
            print("       python generate_content.py hot")
    else:
        print("\n✍️  Sales Angel - Content Generation Engine")
        print("="*80)
        print("\nGenerates personalized outreach from enriched intelligence:")
        print("  • 3-email sequence (intro, value-add, breakup)")
        print("  • 3 call scripts (cold, follow-up, executive)")
        print("  • LinkedIn connection request + follow-up")
        print("\nUsage:")
        print("  python generate_content.py <id>    # Generate for one contact")
        print("  python generate_content.py hot     # Generate for all hot leads")


if __name__ == "__main__":
    asyncio.run(main())
