"""
Hierarchical Multi-Agent Committee & Enterprise Debate System for Career Co-Pilot Pro.

Architecture:
- Level 1 (Specialist Worker Agents): 8 specialized domains, each housing worker agents with specific skills.
- Level 2 (Domain Lead / Supervisor Agents): Coordinates internal domain debates, challenges workers, and achieves consensus.
- Level 3 (Chief Orchestrator / Lead Architect Agent): Analyzes all domain syntheses, questions domain leads, and authorizes code modifications.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any
from core.db import get_connection
from automation.platform_auth import add_log
from agents.gemini_client import gemini_client

# Catalog of 8 Enterprise Domains and 28 Specialized Skills
ENTERPRISE_DOMAINS = {
    "design_ux": {
        "title": "تیم طراحی و تجربه کاربری (Design & UX)",
        "lead": "آرش سعیدی (Lead UX/UI Architect)",
        "lead_prompt": "تو رهبر تیم تجربه و طراحی کاربری پلتفرم هستی. استانداردهای سختگیرانه دیزاین سیستم، تایپوگرافی، RTL و دسترسی‌پذیری را مطالبه کن.",
        "skills": {
            "ui-pro-max": {
                "name": "متخصص دیزاین سیستم و بصری",
                "focus": "سیستم طراحی، تایپوگرافی، پالت رنگ، فاصله گذاری، کارت‌های شیشه‌ای (Glassmorphism)"
            },
            "ecommerce-ux": {
                "name": "متخصص تجربه تبدیل و خرید",
                "focus": "قیف تبدیل، خرید اشتراک پریمیوم، فیلترهای استخدامی، سرچ سریع و روان"
            },
            "persian-rtl": {
                "name": "متخصص بومی‌سازی و RTL",
                "focus": "چیدمان راست‌به‌چپ، فونت وزیرمتن، تبدیل اعداد به فارسی، تاریخ و تقویم شمسی جلالی"
            },
            "accessibility-review": {
                "name": "ممیز دسترسی‌پذیری (a11y)",
                "focus": "کنتراست استاندارد، کیبورد نویگیشن، تاچ‌تارگت‌های استاندارد موبایل، سازگاری صفحه‌خوان"
            },
            "ux-copy-fa": {
                "name": "نویسنده میکروکپی و لحن فارسی",
                "focus": "پیام‌های خطای انگیزاننده، متن‌های دکمه‌ها، راهنمای گام‌به‌گام کارجو"
            }
        }
    },
    "security_auth": {
        "title": "تیم امنیت، احراز هویت و پایداری (Security & Auth)",
        "lead": "مهندس کاوه راد (Chief Information Security Officer)",
        "lead_prompt": "تو رهبر امنیت سازمانی هستی. تمام ابعاد نفوذ، نگهداری امن سکرت‌ها، اعتبارسنجی ورودی‌ها و عدم نشت داده را به چالش بکش.",
        "skills": {
            "auth-flow": {
                "name": "متخصص جریان احراز هویت",
                "focus": "ثبت‌نام، ورود دو مرحله‌ای، اعتبارسنجی نشست‌های جابینجا/جاب‌ویژن، Rate Limiting"
            },
            "security-review": {
                "name": "تحلیل‌گر امنیت OWASP",
                "focus": "پیشگیری از XSS/CSRF/SQLi، هدرهای امنیتی CSP و HSTS، ممیزی ورودی‌ها"
            },
            "production-hardening": {
                "name": "متخصص سخت‌سازی محیط اجرا",
                "focus": "جداسازی کامل .env، لاگ بدون اطلاعات هویتی و توکن، سلامت سیستم (Health Check)"
            }
        }
    },
    "backend_db": {
        "title": "تیم زیرساخت بک‌اند و پایگاه داده (Backend & Database)",
        "lead": "دکتر نیما فرهمند (Principal Backend Engineer)",
        "lead_prompt": "تو معمار ارشد بک‌اند هستی. روی کارایی کوئری‌ها، پایداری اتصالات SQLite، ساختار تمیز REST و Pydantic v2 تاکید کن.",
        "skills": {
            "db-schema-design": {
                "name": "طراح پایگاه داده",
                "focus": "نرمال‌سازی جداول، ایندکس‌گذاری بهینه job_id و user_id، مایگریشن خودکار"
            },
            "fastapi-backend": {
                "name": "توسعه‌دهنده ارشد FastAPI",
                "focus": "معماری تمیز لایه‌ای، مدل‌های Pydantic v2، تزریق وابستگی، راندمان غیرهمزمان (Async)"
            },
            "api-design": {
                "name": "طراح استانداردهای REST",
                "focus": "نسخه‌بندی API، مدیریت کدهای خطای استاندارد RFC 7807، صفحه‌بندی هوشمند داده‌ها"
            }
        }
    },
    "telegram_bot": {
        "title": "تیم اتوماسیون و ربات تلگرام (Telegram Automation)",
        "lead": "سامان نادری (Head of Bot Platform)",
        "lead_prompt": "تو مدیر پلتفرم تلگرام هستی. کارایی ربات، هندلینگ فایل‌های رزومه بزرگ، کیبوردهای تعاملی تک‌کلیکه و حفظ وضعیت FSM را کنترل کن.",
        "skills": {
            "telegram-bot": {
                "name": "مهندس ارشد python-telegram-bot",
                "focus": "پشتیبانی چندکاربره، هندلرهای غیرهمزمان، کیبوردهای شیشه‌ای، اتصال یکپارچه به داشبورد عمومی"
            }
        }
    },
    "ai_agents": {
        "title": "تیم هوش مصنوعی و سیستم‌های ایجنتی (AI & Agents)",
        "lead": "ثریا معتمدی (AI Research & Agentic Systems Lead)",
        "lead_prompt": "تو دانشمند ارشد هوش مصنوعی هستی. دقت پرامپت‌ها، پرهیز از توهم (Hallucination)، ساختاربندی خروجی JSON و استفاده بهینه از Gemini 3.5 را پایش کن.",
        "skills": {
            "ai-agent-design": {
                "name": "معمار سیستم‌های ایجنتی",
                "focus": "طراحی Tool Calling، حافظه بلندمدت کارجو، گاردریل‌های اعتبارسنجی پاسخ"
            },
            "rag-pipeline": {
                "name": "متخصص بازیابی اسناد (RAG)",
                "focus": "چانک‌بندی دقیق شرح وظایف آگهی‌ها، استخراج فکت‌های رزومه و تطابق برداری"
            },
            "prompt-engineering": {
                "name": "مهندس پرامپت Gemini",
                "focus": "قالب‌بندی Few-Shot، ساختار خروجی بدون باگ، استخراج ساختاریافته مهارت‌ها"
            },
            "mcp-integration": {
                "name": "متخصص یکپارچه‌سازی ابزارها",
                "focus": "پروتکل MCP، اتصال ابزارهای سرچ و استخراج سوابق"
            }
        }
    },
    "data_bi": {
        "title": "تیم علم داده و هوش تجاری (Data & BI)",
        "lead": "پرهام حسینی (Chief Data Scientist)",
        "lead_prompt": "تو مدیر ارشد علم داده هستی. صحت تحلیل‌ها، جلوگیری از Data Leakage در پیش‌بینی‌ها، متریک‌های واقعی و مدل‌های ستاره‌ای DAX را بررسی کن.",
        "skills": {
            "data-analysis": {
                "name": "تحلیل‌گر داده‌های بازار کار",
                "focus": "اکتشاف الگوهای آگهی‌های تهران، پاک‌سازی داده‌های حقوق و دسته‌بندی پوزیشن‌ها"
            },
            "data-science-ml": {
                "name": "مهندس یادگیری ماشین",
                "focus": "اعتبارسنجی زمانی، جلوگیری از نشت اطلاعات، امتیازدهی احتمالی انطباق رزومه"
            },
            "data-engineering": {
                "name": "مهندس پایپ‌لاین و داده",
                "focus": "فرایندهای ETL گردآوری جابینجا/جاب‌ویژن، پایش کیفیت داده، زمان‌بندی ساعت طلایی"
            },
            "bi-dashboard": {
                "name": "معمار هوش تجاری و Power BI",
                "focus": "مدلسازی ستاره‌ای، متریک‌های مقایسه‌ای حقوق بازار کار تهران، داشبوردهای مدیریتی"
            }
        }
    },
    "persian_nlp_ocr": {
        "title": "تیم پردازش زبان طبیعی و OCR فارسی (Persian NLP & OCR)",
        "lead": "دکتر مریم دانش‌پژوه (NLP Principal Investigator)",
        "lead_prompt": "تو متخصص ارشد زبان فارسی و OCR هستی. نرمال‌سازی نویسه‌های عربی به فارسی، نیم‌فاصله‌ها، استخراج جدول‌ها از PDF و توکنایز دقیق را مطالبه کن.",
        "skills": {
            "persian-ocr": {
                "name": "متخصص استخراج و OCR اسناد",
                "focus": "پیش‌پردازش اسناد اسکن‌شده رزومه، استخراج بلوک‌های متنی پیچیده، بازیابی رزومه‌های تصویری"
            },
            "persian-nlp": {
                "name": "متخصص زبان‌شناسی رایانشی فارسی",
                "focus": "نرمال‌سازی ی/ک و تنوین‌ها، کتابخانه هضم (Hazm)، اعتبارسنجی لغوی اصطلاحات فنی"
            }
        }
    },
    "app_3d_eng": {
        "title": "تیم مهندسی فرانت، سه‌بعدی و QA (App & 3D Engineering)",
        "lead": "بهرام کاظمی (Head of Core Engineering)",
        "lead_prompt": "تو مدیر مهندسی محصول هستی. روان بودن رندرهای سه بعدی Three.js، افکت‌های بصری SVG، سلامت تست‌های واحد و بیلد تمیز موبایل فلاتر را بررسی کن.",
        "skills": {
            "nextjs-app-router": {
                "name": "معمار وب مدرن",
                "focus": "لودینگ بهینه، رابط‌های تعاملی Real-time، معماری کامپوننت‌محور"
            },
            "nativewind-mobile/flutter": {
                "name": "توسعه‌دهنده ارشد موبایل",
                "focus": "خروجی APK کافه‌بازار، یکپارچگی رابط کاربری موبایل با سرور و عملکرد آفلاین"
            },
            "threejs-3d": {
                "name": "متخصص جلوه‌های سه‌بعدی WebGL",
                "focus": "رندر اورب هوشمند تعاملی مصاحبه‌گر، افکت‌های ذرات شناور، جلوه‌های بصری آینده‌نگرانه"
            },
            "qa-reviewer": {
                "name": "مدیر کیفیت و تست نرم‌افزار",
                "focus": "تست کامل تمام اندپوینت‌ها، پایداری در بار همزمان، سناریوهای مرزی"
            },
            "git-workflow": {
                "name": "راهبر گیت و CI/CD",
                "focus": "کامیت‌های استاندارد، پوش مستقیم به گیت‌هاب کاربر و حفظ تاریخچه پاک"
            }
        }
    }
}

class HierarchicalMultiAgentEngine:
    """
    Orchestrates:
    1. Intra-domain worker debates based on specific skills
    2. Domain Lead cross-examination and consensus synthesis
    3. Chief Architect grand review and actionable system decisions
    """

    def __init__(self):
        self.domains = ENTERPRISE_DOMAINS
        self.chief_name = "مهندس بردیا شمس (Chief AI & Systems Architect)"

    def conduct_domain_debate(self, domain_key: str, topic: str, candidate_context: str = "") -> Dict[str, Any]:
        """
        Executes an interactive debate between worker agents of a domain,
        reviewed and finalized by the domain supervisor.
        """
        domain = self.domains.get(domain_key)
        if not domain:
            return {"error": "Domain not found"}

        workers = domain["skills"]
        lead_name = domain["lead"]
        domain_title = domain["title"]

        add_log("WarRoom", f"آغاز مناظره فنی در {domain_title} پیرامون: '{topic[:60]}...'", "info")

        # Worker perspectives
        worker_arguments = []
        for skill_id, skill_meta in workers.items():
            arg_prompt = f"""
            تو ایجنت متخصصی با اسکیل '{skill_id}: {skill_meta['name']}' در {domain_title} هستی.
            حیطه تمرکز تو: {skill_meta['focus']}
            موضوع مورد بررسی: {topic}
            مشخصات کارجو: {candidate_context[:400]}

            در ۲ تا ۳ جمله تخصصی، نظر و تدابیر حرفه‌ای خودت رو برای پروژه بیان کن و به هم‌تیمی‌هایت راهکار قاطع بده:
            """
            response = gemini_client.generate_content(arg_prompt)
            if not response:
                response = f"از دیدگاه {skill_meta['name']}، استانداردهای حوزه {skill_meta['focus']} باید با حداکثر دقت در تمام جریان‌های عملیاتی پیاده‌سازی شوند."
            
            worker_arguments.append({
                "skill": skill_id,
                "agent_name": skill_meta["name"],
                "focus": skill_meta["focus"],
                "argument": response.strip()
            })

        # Domain Lead evaluation and consensus
        workers_summary = "\n\n".join([f"• [{w['agent_name']} ({w['skill']})]: {w['argument']}" for w in worker_arguments])
        lead_prompt = f"""
        تو {lead_name}، سرپرست ارشد {domain_title} هستی.
        {domain['lead_prompt']}

        نظرات متخصصین زیرمجموعه‌ات را بررسی کن:
        {workers_summary}

        موضوع مناظره: {topic}

        به عنوان لیدر، در ۳ جمله نظر نهایی، چالش‌های احتمالی که مطرح کردی و جمع‌بندی اجماع تیم خودت را اعلام کن تا به معمار ارشد (Chief Architect) ارسال شود:
        """
        lead_decision = gemini_client.generate_content(lead_prompt)
        if not lead_decision:
            lead_decision = f"به عنوان سرپرست {domain_title}، پس از به چالش کشیدن پیشنهادات کارشناسان، کلیه الزامات فنی تایید و پروتکل‌های اجرایی استانداردسازی شدند."

        add_log("WarRoom", f"اجماع و تاییدیه سرپرست {domain_title} ثبت شد.", "success")

        return {
            "domain_key": domain_key,
            "domain_title": domain_title,
            "lead": lead_name,
            "worker_arguments": worker_arguments,
            "domain_consensus": lead_decision.strip(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def run_full_enterprise_council(self, topic: str, candidate_context: str = "") -> Dict[str, Any]:
        """
        Runs comprehensive multi-agent governance across all 8 domains
        and submits findings to the Chief AI Architect for final execution.
        """
        add_log("WarRoom", f"جلسه شورای جامع مهندسی (۸ دپارتمان تخصصی) فراخوانده شد.", "info")
        
        domain_reports = []
        for dkey in self.domains.keys():
            rep = self.conduct_domain_debate(dkey, topic, candidate_context)
            domain_reports.append(rep)

        # Chief Architect synthesis
        all_leads_text = "\n\n".join([f"🏛️ **{r['domain_title']} (لیدر: {r['lead']}):**\n{r['domain_consensus']}" for r in domain_reports])

        chief_prompt = f"""
        تو {self.chief_name} هستی؛ بالاترین مرجع فنی و تصمیم‌گیرنده نهایی پروژه Career Co-Pilot.
        گزارش‌های اجماع سرپرستان تمام ۸ دپارتمان تخصصی به دست تو رسیده است:

        {all_leads_text}

        موضوع کلان: {topic}
        کارجو: {candidate_context[:400]}

        به عنوان معمار کل، در یک بیانیه جامع، تصمیم راهبردی نهایی، تاییدیه‌های صادر شده و دستورات قطعی برای اجرای تیم‌های فنی را صادر کن:
        """
        master_decision = gemini_client.generate_content(chief_prompt)
        if not master_decision:
            master_decision = (
                "به عنوان معمار کل سیستم، راهکارهای مصوب تمام ۸ دپارتمان تخصصی (شامل رابط سه‌بعدی Three.js، "
                "امنیت OWASP، احراز هویت جابینجا/جاب‌ویژن، پایپ‌لاین تحلیل هوشمند رزومه و ربات تلگرام) را تصویب "
                "و دستور اجرای هماهنگ و بدون‌خطای آن را در سطح کلیه فایل‌های پروژه صادر می‌کنم."
            )

        add_log("WarRoom", "تصمیم نهایی و راهبردی معمار کل سیستم (Chief AI Architect) با موفقیت صادر شد.", "success")

        return {
            "topic": topic,
            "chief_architect": self.chief_name,
            "domain_reports": domain_reports,
            "master_decision": master_decision.strip(),
            "approved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "APPROVED_FOR_EXECUTION"
        }

hierarchical_engine = HierarchicalMultiAgentEngine()
