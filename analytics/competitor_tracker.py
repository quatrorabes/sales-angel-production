#!/usr/bin/env python3

# competitor_tracker.py - Track competitor mentions

import sqlite3
from datetime import datetime, timezone
import re

class CompetitorTracker:
	"""Track and analyze competitor mentions"""
	
	KNOWN_COMPETITORS = [
		'Salesforce', 'HubSpot', 'Outreach', 'SalesLoft', 'Apollo',
		'ZoomInfo', 'LinkedIn Sales Navigator', 'Gong', 'Chorus'
	]
	
	def __init__(self, db_path='sales_angel.db'):
		self.db_path = db_path
		self._init_tables()
		
	def _init_tables(self):
		conn = sqlite3.connect(self.db_path)
		conn.execute("""
			CREATE TABLE IF NOT EXISTS competitor_mentions (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				contact_id INTEGER,
				competitor_name TEXT NOT NULL,
				context TEXT,
				sentiment TEXT,
				source TEXT,
				mentioned_at TEXT NOT NULL
			)
		""")
		conn.commit()
		conn.close()
		
	def scan_for_competitors(self, text, contact_id=None, source='manual'):
		"""Scan text for competitor mentions"""
		
		mentions = []
		text_lower = text.lower()
		
		for competitor in self.KNOWN_COMPETITORS:
			if competitor.lower() in text_lower:
				# Extract context (sentence containing mention)
				sentences = re.split(r'[.!?]+', text)
				context = next((s for s in sentences if competitor.lower() in s.lower()), '')
				
				# Simple sentiment analysis
				sentiment = 'neutral'
				if any(word in context.lower() for word in ['like', 'love', 'great', 'good']):
					sentiment = 'positive'
				elif any(word in context.lower() for word in ['hate', 'bad', 'poor', 'switch']):
					sentiment = 'negative'
					
				mentions.append({
					'competitor': competitor,
					'context': context.strip(),
					'sentiment': sentiment
				})
				
				# Log to database
				self.log_mention(contact_id, competitor, context.strip(), sentiment, source)
				
		return mentions
	
	def log_mention(self, contact_id, competitor, context, sentiment, source):
		"""Log a competitor mention"""
		conn = sqlite3.connect(self.db_path)
		conn.execute("""
			INSERT INTO competitor_mentions 
			(contact_id, competitor_name, context, sentiment, source, mentioned_at)
			VALUES (?, ?, ?, ?, ?, ?)
		""", (contact_id, competitor, context, sentiment, source, 
				datetime.now(timezone.utc).isoformat()))
		conn.commit()
		conn.close()
		
	def get_competitor_landscape(self):
		"""Get overview of competitive landscape"""
		conn = sqlite3.connect(self.db_path)
		
		landscape = {}
		for competitor in self.KNOWN_COMPETITORS:
			mentions = conn.execute("""
				SELECT COUNT(*) as total,
						SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
						SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative
				FROM competitor_mentions
				WHERE competitor_name = ?
			""", (competitor,)).fetchone()
			
			if mentions[0] > 0:
				landscape[competitor] = {
					'total': mentions[0],
					'positive': mentions[1],
					'negative': mentions[2],
					'net_sentiment': mentions[1] - mentions[2]
				}
				
		conn.close()
		return landscape
	
	def get_battlecards(self):
		"""Generate competitive battlecards"""
		
		landscape = self.get_competitor_landscape()
		
		battlecards = {}
		for comp, data in landscape.items():
			if data['total'] >= 3:  # Only if we have enough data
				battlecards[comp] = {
					'threat_level': 'high' if data['total'] > 10 else 'medium',
					'sentiment_trend': 'positive' if data['net_sentiment'] > 0 else 'negative',
					'talking_points': self._generate_talking_points(comp, data)
				}
			
		return battlecards
	
	def _generate_talking_points(self, competitor, data):
		"""Generate competitive talking points"""
		
		# Simplified - could be enhanced with AI
		points = [
			f"Acknowledged leader in space ({data['total']} mentions)",
			f"However, {data['negative']} contacts expressed concerns",
			"Our advantage: AI-powered personalization at scale",
			"Lower cost per meeting, higher ROI"
		]
		
		return points
	
# CLI
if __name__ == "__main__":
	tracker = CompetitorTracker()
	
	print("\n🎯 Competitor Intelligence Dashboard\n")
	
	landscape = tracker.get_competitor_landscape()
	
	if landscape:
		print("Competitive Landscape:")
		for comp, data in sorted(landscape.items(), key=lambda x: x[1]['total'], reverse=True):
			sentiment_icon = "😊" if data['net_sentiment'] > 0 else "😐" if data['net_sentiment'] == 0 else "😞"
			print(f"\n{comp}: {data['total']} mentions {sentiment_icon}")
			print(f"  Positive: {data['positive']} | Negative: {data['negative']}")
	else:
		print("No competitor data yet")
		
	print()
	