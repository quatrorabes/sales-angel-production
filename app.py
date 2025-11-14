from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
import logging
import json
import httpx
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, String, Integer, DateTime, Boolean, JSON, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from openai import OpenAI

# Load environment variables
load_dotenv()

# ==================== CONFIGURATION ====================

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/sales_angel")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# ==================== LOGGING ====================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sales_angel_production")

# ==================== DATABASE SETUP ====================

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
        pool_size=10,
        max_overflow=20,
        connect_args={"connect_timeout": 10}
    )
    SessionLocal = sessionmaker(bind=engine)
    Base = declarative_base()
    logger.info(f"✅ Database connected: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'PostgreSQL'}")
except Exception as e:
    logger.error(f"❌ Database connection failed: {str(e)}")
    raise

# ==================== DATABASE MODELS ====================

class Contact(Base):
    """Contact model for storing prospect data"""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    crm_id = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    company = Column(String, index=True)
    job_title = Column(String)
    phone = Column(String)
    linkedin_url = Column(String)
    enriched = Column(Boolean, default=False)
    enrichment_data = Column(JSON)
    email_variants = Column(JSON)
    call_scripts = Column(JSON)
    linkmatch_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LinkedInAction(Base):
    """Track LinkedIn actions from LinkMatch"""
    __tablename__ = "linkedin_actions"

    id = Column(Integer, primary_key=True)
    contact_id = Column(String, index=True)
    action_type = Column(String)  # connection_request, message_sent, etc
    status = Column(String)  # queued, completed, failed
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(engine)

# ==================== FASTAPI APP ====================

