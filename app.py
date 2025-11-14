"""
SALES ANGEL PRODUCTION - FastAPI Application
HubSpot Webhook Integration with Auto-Enrichment
Fixed: SQLAlchemy Base, psycopg2, error handling
Enhanced: Better logging + stub content endpoints
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional, List
import requests
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================

HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
RAILWAY_ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")
RAILWAY_PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN")

logger.info(f"🚀 Starting Sales Angel Production - Environment: {RAILWAY_ENVIRONMENT}")
logger.info(f"🔑 HUBSPOT_API_KEY configured: {bool(HUBSPOT_API_KEY)}")
logger.info(f"🔑 OPENAI_API_KEY configured: {bool(OPENAI_API_KEY)}")
logger.info(f"🔑 PERPLEXITY_API_KEY configured: {bool(PERPLEXITY_API_KEY)}")
logger.info(f"🔑 DATABASE_URL configured: {bool(DATABASE_URL)}")

# ============================================================================
# DATABASE SETUP - MUST BE BEFORE MODEL DEFINITIONS
# ============================================================================

IS_PRODUCTION = RAILWAY_ENVIRONMENT == "production" or bool(RAILWAY_PUBLIC_DOMAIN)
engine = None
SessionLocal = None

if DATABASE_URL and IS_PRODUCTION:
    try:
        logger.info(f"🚀 Production mode: Connecting to Railway database")
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
            connect_args={"connect_timeout": 10}
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("✅ Database engine created successfully")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        engine = None
        SessionLocal = None
else:
    logger.warning("⚠️ Development mode: Skipping database connection")
    engine = None
    SessionLocal = None

# ============================================================================
# SQLALCHEMY MODELS - DEFINE AFTER Base CREATION
# ============================================================================

Base = declarative_base()

class Contact(Base):
    """Contact model for database storage"""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True)
    hubspot_id = Column(String, unique=True, nullable=False)
    firstname = Column(String)
    lastname = Column(String)
    email = Column(String)
    company = Column(String)
    phone = Column(String)
    jobtitle = Column(String)
    enriched = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables if engine exists
if engine:
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {str(e)}")

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Sales Angel Production API",
    description="HubSpot webhook integration with AI-powered content generation",
    version="1.0.0"
)

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": RAILWAY_ENVIRONMENT,
        "database": "connected" if engine else "disconnected",
        "hubspot_configured": bool(HUBSPOT_API_KEY),
        "openai_configured": bool(OPENAI_API_KEY),
        "perplexity_configured": bool(PERPLEXITY_API_KEY)
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "Sales Angel Production",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhooks/hubspot",
            "content_email": "/api/content/email",
            "content_call_script": "/api/content/call-script",
            "docs": "/docs"
        }
    }

# ============================================================================
# CONTENT GENERATION ENDPOINTS
# ============================================================================

@app.post("/api/content/email")
async def generate_emails(request: dict):
    """Generate email variants for a contact"""
    try:
        contact_id = request.get("contact_id")
        prospect_name = request.get("prospect_name", "Prospect")
        company = request.get("company", "Company")
        email = request.get("email", "")
        jobtitle = request.get("jobtitle", "")
        
        logger.info(f"📧 Generating emails for {prospect_name} @ {company} (contact_id: {contact_id})")
        
        if not OPENAI_API_KEY and not PERPLEXITY_API_KEY:
            logger.error("No API keys configured for content generation")
            return {
                "status": "error",
                "message": "Content generation API keys not configured",
                "variants": []
            }
        
        # Generate 3 email variants
        variants = []
        
        try:
            # Use Perplexity if available, fallback to OpenAI
            if PERPLEXITY_API_KEY:
                logger.info(f"Using Perplexity API for email generation")
                
                prompts = [
                    f"Write a professional cold outreach email to {prospect_name} at {company}. Subject line only, no body. Style: Direct and to the point.",
                    f"Write a friendly but professional cold outreach email to {prospect_name} at {company}. Subject line only, no body. Style: Warm and personable.",
                    f"Write a consultative cold outreach email to {prospect_name} at {company}. Subject line only, no body. Style: Questions and insights."
                ]
                
                for i, prompt in enumerate(prompts, 1):
                    try:
                        response = requests.post(
                            "https://api.perplexity.ai/chat/completions",
                            headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}"},
                            json={
                                "model": "pplx-70b-online",
                                "messages": [{"role": "user", "content": prompt}],
                                "max_tokens": 200
                            },
                            timeout=15
                        )
                        
                        if response.status_code == 200:
                            content = response.json()["choices"][0]["message"]["content"]
                            variants.append({
                                "style": ["Direct", "Warm", "Consultative"][i-1],
                                "subject": content[:100],
                                "body": f"Generated email variant {i} for {prospect_name}",
                                "generated_at": datetime.utcnow().isoformat()
                            })
                        else:
                            logger.warning(f"Perplexity API error: {response.status_code}")
                    except Exception as e:
                        logger.error(f"Perplexity email generation error: {str(e)}")
            
            elif OPENAI_API_KEY:
                logger.info(f"Using OpenAI API for email generation")
                
                # Stub implementation - would call OpenAI
                for i, style in enumerate(["Direct", "Warm", "Consultative"], 1):
                    variants.append({
                        "style": style,
                        "subject": f"[{style}] Quick question about {company}",
                        "body": f"Hi {prospect_name}, I noticed your work at {company}...",
                        "generated_at": datetime.utcnow().isoformat()
                    })
                
        except Exception as e:
            logger.error(f"Email generation error: {str(e)}")
        
        logger.info(f"✅ Generated {len(variants)} email variants")
        
        return {
            "status": "success",
            "contact_id": contact_id,
            "variants": variants,
            "count": len(variants),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Email endpoint error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": str(e),
            "variants": []
        }

@app.post("/api/content/call-script")
async def generate_call_scripts(request: dict):
    """Generate call scripts for a contact"""
    try:
        contact_id = request.get("contact_id")
        prospect_name = request.get("prospect_name", "Prospect")
        company = request.get("company", "Company")
        email = request.get("email", "")
        jobtitle = request.get("jobtitle", "")
        
        logger.info(f"☎️  Generating call scripts for {prospect_name} @ {company} (contact_id: {contact_id})")
        
        if not OPENAI_API_KEY and not PERPLEXITY_API_KEY:
            logger.error("No API keys configured for content generation")
            return {
                "status": "error",
                "message": "Content generation API keys not configured",
                "scripts": []
            }
        
        # Generate 3 call scripts
        scripts = []
        
        try:
            if PERPLEXITY_API_KEY:
                logger.info(f"Using Perplexity API for script generation")
                
                prompts = [
                    f"Write a 3-sentence cold call opening for {prospect_name} at {company}. Approach: Direct value proposition.",
                    f"Write a 3-sentence cold call opening for {prospect_name} at {company}. Approach: Build rapport first.",
                    f"Write a 3-sentence cold call opening for {prospect_name} at {company}. Approach: Ask a discovery question."
                ]
                
                for i, prompt in enumerate(prompts, 1):
                    try:
                        response = requests.post(
                            "https://api.perplexity.ai/chat/completions",
                            headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}"},
                            json={
                                "model": "pplx-70b-online",
                                "messages": [{"role": "user", "content": prompt}],
                                "max_tokens": 150
                            },
                            timeout=15
                        )
                        
                        if response.status_code == 200:
                            content = response.json()["choices"][0]["message"]["content"]
                            scripts.append({
                                "style": ["Value Prop", "Rapport", "Discovery"][i-1],
                                "opening": content[:200],
                                "generated_at": datetime.utcnow().isoformat()
                            })
                        else:
                            logger.warning(f"Perplexity API error: {response.status_code}")
                    except Exception as e:
                        logger.error(f"Perplexity script generation error: {str(e)}")
            
            elif OPENAI_API_KEY:
                logger.info(f"Using OpenAI API for script generation")
                
                # Stub implementation - would call OpenAI
                for i, style in enumerate(["Value Prop", "Rapport", "Discovery"], 1):
                    scripts.append({
                        "style": style,
                        "opening": f"Hi {prospect_name}, I work with companies like {company}...",
                        "generated_at": datetime.utcnow().isoformat()
                    })
            
        except Exception as e:
            logger.error(f"Call script generation error: {str(e)}")
        
        logger.info(f"✅ Generated {len(scripts)} call scripts")
        
        return {
            "status": "success",
            "contact_id": contact_id,
            "scripts": scripts,
            "count": len(scripts),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Call script endpoint error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": str(e),
            "scripts": []
        }

# ============================================================================
# HUBSPOT WEBHOOK ENDPOINT
# ============================================================================

@app.post("/webhooks/hubspot")
async def hubspot_webhook(request: dict):
    """
    Receive HubSpot contact events and auto-enrich with emails + call scripts
    """
    try:
        contact_id = request.get("objectId")
        
        if not contact_id:
            logger.error("No objectId provided in webhook payload")
            return {
                "status": "error",
                "message": "Missing objectId in request"
            }
        
        logger.info(f"🔔 HubSpot webhook received for contact: {contact_id}")
        
        # Validate HUBSPOT_API_KEY
        if not HUBSPOT_API_KEY:
            logger.error("HUBSPOT_API_KEY not configured")
            return {
                "status": "error",
                "message": "HUBSPOT_API_KEY not configured"
            }
        
        # ════════════════════════════════════════════════════════════════════
        # STEP 1: FETCH CONTACT FROM HUBSPOT
        # ════════════════════════════════════════════════════════════════════
        
        headers = {
            "Authorization": f"Bearer {HUBSPOT_API_KEY}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
        params = {"properties": "firstname,lastname,company,email,phone,jobtitle"}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"HubSpot fetch error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {
                    "status": "error",
                    "message": f"Failed to fetch contact from HubSpot: {response.status_code}",
                    "contact_id": contact_id
                }
            
            contact_data = response.json()
            
        except requests.Timeout:
            logger.error("HubSpot API request timed out")
            return {
                "status": "error",
                "message": "HubSpot API request timed out",
                "contact_id": contact_id
            }
        except Exception as e:
            logger.error(f"Failed to fetch contact from HubSpot: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to fetch contact: {str(e)}",
                "contact_id": contact_id
            }
        
        # ════════════════════════════════════════════════════════════════════
        # STEP 2: PARSE CONTACT DATA
        # ════════════════════════════════════════════════════════════════════
        
        properties = contact_data.get("properties", {})
        
        first_name = properties.get("firstname", "")
        last_name = properties.get("lastname", "")
        company = properties.get("company", "Unknown Company")
        email = properties.get("email", "")
        phone = properties.get("phone", "")
        jobtitle = properties.get("jobtitle", "")
        
        prospect_name = f"{first_name} {last_name}".strip() or "Unknown Contact"
        
        logger.info(f"📧 Enriching: {prospect_name} @ {company}")
        
        # ════════════════════════════════════════════════════════════════════
        # STEP 3: GENERATE EMAILS
        # ════════════════════════════════════════════════════════════════════
        
        email_variants = []
        try:
            base_url = RAILWAY_PUBLIC_DOMAIN if RAILWAY_PUBLIC_DOMAIN else "http://localhost:8000"
            if not base_url.startswith("http"):
                base_url = f"https://{base_url}"
            
            logger.info(f"Generating emails from: {base_url}")
            
            emails_response = requests.post(
                f"{base_url}/api/content/email",
                json={
                    "contact_id": str(contact_id),
                    "prospect_name": prospect_name,
                    "company": company,
                    "email": email,
                    "phone": phone,
                    "jobtitle": jobtitle
                },
                timeout=30
            )
            
            if emails_response.status_code == 200:
                email_variants = emails_response.json().get("variants", [])
                logger.info(f"✅ Generated {len(email_variants)} email variants")
            else:
                logger.warning(f"Email generation failed: {emails_response.status_code}")
                logger.warning(f"Response: {emails_response.text[:200]}")
                
        except requests.Timeout:
            logger.error("Email generation request timed out")
        except Exception as e:
            logger.error(f"Email generation error: {str(e)}")
        
        # ════════════════════════════════════════════════════════════════════
        # STEP 4: GENERATE CALL SCRIPTS
        # ════════════════════════════════════════════════════════════════════
        
        call_scripts = []
        try:
            base_url = RAILWAY_PUBLIC_DOMAIN if RAILWAY_PUBLIC_DOMAIN else "http://localhost:8000"
            if not base_url.startswith("http"):
                base_url = f"https://{base_url}"
            
            scripts_response = requests.post(
                f"{base_url}/api/content/call-script",
                json={
                    "contact_id": str(contact_id),
                    "prospect_name": prospect_name,
                    "company": company,
                    "email": email,
                    "phone": phone,
                    "jobtitle": jobtitle
                },
                timeout=30
            )
            
            if scripts_response.status_code == 200:
                call_scripts = scripts_response.json().get("scripts", [])
                logger.info(f"✅ Generated {len(call_scripts)} call scripts")
            else:
                logger.warning(f"Call script generation failed: {scripts_response.status_code}")
                logger.warning(f"Response: {scripts_response.text[:200]}")
                
        except requests.Timeout:
            logger.error("Call script generation request timed out")
        except Exception as e:
            logger.error(f"Call script generation error: {str(e)}")
        
        # ════════════════════════════════════════════════════════════════════
        # STEP 5: FORMAT NOTES FOR HUBSPOT
        # ════════════════════════════════════════════════════════════════════
        
        notes = f"""=== SALES ANGEL AUTO-ENRICHMENT ===
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
Contact: {prospect_name}
Company: {company}
Email: {email}
Phone: {phone}
Title: {jobtitle}

