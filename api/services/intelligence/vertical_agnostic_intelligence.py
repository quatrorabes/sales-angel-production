#!/usr/bin/env python3
"""
VERTICAL-AGNOSTIC SELF-LEARNING INTELLIGENCE PLATFORM
Worth $100M+ because it works for ANY industry
"""

import os
import yaml
import json
import sqlite3
import requests
from openai import OpenAI
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import pickle
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split

class VerticalAgnosticIntelligence:
    """
    The MONEY MAKER - Works for ANY vertical
    """
    
    def __init__(self, vertical="commercial_lending"):
        self.vertical = vertical
        self.load_vertical_config()
        self.init_learning_system()
        self.load_ml_models()
        
    def load_vertical_config(self):
        """Load industry-specific configuration"""
        config_path = f"configs/verticals/{self.vertical}.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.vertical_config = yaml.safe_load(f)
        else:
            # Default config if vertical doesn't exist
            self.vertical_config = self.create_default_config()
    
    def create_default_config(self):
        """Create default config for new verticals"""
        return {
            "name": f"{self.vertical.title()} Intelligence",
            "version": "1.0",
            "target_personas": ["Decision Makers", "Influencers", "Users"],
            "pain_points": ["Efficiency", "Cost", "Growth", "Competition"],
            "trigger_events": ["Expansion", "New Leadership", "Funding", "Problems"]
        }
    
    def init_learning_system(self):
        """Initialize the self-learning database"""
        self.conn = sqlite3.connect(f'data/{self.vertical}_intelligence.db')
        cursor = self.conn.cursor()
        
        # Universal tables that work for ANY vertical
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrichment_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vertical TEXT,
                pattern_type TEXT,
                pattern_content TEXT,
                success_rate REAL,
                usage_count INTEGER,
                revenue_impact REAL,
                last_updated TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outcome_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id TEXT,
                vertical TEXT,
                enrichment_quality REAL,
                action_taken TEXT,
                outcome TEXT,
                revenue REAL,
                time_to_close INTEGER,
                success_factors TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_evolution (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vertical TEXT,
                prompt_version TEXT,
                prompt_text TEXT,
                performance_score REAL,
                a_b_test_group TEXT,
                created_date TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def generate_vertical_specific_prompt(self, contact, context=None):
        """Generate prompts specific to the vertical"""
        base_prompt = f"""
        You are analyzing a contact in the {self.vertical_config['name']} industry.
        
        Contact: {contact.get('name')} at {contact.get('company')}
        Title: {contact.get('title')}
        
        Industry-Specific Focus Areas:
        """
        
        # Add vertical-specific intelligence requirements
        if 'specific_intelligence' in self.vertical_config:
            for intel in self.vertical_config['specific_intelligence']:
                base_prompt += f"\n- {intel}"
        
        # Add pain points to investigate
        base_prompt += "\n\nIdentify these specific pain points:"
        for pain in self.vertical_config.get('pain_points', []):
            base_prompt += f"\n- {pain}"
        
        # Add trigger events to look for
        base_prompt += "\n\nLook for these trigger events:"
        for trigger in self.vertical_config.get('trigger_events', []):
            base_prompt += f"\n- {trigger}"
        
        # Add custom prompts if defined
        if 'custom_prompts' in self.vertical_config:
            base_prompt += f"\n\n{self.vertical_config['custom_prompts'].get('person_focus', '')}"
        
        # Add learning from past successes
        successful_patterns = self.get_successful_patterns()
        if successful_patterns:
            base_prompt += "\n\nBased on past successes in this vertical, also investigate:"
            for pattern in successful_patterns[:3]:
                base_prompt += f"\n- {pattern[0]}"
        
        return base_prompt
    
    def get_successful_patterns(self):
        """Get patterns that led to success in this vertical"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT pattern_content, success_rate
            FROM enrichment_patterns
            WHERE vertical = ? AND success_rate > 0.7
            ORDER BY revenue_impact DESC
            LIMIT 5
        ''', (self.vertical,))
        return cursor.fetchall()
    
    def enrich_with_vertical_intelligence(self, contact):
        """Perform vertical-specific enrichment"""
        
        # Generate vertical-specific prompt
        prompt = self.generate_vertical_specific_prompt(contact)
        
        # Choose API based on vertical needs
        if self.vertical in ['insurance', 'real_estate']:
            # These need more real-time data
            enrichment = self.call_perplexity_with_vertical_context(contact, prompt)
        else:
            # These need deeper analysis
            enrichment = self.call_openai_with_vertical_context(contact, prompt)
        
        # Add vertical-specific scoring
        enrichment['vertical_score'] = self.calculate_vertical_fit_score(enrichment)
        
        # Predict success in this vertical
        enrichment['success_probability'] = self.predict_vertical_success(enrichment)
        
        # Generate vertical-specific outreach
        enrichment['vertical_outreach'] = self.generate_vertical_outreach(enrichment)
        
        return enrichment
    
    def calculate_vertical_fit_score(self, enrichment):
        """Calculate how well this fits the vertical"""
        score = 0
        
        # Check for vertical-specific keywords
        content = str(enrichment).lower()
        for keyword in self.vertical_config.get('keywords', []):
            if keyword.lower() in content:
                score += 10
        
        # Check for pain point matches
        for pain in self.vertical_config.get('pain_points', []):
            if pain.lower() in content:
                score += 15
        
        # Check for trigger events
        for trigger in self.vertical_config.get('trigger_events', []):
            if trigger.lower() in content:
                score += 20
        
        return min(score, 100)
    
    def call_perplexity_with_vertical_context(self, contact, prompt):
        """Call Perplexity with vertical-specific context"""
        
        # Add vertical context to the system message
        system_message = f"""You are an expert in {self.vertical_config['name']}. 
        You understand the specific challenges, terminology, and success factors in this industry.
        Market size: {self.vertical_config.get('market_size', 'Large')}
        Key personas: {', '.join(self.vertical_config.get('target_personas', []))}"""
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}"},
            json={
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            }
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def call_openai_with_vertical_context(self, contact, prompt):
        """Call OpenAI with vertical-specific context"""
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are a {self.vertical_config['name']} expert."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def generate_vertical_outreach(self, enrichment):
        """Generate outreach specific to the vertical"""
        
        templates = {
            "commercial_lending": """
                Hi {name},
                
                I noticed {company}'s recent {trigger_event}. With rates at {current_rate}%, 
                many in your position are {pain_point}.
                
                We've helped similar {vertical} companies secure {benefit}.
                
                Worth a quick call to discuss {specific_opportunity}?
            """,
            "insurance": """
                Hi {name},
                
                Following {company}'s {recent_activity}, I wanted to reach out.
                
                We specialize in helping {vertical} professionals with {pain_point},
                especially when {trigger_event}.
                
                Can we schedule 15 minutes to discuss {opportunity}?
            """,
            "residential_real_estate": """
                Hi {name},
                
                Saw your recent {achievement} at {company}. Impressive!
                
                With {market_condition}, many agents are struggling with {pain_point}.
                
                We've helped agents increase {metric} by {percentage}%.
                
                Open to a brief call about {specific_solution}?
            """
        }
        
        # Use vertical-specific template or default
        template = templates.get(self.vertical, templates['commercial_lending'])
        
        # Fill in the template with enrichment data
        outreach = template.format(
            name=enrichment.get('name', 'there'),
            company=enrichment.get('company', 'your company'),
            trigger_event=enrichment.get('trigger_event', 'expansion'),
            pain_point=enrichment.get('main_pain_point', 'growth challenges'),
            vertical=self.vertical,
            # Add more dynamic fields
        )
        
        return outreach
    
    def predict_vertical_success(self, enrichment):
        """Predict success probability in this vertical"""
        
        if not hasattr(self, 'vertical_model') or self.vertical_model is None:
            return 0.5
        
        # Extract vertical-specific features
        features = self.extract_vertical_features(enrichment)
        
        try:
            # Use the trained model
            probability = self.vertical_model.predict_proba([features])[0][1]
            return probability
        except:
            return 0.5
    
    def extract_vertical_features(self, enrichment):
        """Extract features specific to the vertical"""
        features = []
        
        # Universal features
        features.append(enrichment.get('vertical_score', 0))
        features.append(len(str(enrichment)) / 1000)  # Content depth
        
        # Vertical-specific features
        if self.vertical == "commercial_lending":
            features.append(1 if 'loan' in str(enrichment).lower() else 0)
            features.append(1 if 'rate' in str(enrichment).lower() else 0)
            features.append(1 if 'portfolio' in str(enrichment).lower() else 0)
        elif self.vertical == "insurance":
            features.append(1 if 'premium' in str(enrichment).lower() else 0)
            features.append(1 if 'carrier' in str(enrichment).lower() else 0)
            features.append(1 if 'claims' in str(enrichment).lower() else 0)
        # Add more verticals
        
        return features
    
    def load_ml_models(self):
        """Load or create ML models for this vertical"""
        model_path = f'models/{self.vertical}_model.pkl'
        
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.vertical_model = pickle.load(f)
        else:
            # Create a new model for this vertical
            self.vertical_model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            )
    
    def learn_from_outcome(self, contact_id, outcome):
        """Learn from outcomes in this vertical"""
        cursor = self.conn.cursor()
        
        # Record the outcome
        cursor.execute('''
            INSERT INTO outcome_tracking
            (contact_id, vertical, outcome, revenue, success_factors)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            contact_id,
            self.vertical,
            outcome.get('result'),
            outcome.get('revenue', 0),
            json.dumps(outcome.get('success_factors', []))
        ))
        
        # Update pattern success rates
        if outcome.get('result') == 'success':
            self.update_successful_patterns(outcome)
        
        # Retrain model periodically
        if self.should_retrain():
            self.retrain_vertical_model()
        
        self.conn.commit()
    
    def update_successful_patterns(self, outcome):
        """Update patterns that led to success"""
        cursor = self.conn.cursor()
        
        for factor in outcome.get('success_factors', []):
            cursor.execute('''
                INSERT OR REPLACE INTO enrichment_patterns
                (vertical, pattern_type, pattern_content, success_rate, usage_count, revenue_impact)
                VALUES (?, ?, ?, 
                    COALESCE((SELECT success_rate FROM enrichment_patterns 
                              WHERE vertical = ? AND pattern_content = ?), 0) + 0.1,
                    COALESCE((SELECT usage_count FROM enrichment_patterns 
                              WHERE vertical = ? AND pattern_content = ?), 0) + 1,
                    COALESCE((SELECT revenue_impact FROM enrichment_patterns 
                              WHERE vertical = ? AND pattern_content = ?), 0) + ?
                )
            ''', (
                self.vertical, 'success_factor', factor,
                self.vertical, factor,
                self.vertical, factor,
                self.vertical, factor, outcome.get('revenue', 0)
            ))
    
    def should_retrain(self):
        """Determine if model needs retraining"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM outcome_tracking 
            WHERE vertical = ?
        ''', (self.vertical,))
        count = cursor.fetchone()[0]
        
        # Retrain every 50 new outcomes
        return count % 50 == 0 and count > 0
    
    def retrain_vertical_model(self):
        """Retrain the model with vertical-specific data"""
        cursor = self.conn.cursor()
        
        # Get training data for this vertical
        cursor.execute('''
            SELECT * FROM outcome_tracking
            WHERE vertical = ?
        ''', (self.vertical,))
        
        data = cursor.fetchall()
        if len(data) > 20:  # Need minimum data
            X = []
            y = []
            
            for row in data:
                # Extract features
                features = [
                    row[3],  # enrichment_quality
                    # Add more features
                ]
                X.append(features)
                y.append(1 if row[5] == 'success' else 0)
            
            # Split and train
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            self.vertical_model.fit(X_train, y_train)
            
            # Save the model
            with open(f'models/{self.vertical}_model.pkl', 'wb') as f:
                pickle.dump(self.vertical_model, f)
            
            print(f"✅ Retrained {self.vertical} model - Accuracy: {self.vertical_model.score(X_test, y_test):.2%}")
    
    def switch_vertical(self, new_vertical):
        """Switch to a different vertical"""
        self.vertical = new_vertical
        self.load_vertical_config()
        self.init_learning_system()
        self.load_ml_models()
        print(f"✅ Switched to {new_vertical} vertical")
    
    def get_vertical_insights(self):
        """Get insights specific to this vertical"""
        cursor = self.conn.cursor()
        
        insights = {
            "vertical": self.vertical,
            "total_enrichments": 0,
            "success_rate": 0,
            "avg_revenue": 0,
            "best_patterns": [],
            "optimal_times": [],
            "top_pain_points": []
        }
        
        # Get success metrics
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as success_rate,
                AVG(revenue) as avg_revenue
            FROM outcome_tracking
            WHERE vertical = ?
        ''', (self.vertical,))
        
        result = cursor.fetchone()
        if result:
            insights["total_enrichments"] = result[0]
            insights["success_rate"] = result[1] or 0
            insights["avg_revenue"] = result[2] or 0
        
        # Get best performing patterns
        cursor.execute('''
            SELECT pattern_content, success_rate, revenue_impact
            FROM enrichment_patterns
            WHERE vertical = ?
            ORDER BY revenue_impact DESC
            LIMIT 5
        ''', (self.vertical,))
        
        insights["best_patterns"] = cursor.fetchall()
        
        return insights

