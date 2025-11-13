#!/usr/bin/env python3

# success_predictor.py - ML model to predict deal success

import sqlite3
from datetime import datetime
import json

class SuccessPredictor:
	"""Predict likelihood of deal closing"""
	
	def __init__(self, db_path='sales_angel.db'):
		self.db_path = db_path
		
	def predict_success(self, contact_id):
		"""Predict success probability for a contact"""
		
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		
		contact = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
		
		if not contact:
			conn.close()
			return None
		
		# Convert to dict for easier access
		contact = dict(contact)
		
		# Simple scoring model (can be enhanced with real ML)
		score = 0
		factors = []
		
		# Factor 1: Lead score (40% weight)
		lead_score = contact.get('score', 0)
		if lead_score >= 90:
			score += 40
			factors.append(("Excellent lead score", 40))
		elif lead_score >= 75:
			score += 30
			factors.append(("Good lead score", 30))
		elif lead_score >= 60:
			score += 20
			factors.append(("Moderate lead score", 20))
		else:
			score += 10
			factors.append(("Low lead score", 10))
			
		# Factor 2: Tier (20% weight)
		tier = contact.get('tier', 'COLD')
		tier_scores = {'HOT': 20, 'WARM': 15, 'QUALIFIED': 10, 'COLD': 5}
		tier_score = tier_scores.get(tier, 5)
		score += tier_score
		factors.append((f"Tier: {tier}", tier_score))
		
		# Factor 3: Engagement (30% weight)
		try:
			activities = conn.execute("""
				SELECT COUNT(*) FROM activities WHERE contact_id = ?
			""", (contact_id,)).fetchone()[0]
			
			if activities >= 5:
				score += 30
				factors.append(("High engagement", 30))
			elif activities >= 3:
				score += 20
				factors.append(("Moderate engagement", 20))
			elif activities >= 1:
				score += 10
				factors.append(("Some engagement", 10))
		except:
			pass
			
		# Factor 4: Recency (10% weight)
		enriched_at = contact.get('enriched_at')
		if enriched_at:
			try:
				from datetime import datetime
				enriched = datetime.fromisoformat(enriched_at.replace('Z', '+00:00'))
				days_old = (datetime.now() - enriched).days
				
				if days_old <= 7:
					score += 10
					factors.append(("Recent data", 10))
				elif days_old <= 30:
					score += 5
					factors.append(("Fresh data", 5))
			except:
				pass
				
		conn.close()
		
		# Convert to percentage
		probability = min(score, 100)
		
		# Determine recommendation
		if probability >= 75:
			recommendation = "🔥 PRIORITY - Engage immediately"
			action = "Schedule meeting this week"
		elif probability >= 60:
			recommendation = "✨ HIGH POTENTIAL - Quick follow-up"
			action = "Send personalized email today"
		elif probability >= 40:
			recommendation = "💭 MODERATE - Nurture campaign"
			action = "Add to drip campaign"
		else:
			recommendation = "❄️ LOW - Long-term nurture"
			action = "Quarterly check-in"
			
		return {
			'contact_id': contact_id,
			'probability': probability,
			'confidence': 'medium',
			'factors': factors,
			'recommendation': recommendation,
			'suggested_action': action,
			'predicted_close_days': 30 if probability >= 75 else 60 if probability >= 60 else 90
		}
	
		# Factor 4: Recency (10% weight)
		if contact.get('enriched_at'):
			try:
				enriched = datetime.fromisoformat(contact['enriched_at'])
				days_old = (datetime.now() - enriched).days
				
				if days_old <= 7:
					score += 10
					factors.append(("Recent data", 10))
				elif days_old <= 30:
					score += 5
					factors.append(("Fresh data", 5))
			except:
				pass
				
		conn.close()
		
		# Convert to percentage
		probability = min(score, 100)
		
		# Determine recommendation
		if probability >= 75:
			recommendation = "🔥 PRIORITY - Engage immediately"
			action = "Schedule meeting this week"
		elif probability >= 60:
			recommendation = "✨ HIGH POTENTIAL - Quick follow-up"
			action = "Send personalized email today"
		elif probability >= 40:
			recommendation = "💭 MODERATE - Nurture campaign"
			action = "Add to drip campaign"
		else:
			recommendation = "❄️ LOW - Long-term nurture"
			action = "Quarterly check-in"
			
		return {
			'contact_id': contact_id,
			'probability': probability,
			'confidence': 'medium',  # Would be higher with more data
			'factors': factors,
			'recommendation': recommendation,
			'suggested_action': action,
			'predicted_close_days': 30 if probability >= 75 else 60 if probability >= 60 else 90
		}
	
	def batch_predict(self, contact_ids=None):
		"""Predict for multiple contacts"""
		
		if contact_ids is None:
			conn = sqlite3.connect(self.db_path)
			contact_ids = [row[0] for row in conn.execute(
				"SELECT id FROM contacts WHERE enriched = 1"
			).fetchall()]
			conn.close()
			
		predictions = []
		for cid in contact_ids:
			pred = self.predict_success(cid)
			if pred:
				predictions.append(pred)
				
		# Sort by probability
		predictions.sort(key=lambda x: x['probability'], reverse=True)
		
		return predictions
	
	def get_prioritized_list(self, limit=10):
		"""Get top contacts to focus on"""
		
		predictions = self.batch_predict()
		return predictions[:limit]
	
# CLI
if __name__ == "__main__":
	import sys
	
	predictor = SuccessPredictor()
	
	if len(sys.argv) > 1:
		contact_id = int(sys.argv[1])
		pred = predictor.predict_success(contact_id)
		
		if pred:
			print(f"\n🎯 Success Prediction for Contact {contact_id}")
			print("="*70)
			print(f"\nSuccess Probability: {pred['probability']}%")
			print(f"Confidence: {pred['confidence']}")
			print(f"\n{pred['recommendation']}")
			print(f"Action: {pred['suggested_action']}")
			print(f"\nPredicted Close: {pred['predicted_close_days']} days")
			
			print(f"\n📊 Contributing Factors:")
			for factor, points in pred['factors']:
				print(f"  • {factor}: +{points}")
			print()
	else:
		print("\n🏆 Top 10 Contacts to Focus On:\n")
		top = predictor.get_prioritized_list(10)
		
		for i, pred in enumerate(top, 1):
			print(f"{i}. Contact {pred['contact_id']} - {pred['probability']}% probability")
			print(f"   {pred['recommendation']}")
			print()
			