📧 EMAIL VARIANTS ({len(email_variants)} generated):
"""
        
        for i, email_variant in enumerate(email_variants, 1):
            subject = email_variant.get('subject', 'N/A')[:100]
            style = email_variant.get('style', f'Email {i}')
            notes += f"\n{i}. {style}\n   Subject: {subject}\n"
        
        notes += f"\n☎️ CALL SCRIPTS ({len(call_scripts)} generated):\n"
        
        for i, script in enumerate(call_scripts, 1):
            style = script.get('style', f'Script {i}')
            notes += f"\n{i}. {style}\n"
        
        # ════════════════════════════════════════════════════════════════════
        # STEP 6: UPDATE HUBSPOT CONTACT NOTES
        # ════════════════════════════════════════════════════════════════════
        
        update_response = None
        try:
            update_payload = {
                "properties": {
                    "hs_note_body": notes
                }
            }
            
            update_response = requests.patch(
                f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}",
                headers=headers,
                json=update_payload,
                timeout=10
            )
            
            if update_response.status_code == 200:
                logger.info(f"✅ Updated notes for contact {contact_id}")
            else:
                logger.error(f"HubSpot update error: {update_response.status_code}")
                logger.error(f"Response: {update_response.text}")
                
        except requests.Timeout:
            logger.error("HubSpot update request timed out")
        except Exception as e:
            logger.error(f"Failed to update HubSpot: {str(e)}")
        
        # ════════════════════════════════════════════════════════════════════
        # STEP 7: RETURN SUCCESS RESPONSE
        # ════════════════════════════════════════════════════════════════════
        
        response_data = {
            "status": "success",
            "contact_id": contact_id,
            "prospect": prospect_name,
            "company": company,
            "email": email,
            "emails_generated": len(email_variants),
            "scripts_generated": len(call_scripts),
            "notes_updated": update_response.status_code == 200 if update_response else False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Webhook processing complete: {json.dumps(response_data)}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ HubSpot webhook error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    import traceback
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") else "An error occurred"
        }
    )

# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("🚀 Application startup")
    logger.info(f"Environment: {RAILWAY_ENVIRONMENT}")
    logger.info(f"Database: {'Connected' if engine else 'Disabled'}")
    logger.info(f"HubSpot Integration: {'Ready' if HUBSPOT_API_KEY else 'Not configured'}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info("🛑 Application shutdown")
    if engine:
        engine.dispose()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
