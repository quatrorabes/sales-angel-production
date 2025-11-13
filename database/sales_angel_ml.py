#!/usr/bin/env python3
"""
SALES ANGEL - ML LEARNING ENGINE
Learns from user feedback and adapts generation parameters
Tracks quality metrics and improves over time
"""

import json
from typing import Dict, List, Any
from collections import defaultdict
from sales_angel_db import SalesAngelDB

class ContentQualityPredictor:
    """ML model that learns from user feedback"""

    def __init__(self, db: SalesAngelDB):
        self.db = db
        self.feature_weights = {
            'style': {},
            'variant_num': {},
            'word_count': 0.1,
            'has_specific_reference': 0.2,
            'has_social_proof': 0.15
        }

    def train(self):
        """
        Train model from user feedback
        Updates weights based on what users accept/reject
        """
        ml_features = self.db.get_ml_features()

        # Update style weights
        for style, stats in ml_features.get('by_style', {}).items():
            count = stats['count']
            accepted = stats['accepted']
            acceptance_rate = accepted / count if count > 0 else 0.5
            self.feature_weights['style'][style] = acceptance_rate

        # Update variant weights
        for variant, stats in ml_features.get('by_variant', {}).items():
            count = stats['count']
            accepted = stats['accepted']
            acceptance_rate = accepted / count if count > 0 else 0.5
            self.feature_weights['variant_num'][variant] = acceptance_rate

        return self.feature_weights

    def score_content(self, content: Dict[str, Any]) -> float:
        """
        Predict quality score (0-1) based on learned patterns
        Higher score = more likely user will accept
        """
        score = 0.5  # Base score

        # Style component
        style = content.get('style', 'Unknown')
        if style in self.feature_weights['style']:
            score += self.feature_weights['style'][style] * 0.4

        # Variant component
        variant = content.get('variant_num', 0)
        if variant in self.feature_weights['variant_num']:
            score += self.feature_weights['variant_num'][variant] * 0.3

        # Length component (shorter often better for calls, emails moderate)
        word_count = len(content.get('body', '').split())
        if word_count > 0:
            # Prefer 60-100 words; penalty outside
            if 60 <= word_count <= 100:
                score += 0.15
            elif 50 <= word_count <= 150:
                score += 0.05

        # Has specific reference
        body = content.get('body', '').lower()
        if any(word in body for word in ['bank', 'lending', 'credit', 'deal']):
            score += 0.1

        return min(score, 1.0)

    def get_recommendations(self, contact: Dict[str, Any]) -> Dict[str, str]:
        """
        Get explanations for why each option is good or bad
        """
        ml_features = self.db.get_ml_features()
        acceptance_rate = ml_features.get('acceptance_rate', 0.5)

        recommendations = {
            'accept': self._build_accept_reasoning(contact, ml_features),
            'reject': self._build_reject_reasoning(contact, ml_features),
            'overall_quality': self._quality_summary(ml_features)
        }

        return recommendations

    def _build_accept_reasoning(self, content: Dict[str, Any], ml_features: Dict) -> str:
        """Build explanation for accepting content"""
        reasons = []

        style = content.get('style', 'Unknown')
        if style in ml_features.get('by_style', {}):
            acceptance = ml_features['by_style'][style]['accepted']
            total = ml_features['by_style'][style]['count']
            if acceptance and total:
                pct = (acceptance / total) * 100
                reasons.append(f"✅ {style} style: {pct:.0f}% user acceptance rate")

        # Check for specificity
        body = content.get('body', '').lower()
        if any(term in body for term in ['specific', 'bank', 'lending', 'credit']):
            reasons.append("✅ References specific lending context")

        if len(content.get('body', '').split()) < 100:
            reasons.append("✅ Concise (under 100 words - improves response rates)")

        if content.get('cta'):
            reasons.append(f"✅ Clear CTA: '{content['cta']}'")

        if not reasons:
            reasons.append("✅ Content is structured and ready to use")

        return " | ".join(reasons)

    def _build_reject_reasoning(self, content: Dict[str, Any], ml_features: Dict) -> str:
        """Build explanation for rejecting content"""
        reasons = []

        style = content.get('style', 'Unknown')
        if style in ml_features.get('by_style', {}):
            acceptance = ml_features['by_style'][style]['accepted']
            total = ml_features['by_style'][style]['count']
            if total > 5 and acceptance:  # Only flag if enough data
                pct = (acceptance / total) * 100
                if pct < 40:
                    reasons.append(f"⚠️  {style} style: only {pct:.0f}% acceptance rate (below average)")

        # Check for generic language
        body = content.get('body', '').lower()
        generic_terms = ['hope you are well', 'reach out', 'let me know', 'interested in']
        if any(term in body for term in generic_terms):
            reasons.append("⚠️  Contains generic opening (reduces response rates)")

        # Check length
        word_count = len(content.get('body', '').split())
        if word_count > 150:
            reasons.append(f"⚠️  Too long ({word_count} words - aim for 60-100)")

        if not content.get('cta'):
            reasons.append("⚠️  No clear call-to-action")

        # Check for banned terms
        banned = ['fintech', 'software', 'platform', 'app', 'AI solution']
        if any(term.lower() in body for term in banned):
            reasons.append("🚫 Contains off-topic terms (fintech/software/etc.)")

        if not reasons:
            reasons.append("⚠️  Consider if this matches your style preferences")

        return " | ".join(reasons)

    def _quality_summary(self, ml_features: Dict) -> str:
        """Overall quality assessment"""
        acceptance_rate = ml_features.get('acceptance_rate', 0.5)

        if acceptance_rate >= 0.75:
            return f"🟢 HIGH QUALITY: {acceptance_rate*100:.0f}% acceptance rate"
        elif acceptance_rate >= 0.50:
            return f"🟡 MODERATE: {acceptance_rate*100:.0f}% acceptance rate"
        else:
            return f"🔴 NEEDS IMPROVEMENT: {acceptance_rate*100:.0f}% acceptance rate"


