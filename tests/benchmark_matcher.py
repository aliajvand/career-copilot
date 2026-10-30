"""
Precision@K Benchmark Suite for Job Matcher Engine.
Built with skills: llm-eval + data-science-ml
Evaluates 20 labeled resume/job pairs to measure Precision@K before and after semantic vector re-ranking.
"""

import sys
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
sys.path.append(str(Path(__file__).resolve().parent.parent))

from typing import List, Dict, Any
from agents.matcher_agent import job_matcher_agent, SemanticVectorIndex

# 20 Manually Labeled Resume/Job Evaluation Pairs
LABELED_PAIRS = [
    # Candidate: Ali Ajvand (Data Scientist, BI, Python, SQL, Power BI)
    {"id": 1, "title": "Data Analyst (Power BI)", "skills": ["SQL", "Power BI", "Python"], "label": 1},
    {"id": 2, "title": "BI Developer", "skills": ["SQL Server", "Power BI", "ETL"], "label": 1},
    {"id": 3, "title": "AI Agent Developer", "skills": ["Python", "FastAPI", "LLM", "RAG"], "label": 1},
    {"id": 4, "title": "Senior Data Scientist", "skills": ["Machine Learning", "Python", "Pandas"], "label": 1},
    {"id": 5, "title": "Database Administrator", "skills": ["PostgreSQL", "SQL", "Backup"], "label": 1},
    {"id": 6, "title": "Growth Data Analyst", "skills": ["Google Analytics", "SQL", "Excel"], "label": 1},
    {"id": 7, "title": "Business Analyst", "skills": ["Power BI", "Excel", "KPI Analysis"], "label": 1},
    {"id": 8, "title": "Data Engineer", "skills": ["Python", "ETL", "Spark", "SQL"], "label": 1},
    {"id": 9, "title": "Flutter Mobile Developer", "skills": ["Dart", "Flutter", "Bloc"], "label": 0},
    {"id": 10, "title": "Civil Engineer", "skills": ["AutoCAD", "ETABS"], "label": 0},
    {"id": 11, "title": "Graphic Designer", "skills": ["Photoshop", "Illustrator"], "label": 0},
    {"id": 12, "title": "Frontend React Developer", "skills": ["React", "JavaScript", "CSS"], "label": 0},
    {"id": 13, "title": "Legal Advisor", "skills": ["Contract Law", "Compliance"], "label": 0},
    {"id": 14, "title": "Accountant", "skills": ["Accounting", "Tax", "Sepidar"], "label": 0},
    {"id": 15, "title": "Content Specialist", "skills": ["Copywriting", "SEO", "WordPress"], "label": 0},
    {"id": 16, "title": "Office Manager", "skills": ["Secretarial", "Office Suite"], "label": 0},
    {"id": 17, "title": "Mechanical Engineer", "skills": ["SolidWorks", "HVAC"], "label": 0},
    {"id": 18, "title": "Sales Representative", "skills": ["Cold Calling", "Negotiation"], "label": 0},
    {"id": 19, "title": "Risk & Fraud Data Analyst", "skills": ["SQL", "Python", "Fraud Detection"], "label": 1},
    {"id": 20, "title": "Chef / Cook", "skills": ["Culinary", "Food Safety"], "label": 0}
]

def run_benchmark(k: int = 5) -> Dict[str, Any]:
    candidate_skills = ["Python", "SQL", "Power BI", "Data Analysis", "Machine Learning", "FastAPI", "RAG"]

    # 1. Baseline: Pure Keyword Overlap
    def naive_score(pair):
        overlap = len(set(s.lower() for s in candidate_skills) & set(s.lower() for s in pair["skills"]))
        return overlap

    baseline_ranked = sorted(LABELED_PAIRS, key=naive_score, reverse=True)
    baseline_top_k = baseline_ranked[:k]
    baseline_relevant = sum(1 for item in baseline_top_k if item["label"] == 1)
    precision_baseline = baseline_relevant / k

    # 2. Upgraded: Semantic Vector & Title Re-ranking
    def upgraded_score(pair):
        score, _, _ = job_matcher_agent._compute_semantic_score(
            user_skills=candidate_skills,
            user_resume="Data Scientist with deep expertise in Python, SQL, Power BI, and Machine Learning.",
            job_skills=pair["skills"],
            job_title=pair["title"],
            job_description=f"Hiring for {pair['title']} requiring {', '.join(pair['skills'])}"
        )
        return score

    upgraded_ranked = sorted(LABELED_PAIRS, key=upgraded_score, reverse=True)
    upgraded_top_k = upgraded_ranked[:k]
    upgraded_relevant = sum(1 for item in upgraded_top_k if item["label"] == 1)
    precision_upgraded = upgraded_relevant / k

    return {
        "k": k,
        "total_pairs": len(LABELED_PAIRS),
        "precision_baseline": precision_baseline,
        "precision_upgraded": precision_upgraded,
        "improvement_pct": ((precision_upgraded - precision_baseline) / max(0.01, precision_baseline)) * 100
    }

if __name__ == "__main__":
    res = run_benchmark(k=5)
    print("=" * 60)
    print("🎯 Matcher Precision@K Benchmark Results:")
    print(f"Total Test Pairs: {res['total_pairs']}")
    print(f"Baseline Precision@{res['k']}: {res['precision_baseline'] * 100:.1f}%")
    print(f"Upgraded Precision@{res['k']}: {res['precision_upgraded'] * 100:.1f}%")
    print(f"Relative Improvement: +{res['improvement_pct']:.1f}%")
    print("=" * 60)
