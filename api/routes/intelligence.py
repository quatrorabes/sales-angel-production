from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ALL your battle-tested modules
from services.enrichment.profile_enrichment_engine import ProfileEnrichmentEngine
from services.enrichment.perplexity_deep_enrichment import perplexity_enrich_contact
from services.enrichment.sales_automation_perplexity_enrichment_v3 import (
    get_structured_score, 
    get_structured_insights
)
from services.intelligence.kernel_generator_enhanced import AIKernelGenerator
from services.content.email_generator_quality import generate_email_variants
from services.content.call_script_generator_unified import UnifiedCallScriptGenerator

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])

class EnrichmentRequest(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    vertical: str = "saas"  # saas, lending, insurance, etc.

@router.post("/full-stack")
async def full_stack_intelligence(request: EnrichmentRequest):
    """
    THE MASTER ENDPOINT - Complete intelligence pipeline:
    1. Deep Perplexity enrichment (18 steps)
    2. Scoring & insights extraction
    3. Email generation (3 variants)
    4. Call scripts (3 variants with DISC)
    5. Kernel generation
    """
    
    # Step 1: Deep Enrichment
    enriched_data = perplexity_enrich_contact(
        request.name,
        request.company,
        request.linkedin_url
    )
    
    # Step 2: Extract structured scoring
    score_data = get_structured_score(enriched_data)
    insights = get_structured_insights(enriched_data)
    
    # Step 3: Generate content
    contact_data = request.dict()
    emails = generate_email_variants(contact_data, enriched_data)
    
    # Step 4: Generate call scripts
    script_gen = UnifiedCallScriptGenerator()
    scripts = script_gen.generate_all_scripts(contact_data)
    
    return {
        "contact": contact_data,
        "enrichment": enriched_data,
        "scoring": score_data,
        "insights": insights,
        "emails": emails,
        "scripts": scripts
    }
