import json
import hashlib
from pathlib import Path
from core.db import get_connection

def load_jobs():
    path = Path("data/tehran_tech_jobs_30days.json")
    if not path.exists():
        print("Dataset not found!")
        return

    items = json.loads(path.read_text(encoding="utf-8"))
    conn = get_connection()
    cursor = conn.cursor()

    inserted = 0
    for item in items:
        hash_input = f"{item['platform']}_{item['title']}_{item['company']}".encode('utf-8')
        job_id = hashlib.sha256(hash_input).hexdigest()[:12]

        cursor.execute("SELECT id FROM jobs WHERE job_id = ?", (job_id,))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO jobs (
                job_id, platform, title, company, location, salary_range, 
                url, description, skills_required, status, created_at, is_deleted
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'discovered', ?, 0)
            """, (
                job_id, item["platform"], item["title"], item["company"],
                item["location"], item["salary_range"], item["url"],
                item["description"], json.dumps(item["skills_required"], ensure_ascii=False),
                item.get("posted_at")
            ))
            inserted += 1

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE is_deleted = 0")
    total = cursor.fetchone()[0]
    conn.close()
    print(f"Inserted {inserted} jobs. Total active in DB: {total}")

if __name__ == "__main__":
    load_jobs()