class AdaptivePromptOptimizer:
    """
    Uses feedback to optimize prompts for future generations
    Adjusts style preferences based on user patterns
    """

    def __init__(self, db: SalesAngelDB):
        self.db = db
        self.user_preferences = {}

    def analyze_preferences(self) -> Dict[str, Any]:
        """
        Analyze user's acceptance patterns
        Returns preferred styles, variants, approaches
        """
        ml_features = self.db.get_ml_features()

        # Find best styles
        by_style = ml_features.get('by_style', {})
        ranked_styles = sorted(
            by_style.items(),
            key=lambda x: (x[1]['accepted'] / x[1]['count'] if x[1]['count'] > 0 else 0),
            reverse=True
        )

        # Find best variants
        by_variant = ml_features.get('by_variant', {})
        ranked_variants = sorted(
            by_variant.items(),
            key=lambda x: (x[1]['accepted'] / x[1]['count'] if x[1]['count'] > 0 else 0),
            reverse=True
        )

        preferences = {
            'preferred_styles': [style for style, _ in ranked_styles[:2]],
            'preferred_variants': [var for var, _ in ranked_variants[:2]],
            'overall_acceptance': ml_features.get('acceptance_rate', 0),
            'improvement_areas': [style for style, _ in ranked_styles[-1:]] if ranked_styles else []
        }

        self.user_preferences = preferences
        return preferences

    def get_optimized_prompt_adjustments(self) -> str:
        """
        Returns prompt adjustments based on learned preferences
        To be used in next generation round
        """
        if not self.user_preferences:
            self.analyze_preferences()

        prefs = self.user_preferences
        adjustments = []

        if prefs.get('preferred_styles'):
            top_styles = ", ".join(prefs['preferred_styles'][:2])
            adjustments.append(f"Focus on these styles (highest acceptance): {top_styles}")

        if prefs.get('overall_acceptance', 0) > 0.7:
            adjustments.append("User has high acceptance - maintain current quality standards")
        elif prefs.get('overall_acceptance', 0) < 0.5:
            adjustments.append("Lower acceptance - emphasize specificity and personalization")

        if prefs.get('improvement_areas'):
            poor_styles = ", ".join(prefs['improvement_areas'])
            adjustments.append(f"Avoid overusing: {poor_styles}")

        return "\n".join(adjustments) if adjustments else "Continue with current approach"


if __name__ == "__main__":
    db = SalesAngelDB()
    predictor = ContentQualityPredictor(db)
    optimizer = AdaptivePromptOptimizer(db)

    print("✅ ML Learning system initialized")
    print()
    print("Features:")
    print("- Content quality prediction")
    print("- User preference analysis")
    print("- Adaptive prompt optimization")