app = FastAPI(
    title="Sales Angel Intelligence API - Production",
    version="3.0.0",
    description="Full-stack AI sales intelligence platform with Perplexity, OpenAI, LinkMatch, and HubSpot integration"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== PYDANTIC MODELS ====================

class ContactRequest(BaseModel):
    name: str
    email: str
    company: str
    job_title: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None

class EnrichmentRequest(BaseModel):
    contact_id: str
    name: str
    company: str

class EmailGenerationRequest(BaseModel):
    contact_id: str
    prospect_name: str
    company: str
    job_title: Optional[str] = None
    enrichment_data: Optional[Dict] = None

class CallScriptRequest(BaseModel):
    contact_id: str
    prospect_name: str
    company: str
    job_title: Optional[str] = None

# ==================== PROFILE ENRICHMENT ENGINE (FROM YOUR FILE) ====================

class ProfileEnrichmentEngine:
    """Perplexity-powered enrichment with 11-step person + 5-step company framework"""

    def __init__(self):
        self.api_key = PERPLEXITY_API_KEY
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found")
        self.base_url = 'https://api.perplexity.ai/chat/completions'
        self.model = 'llama-3.1-sonar-large-128k-online'

    async def enrich_person(self, name: str, company: Optional[str] = None, additional_context: str = "") -> Dict:
        """YOUR 11-STEP PERSON ENRICHMENT FRAMEWORK - PRESERVED EXACTLY"""
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
        11. Additional Insights: Find relevant company news or fun facts; add these to "talking points".

        Be thorough, accurate, and concise in your reporting.
        Return the profile in a structured format with clear section headers.
        """

        return await self._call_perplexity_api(user_prompt, 'person')

    async def enrich_company(self, company_name: str, additional_context: str = "") -> Dict:
        """YOUR 5-STEP COMPANY ENRICHMENT FRAMEWORK - PRESERVED EXACTLY"""
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

        return await self._call_perplexity_api(user_prompt, 'company')

    async def _call_perplexity_api(self, user_prompt: str, profile_type: str) -> Dict:
        """Call Perplexity API with structured prompts"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an AI profile-building assistant. Generate comprehensive, accurate profiles using public web sources.'
                },
                {
                    'role': 'user',
                    'content': user_prompt
                }
            ],
            'return_citations': True,
            'search_recency_filter': 'month',
            'temperature': 0.2,
            'max_tokens': 4000
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                profile_content = data['choices'][0]['message']['content']
                citations = data.get('citations', [])

                logger.info(f"✅ Perplexity enrichment complete - {len(citations)} citations")

                return {
                    'profile_type': profile_type,
                    'content': profile_content,
                    'citations': citations,
                    'citation_count': len(citations),
                    'generated_at': datetime.utcnow().isoformat(),
                    'parsed_sections': self._parse_sections(profile_content, profile_type)
                }

        except Exception as e:
            logger.error(f"❌ Perplexity API error: {str(e)}")
            return {
                'profile_type': profile_type,
                'error': str(e),
                'content': None,
                'citations': []
            }

    def _parse_sections(self, content: str, profile_type: str) -> Dict:
        """Parse structured profile sections"""
        sections = {}

        if profile_type == 'person':
            headers = ['Overview', 'Background', 'Education', 'Recent Mentions',
                      'Social Profiles', 'Personality Detail', 'Assessment',
                      'Sales Opportunities', 'Deal History', 'Profile Accuracy',
                      'Additional Insights']
        else:
            headers = ['Overview', 'Products & Services', 'Products and Services',
                      'Leadership', 'Market & Competitors', 'Recent News']

        lines = content.split('\n')
        current_section = 'raw'
        current_content = []

        for line in lines:
            is_header = False
            for header in headers:
                if header.lower() in line.lower() and (line.startswith('#') or line.endswith(':') or '**' in line):
                    if current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = header.lower().replace(' ', '_').replace('&', 'and')
                    current_content = []
                    is_header = True
                    break

            if not is_header and line.strip():
                current_content.append(line)

        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
            
        return sections
    
    # ==================== HUBSPOT WEBHOOK INTEGRATION ====================
  
    @app.post("/webhooks/hubspot")
    async def hubspot_webhook(request: dict):
      """Receive HubSpot contact events"""
      try:
        contact_id = request.get("objectId")
        logger.info(f"🔔 HubSpot webhook received for contact: {contact_id}")
        
        # ... all your code ...
        
        return {
          "status": "success",
          "contact_id": contact_id,
          "prospect": prospect_name,
          "company": company,
          "emails_generated": len(email_variants),
          "scripts_generated": len(call_scripts)
        }
      
      except Exception as e:
        logger.error(f"❌ HubSpot webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}
      
      
    # Initialize enrichment engine
    enrichment_engine = ProfileEnrichmentEngine()

# Initialize enrichment engine
enrichment_engine = ProfileEnrichmentEngine()

# ==================== EMAIL GENERATION (FROM YOUR FILE) ====================

class EmailGenerator:
    """OpenAI GPT-4 email generation with 3 approaches - PRESERVED EXACTLY"""

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.email_approaches = [
            {
                "style": "Problem-Agitate-Solve",
                "description": "Lead with relevant problem, acknowledge impact, present solution",
            },
            {
                "style": "Social Proof",
                "description": "Reference similar success, build credibility, invite conversation",
            },
            {
                "style": "Value-First Consultative",
                "description": "Offer genuine value with no pitch, build rapport, then explore fit",
            }
        ]

    async def generate_email_variants(self, contact_data: Dict, enrichment_data: Optional[Dict] = None, business_profile: Optional[Dict] = None) -> List[Dict]:
        """Generate 3 high-quality, personalized email variants - YOUR EXACT LOGIC"""

        # Build prospect context
        prospect_context = f"""
        PROSPECT:
        Name: {contact_data.get('prospect_name', 'Unknown')} 
        Company: {contact_data.get('company', 'Unknown')}
        Title: {contact_data.get('job_title', 'Unknown')}
        Email: {contact_data.get('email', 'Unknown')}
        """

        # Add enrichment if available
        if enrichment_data:
            if enrichment_data.get('overview'):
                prospect_context += f"\nBackground: {enrichment_data['overview']}"
            if enrichment_data.get('recent_mentions'):
                prospect_context += f"\nRecent News: {enrichment_data['recent_mentions']}"
            if enrichment_data.get('sales_opportunities'):
                prospect_context += f"\nSignals: {enrichment_data['sales_opportunities']}"

        # Build business context
        business_context = ""
        if business_profile:
            business_context = f"""
            YOUR BUSINESS:
            What you do: {business_profile.get('what_you_do', '')}
            Who you serve: {business_profile.get('target', '')}
            Value proposition: {business_profile.get('value_prop', '')}
            """

        variants = []

        for approach in self.email_approaches:
            try:
                if approach["style"] == "Problem-Agitate-Solve":
                    instructions = f"""Write a short, highly personalized B2B sales email using the Problem-Agitate-Solve framework.

{prospect_context}
{business_context}

REQUIREMENTS:
- Reference something SPECIFIC about their company, role, or recent news
- Lead with a problem they LIKELY face in their industry/role
- Acknowledge the impact/cost of that problem
- Briefly mention how similar companies solved it
- Keep it under 80 words
- Natural, conversational tone
- NO generic openers like "I hope this email finds you well"
- End with a simple, low-pressure question

FORMAT:
Subject: [subject line]
Body: [email body]"""

                elif approach["style"] == "Social Proof":
                    instructions = f"""Write a short, highly personalized B2B sales email using social proof.

{prospect_context}
{business_context}

REQUIREMENTS:
- Reference a similar company or success story relevant to THEIR situation
- Connect that proof point to something specific about THEM
- Show you understand their world
- Keep it under 80 words
- Natural tone, NO generic openers
- End with offering to share more details if relevant

FORMAT:
Subject: [subject line]
Body: [email body]"""

                else:  # Value-First
                    instructions = f"""Write a short, highly personalized B2B sales email offering value first.

{prospect_context}
{business_context}

REQUIREMENTS:
- Reference something specific about their company/role/industry
- Offer something useful (insight, data, article) with NO strings attached
- Show you did research and understand their situation
- Keep it under 80 words
- Natural, conversational, helpful tone
- NO generic openers
- Signature question: "Would this be valuable?"

FORMAT:
Subject: [subject line]
Body: [email body]"""

                # Call OpenAI
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a world-class B2B sales copywriter who writes highly personalized, research-backed emails that get responses. Never use templates or corporate-speak."
                        },
                        {
                            "role": "user",
                            "content": instructions
                        }
                    ],
                    temperature=0.7,
                    max_tokens=400
                )

                content = response.choices[0].message.content.strip()

                # Parse subject and body
                subject = ""
                body = ""

                for line in content.split('\n'):
                    if line.startswith('Subject:'):
                        subject = line.replace('Subject:', '').strip()
                    elif line.startswith('Body:'):
                        body = line.replace('Body:', '').strip()
                    elif body:
                        if line.strip():
                            body += "\n" + line.strip()

                if not subject:
                    subject = f"Quick thought about {contact_data.get('company', 'your company')}"

                variant = {
                    'subject': subject,
                    'body': body.strip() if body else content[:200],
                    'style': approach['style'],
                    'description': approach['description']
                }

                variants.append(variant)
                logger.info(f"✅ Generated email variant: {approach['style']}")

            except Exception as e:
                logger.error(f"❌ Email generation error: {str(e)}")
                variants.append({
                    'subject': f"Thought about {contact_data.get('company', 'your company')}",
                    'body': f"Hi {contact_data.get('prospect_name', 'there')},\n\nI work with companies like {contact_data.get('company', 'yours')}. Would be worth a conversation?",
                    'style': approach['style'] + " (Fallback)",
                    'description': "Template fallback"
                })

        return variants

