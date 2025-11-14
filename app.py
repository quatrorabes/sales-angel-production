"""
Sales Angel - HubSpot Webhook + Perplexity Integration

- Framework: FastAPI
- External APIs:
    - HubSpot CRM v3 (contacts)
    - Perplexity Chat Completions (model: sonar-pro)
- Environment variables (set in Railway):
    - HUBSPOT_API_KEY
    - PERPLEXITY_API_KEY

Behavior:
- POST /webhooks/hubspot with JSON: {"objectId": "<hubspot_contact_id>"}
- Fetches contact (firstname, lastname, company, email, jobtitle) from HubSpot
- Generates:
    - 3 email variants (subject + body)
    - 3 call scripts
- Writes results back to HubSpot contact properties:
    - email_framework   (multi-line text)
    - call_framework    (multi-line text)
    - last_enrichment   (date, YYYY-MM-DD)
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any

import requests
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# -------------------------------------------------------------------------
# Environment & Logging
# -------------------------------------------------------------------------

load_dotenv()

HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("sales_angel_app")

if not HUBSPOT_API_KEY:
    logger.error("HUBSPOT_API_KEY is not configured")

if not PERPLEXITY_API_KEY:
    logger.error("PERPLEXITY_API_KEY is not configured")

# -------------------------------------------------------------------------
# FastAPI app
# -------------------------------------------------------------------------

app = FastAPI(
    title="Sales Angel Production API",
    description="HubSpot webhook integration with Perplexity sonar-pro",
    version="1.0.0",
)

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------

HUBSPOT_BASE_URL = "https://api.hubapi.com"
PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "sonar-pro"


# -------------------------------------------------------------------------
# Perplexity helpers
# -------------------------------------------------------------------------

def call_perplexity(prompt: str, max_tokens: int = 300) -> str:
    """
    Call Perplexity sonar-pro with a simple user prompt.
    Returns the assistant message content as plain text.
    """
    if not PERPLEXITY_API_KEY:
        raise RuntimeError("PERPLEXITY_API_KEY not configured")

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }

    response = requests.post(PERPLEXITY_URL, headers=headers, json=payload, timeout=20)
    if response.status_code != 200:
        logger.error(
            f"Perplexity API error {response.status_code}: {response.text[:500]}"
        )
        raise RuntimeError(f"Perplexity API error {response.status_code}")

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return content.strip()


def generate_email_variants(
    prospect_name: str,
    company: str,
    job_title: str = "",
) -> List[Dict[str, Any]]:
    """
    Generate 3 email variants: Direct, Warm, Consultative.
    Each item: {"style": str, "subject": str, "body": str}
    """
    styles = [
        ("Direct", "Write a concise, direct cold email."),
        ("Warm", "Write a warm, relationship-building cold email."),
        ("Consultative", "Write a consultative, question-led cold email."),
    ]

    variants: List[Dict[str, Any]] = []

    for style_name, style_desc in styles:
        prompt = (
            f"You are a senior B2B sales copywriter.\n"
            f"Prospect: {prospect_name}\n"
            f"Company: {company or 'Unknown Company'}\n"
            f"Title: {job_title or 'Unknown title'}\n\n"
            f"{style_desc}\n"
            f"Output format strictly as:\n"
            f"Subject: <one compelling subject line>\n"
            f"Body:\n"
            f"<email body, 4–7 short paragraphs>"
        )

        try:
            raw = call_perplexity(prompt, max_tokens=400)

            subject = "N/A"
            body = raw

            if "Subject:" in raw:
                parts = raw.split("Body:", 1)
                subject_line = parts[0].replace("Subject:", "").strip()
                subject = subject_line[:150]
                if len(parts) > 1:
                    body = parts[1].strip()

            variants.append(
                {
                    "style": style_name,
                    "subject": subject,
                    "body": body,
                }
            )
        except Exception as e:
            logger.error(f"Email generation failed for style {style_name}: {e}")

    return variants


def generate_call_scripts(
    prospect_name: str,
    company: str,
    job_title: str = "",
) -> List[Dict[str, Any]]:
    """
    Generate 3 call scripts: Value Prop, Rapport, Discovery.
    Each item: {"style": str, "script": str}
    """
    styles = [
        ("Value Prop", "Direct value proposition opening and 3 concise points."),
        ("Rapport", "Start with rapport, then transition to value and ask for time."),
        ("Discovery", "Ask 3–5 strong discovery questions with brief intro and close."),
    ]

    scripts: List[Dict[str, Any]] = []

    for style_name, style_desc in styles:
        prompt = (
            f"You are a senior SDR crafting a cold call script.\n"
            f"Prospect: {prospect_name}\n"
            f"Company: {company or 'Unknown Company'}\n"
            f"Title: {job_title or 'Unknown title'}\n\n"
            f"{style_desc}\n"
            f"Output format strictly as:\n"
            f"Script:\n"
            f"<call script in 6–10 lines>"
        )

        try:
            raw = call_perplexity(prompt, max_tokens=300)
            script_text = raw

            if "Script:" in raw:
                script_text = raw.split("Script:", 1)[1].strip()

            scripts.append(
                {
                    "style": style_name,
                    "script": script_text,
                }
            )
        except Exception as e:
            logger.error(f"Call script generation failed for style {style_name}: {e}")

    return scripts


# -------------------------------------------------------------------------
# HubSpot helpers
# -------------------------------------------------------------------------

def fetch_hubspot_contact(contact_id: str) -> Dict[str, Any]:
    """
    Fetch a contact from HubSpot by ID with selected properties.
    """
    if not HUBSPOT_API_KEY:
        raise RuntimeError("HUBSPOT_API_KEY not configured")

    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json",
    }

    params = {
        "properties": "firstname,lastname,company,email,jobtitle",
    }

    url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/{contact_id}"
    resp = requests.get(url, headers=headers, params=params, timeout=10)

    if resp.status_code != 200:
        logger.error(f"HubSpot fetch error {resp.status_code}: {resp.text[:500]}")
        raise RuntimeError(f"Failed to fetch HubSpot contact: {resp.status_code}")

    return resp.json().get("properties", {}) or {}


def update_hubspot_framework_fields(
    contact_id: str,
    email_variants: List[Dict[str, Any]],
    call_scripts: List[Dict[str, Any]],
) -> bool:
    """
    Update HubSpot contact properties:
        - email_framework
        - call_framework
        - last_enrichment
    """

    if not HUBSPOT_API_KEY:
        logger.error("HUBSPOT_API_KEY not configured")
        return False

    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json",
    }

    # Build multi-line text content for email_framework
    email_lines: List[str] = ["=== SALES ANGEL EMAIL FRAMEWORK ==="]
    for i, v in enumerate(email_variants, start=1):
        email_lines.append(f"\n[{i}] {v.get('style', 'Variant')}")
        email_lines.append(f"Subject: {v.get('subject', 'N/A')}")
        email_lines.append("Body:")
        email_lines.append(v.get("body", "").strip())
        email_lines.append("-" * 60)

    email_text = "\n".join(email_lines)

    # Build multi-line text content for call_framework
    call_lines: List[str] = ["=== SALES ANGEL CALL FRAMEWORK ==="]
    for i, s in enumerate(call_scripts, start=1):
        call_lines.append(f"\n[{i}] {s.get('style', 'Script')}")
        call_lines.append("Script:")
        call_lines.append(s.get("script", "").strip())
        call_lines.append("-" * 60)

    call_text = "\n".join(call_lines)

    payload = {
        "properties": {
            "email_framework": email_text,
            "call_framework": call_text,
            "last_enrichment": datetime.utcnow().strftime("%Y-%m-%d"),
        }
    }

    url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/{contact_id}"
    resp = requests.patch(url, headers=headers, json=payload, timeout=10)

    if resp.status_code == 200:
        logger.info(f"✅ HubSpot updated for contact {contact_id}")
        return True

    logger.error(f"HubSpot update error {resp.status_code}: {resp.text[:500]}")
    return False


# -------------------------------------------------------------------------
# Health endpoint
# -------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "hubspot_configured": bool(HUBSPOT_API_KEY),
        "perplexity_configured": bool(PERPLEXITY_API_KEY),
        "timestamp": datetime.utcnow().isoformat(),
    }


# -------------------------------------------------------------------------
# Webhook endpoint
# -------------------------------------------------------------------------

@app.post("/webhooks/hubspot")
async def hubspot_webhook(payload: Dict[str, Any]):
    """
    HubSpot Webhook:
    Expects JSON: {"objectId": "<hubspot_contact_id>"}
    """
    try:
        contact_id = str(payload.get("objectId") or "").strip()
        if not contact_id:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing objectId in payload"},
            )

        logger.info(f"🔔 HubSpot webhook received for contact: {contact_id}")

        # 1) Fetch contact data
        props = fetch_hubspot_contact(contact_id)
        first_name = props.get("firstname", "") or ""
        last_name = props.get("lastname", "") or ""
        company = props.get("company", "") or ""
        email = props.get("email", "") or ""
        job_title = props.get("jobtitle", "") or ""

        prospect_name = (first_name + " " + last_name).strip() or "Unknown Contact"
        logger.info(f"📧 Enriching: {prospect_name} @ {company or 'Unknown Company'}")

        # 2) Generate content via Perplexity
        email_variants: List[Dict[str, Any]] = []
        call_scripts: List[Dict[str, Any]] = []

        try:
            email_variants = generate_email_variants(prospect_name, company, job_title)
            logger.info(f"✅ Generated {len(email_variants)} email variants")
        except Exception as e:
            logger.error(f"Email generation error: {e}")

        try:
            call_scripts = generate_call_scripts(prospect_name, company, job_title)
            logger.info(f"✅ Generated {len(call_scripts)} call scripts")
        except Exception as e:
            logger.error(f"Call script generation error: {e}")

        # 3) Update HubSpot
        properties_updated = update_hubspot_framework_fields(
            contact_id=contact_id,
            email_variants=email_variants,
            call_scripts=call_scripts,
        )

        response_data = {
            "status": "success",
            "contact_id": contact_id,
            "prospect": prospect_name,
            "company": company or None,
            "email": email or None,
            "emails_generated": len(email_variants),
            "scripts_generated": len(call_scripts),
            "properties_updated": properties_updated,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"✅ Webhook processing complete: {response_data}")
        return response_data

    except Exception as exc:
        logger.error(f"❌ Webhook error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(exc),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


# -------------------------------------------------------------------------
# Local dev entrypoint (optional)
# -------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
        log_level="info",
    )
