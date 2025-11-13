#!/usr/bin/env python3

# adaptive_learning_engine.py - AI that learns from your results

import sqlite3
from datetime import datetime, timezone
from collections import defaultdict
import json

class AdaptiveLearningEngine:
		"""Learn which content variants perform best and auto-optimize"""
	
		def __init__(self, db_path='sales_angel.db'):
				self.db_path = db_path
				self._init_tables()
			
		def _init_tables(self):
				"""Create learning tables"""
				conn = sqlite3.connect(self.db_path)
			
				# Variant performance tracking
				conn.execute("""
						CREATE TABLE IF NOT EXISTS variant_performance (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								variant_type TEXT NOT NULL,
								variant_number INTEGER NOT NULL,
								contact_tier TEXT,
								contact_score_range TEXT,
								sent_count INTEGER DEFAULT 0,
								opened_count INTEGER DEFAULT 0,
								replied_count INTEGER DEFAULT 0,
								meeting_count INTEGER DEFAULT 0,
								last_updated TEXT,
								performance_score REAL DEFAULT 0.0,
								UNIQUE(variant_type, variant_number, contact_tier, contact_score_range)
						)
				""")
			
				# Learning insights
				conn.execute("""
						CREATE TABLE IF NOT EXISTS learning_insights (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								insight_type TEXT NOT NULL,
								insight_text TEXT NOT NULL,
								confidence REAL NOT NULL,
								evidence_count INTEGER NOT NULL,
								created_at TEXT NOT NULL,
								status TEXT DEFAULT 'active'
						)
				""")
			
				conn.commit()
				conn.close()
			
		def record_outcome(self, contact_id, variant_type, variant_num, outcome):
				"""Record outcome for a specific variant use"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				# Get contact details
				contact = conn.execute("""
						SELECT tier, score FROM contacts WHERE id = ?
				""", (contact_id,)).fetchone()
			
				if not contact:
						conn.close()
						return
			
				tier = contact['tier']
				score = contact['score']
				score_range = self._get_score_range(score)
			
				# Get or create performance record
				perf = conn.execute("""
						SELECT * FROM variant_performance 
						WHERE variant_type = ? AND variant_number = ? 
							AND contact_tier = ? AND contact_score_range = ?
				""", (variant_type, variant_num, tier, score_range)).fetchone()
			
				if perf:
						# Update existing
						updates = {
								'sent_count': perf['sent_count'],
								'opened_count': perf['opened_count'],
								'replied_count': perf['replied_count'],
								'meeting_count': perf['meeting_count']
						}
					
						if outcome in ['sent', 'delivered']:
								updates['sent_count'] += 1
						elif outcome in ['opened', 'viewed']:
								updates['opened_count'] += 1
						elif outcome in ['replied', 'response']:
								updates['replied_count'] += 1
						elif outcome in ['meeting', 'booked']:
								updates['meeting_count'] += 1
							
						# Calculate performance score
						score = self._calculate_performance_score(
								updates['sent_count'],
								updates['opened_count'],
								updates['replied_count'],
								updates['meeting_count']
						)
					
						conn.execute("""
								UPDATE variant_performance 
								SET sent_count = ?, opened_count = ?, replied_count = ?, 
										meeting_count = ?, performance_score = ?, last_updated = ?
								WHERE id = ?
						""", (updates['sent_count'], updates['opened_count'], 
									updates['replied_count'], updates['meeting_count'],
									score, datetime.now(timezone.utc).isoformat(), perf['id']))
				else:
						# Create new
						initial_counts = {
								'sent': 1 if outcome in ['sent', 'delivered'] else 0,
								'opened': 1 if outcome in ['opened', 'viewed'] else 0,
								'replied': 1 if outcome in ['replied', 'response'] else 0,
								'meeting': 1 if outcome in ['meeting', 'booked'] else 0
						}
					
						score = self._calculate_performance_score(**initial_counts)
					
						conn.execute("""
								INSERT INTO variant_performance 
								(variant_type, variant_number, contact_tier, contact_score_range,
									sent_count, opened_count, replied_count, meeting_count,
									performance_score, last_updated)
								VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
						""", (variant_type, variant_num, tier, score_range,
									initial_counts['sent'], initial_counts['opened'],
									initial_counts['replied'], initial_counts['meeting'],
									score, datetime.now(timezone.utc).isoformat()))
					
				conn.commit()
				conn.close()
			
				# Check for new insights
				self._analyze_patterns()
			
		def _get_score_range(self, score):
				"""Bucket scores into ranges"""
				if score >= 80:
						return '80-100'
				elif score >= 60:
						return '60-79'
				elif score >= 40:
						return '40-59'
				else:
						return '0-39'
			
		def _calculate_performance_score(self, sent, opened, replied, meeting):
				"""Calculate weighted performance score"""
				if sent == 0:
						return 0.0
			
				# Weighted scores
				open_rate = (opened / sent) * 100 if sent > 0 else 0
				reply_rate = (replied / sent) * 100 if sent > 0 else 0
				meeting_rate = (meeting / sent) * 100 if sent > 0 else 0
			
				# Weighted formula (meetings matter most!)
				score = (open_rate * 1) + (reply_rate * 3) + (meeting_rate * 10)
				return round(score, 2)
	
		def get_best_variant(self, variant_type, tier, score):
				"""Get recommended variant based on learning"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				score_range = self._get_score_range(score)
			
				# Get performance for all variants in this segment
				variants = conn.execute("""
						SELECT variant_number, performance_score, sent_count,
										replied_count, meeting_count
						FROM variant_performance
						WHERE variant_type = ? 
							AND contact_tier = ? 
							AND contact_score_range = ?
							AND sent_count >= 3
						ORDER BY performance_score DESC
						LIMIT 1
				""", (variant_type, tier, score_range)).fetchone()
			
				conn.close()
			
				if variants:
						return {
								'recommended_variant': variants['variant_number'],
								'confidence': 'high' if variants['sent_count'] >= 10 else 'medium',
								'performance_score': variants['performance_score'],
								'evidence': f"{variants['sent_count']} sends, {variants['replied_count']} replies, {variants['meeting_count']} meetings"
						}
				else:
						# Not enough data - suggest variant 1 as default
						return {
								'recommended_variant': 1,
								'confidence': 'low',
								'performance_score': 0,
								'evidence': 'Insufficient data - using default'
						}
			
		def _analyze_patterns(self):
				"""Analyze patterns and generate insights"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				# Find patterns
				insights = []
			
				# Pattern 1: Best performing variant overall
				best_email = conn.execute("""
						SELECT variant_number, AVG(performance_score) as avg_score,
										SUM(sent_count) as total_sent
						FROM variant_performance
						WHERE variant_type = 'email' AND sent_count >= 5
						GROUP BY variant_number
						ORDER BY avg_score DESC
						LIMIT 1
				""").fetchone()
			
				if best_email and best_email['avg_score'] > 0:
						insights.append({
								'type': 'best_variant',
								'text': f"Email variant {best_email['variant_number']} performs best overall (score: {best_email['avg_score']:.1f}, {best_email['total_sent']} sends)",
								'confidence': 0.8 if best_email['total_sent'] >= 20 else 0.6,
								'evidence': best_email['total_sent']
						})
					
				# Pattern 2: Tier-specific insights
				for tier in ['HOT', 'WARM', 'QUALIFIED']:
						best_for_tier = conn.execute("""
								SELECT variant_number, performance_score, sent_count
								FROM variant_performance
								WHERE variant_type = 'email' 
									AND contact_tier = ?
									AND sent_count >= 3
								ORDER BY performance_score DESC
								LIMIT 1
						""", (tier,)).fetchone()
					
						if best_for_tier:
								insights.append({
										'type': 'tier_specific',
										'text': f"{tier} contacts respond best to variant {best_for_tier['variant_number']} (score: {best_for_tier['performance_score']:.1f})",
										'confidence': 0.7 if best_for_tier['sent_count'] >= 10 else 0.5,
										'evidence': best_for_tier['sent_count']
								})
							
				# Save new insights
				for insight in insights:
						# Check if similar insight exists
						existing = conn.execute("""
								SELECT id FROM learning_insights
								WHERE insight_text = ? AND status = 'active'
						""", (insight['text'],)).fetchone()
					
						if not existing:
								conn.execute("""
										INSERT INTO learning_insights
										(insight_type, insight_text, confidence, evidence_count, created_at)
										VALUES (?, ?, ?, ?, ?)
								""", (insight['type'], insight['text'], insight['confidence'],
											insight['evidence'], datetime.now(timezone.utc).isoformat()))
							
				conn.commit()
				conn.close()
			
		def get_insights(self, min_confidence=0.5):
				"""Get current learning insights"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				insights = conn.execute("""
						SELECT * FROM learning_insights
						WHERE status = 'active' AND confidence >= ?
						ORDER BY confidence DESC, created_at DESC
				""", (min_confidence,)).fetchall()
			
				conn.close()
				return [dict(i) for i in insights]
	
		def generate_recommendations(self, contact_id):
				"""Generate personalized recommendations for a contact"""
			
				conn = sqlite3.connect(self.db_path)
				conn.row_factory = sqlite3.Row
			
				contact = conn.execute("""
						SELECT tier, score FROM contacts WHERE id = ?
				""", (contact_id,)).fetchone()
			
				conn.close()
			
				if not contact:
						return None
			
				email_rec = self.get_best_variant('email', contact['tier'], contact['score'])
				call_rec = self.get_best_variant('call', contact['tier'], contact['score'])
			
				return {
						'contact_id': contact_id,
						'tier': contact['tier'],
						'score': contact['score'],
						'recommended_email_variant': email_rec,
						'recommended_call_variant': call_rec,
						'general_insights': self.get_insights(min_confidence=0.6)
				}
	
		def print_learning_summary(self):
				"""Print beautiful learning summary"""
			
				print("\n" + "="*80)
				print("🧠 ADAPTIVE LEARNING ENGINE - Intelligence Summary")
				print("="*80 + "\n")
			
				# Overall stats
				conn = sqlite3.connect(self.db_path)
			
				total_data = conn.execute("""
						SELECT COUNT(*) as segments, 
										SUM(sent_count) as total_sent,
										SUM(replied_count) as total_replied,
										SUM(meeting_count) as total_meetings
						FROM variant_performance
				""").fetchone()
			
				print("📊 Learning Data:")
				print(f"  Segments Analyzed: {total_data[0]}")
				print(f"  Total Sends Tracked: {total_data[1]}")
				print(f"  Total Replies: {total_data[2]}")
				print(f"  Total Meetings: {total_data[3]}")
				print()
			
				# Best performers
				print("🏆 Top Performers:")
				top_performers = conn.execute("""
						SELECT variant_type, variant_number, contact_tier,
										performance_score, sent_count, replied_count, meeting_count
						FROM variant_performance
						WHERE sent_count >= 5
						ORDER BY performance_score DESC
						LIMIT 5
				""").fetchall()
			
				for p in top_performers:
						print(f"  {p[0].title()} V{p[1]} ({p[2]}): Score {p[3]:.1f} | {p[4]} sent, {p[5]} replies, {p[6]} meetings")
				print()
			
				# Insights
				insights = self.get_insights(min_confidence=0.5)
				if insights:
						print("💡 Key Insights:")
						for insight in insights[:5]:
								confidence_icon = "🔥" if insight['confidence'] >= 0.8 else "✨" if insight['confidence'] >= 0.6 else "💭"
								print(f"  {confidence_icon} {insight['insight_text']}")
								print(f"     Confidence: {insight['confidence']*100:.0f}% | Evidence: {insight['evidence_count']} samples")
							
				conn.close()
				print("\n" + "="*80 + "\n")
			
			
# CLI
if __name__ == "__main__":
		import sys
	
		engine = AdaptiveLearningEngine()
	
		if len(sys.argv) < 2:
				print("""
