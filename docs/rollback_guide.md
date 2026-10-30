# Career Co-Pilot Enterprise - Operational Runbook & Rollback Guide

## 1. System Overview & Architecture
Career Co-Pilot Enterprise runs on a dual-tier architecture:
- **FastAPI Core**: Serves REST endpoints (`/health`, `/metrics`, `/api/jobs`, `/api/interview`, `/api/warroom`)
- **Telegram Bot**: Polling / Webhook daemon providing 24/7 candidate monitoring
- **Database**: SQLite / PostgreSQL with Alembic migration versioning

## 2. Health Monitoring & Observability
- **Health Check**: `GET /health` -> `{"status": "healthy", "database": "connected"}`
- **Metrics Check**: `GET /metrics` -> Returns active jobs, applications count, and audit event metrics.
- **Log Stream**: Structured JSON audit logs stored in `audit_logs` table.

## 3. Step-by-Step Rollback Procedure

### Scenario A: Git Release Rollback
If a regression is deployed to `main`:
```bash
# 1. Identify previous stable commit hash
git log -n 5 --oneline

# 2. Revert to stable commit
git revert HEAD --no-edit
git push origin main
```

### Scenario B: Database Migration Rollback (Alembic)
If a database schema migration fails:
```bash
# Downgrade to previous revision
alembic downgrade -1
```

### Scenario C: Cloudflare Tunnel & Process Restart
```powershell
# Stop all services
taskkill /F /IM uvicorn.exe
taskkill /F /IM cloudflared.exe

# Start clean instance
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8088
.\bin\cloudflared.exe tunnel --url http://127.0.0.1:8088
```
