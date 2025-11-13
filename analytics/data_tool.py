 #!/usr/bin/env python3
"""
SALES ANGEL - DATA INSPECTION & EXPORT TOOL
No UI, just raw data access for analysis and enhancement
"""

import sqlite3
import json
import csv
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = "sales_angel.db"

class SalesAngelDataTool:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    def show_stats(self):
        """Show database statistics"""
        print()
        print("=" * 80)
        print("DATABASE STATISTICS")
        print("=" * 80)

        cursor = self.conn.cursor()

        # Contacts stats
        cursor.execute("SELECT COUNT(*) FROM contacts")
        total_contacts = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(score) FROM contacts")
        avg_score = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM contacts WHERE company IS NOT NULL")
        with_company = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM contacts WHERE email IS NOT NULL")
        with_email = cursor.fetchone()[0]

        print(f"Total Contacts:           {total_contacts}")
        print(f"With Company:             {with_company}")
        print(f"With Email:               {with_email}")
        print(f"Average Score:            {avg_score:.1f}")
        print()

        # Generated content stats
        cursor.execute("SELECT COUNT(*) FROM generated_content")
        total_content = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM generated_content WHERE content_type = 'email'")
        emails = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM generated_content WHERE content_type = 'call'")
        calls = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM generated_content WHERE status = 'pending'")
        pending = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM generated_content WHERE status = 'accepted'")
        accepted = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM generated_content WHERE status = 'rejected'")
        rejected = cursor.fetchone()[0]

        print(f"Total Generated Content:  {total_content}")
        print(f"  - Emails:               {emails}")
        print(f"  - Calls:                {calls}")
        print()
        print(f"Content Status:")
        print(f"  - Pending:              {pending}")
        print(f"  - Accepted:             {accepted}")
        print(f"  - Rejected:             {rejected}")
        print()

        # ML Feedback
        cursor.execute("SELECT COUNT(*) FROM ml_feedback")
        total_feedback = cursor.fetchone()[0]

        if total_feedback > 0:
            cursor.execute("SELECT COUNT(*) FROM ml_feedback WHERE user_action = 'accepted'")
            fb_accepted = cursor.fetchone()[0]
            acceptance_rate = (fb_accepted / total_feedback) * 100
            print(f"ML Feedback Records:      {total_feedback}")
            print(f"  - Acceptance Rate:     {acceptance_rate:.1f}%")
        print()
        print("=" * 80)

    def list_contacts(self, limit=20):
        """List all contacts"""
        print()
        print("=" * 80)
        print(f"CONTACTS (showing {limit}):")
        print("=" * 80)

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, firstname, lastname, company, email, score FROM contacts LIMIT ?", (limit,))

        contacts = cursor.fetchall()

        for c in contacts:
            print(f"[{c['id']:3d}] {c['firstname']:20s} {c['lastname']:20s} | {c['company'][:40]:40s} | Score: {c['score']}")
            print(f"       Email: {c['email']}")

        print()

    def export_contacts_json(self, output_file="contacts_export.json"):
        """Export all contacts to JSON"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM contacts ORDER BY score DESC")

        contacts = [dict(row) for row in cursor.fetchall()]

        with open(output_file, 'w') as f:
            json.dump(contacts, f, indent=2)

        print(f"✅ Exported {len(contacts)} contacts to {output_file}")

    def export_generated_content_json(self, output_file="generated_content.json"):
        """Export all generated content to JSON"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT gc.*, c.firstname, c.lastname, c.company 
            FROM generated_content gc
            JOIN contacts c ON gc.contact_id = c.id
            ORDER BY gc.generated_at DESC
        """)

        content = []
        for row in cursor.fetchall():
            item = dict(row)
            # Parse JSON fields
            if item.get('lines'):
                try:
                    item['lines'] = json.loads(item['lines'])
                except:
                    pass
            if item.get('objections'):
                try:
                    item['objections'] = json.loads(item['objections'])
                except:
                    pass
            content.append(item)

        with open(output_file, 'w') as f:
            json.dump(content, f, indent=2)

        print(f"✅ Exported {len(content)} content pieces to {output_file}")

    def export_to_csv(self, output_file="sales_angel_export.csv"):
        """Export contacts with generated content counts to CSV"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                c.id,
                c.firstname,
                c.lastname,
                c.company,
                c.email,
                c.phone,
                c.score,
                COUNT(CASE WHEN gc.content_type = 'email' THEN 1 END) as email_count,
                COUNT(CASE WHEN gc.content_type = 'call' THEN 1 END) as call_count,
                COUNT(CASE WHEN gc.status = 'accepted' THEN 1 END) as accepted_count,
                COUNT(CASE WHEN gc.status = 'rejected' THEN 1 END) as rejected_count
            FROM contacts c
            LEFT JOIN generated_content gc ON c.id = gc.contact_id
            GROUP BY c.id
            ORDER BY c.score DESC
        """)

        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'ID', 'First Name', 'Last Name', 'Company', 'Email', 'Phone', 'Score',
                'Emails Generated', 'Calls Generated', 'Content Accepted', 'Content Rejected'
            ])

            for row in cursor.fetchall():
                writer.writerow(row)

        print(f"✅ Exported to {output_file}")

    def show_pending_content(self, limit=10):
        """Show pending content waiting for review"""
        print()
        print("=" * 80)
        print(f"PENDING CONTENT (first {limit}):")
        print("=" * 80)

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT gc.id, gc.contact_id, gc.content_type, gc.variant_num, gc.style,
                   c.firstname, c.lastname, gc.generated_at
            FROM generated_content gc
            JOIN contacts c ON gc.contact_id = c.id
            WHERE gc.status = 'pending'
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        if not rows:
            print("✅ No pending content!")
            return

        for row in rows:
            print(f"[{row['id']:4d}] {row['content_type'].upper():5s} (Variant {row['variant_num']}) | {row['style'][:30]:30s}")
            print(f"       {row['firstname']} {row['lastname']} | Generated: {row['generated_at']}")

        print()

    def show_ml_stats(self):
        """Show ML learning statistics"""
        print()
        print("=" * 80)
        print("ML LEARNING STATISTICS:")
        print("=" * 80)

        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT style, COUNT(*) as total, 
                   SUM(CASE WHEN user_action = 'accepted' THEN 1 ELSE 0 END) as accepted
            FROM ml_feedback
            GROUP BY style
            ORDER BY accepted DESC
        """)

        stats = cursor.fetchall()

        if not stats:
            print("No ML feedback yet")
            return

        print("\nPerformance by Style:")
        for s in stats:
            pct = (s['accepted'] / s['total'] * 100) if s['total'] > 0 else 0
            print(f"  {s['style']:35s}: {s['accepted']:3d}/{s['total']:3d} ({pct:5.1f}%)")

        print()

    def export_for_enhancement(self, output_file="sales_angel_data_for_enhancement.json"):
        """Export all data in a structured format for enhancement/analysis"""

        cursor = self.conn.cursor()

        # Get all contacts with their content
        cursor.execute("SELECT * FROM contacts ORDER BY score DESC")
        contacts = cursor.fetchall()

        data = {
            'export_date': datetime.now().isoformat(),
            'contacts': []
        }

        for contact in contacts:
            contact_id = contact['id']

            cursor.execute("""
                SELECT * FROM generated_content 
                WHERE contact_id = ? 
                ORDER BY generated_at
            """, (contact_id,))

            content_items = []
            for content in cursor.fetchall():
                item = dict(content)
                # Parse JSON fields
                if item.get('lines'):
                    try:
                        item['lines'] = json.loads(item['lines'])
                    except:
                        pass
                if item.get('objections'):
                    try:
                        item['objections'] = json.loads(item['objections'])
                    except:
                        pass
                content_items.append(item)

            contact_data = dict(contact)
            contact_data['generated_content'] = content_items
            data['contacts'].append(contact_data)

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Exported all data to {output_file}")
        print(f"   Contacts: {len(data['contacts'])}")
        print(f"   Ready for enhancement/analysis")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Sales Angel Data Tool")
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--contacts', action='store_true', help='List contacts')
    parser.add_argument('--pending', action='store_true', help='Show pending content')
    parser.add_argument('--ml-stats', action='store_true', help='Show ML statistics')
    parser.add_argument('--export-json', action='store_true', help='Export all to JSON')
    parser.add_argument('--export-csv', action='store_true', help='Export to CSV')
    parser.add_argument('--export-enhancement', action='store_true', help='Export for enhancement')
    parser.add_argument('--all', action='store_true', help='Show everything')

    args = parser.parse_args()

    tool = SalesAngelDataTool()

    try:
        if args.all:
            tool.show_stats()
            tool.list_contacts(limit=10)
            tool.show_pending_content()
            tool.show_ml_stats()
            tool.export_json("contacts.json")
            tool.export_to_csv("data.csv")
        else:
            if args.stats or not any(vars(args).values()):
                tool.show_stats()
            if args.contacts:
                tool.list_contacts()
            if args.pending:
                tool.show_pending_content()
            if args.ml_stats:
                tool.show_ml_stats()
            if args.export_json:
                tool.export_contacts_json()
                tool.export_generated_content_json()
            if args.export_csv:
                tool.export_to_csv()
            if args.export_enhancement:
                tool.export_for_enhancement()

    finally:
        tool.close()


if __name__ == "__main__":
    main()