email_generator = None
call_script_generator = None
perplexity_enricher = None


# ==================== CALL SCRIPT GENERATOR (FROM YOUR FILE) ====================

class CallScriptGenerator:
    """Perplexity + DISC personality call script generation - PRESERVED EXACTLY"""

    def __init__(self):
        self.perplexity_key = PERPLEXITY_API_KEY
        self.disc_approaches = {
            "D": {
                "opening": "Get to the point in 10 seconds",
                "pace": "Fast, efficient",
                "focus": "Results and ROI",
                "objection_style": "Direct counter with data"
            },
            "I": {
                "opening": "Build rapport first (20 seconds)",
                "pace": "Conversational, energetic",
                "focus": "People and relationships",
                "objection_style": "Story-based response"
            },
            "S": {
                "opening": "Warm, ask about their team",
                "pace": "Patient, supportive",
                "focus": "Stability and support",
                "objection_style": "Reassurance and case studies"
            },
            "C": {
                "opening": "Professional, agenda-driven",
                "pace": "Methodical, detailed",
                "focus": "Data and accuracy",
                "objection_style": "Provide detailed proof"
            }
        }

        self.script_styles = {
            1: "Direct & Value-Focused",
            2: "Consultative & Rapport-Building",
            3: "Executive / Insight-Led"
        }

    def detect_disc_profile(self, enrichment_data: Optional[Dict]) -> str:
        """Auto-detect DISC profile from enrichment data"""
        if not enrichment_data:
            return 'D'  # Default

        content = str(enrichment_data).lower()

        if any(word in content for word in ['direct', 'results', 'decisive', 'leading']):
            return 'D'
        elif any(word in content for word in ['social', 'enthusiastic', 'energetic', 'people']):
            return 'I'
        elif any(word in content for word in ['steady', 'patient', 'supportive', 'team']):
            return 'S'
        elif any(word in content for word in ['analytical', 'precise', 'detailed', 'data']):
            return 'C'

        return 'D'

    async def generate_script(self, prospect_name: str, company: str, job_title: str, enrichment_data: Optional[Dict] = None, variant: int = 1) -> str:
        """Generate personalized call script with DISC adaptation - YOUR EXACT LOGIC"""

        # Detect personality
        disc = self.detect_disc_profile(enrichment_data)
        approach = self.disc_approaches[disc]
        style = self.script_styles[variant]

        intel = ""
        if enrichment_data:
            intel = json.dumps(enrichment_data, default=str)[:1200]

        prompt = f"""You are writing a {style} cold-call script for {prospect_name}, {job_title} at {company}.

PERSONALITY TYPE: {disc} - {approach['focus']}
OPENING STYLE: {approach['opening']}
PACE: {approach['pace']}

INTELLIGENCE:
{intel}

GOAL: Book a 15-minute meeting.

Format your response EXACTLY as:

════════════════════════════════════
CALL SCRIPT – {style}
{prospect_name} – {job_title} at {company}
Personality: {disc}-Type
════════════════════════════════════

📞 OPENER:
[{approach['opening']} - exact words using intelligence]

🎯 HOOK / VALUE:
[1-sentence pain point + 1-sentence outcome]

❓ DISCOVERY QUESTIONS:
• [Question 1 aligned with {disc} personality]
• [Question 2 focused on {approach['focus']}]
• [Question 3 about timing/urgency]

🛡️ OBJECTION HANDLING:
IF "Not interested": [{approach['objection_style']}]
IF "Send me info": [Response matching {disc} style]
IF "Too busy": [Response respecting their {approach['pace']}]

✅ CLOSE:
[Propose specific times matching {disc} preference]

📝 PERSONALITY NOTES:
• DO: {approach['focus']}
• DON'T: [What to avoid with {disc} types]
• PACE: {approach['pace']}

════════════════════════════════════"""

        payload = {
            "model": "sonar-pro",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
            "temperature": 0.7,
            "top_p": 0.9
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.perplexity_key}"}
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"].strip()

        except Exception as e:
            logger.error(f"❌ Call script generation error: {str(e)}")
            return self.fallback_script(prospect_name, company, disc, variant)

    def fallback_script(self, prospect_name: str, company: str, disc: str, variant: int) -> str:
        """Fallback script if API fails"""
        approach = self.disc_approaches[disc]
        style = self.script_styles[variant]

        return f"""
════════════════════════════════════
CALL SCRIPT – {style}
{prospect_name} at {company}
Personality: {disc}-Type
════════════════════════════════════

📞 OPENER:
"Hi {prospect_name}, I know you're busy so I'll be brief..."

🎯 HOOK / VALUE:
"We help companies like {company} [specific benefit]."

❓ DISCOVERY QUESTIONS:
• "What's your current process for [area]?"
• "What would make the biggest impact?"
• "Who else should be involved?"

🛡️ OBJECTION HANDLING:
IF "Not interested": "{approach['objection_style']}"
IF "Send me info": "Happy to - what specifically interests you?"
IF "Too busy": "I understand - when works better?"

✅ CLOSE:
"Would Tuesday 2pm or Wednesday 10am work better?"

📝 PERSONALITY NOTES:
• Focus: {approach['focus']}
• Pace: {approach['pace']}

════════════════════════════════════"""