╔══════════════════════════════════════════════════════════════╗
║            ADAPTIVE LEARNING ENGINE                           ║
║     AI That Learns Which Variants Work Best                   ║
╚══════════════════════════════════════════════════════════════╝

Usage:
	python adaptive_learning_engine.py summary
	python adaptive_learning_engine.py recommend <contact_id>
	python adaptive_learning_engine.py record <contact_id> <type> <variant> <outcome>

Examples:
	python adaptive_learning_engine.py summary
	python adaptive_learning_engine.py recommend 157153
	python adaptive_learning_engine.py record 157153 email 1 replied
	python adaptive_learning_engine.py record 157153 email 2 meeting
""")
				sys.exit(1)
			
		command = sys.argv[1]
	
		if command == 'summary':
				engine.print_learning_summary()
			
		elif command == 'recommend':
				contact_id = int(sys.argv[2])
				rec = engine.generate_recommendations(contact_id)
			
				if rec:
						print(f"\n🎯 Recommendations for Contact {contact_id}")
						print("="*70)
						print(f"Tier: {rec['tier']} | Score: {rec['score']}\n")
					
						print("📧 Email:")
						email = rec['recommended_email_variant']
						print(f"  Use Variant {email['recommended_variant']}")
						print(f"  Confidence: {email['confidence'].upper()}")
						print(f"  Evidence: {email['evidence']}\n")
					
						print("📞 Call:")
						call = rec['recommended_call_variant']
						print(f"  Use Variant {call['recommended_variant']}")
						print(f"  Confidence: {call['confidence'].upper()}")
						print(f"  Evidence: {call['evidence']}\n")
					
		elif command == 'record':
				contact_id = int(sys.argv[2])
				variant_type = sys.argv[3]
				variant_num = int(sys.argv[4])
				outcome = sys.argv[5]
			
				engine.record_outcome(contact_id, variant_type, variant_num, outcome)
				print(f"✅ Recorded: {variant_type} variant {variant_num} → {outcome}")
			