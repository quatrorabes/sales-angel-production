#!/usr/bin/env python3
"""
UNIFIED CALL SCRIPT GENERATOR v4.0
Combines: Perplexity enrichment + DISC personality + 3 script variants
"""

import os
import sqlite3
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class UnifiedCallScriptGenerator:
    """The ULTIMATE call script generator combining all approaches"""
    
    def __init__(self, db_path='sales_angel.db'):
        self.db_path = db_path
        self.perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        # DISC approaches from File #2
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
        
        # Script styles from File #1
        self.script_styles = {
            1: "Direct & Value-Focused",
            2: "Consultative & Rapport-Building",
            3: "Executive / Insight-Led"
        }
    
    def get_profile(self, contact_id: int) -> Optional[Dict]:
        """Get enriched profile with personality data"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT firstname, lastname, company, phone, jobtitle,
                   score, tier, profile_content, deep_intel,
                   personality_profile, key_intelligence
            FROM contacts 
            WHERE id = ? AND enriched = 1
        """, (contact_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def detect_disc_profile(self, profile: Dict) -> str:
        """Auto-detect DISC profile from enrichment data"""
        personality = profile.get('personality_profile', '').lower()
        
        # Simple detection logic (enhance with ML later)
        if any(word in personality for word in ['direct', 'results', 'decisive']):
            return 'D'
        elif any(word in personality for word in ['social', 'enthusiastic', 'people']):
            return 'I'
        elif any(word in personality for word in ['steady', 'patient', 'supportive']):
            return 'S'
        elif any(word in personality for word in ['analytical', 'precise', 'detailed']):
            return 'C'
        else:
            return 'D'  # Default to Direct
    
    def generate_script(self, profile: Dict, variant: int) -> str:
        """Generate script using best approach based on variant"""
        
        # Extract data
        name = f"{profile.get('firstname','')} {profile.get('lastname','')}"
        title = profile.get('jobtitle','')
        company = profile.get('company','')
        intel = (profile.get('profile_content') or profile.get('deep_intel', ''))[:1200]
        
        # Detect personality
        disc = self.detect_disc_profile(profile)
        approach = self.disc_approaches[disc]
        style = self.script_styles[variant]
        
        # Build the ultimate prompt combining all approaches
        prompt = f"""You are writing a {style} cold-call script for {name}, {title} at {company}.
        
PERSONALITY TYPE: {disc} - {approach['focus']}
OPENING STYLE: {approach['opening']}
PACE: {approach['pace']}

INTELLIGENCE:
{intel}

GOAL: Book a 15-minute meeting.

Format your response EXACTLY as:

════════════════════════════════════
CALL SCRIPT – {style}
{name} – {title} at {company}
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

════════════════════════════════════
"""
        
        # Use Perplexity for generation (like File #1)
        payload = {
            "model": "sonar-pro",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            r = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.perplexity_key}"},
                timeout=45
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Error: {e}")
            return self.fallback_script(profile, variant, disc)
    
    def fallback_script(self, profile: Dict, variant: int, disc: str) -> str:
        """Fallback if API fails"""
        name = f"{profile.get('firstname','')}"
        company = profile.get('company','')
        approach = self.disc_approaches[disc]
        
        return f"""
════════════════════════════════════
CALL SCRIPT – {self.script_styles[variant]}
{name} at {company}
Personality: {disc}-Type
════════════════════════════════════

📞 OPENER:
"Hi {name}, I know you're busy so I'll be brief..."

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

════════════════════════════════════
"""
    
    def generate_all_scripts(self, contact_id: int) -> Dict:
        """Generate all 3 variants with personality optimization"""
        profile = self.get_profile(contact_id)
        if not profile:
            return None
        
        disc = self.detect_disc_profile(profile)
        scripts = {}
        
        print(f"\n🎯 Generating scripts for {profile['firstname']} {profile['lastname']}")
        print(f"   Detected personality: {disc}-Type")
        print(f"   Company: {profile['company']}")
        print(f"   Score: {profile['score']} | Tier: {profile['tier']}\n")
        
        for variant in (1, 2, 3):
            print(f"   Variant {variant} ({self.script_styles[variant]})... ", end="", flush=True)
            try:
                scripts[variant] = self.generate_script(profile, variant)
                print(f"✅ ({len(scripts[variant])} chars)")
            except Exception as e:
                print(f"❌ {e}")
        
        # Save to database
        if len(scripts) == 3:
            self.save_scripts(contact_id, scripts)
            print("\n✅ All scripts generated and saved!")
        
        return scripts
    
    def save_scripts(self, contact_id: int, scripts: Dict):
        """Save scripts to database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE contacts SET
                call_script_1=?, call_script_2=?, call_script_3=?,
                scripts_generated_at=?
            WHERE id=?
        """, (
            scripts[1], scripts[2], scripts[3],
            datetime.utcnow().isoformat(), contact_id
        ))
        conn.commit()
        conn.close()

# CLI Interface
if __name__ == "__main__":
    import sys
    
    generator = UnifiedCallScriptGenerator()
    
    if len(sys.argv) < 2:
        print("Usage: python call_script_generator_unified.py <contact_id>")
        sys.exit(1)
    
    contact_id = int(sys.argv[1])
    scripts = generator.generate_all_scripts(contact_id)
    
    if scripts:
        for variant, script in scripts.items():
            print(f"\n{'='*70}")
            print(script)