call_script_generator = CallScriptGenerator()

# ==================== LINKMATCH INTEGRATION (PRODUCTION VERSION) ====================

class LinkMatchIntegration:
    """LinkMatch Pro integration - LinkedIn automation via HubSpot"""

    def __init__(self):
        self.hubspot_key = HUBSPOT_API_KEY
        self.hubspot_base = "https://api.hubapi.com"

    async def get_linkedin_profile(self, contact_id: str) -> Dict:
        """Retrieve LinkedIn profile data from HubSpot (synced by LinkMatch)"""
        url = f"{self.hubspot_base}/crm/v3/objects/contacts/{contact_id}"
        headers = {"Authorization": f"Bearer {self.hubspot_key}"}

        params = {
            "properties": [
                "linkedin_profile_url", "linkedin_headline", "linkedin_bio",
                "linkedin_connections_count", "linkedin_posts_count",
                "linkedin_last_activity_date", "linkmatch_connection_status",
                "linkmatch_verified_email"
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                props = response.json().get("properties", {})

                return {
                    "linkedin_url": props.get("linkedin_profile_url"),
                    "headline": props.get("linkedin_headline"),
                    "bio": props.get("linkedin_bio"),
                    "connections": int(props.get("linkedin_connections_count", 0)) if props.get("linkedin_connections_count") else None,
                    "posts_count": int(props.get("linkedin_posts_count", 0)) if props.get("linkedin_posts_count") else None,
                    "last_activity": props.get("linkedin_last_activity_date"),
                    "connection_status": props.get("linkmatch_connection_status", "unknown"),
                    "verified_email": props.get("linkmatch_verified_email")
                }

        except Exception as e:
            logger.error(f"❌ LinkMatch profile fetch error: {str(e)}")
            return {}

    async def request_connection(self, contact_id: str, message: Optional[str] = None) -> bool:
        """Queue LinkedIn connection request via LinkMatch"""
        url = f"{self.hubspot_base}/crm/v3/objects/contacts/{contact_id}"
        headers = {"Authorization": f"Bearer {self.hubspot_key}", "Content-Type": "application/json"}

        payload = {
            "properties": {
                "linkmatch_action": "send_connection_request",
                "linkmatch_action_timestamp": datetime.utcnow().isoformat(),
                "linkmatch_connection_message": message or "I'd like to connect!",
                "linkmatch_action_status": "queued"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.patch(url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"✅ Connection request queued for {contact_id}")
                return True

        except Exception as e:
            logger.error(f"❌ Connection request error: {str(e)}")
            return False

linkmatch = LinkMatchIntegration()

# ==================== ROOT ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "message": "Sales Angel Production API - Full Integration",
        "status": "operational",
        "version": "3.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": ENVIRONMENT,
        "endpoints": [
            "/api/enrichment/person",
            "/api/enrichment/company",
            "/api/content/email",
            "/api/content/call-script",
            "/api/linkmatch/profile/{contact_id}",
            "/api/linkmatch/connect/{contact_id}",
            "/health",
            "/docs"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ==================== ENRICHMENT ENDPOINTS ====================

@app.post("/api/enrichment/person")
async def enrich_person(request: EnrichmentRequest):
    """Enrich person using your 11-step framework"""
    try:
        profile = await enrichment_engine.enrich_person(
            name=request.name,
            company=request.company,
            additional_context=""
        )
        return {"status": "success", "profile": profile}
    except Exception as e:
        logger.error(f"❌ Person enrichment error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enrichment/company")
async def enrich_company(request: EnrichmentRequest):
    """Enrich company using your 5-step framework"""
    try:
        profile = await enrichment_engine.enrich_company(
            company_name=request.company,
            additional_context=""
        )
        return {"status": "success", "profile": profile}
    except Exception as e:
        logger.error(f"❌ Company enrichment error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CONTENT GENERATION ENDPOINTS ====================

@app.post("/api/content/email")
async def generate_email(request: EmailGenerationRequest):
    """Generate 3 personalized email variants"""
    try:
        variants = await email_generator.generate_email_variants(
            contact_data={
                "prospect_name": request.prospect_name,
                "company": request.company,
                "job_title": request.job_title,
                "email": ""
            },
            enrichment_data=request.enrichment_data
        )

        return {
            "status": "success",
            "contact_id": request.contact_id,
            "prospect": request.prospect_name,
            "company": request.company,
            "variants": variants,
            "total_variants": len(variants),
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Email generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/call-script")
async def generate_call_script(request: CallScriptRequest):
    """Generate 3 DISC-personalized call scripts"""
    try:
        scripts = []
        for variant in range(1, 4):
            script = await call_script_generator.generate_script(
                prospect_name=request.prospect_name,
                company=request.company,
                job_title=request.job_title,
                enrichment_data=None,
                variant=variant
            )
            scripts.append({
                "variant": variant,
                "style": call_script_generator.script_styles[variant],
                "script": script
            })

        return {
            "status": "success",
            "contact_id": request.contact_id,
            "prospect": request.prospect_name,
            "company": request.company,
            "scripts": scripts,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Call script error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== LINKMATCH ENDPOINTS ====================

@app.get("/api/linkmatch/profile/{contact_id}")
async def linkmatch_profile(contact_id: str):
    """Get LinkedIn profile from LinkMatch"""
    try:
        profile = await linkmatch.get_linkedin_profile(contact_id)
        return {"status": "success", "contact_id": contact_id, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/linkmatch/connect/{contact_id}")
async def linkmatch_connect(contact_id: str, message: Optional[str] = None):
    """Request LinkedIn connection via LinkMatch"""
    try:
        success = await linkmatch.request_connection(contact_id, message)
        return {
            "status": "success" if success else "failed",
            "contact_id": contact_id,
            "action": "connection_requested"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STATUS ENDPOINTS ====================

@app.get("/api/status")
async def system_status():
    return {
        "status": "operational",
        "modules": {
            "enrichment": "ready",
            "email_generation": "ready",
            "call_scripts": "ready",
            "linkmatch": "ready",
            "database": "connected"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
  