import sys
import json
import requests
import sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

def fetch_real_jobvision_jobs(keyword="تحلیل داده", max_count=30):
    url = "https://candidateapi.jobvision.ir/api/v1/JobPost/List"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json'
    }
    payload = {
        "keyword": keyword,
        "page": 1,
        "pageSize": max_count,
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"API returned status {r.status_code}")
            return []
        data = r.json()
        job_posts = data.get("data", {}).get("jobPosts", [])
        return job_posts
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return []

def sync_real_jobs_to_db():
    conn = sqlite3.connect('data/career_copilot.db')
    c = conn.cursor()
    
    keywords = ["تحلیل داده", "هوش تجاری", "Data Analyst", "پایتون"]
    all_jobs = []
    seen_ids = set()

    for kw in keywords:
        posts = fetch_real_jobvision_jobs(kw, max_count=20)
        for p in posts:
            jid = str(p.get("id"))
            if jid not in seen_ids:
                seen_ids.add(jid)
                all_jobs.append(p)

    print(f"Total unique real jobs fetched: {len(all_jobs)}")

    # Add real jobs into SQLite
    inserted = 0
    for p in all_jobs:
        job_id = f"jv-{p.get('id')}"
        title = p.get("title", "")
        company = p.get("company", {}).get("nameFa", "") or p.get("company", {}).get("nameEn", "شرکت نامشخص")
        city = p.get("location", {}).get("city", {}).get("titleFa", "تهران")
        url = f"https://jobvision.ir/jobs/{p.get('id')}"
        work_type = p.get("workType", {}).get("titleFa", "تمام وقت")
        category = ""
        cats = p.get("jobCategories", [])
        if cats:
            category = cats[0].get("titleFa", "")

        # Calculate a realistic match score based on title
        title_lower = title.lower()
        score = 85
        if "ارشد" in title or "senior" in title_lower:
            score = 92
        elif "داده" in title or "data" in title_lower:
            score = 95
        elif "هوش تجاری" in title or "bi" in title_lower:
            score = 94

        c.execute("""
        INSERT INTO jobs (job_id, title, company, platform, match_score, status, url, created_at)
        VALUES (?, ?, ?, 'jobvision', ?, 'new', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(job_id) DO UPDATE SET
            title = excluded.title,
            company = excluded.company,
            url = excluded.url,
            match_score = excluded.match_score
        """, (job_id, title, company, score, url))
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Successfully synced {inserted} real Jobvision jobs into database!")

if __name__ == "__main__":
    sync_real_jobs_to_db()
