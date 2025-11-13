#!/usr/bin/env python3
"""
LOAN CALL GENERATOR - LENDING-FOCUSED COLD CALL SCRIPTS
Domain: SBA 504, SBA 7(a), Conventional Lending
Generates 3 personalized 30-45 second call openers with objection handling
Returns strict JSON for safe parsing and database storage
"""

import json
import csv
import sys
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
try:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env")
        sys.exit(1)
    client = OpenAI(api_key=api_key)
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

MODEL = "gpt-4"
BANNED_TERMS = [
    "fintech", "software", "platform", "app", "digital tool", 
    "AI", "SaaS", "automation", "dashboard", "analytics",
    "CRM", "workflow", "integration", "database"
]
MAX_REGENERATIONS = 2

# ============================================================================
# PROMPT BUILDER
# ============================================================================

def _build_prompt(contact: Dict[str, Any], provider_name: Optional[str] = None) -> str:
    """Builds tightly-scoped prompt for cold-call scripts with strict JSON output"""

    provider = provider_name or "our team"

    return f"""
You are writing three concise cold-call OPENERS (30-45 seconds each, 60-85 words).
Return STRICT JSON ONLY.

Each variant must have:
- "style": one of ["Problem-Agitate-Solve","Social Proof","Value-First Consultative"]
- "lines": array of 3-6 short lines (max 18 words each)
- "cta": single low-pressure question
- "objections": dict with "busy", "not_interested", "send_info" replies

PHONE STYLE (CRITICAL):
- Direct, ROI-focused. Assume ESTJ/C-type: data-driven, brief.
- Start with permission: "Got 30 seconds?" 
- Reference something SPECIFIC about {contact.get('company')} or their role
- State a LENDING PROBLEM they face (strategy, credit, timing, risk, structure, compliance, rates)
- Acknowledge impact/cost
- Brief social proof (similar banks solved this)
- NO fintech/software/platform/app/AI/automation suggestions
- NO fluffy openers
- Max 85 words total

WHAT WE OFFER (only):
- Flexible credit, nationwide reach, quick closings, story lending
- SBA 504, 7(a), Conventional products

GUARDRAILS:
- We are a LENDER (capital/credit only)
- NOT fintech, software, platforms, apps, AI, automation, dashboards, CRM, tools
- Solutions must be lending-related ONLY

CONTACT:
Name: {contact.get('name', 'Unknown')}
Company: {contact.get('company', 'Unknown')}
Title: {contact.get('title', 'Unknown')}
MBTI: {contact.get('mbti', 'Unknown')}
DISC: {contact.get('disc', 'Unknown')}
News: {contact.get('news', 'Unknown')}
Needs: {contact.get('value_props', 'Unknown')}

OUTPUT (JSON ONLY, no prose):
{{
  "variant_1": {{
    "style": "Problem-Agitate-Solve",
    "lines": ["<line 1>", "<line 2>", "<line 3>", "<line 4>"],
    "cta": "<question>",
    "objections": {{"busy": "<reply>", "not_interested": "<reply>", "send_info": "<reply>"}}
  }},
  "variant_2": {{...}},
  "variant_3": {{...}}
}}
""".strip()


# ============================================================================
# API CALLS
# ============================================================================

def _call_model(prompt: str) -> str:
    """Call OpenAI API"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=2000
    )
    return resp.choices[0].message.content.strip()


def _contains_banned(text: str) -> bool:
    """Check for banned terms"""
    lower = text.lower()
    return any(term.lower() in lower for term in BANNED_TERMS)


# ============================================================================
# GENERATION LOGIC
# ============================================================================

def generate_call_variants_api(
    contact_data: Dict[str, Any],
    provider_name: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Generate 3 cold-call variants with strict JSON output.
    Auto-regenerates if banned terms or parse errors occur.
    """

    prompt = _build_prompt(contact_data, provider_name)
    raw = None

    for attempt in range(MAX_REGENERATIONS + 1):
        if verbose:
            print(f"  [Attempt {attempt + 1}/{MAX_REGENERATIONS + 1}]", end=" ")

        raw = _call_model(prompt)

        # Check for banned terms
        if _contains_banned(raw):
            if verbose:
                print("⚠️  Banned terms detected")
            prompt += "\n\nREGENERATE: Remove fintech/software/platform/app/AI/automation. Lending only."
            continue

        # Try JSON parse
        try:
            data = json.loads(raw)

            # Double-check parsed JSON
            joined = json.dumps(data)
            if _contains_banned(joined):
                if verbose:
                    print("⚠️  Banned terms in JSON")
                prompt += "\n\nREGENERATE: Remove disallowed terms from JSON."
                continue

            # Verify all variants
            for key in ["variant_1", "variant_2", "variant_3"]:
                if key not in data:
                    raise ValueError(f"Missing {key}")

            if verbose:
                print("✅ Valid")

            return data

        except Exception as e:
            if verbose:
                print(f"❌ Parse error")
            prompt += "\n\nREGENERATE: Return VALID JSON only. No prose."
            continue

    # Fallback
    return {
        "error": f"Failed after {MAX_REGENERATIONS + 1} attempts",
        "raw": raw[:300] if raw else None
    }