# Main execution
if __name__ == "__main__":
    import sys
    
    # Get vertical from command line or default
    vertical = sys.argv[1] if len(sys.argv) > 1 else "commercial_lending"
    
    # Initialize for specific vertical
    print(f"🚀 Initializing {vertical.upper()} Intelligence Platform")
    intelligence = VerticalAgnosticIntelligence(vertical=vertical)
    
    # Example contact
    contact = {
        "id": "123",
        "name": "John Smith",
        "company": "ABC Corp",
        "title": "CEO",
        "linkedin": "linkedin.com/in/johnsmith"
    }
    
    # Perform vertical-specific enrichment
    enriched = intelligence.enrich_with_vertical_intelligence(contact)
    print(f"✅ Enriched with {enriched.get('vertical_score', 0)}% vertical fit")
    print(f"📊 Success probability: {enriched.get('success_probability', 0):.0%}")
    
    # Simulate learning
    outcome = {
        "result": "success",
        "revenue": 50000,
        "success_factors": ["trigger_event_match", "pain_point_addressed", "timing"]
    }
    intelligence.learn_from_outcome("123", outcome)
    
    # Get vertical insights
    insights = intelligence.get_vertical_insights()
    print(f"\n📈 {vertical.upper()} Insights:")
    print(f"   Success Rate: {insights['success_rate']:.0%}")
    print(f"   Avg Revenue: ${insights['avg_revenue']:,.0f}")
    
    # Demo switching verticals
    print("\n🔄 Switching to INSURANCE vertical...")
    intelligence.switch_vertical("insurance")
    
    # Enrich same contact with new vertical context
    insurance_enriched = intelligence.enrich_with_vertical_intelligence(contact)
    print(f"✅ Insurance vertical score: {insurance_enriched.get('vertical_score', 0)}%")
