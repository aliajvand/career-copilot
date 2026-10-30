class MarketSalaryAgent:
    """
    Agent responsible for:
    - Official salary benchmarks across all Iranian provinces based on Jobvision's 1403/1404 Comprehensive Salary Report (جامعه آماری ۷۴,۰۰۰ نفری جاب‌ویژن)
    - Recommending optimal salary bids based on role, seniority level, and candidate city
    - Tracking high-demand tech skills in the Iranian tech ecosystem
    """
    
    # Official Iranian Tech Salary Benchmarks based on Jobvision 1403/1404 Report (in Million Tomans / میلیون تومان خالص ماهانه)
    SALARY_BENCHMARKS = {
        "data_scientist": {
            "title_fa": "دانشمند داده و یادگیری ماشین (Data Scientist / ML)",
            "junior": {"min": 25, "median": 32, "max": 40},
            "mid": {"min": 42, "median": 55, "max": 70},
            "senior": {"min": 75, "median": 95, "max": 130},
            "hot_skills": ["پایتون", "یادگیری ماشین", "PyTorch", "RAG & FAISS", "پیش‌بینی سری‌های زمانی", "SQL پیشرفته"],
            "demand_index": 98
        },
        "data_analyst": {
            "title_fa": "تحلیل‌گر داده و هوش تجاری (Data & BI Analyst)",
            "junior": {"min": 22, "median": 28, "max": 35},
            "mid": {"min": 35, "median": 45, "max": 58},
            "senior": {"min": 55, "median": 72, "max": 90},
            "hot_skills": ["SQL", "Power BI & DAX", "Python", "مدل‌سازی Star Schema", "طراحی خطوط لوله ETL", "تحلیل کسب‌وکار"],
            "demand_index": 94
        },
        "data_engineer": {
            "title_fa": "مهندس کلان‌داده و پایپ‌لاین (Data Engineer / Big Data)",
            "junior": {"min": 26, "median": 34, "max": 42},
            "mid": {"min": 42, "median": 58, "max": 75},
            "senior": {"min": 75, "median": 100, "max": 135},
            "hot_skills": ["PostgreSQL", "Apache Kafka", "dbt", "Airflow", "ClickHouse", "Spark & PySpark"],
            "demand_index": 96
        },
        "python_developer": {
            "title_fa": "توسعه‌دهنده پایتون و بک‌اند (Python / FastAPI / Django)",
            "junior": {"min": 24, "median": 30, "max": 38},
            "mid": {"min": 38, "median": 50, "max": 65},
            "senior": {"min": 65, "median": 88, "max": 115},
            "hot_skills": ["FastAPI", "PostgreSQL", "Docker", "Redis", "AsyncIO", "میکروسرویس"],
            "demand_index": 95
        },
        "ai_engineer": {
            "title_fa": "مهندس هوش مصنوعی و مدل‌های زبانی (AI & GenAI / Agentic Engineer)",
            "junior": {"min": 28, "median": 38, "max": 48},
            "mid": {"min": 50, "median": 70, "max": 90},
            "senior": {"min": 85, "median": 115, "max": 150},
            "hot_skills": ["LangChain", "Agentic Workflows", "Gemini API", "Vector Databases", "Prompt Engineering", "Fine-Tuning"],
            "demand_index": 99
        },
        "frontend_developer": {
            "title_fa": "توسعه‌دهنده فرانت‌اند (React / Next.js / TypeScript)",
            "junior": {"min": 20, "median": 26, "max": 34},
            "mid": {"min": 34, "median": 45, "max": 58},
            "senior": {"min": 58, "median": 76, "max": 100},
            "hot_skills": ["React", "TypeScript", "Tailwind CSS", "Next.js", "PWA", "State Management"],
            "demand_index": 90
        }
    }

    # Jobvision Provincial Multipliers (ضرایب استانی گزارش حقوق جاب‌ویژن)
    PROVINCE_MULTIPLIERS = {
        "تهران": 1.0,
        "کرج": 0.88,
        "اصفهان": 0.85,
        "مشهد": 0.84,
        "شیراز": 0.83,
        "تبریز": 0.82,
        "اهواز": 0.85,
        "قم": 0.80,
        "سایر استان‌ها": 0.74
    }

    def get_benchmark(self, role_key: str = "data_scientist", level: str = "mid", city: str = "تهران") -> dict:
        role_data = self.SALARY_BENCHMARKS.get(role_key, self.SALARY_BENCHMARKS["data_scientist"])
        salary_info = role_data.get(level, role_data["mid"])

        mult = self.PROVINCE_MULTIPLIERS.get(city, 1.0)
        min_sal = round(salary_info["min"] * mult, 1)
        med_sal = round(salary_info["median"] * mult, 1)
        max_sal = round(salary_info["max"] * mult, 1)
        
        # Recommendation for application bid
        recommended_text = f"{int(med_sal)} الی {int(max_sal)} میلیون تومان (خالص ماهانه)"
        
        return {
            "role_fa": role_data["title_fa"],
            "level": level,
            "city": city,
            "min_salary": min_sal,
            "median_salary": med_sal,
            "max_salary": max_sal,
            "recommended_bid": recommended_text,
            "hot_skills": role_data["hot_skills"],
            "demand_index": role_data["demand_index"],
            "data_source": "گزارش سراسری حقوق و دستمزد جاب‌ویژن سال ۱۴۰۳ (جامعه آماری ۷۴,۰۰۰ نفری متخصصان ایران)"
        }

    def get_all_roles(self) -> list:
        return [
            {"key": k, "title": v["title_fa"], "demand": v["demand_index"]}
            for k, v in self.SALARY_BENCHMARKS.items()
        ]

market_salary_agent = MarketSalaryAgent()
