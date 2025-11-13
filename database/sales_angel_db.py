#!/usr/bin/env python3
"""
SALES ANGEL - DATABASE INTEGRATION LAYER
Manages all database operations, schemas, and content storage
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class SalesAngelDB:
    """Main database interface for Sales Angel"""
    
    def __init__(self, db_path: str = "sales_angel.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Contacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY,
                firstname TEXT,
                lastname TEXT,
                email TEXT UNIQUE,
                phone TEXT,
                company TEXT,
                jobtitle TEXT,
                mbti TEXT,
                disc TEXT,
                score REAL,
                hubspot_id TEXT,
                enriched_profile TEXT,
                enriched_at TIMESTAMP,
                enrichment_cost REAL,
                lifecycle_stage TEXT,
                source TEXT DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Generated content table (emails + calls)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_content (
                id INTEGER PRIMARY KEY,
                contact_id INTEGER NOT NULL,
                content_type TEXT NOT NULL,
                variant_num INTEGER,
                style TEXT,
                subject TEXT,
                body TEXT,
                lines TEXT,
                cta TEXT,
                objections TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                feedback_score INTEGER,
                user_rating INTEGER,
                user_notes TEXT,
                accepted_at TIMESTAMP,
                rejected_at TIMESTAMP,
                FOREIGN KEY(contact_id) REFERENCES contacts(id)
            )
        """)
        
        # ML Training data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_feedback (
                id INTEGER PRIMARY KEY,
                content_id INTEGER NOT NULL,
                contact_id INTEGER NOT NULL,
                user_action TEXT NOT NULL,
                reasoning TEXT,
                variant_num INTEGER,
                style TEXT,
                key_factors TEXT,
                feedback_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(content_id) REFERENCES generated_content(id),
                FOREIGN KEY(contact_id) REFERENCES contacts(id)
            )
        """)
        
        # Model metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_metrics (
                id INTEGER PRIMARY KEY,
                metric_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_generated INTEGER,
                total_accepted INTEGER,
                total_rejected INTEGER,
                acceptance_rate REAL,
                avg_feedback_score REAL,
                model_accuracy REAL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_contact(self, contact_data: Dict[str, Any]) -> int:
        """Add contact to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO contacts 
                (firstname, lastname, email, phone, company, jobtitle, mbti, disc, score, 
                 hubspot_id, lifecycle_stage, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contact_data.get('firstname'),
                contact_data.get('lastname'),
                contact_data.get('email'),
                contact_data.get('phone'),
                contact_data.get('company'),
                contact_data.get('jobtitle'),
                contact_data.get('mbti'),
                contact_data.get('disc'),
                contact_data.get('score', 0),
                contact_data.get('hubspot_id'),
                contact_data.get('lifecycle_stage'),
                contact_data.get('source', 'manual')
            ))
            
            conn.commit()
            contact_id = cursor.lastrowid
            conn.close()
            return contact_id
        except sqlite3.IntegrityError:
            # Email already exists
            conn.close()
            return None
    
    def get_contact_by_email(self, email: str) -> Optional[Dict]:
        """Get contact by email address"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, firstname, lastname, email, company, jobtitle
            FROM contacts
            WHERE email = ?
        """, (email,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'firstname': result[1],
                'lastname': result[2],
                'email': result[3],
                'company': result[4],
                'jobtitle': result[5]
            }
        return None
    
    def get_contact_by_id(self, contact_id: int) -> Optional[Dict]:
        """Get contact by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, firstname, lastname, email, company, jobtitle, enriched_profile
            FROM contacts
            WHERE id = ?
        """, (contact_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'firstname': result[1],
                'lastname': result[2],
                'email': result[3],
                'company': result[4],
                'jobtitle': result[5],
                'enriched_profile': result[6]
            }
        return None
    
    def save_generated_content(self, contact_id: int, content_type: str, content_data: Dict[str, Any]) -> int:
        """Save generated email or call content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO generated_content
            (contact_id, content_type, variant_num, style, subject, body, lines, cta, objections, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contact_id,
            content_type,
            content_data.get('variant_num'),
            content_data.get('style'),
            content_data.get('subject'),
            content_data.get('body'),
            json.dumps(content_data.get('lines', [])),
            content_data.get('cta'),
            json.dumps(content_data.get('objections', {}))
        ))
        
        conn.commit()
        content_id = cursor.lastrowid
        conn.close()
        return content_id
    
    def record_user_feedback(self, content_id: int, contact_id: int, action: str, reasoning: str = "", variant_num: int = None, style: str = None):
        """Record user's accept/reject decision"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update content status
        column_name = "accepted_at" if action.lower() == "accepted" else "rejected_at"
        cursor.execute(f"""
            UPDATE generated_content
            SET status = ?, {column_name} = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (action.lower(), content_id))
        
        # Record in ML training data
        cursor.execute("""
            INSERT INTO ml_feedback (content_id, contact_id, user_action, reasoning, variant_num, style)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (content_id, contact_id, action, reasoning, variant_num, style))
        
        conn.commit()
        conn.close()
    
    def get_content_quality_score(self, style: str) -> float:
        """Calculate quality score for a style based on user feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN user_action = 'accepted' THEN 1 ELSE 0 END) as accepted
            FROM ml_feedback
            WHERE style = ?
        """, (style,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result[0] == 0:
            return 0.5  # Neutral for untested styles
        return result[1] / result[0] if result[1] else 0
    
    def get_ml_features(self) -> Dict[str, Any]:
        """Get aggregate ML features from user feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall acceptance rate
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN user_action = 'accepted' THEN 1 ELSE 0 END) as accepted
            FROM ml_feedback
        """)
        
        total, accepted = cursor.fetchone()
        
        # Acceptance by style
        cursor.execute("""
            SELECT style,
                   COUNT(*) as count,
                   SUM(CASE WHEN user_action = 'accepted' THEN 1 ELSE 0 END) as accepted
            FROM ml_feedback
            GROUP BY style
        """)
        
        style_stats = cursor.fetchall()
        
        # Acceptance by variant number
        cursor.execute("""
            SELECT variant_num,
                   COUNT(*) as count,
                   SUM(CASE WHEN user_action = 'accepted' THEN 1 ELSE 0 END) as accepted
            FROM ml_feedback
            GROUP BY variant_num
        """)
        
        variant_stats = cursor.fetchall()
        conn.close()
        
        return {
            'total_feedback': total or 0,
            'total_accepted': accepted or 0,
            'acceptance_rate': (accepted / total if total else 0),
            'by_style': {style: {'count': count, 'accepted': acc} for style, count, acc in style_stats},
            'by_variant': {var: {'count': count, 'accepted': acc} for var, count, acc in variant_stats}
        }
    
    def get_pending_content(self, contact_id: int = None) -> List[Dict]:
        """Get pending content for review"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if contact_id:
            cursor.execute("""
                SELECT * FROM generated_content
                WHERE status = 'pending' AND contact_id = ?
                ORDER BY generated_at DESC
            """, (contact_id,))
        else:
            cursor.execute("""
                SELECT * FROM generated_content
                WHERE status = 'pending'
                ORDER BY generated_at DESC
            """)
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def get_all_contacts(self, limit: int = None) -> List[Dict]:
        """Get all contacts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if limit:
            cursor.execute("""
                SELECT id, firstname, lastname, email, company, jobtitle
                FROM contacts
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        else:
            cursor.execute("""
                SELECT id, firstname, lastname, email, company, jobtitle
                FROM contacts
                ORDER BY created_at DESC
            """)
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': r[0],
                'firstname': r[1],
                'lastname': r[2],
                'email': r[3],
                'company': r[4],
                'jobtitle': r[5]
            }
            for r in results
        ]


if __name__ == "__main__":
    db = SalesAngelDB()
    print("✅ Database initialized: sales_angel.db")
