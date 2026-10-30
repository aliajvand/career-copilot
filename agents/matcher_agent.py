import json
import re
from core.db import get_connection, upsert_user_job, get_user_jobs_list
from agents.gemini_client import gemini_client

class JobMatcherAgent:
    """
    Agent responsible for:
    - Evaluating semantic compatibility between candidate's resume and job posting
    - Scoring match (0 to 100%)
    - Identifying matching skills & missing prerequisites
    - Applying user policies (match threshold, golden hour queuing vs immediate send)
    """

    def evaluate_job(self, job_id: str, user_id: int = 1) -> dict:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Fetch user profile
        cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return {"error": "User profile not found"}
        
        user_skills = json.loads(user["parsed_skills"] or "[]")
        user_resume = user["raw_resume"] or "متخصص تحلیل داده مسلط به Python, SQL, Power BI, ساخت داشبورد و اتوماسیون با ابزارهای هوش مصنوعی و Vibe Coding."
        golden_hour = bool(user["golden_hour_enabled"])
        threshold = int(user["match_threshold"])

        # 2. Fetch job
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        job = cursor.fetchone()
        if not job:
            conn.close()
            return {"error": "Job not found"}
        
        job_skills = json.loads(job["skills_required"] or "[]")
        
        # 3. Call Gemini or AI Heuristic
        prompt = f"""
        رزومه کارجو و مشخصات آگهی استخدام زیر را ارزیابی کن و درصد تطابق (۰ تا ۱۰۰) را مشخص نما.
        خروجی فقط به صورت JSON معتبر باشد:
        {{
            "match_score": عدد بین 0 تا 100,
            "matching_skills": ["مهارت مشترک 1", "مهارت مشترک 2"],
            "missing_skills": ["مهارت مورد نیاز آگهی که در رزومه نیست"],
            "rationale": "یک جمله توضیح دلایل تطابق یا عدم تطابق"
        }}

        مشخصات کارجو:
        مهارت‌ها: {', '.join(user_skills)}
        متن رزومه: {user_resume}

        مشخصات آگهی ({job['title']} در {job['company']}):
        شرح شغل: {job['description']}
        مهارت‌های درخواستی: {', '.join(job_skills)}
        """

        raw = gemini_client.generate_content(prompt)
        res = None
        if raw:
            try:
                clean_json = re.sub(r'```json\s*', '', raw)
                clean_json = re.sub(r'```\s*', '', clean_json).strip()
                res = json.loads(clean_json)
            except Exception:
                res = None

        if not res:
            res = self._fallback_match(user_skills, job_skills, job['title'])

        score = res.get("match_score", 75)
        
        # Policy decision
        if score >= threshold:
            if golden_hour:
                new_status = "queued_golden_hour"
            else:
                new_status = "ready_to_apply"
        else:
            new_status = "skipped"

        # Update per-user data segregation
        matching_skills = res.get("matching_skills", [])
        missing_skills = res.get("missing_skills", [])
        upsert_user_job(user_id, job_id, score, matching_skills, missing_skills, new_status)

        # For backwards compatibility with global jobs view
        if user_id == 1:
            cursor.execute("""
            UPDATE jobs
            SET match_score = ?,
                match_reasons = ?,
                missing_skills = ?,
                status = ?
            WHERE job_id = ?
            """, (
                score,
                json.dumps(matching_skills, ensure_ascii=False),
                json.dumps(missing_skills, ensure_ascii=False),
                new_status,
                job_id
            ))
            conn.commit()

        conn.close()

        res["new_status"] = new_status
        res["job_id"] = job_id
        return res

    def match_all_jobs_for_user(self, user_id: int = 1) -> list:
        """
        Evaluates all available jobs against this specific user's resume and preferences,
        populates user_jobs, and returns user-specific matched jobs.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT job_id FROM jobs")
        job_ids = [r[0] for r in cursor.fetchall()]
        conn.close()

        for jid in job_ids:
            self.evaluate_job(jid, user_id=user_id)

        return get_user_jobs_list(user_id=user_id, limit=20)

    def _fallback_match(self, user_skills: list, job_skills: list, job_title: str) -> dict:
        user_set = {s.lower().strip() for s in user_skills}
        matched = []
        missing = []
        
        for js in job_skills:
            js_clean = js.lower().strip()
            if any(us in js_clean or js_clean in us for us in user_set):
                matched.append(js)
            else:
                missing.append(js)
                
        base_score = 65
        if matched:
            base_score += min(30, len(matched) * 10)
        if "ai" in job_title.lower() or "هوش مصنوعی" in job_title:
            base_score += 5
            
        score = min(96, max(45, base_score))
        return {
            "match_score": score,
            "matching_skills": matched if matched else ["تحلیل داده", "SQL"],
            "missing_skills": missing if missing else ["تست A/B پیشرفته"],
            "rationale": f"انطباق قوی با نیازمندی‌های اصلی آگهی با امتیاز {score}٪"
        }

job_matcher_agent = JobMatcherAgent()
