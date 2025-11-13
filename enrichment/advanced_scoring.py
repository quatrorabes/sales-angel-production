#!/usr/bin/env python3
"""
ADVANCED SCORING SYSTEM
Dynamic contact scoring based on:
- Base score (database)
- Enrichment depth
- Decision maker status
- ML feedback history
- Recency
"""

import sqlite3
import json
from datetime import datetime, timedelta

class AdvancedScoring:

    def __init__(self, db_path="sales_angel.db"):
        self.db_path = db_path

    def calculate_score(self, contact_id):
        """
        Calculate comprehensive contact score (0-100)

        Components:
        - Base Score: 40 pts (from import)
        - Enrichment: 20 pts (industry, size, events, decision maker)
        - ML Feedback: 25 pts (acceptance history)
        - Recency: 10 pts (recent activity boost)
        - Engagement: 5 pts (interactions)
        """

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get contact
        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        contact = cursor.fetchone()

        if not contact:
            return 0

        score = 0

        # 1. BASE SCORE (40 pts)
        base = min(contact['score'] or 60, 100)
        score += (base / 100) * 40

        # 2. ENRICHMENT (20 pts)
        if contact['enrichment_data']:
            enrich = json.loads(contact['enrichment_data'])
            enrich_score = 10  # Base 10 for being enriched

            if enrich.get('decision_maker'):
                enrich_score += 5
            if enrich.get('recent_events'):
                enrich_score += 3
            if enrich.get('company_size'):
                enrich_score += 2

            score += enrich_score

        # 3. ML FEEDBACK (25 pts)
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN user_action='accepted' THEN 1 ELSE 0 END) as accepted
            FROM ml_feedback
            WHERE contact_id = ?
        """, (contact_id,))

        fb = cursor.fetchone()
        if fb['total'] and fb['total'] > 0:
            acceptance_rate = (fb['accepted'] / fb['total'])
            score += acceptance_rate * 25

        # 4. RECENCY (10 pts)
        if contact['enriched_at']:
            enriched_date = datetime.fromisoformat(contact['enriched_at'])
            days_old = (datetime.now() - enriched_date).days

            if days_old < 7:
                score += 10
            elif days_old < 30:
                score += 5

        conn.close()

        return min(score, 100)

    def batch_update_scores(self):
        """Update all contact scores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM contacts")

        for row in cursor.fetchall():
            contact_id = row[0]
            new_score = self.calculate_score(contact_id)

            cursor.execute("""
                UPDATE contacts SET score = ? WHERE id = ?
            """, (new_score, contact_id))

        conn.commit()
        conn.close()

    def get_top_contacts(self, limit=50):
        """Get top scored contacts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate all scores inline
        cursor.execute("""
            SELECT id, firstname, lastname, company, score, enrichment_data
            FROM contacts
            ORDER BY score DESC
            LIMIT ?
        """, (limit,))

        results = cursor.fetchall()
        conn.close()

        return results

if __name__ == "__main__":
    scorer = AdvancedScoring()
    print("Updating scores for all contacts...")
    scorer.batch_update_scores()
    print("✅ Scores updated")
