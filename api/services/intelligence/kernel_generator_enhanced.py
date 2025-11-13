import logging
import os
from typing import Dict
from datetime import datetime

from backend.app.services.perplexity_enrichment import PerplexityEnrichmentClient

logger = logging.getLogger(__name__)

class AIKernelGenerator:
    """
    Enhanced AI Kernel Generator with Perplexity enrichment
    Generates WHO/WHY/WHAT kernels powered by real-time intelligence
    """
    
    def __init__(self):
        self.value_props = {
            "Financial Services": "Help pre-qualified CRE borrowers close deals 30% faster (45 days vs. 65 avg)",
            "Commercial Real Estate": "Help lenders originate 5-10 more loans/year with AI-powered pipeline",
            "Insurance": "Help agents cross-sell 3x more policies with AI opportunity detection",
            "Mortgage": "Help loan officers close refinance deals 20% faster",
            "SBA Lending": "Help SBA lenders source deal flow 40% faster with AI prospecting",
        }
        
        # Initialize Perplexity client if API key is available
        perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        self.perplexity_client = PerplexityEnrichmentClient(perplexity_key) if perplexity_key else None
        self.enrichment_enabled = bool(perplexity_key)
    
    async def generate_kernel(self, contact: Dict, use_enrichment: bool = True) -> Dict:
        """Generate complete kernel for a contact with optional Perplexity enrichment"""
        try:
            # Step 1: Enrich contact with Perplexity (if enabled)
            enriched_contact = contact
            if self.enrichment_enabled and use_enrichment:
                try:
                    enriched_contact = await self.perplexity_client.enrich_contact(contact)
                except Exception as e:
                    logger.warning(f"Enrichment failed for {contact.get('name')}, using basic data: {e}")
                    enriched_contact = contact
            
            # Step 2: Generate kernel components
            who = self._generate_who(enriched_contact)
            why_now, urgency = self._generate_why_now(enriched_contact)
            what_to_say = self._generate_what_to_say(enriched_contact)
            your_edge = self._generate_your_edge(enriched_contact)
            optimal_timing = self._calculate_optimal_timing(enriched_contact)
            priority_score = self._calculate_priority_score(enriched_contact, urgency)
            
            return {
                "id": contact.get('id'),
                "who": who,
                "why_now": why_now,
                "what_to_say": what_to_say,
                "your_edge": your_edge,
                "optimal_timing": optimal_timing,
                "urgency": urgency,
                "priority_score": priority_score,
                "enriched": enriched_contact.get('enriched', False),
                "enrichment_signals": enriched_contact.get('enrichment_data', {}).get('signals', []),
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating kernel: {str(e)}")
            return self._generate_fallback_kernel(contact)
    
    def _generate_who(self, contact: Dict) -> str:
        """Generate WHO section with enriched context"""
        base_who = f"{contact['name']}, {contact['job_title']} at {contact['company']}"
        
        # Add enrichment context if available
        enrichment_data = contact.get('enrichment_data', {})
        if enrichment_data.get('signals'):
            # Add top signal as context
            top_signal = enrichment_data['signals'][0] if enrichment_data['signals'] else ""
            if "Recent role change" in top_signal:
                base_who += " (Recently promoted/changed roles)"
            elif "Company growth" in top_signal:
                base_who += " (Company in expansion mode)"
        
        return base_who
    
    def _generate_why_now(self, contact: Dict) -> tuple:
        """Generate WHY NOW with Perplexity intelligence"""
        enrichment_data = contact.get('enrichment_data', {})
        ai_insights = contact.get('ai_insights', '')
        
        # Use enriched intelligence if available
        if ai_insights and 'No recent' not in ai_insights:
            # Parse enriched signals for urgency
            if '🔥' in ai_insights:
                urgency = "🔥 HOT"
                why_now = ai_insights.replace('🔥 Recent role change: ', '').replace('...', '')
                if len(why_now) > 200:
                    why_now = why_now[:200] + "..."
                return why_now, urgency
            
            elif '💰' in ai_insights:
                urgency = "🟡 WARM"
                why_now = ai_insights.replace('💰 Company growth: ', '').replace('...', '')
                if len(why_now) > 200:
                    why_now = why_now[:200] + "..."
                return why_now, urgency
            
            elif '🏢' in ai_insights:
                urgency = "🟡 WARM"  
                why_now = ai_insights.replace('🏢 Hiring activity: ', '').replace('...', '')
                if len(why_now) > 200:
                    why_now = why_now[:200] + "..."
                return why_now, urgency
        
        # Fallback to basic logic
        name = contact.get('name', '').split()[0]
        job_title = contact.get('job_title', '').lower()
        
        if 'vp' in job_title or 'director' in job_title or 'manager' in job_title:
            return f"{name} has decision-making authority in their role. Good time to connect on strategic initiatives.", "🟡 WARM"
        elif 'officer' in job_title or 'lender' in job_title:
            return f"{name} is actively working deals. Perfect timing to discuss deal flow.", "🟡 WARM"
        else:
            return f"{name} is established in their role at {contact.get('company', 'their company')}.", "❄️ COLD"
    
    def _generate_what_to_say(self, contact: Dict) -> str:
        """Generate contextual questions based on job title and enrichment"""
        job_title = contact.get('job_title', '').lower()
        enrichment_data = contact.get('enrichment_data', {})
        
        # Enhanced questions based on enrichment signals
        if enrichment_data.get('signals'):
            for signal in enrichment_data['signals']:
                if 'Recent role change' in signal:
                    return "1. How are you settling into your new role?\n2. What are your key priorities in this position?\n3. How can I help you hit the ground running?"
                
                elif 'Company growth' in signal or 'funding' in signal.lower():
                    return "1. How is the company's growth affecting your department?\n2. What new opportunities does this create for you?\n3. Are you looking to expand your team or capabilities?"
                
                elif 'Hiring activity' in signal:
                    return "1. I see you're growing the team - what roles are you prioritizing?\n2. What challenges are you facing with the expansion?\n3. How can I support your growth initiatives?"
        
        # Fallback questions by job type
        if any(term in job_title for term in ['lending', 'loan', 'credit']):
            return "1. What's your current focus for originations this quarter?\n2. How are you seeing the market for commercial deals?\n3. What's your typical timeline from application to close?"
        
        elif any(term in job_title for term in ['commercial', 'cre', 'real estate']):
            return "1. What types of commercial assets are you most active in?\n2. How are you evaluating opportunities in this market?\n3. What's your typical hold period and return target?"
        
        elif any(term in job_title for term in ['vp', 'director', 'manager', 'head']):
            return "1. What are your main strategic priorities this year?\n2. What's the biggest challenge facing your team?\n3. How do you see the market evolving?"
        
        else:
            return "1. What are your primary business objectives right now?\n2. What's your biggest challenge in your current role?\n3. How are you approaching growth in this market?"
    
    def _generate_your_edge(self, contact: Dict) -> str:
        """Generate value proposition based on industry and enrichment"""
        industry = contact.get('industry', 'Commercial Real Estate')
        enrichment_data = contact.get('enrichment_data', {})
        
        # Customize edge based on signals
        if enrichment_data.get('signals'):
            for signal in enrichment_data['signals']:
                if 'growth' in signal.lower() or 'expansion' in signal.lower():
                    return "Help you scale your growing business with AI-powered deal sourcing and relationship intelligence."
        
        return self.value_props.get(industry, "AI-powered sales intelligence that increases response rates 20x.")
    
    def _calculate_optimal_timing(self, contact: Dict) -> Dict:
        """Calculate optimal timing with enrichment insights"""
        enrichment_data = contact.get('enrichment_data', {})
        
        # Adjust timing based on signals
        if enrichment_data.get('urgency_level') == '🔥 HOT':
            return {
                "best_day": "Today or Tomorrow",
                "best_time_window": "9:00 AM - 11:00 AM (urgent)",
                "contact_method_1": "LinkedIn message (mention recent change)",
                "contact_method_2": "Email within 2 hours",
                "contact_method_3": "Phone call same day",
                "expected_response_rate": "45-60% (hot signal)"
            }
        
        elif enrichment_data.get('urgency_level') == '🟡 WARM':
            return {
                "best_day": "Tuesday or Wednesday", 
                "best_time_window": "9:00 AM - 11:00 AM",
                "contact_method_1": "Email (reference company news/growth)",
                "contact_method_2": "LinkedIn message after 4 hours",
                "contact_method_3": "Phone call next day",
                "expected_response_rate": "28-40% (warm signal)"
            }
        
        else:
            return {
                "best_day": "Tuesday",
                "best_time_window": "9:00 AM - 11:00 AM",
                "contact_method_1": "Email (industry-specific)",
                "contact_method_2": "LinkedIn message after 24 hours",
                "contact_method_3": "Phone call after 48 hours",
                "expected_response_rate": "12-25% (standard)"
            }
    
    def _calculate_priority_score(self, contact: Dict, urgency: str) -> int:
        """Enhanced priority scoring with enrichment boost"""
        score = 0
        
        # Base score from lead score
        lead_score = contact.get('lead_score', 0)
        score += min(lead_score / 2.5, 40)  # Max 40 points
        
        # Urgency boost
        if "🔥" in urgency:
            score += 40
        elif "🟡" in urgency:
            score += 25
        else:
            score += 10
        
        # Enrichment boost
        enrichment_data = contact.get('enrichment_data', {})
        priority_boost = enrichment_data.get('priority_boost', 0)
        score += priority_boost
        
        # Status boost
        status = contact.get('status', '').lower()
        if status == 'new':
            score += 10
        elif status == 'contacted':
            score += 5
        
        return min(int(score), 100)
    
    def _generate_fallback_kernel(self, contact: Dict) -> Dict:
        """Generate fallback kernel when enrichment fails"""
        return {
            "id": contact.get('id'),
            "who": f"{contact.get('name', 'Contact')}, {contact.get('job_title', 'Professional')} at {contact.get('company', 'Company')}",
            "why_now": "Established professional in their field",
            "what_to_say": "1. What are your current priorities?\n2. How can we help you achieve your goals?\n3. When might be a good time to chat?",
            "your_edge": "AI-powered sales intelligence platform",
            "optimal_timing": {
                "best_day": "Tuesday",
                "best_time_window": "9:00-11:00 AM",
                "contact_method_1": "Email",
                "contact_method_2": "LinkedIn",
                "expected_response_rate": "15-25%"
            },
            "urgency": "❄️ COLD",
            "priority_score": 50,
            "enriched": False,
            "enrichment_signals": [],
            "generated_at": datetime.now().isoformat()
        }