# ============================================================================
# BATCH PROCESSING
# ============================================================================

def process_csv_to_jsonl(
    input_csv: str,
    output_jsonl: str,
    provider_name: Optional[str] = None,
    verbose: bool = False
) -> None:
    """Process CSV with enriched contacts, generate calls, output JSONL"""

    if not os.path.exists(input_csv):
        print(f"❌ CSV not found: {input_csv}")
        return

    total = 0
    f_in = open(input_csv, newline='', encoding='utf-8')
    f_out = open(output_jsonl, "w", encoding="utf-8")

    try:
        reader = csv.DictReader(f_in)

        for i, row in enumerate(reader, 1):
            if verbose:
                print(f"[{i}] {row.get('name')} @ {row.get('company')}")

            result = generate_call_variants_api(row, provider_name=provider_name, verbose=verbose)

            record = {
                "contact": {
                    "name": row.get("name"),
                    "company": row.get("company"),
                    "title": row.get("title")
                },
                "variants": result
            }

            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
            total += 1

    finally:
        f_in.close()
        f_out.close()

    print(f"✅ Processed {total} contacts. Output: {output_jsonl}")


# ============================================================================
# FORMATTING / DISPLAY
# ============================================================================

def print_call_report(contact_data: Dict[str, Any], variants: Dict[str, Any]) -> None:
    """Pretty print the call scripts"""

    print()
    print("="*80)
    print(f"☎️  CALL SCRIPTS FOR: {contact_data.get('name')} @ {contact_data.get('company')}")
    print(f"   Title: {contact_data.get('title')}")
    print(f"   Profile: {contact_data.get('mbti')} / {contact_data.get('disc')}")
    print("="*80)
    print()

    if "error" in variants:
        print(f"❌ ERROR: {variants['error']}")
        if variants.get('raw'):
            print(f"Raw (first 300 chars): {variants['raw']}")
        return

    for i in range(1, 4):
        key = f"variant_{i}"
        if key not in variants:
            continue

        v = variants[key]
        print(f"VARIANT {i}: {v.get('style', 'Unknown')}")
        print("-" * 80)
        print("Script:")
        for line in v.get('lines', []):
            print(f"  • {line}")
        print(f"\nCTA: {v.get('cta', 'N/A')}")
        print("\nIf they say...")
        for obj_type, reply in v.get('objections', {}).items():
            print(f"  '{obj_type}': {reply}")
        print()
        print("="*80)
        print()


# ============================================================================
# MAIN / TEST
# ============================================================================

if __name__ == "__main__":
    print()
    print("🚀 LOAN CALL GENERATOR")
    print("Domain: SBA 504 | 7(a) | Conventional")
    print("Output: 3 cold-call openers + objection handling")
    print()

    # Test contact
    test_contact = {
        "name": "Bart Hutchins",
        "company": "California Bank & Trust",
        "title": "Experienced CRE Lender | 20+ Years",
        "mbti": "ESTJ",
        "disc": "C-Type",
        "news": "Expanding portfolio; rising rates; compliance focus",
        "value_props": "Flexible credit; nationwide; quick closings; story lending"
    }

    print(f"Generating for: {test_contact['name']}")
    print(f"Company: {test_contact['company']}")
    print()

    # Generate
    variants = generate_call_variants_api(test_contact, provider_name="Summit Capital", verbose=True)

    # Display
    print_call_report(test_contact, variants)

    print("="*80)
    print("✅ COMPLETE")
    print("="*80)
    print()
    print("Batch mode:")
    print("  from loan_call_generator import process_csv_to_jsonl")
    print("  process_csv_to_jsonl('contacts.csv', 'calls.jsonl', 'Summit Capital', verbose=True)")
    print()
