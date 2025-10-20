# 🎯 QUICK REFERENCE CARD - GRUPO_GAD

**Last Updated**: 2025-10-20  
**Status**: 🟢 PRODUCTION (Needs DB)  
**Print/Bookmark This File** 

---

## 🌐 PRODUCTION URL

```
https://grupo-gad.fly.dev
```

### Quick Links
- 🏥 Health: https://grupo-gad.fly.dev/health
- 📚 API Docs: https://grupo-gad.fly.dev/docs
- 🔌 WebSocket: https://grupo-gad.fly.dev/ws/stats
- 📊 Metrics: https://grupo-gad.fly.dev/metrics

---

## 🛠️ MOST USED COMMANDS

### View Logs (Real-time)
```bash
flyctl logs -a grupo-gad --follow
```

### Check Status
```bash
flyctl status -a grupo-gad
```

### See All Machines
```bash
flyctl machines list -a grupo-gad
```

### SSH into Machine
```bash
flyctl ssh console -a grupo-gad
```

### Deploy After Changes
```bash
flyctl deploy --local-only -a grupo-gad
```

### Set a Secret
```bash
flyctl secrets set VAR_NAME="value" -a grupo-gad
```

---

## 📖 DOCUMENTATION QUICK LINKS

| Need | Read | Time |
|------|------|------|
| Understand current state | `STATE_OF_REPO.md` | 5 min |
| Set up database | `bash setup-db.sh` | 5 min |
| Step-by-step roadmap | `NEXT_ITERATION.md` | 10 min |
| High-level overview | `EXECUTIVE_SUMMARY.md` | 10 min |
| Complete reading index | `DOCUMENTATION_INDEX.md` | 5 min |
| Database provider options | `SUPABASE_SETUP.md` | 5 min |

---

## 🔄 DATABASE SETUP (NEXT STEPS)

### Option 1: Supabase (⭐ RECOMMENDED)
1. Go to https://supabase.com
2. Create new project
3. Copy CONNECTION STRING
4. Tell agent: provide the URL

### Option 2: Render (⚡ FASTER)
1. Go to https://render.com
2. Create PostgreSQL database
3. Copy DATABASE_URL
4. Tell agent: provide the URL

### Option 3: Railway (🔄 REUSE)
1. Go to https://railway.app
2. Find existing database
3. Copy connection string
4. Tell agent: provide the URL

---

## 📊 KEY METRICS

```
App Status:       🟢 LIVE
Health Check:     ✅ OK (200)
WebSocket:        ✅ INITIALIZED
HTTPS/TLS:        ✅ ACTIVE
Machines:         2 (HA)
Region:           Dallas (dfw)
CPU per Machine:  1 shared
Memory:           512 MB
Docker Image:     87 MB
Uptime:           100% (since deploy)
```

---

## 🚀 WHAT'S WORKING NOW

```
✅ API Endpoints
✅ Health Checks
✅ WebSocket System
✅ API Documentation
✅ HTTPS/TLS
✅ Real-time Logs

⏳ Database (Needs setup)
⏳ Data Persistence
⏳ User Authentication
```

---

## 📋 NEXT PHASE CHECKLIST

- [ ] Choose PostgreSQL provider
- [ ] Run `bash setup-db.sh`
- [ ] Wait for agent to redeploy
- [ ] Verify `curl /health` shows connected=true
- [ ] Configure secrets (if needed)
- [ ] Run full E2E tests

---

## 🔐 IMPORTANT FILES

```
/home/eevan/ProyectosIA/GRUPO_GAD/

├── src/api/main.py           (Modified: ALLOW_NO_DB)
├── fly.toml                  (Modified: Region, ENV)
├── STATE_OF_REPO.md          ← READ THIS FIRST
├── setup-db.sh               ← RUN THIS SECOND
├── NEXT_ITERATION.md         ← DETAILED ROADMAP
├── DOCUMENTATION_INDEX.md    ← ALL RESOURCES
└── ...
```

---

## 💾 GIT COMMANDS

```bash
# See recent commits
git log --oneline -10

# See changes
git status

# See diff
git diff

# Pull latest
git pull origin master

# Push changes
git push origin master
```

---

## ⚠️ COMMON ISSUES

### "Connection refused" on /health
- ✓ App might be redeploying
- ✓ Check `flyctl logs -a grupo-gad --follow`
- ✓ Wait 30-60 seconds

### Database errors
- ✓ DATABASE_URL not configured yet
- ✓ Run `bash setup-db.sh` first
- ✓ Then redeploy

### App is slow
- ✓ Can be slow on first request (cold start)
- ✓ Normal on shared CPU tier
- ✓ For production, upgrade machine size

---

## 📞 QUICK COMMUNICATION

### If problem: Report to agent
```
"I'm getting [ERROR MESSAGE] when [DOING WHAT]"
```

### If asking for help:
```
"Can you help me with [SPECIFIC TASK]"
```

### If providing database URL:
```
"I have DATABASE_URL: postgresql://..."
```

---

## ⏱️ TIMELINE TO FULL PRODUCTION

```
NOW: Read STATE_OF_REPO.md                  (5 min)
     ↓
THEN: Run bash setup-db.sh                  (5 min)
     ↓
WAIT: Agent configures & redeploys          (5 min)
     ↓
VERIFY: Check health endpoint                (1 min)
     ↓
DONE: 🎉 Full production setup complete! (16 min total)
```

---

## 🎯 ONE-LINER COMMANDS

```bash
# Test app is alive
curl https://grupo-gad.fly.dev/health

# See recent logs
flyctl logs -a grupo-gad --no-tail | tail -20

# Check machine status
flyctl machines list -a grupo-gad

# Quick test WebSocket
curl -s https://grupo-gad.fly.dev/ws/stats | jq .

# Redeploy immediately
flyctl deploy --local-only -a grupo-gad && flyctl logs -a grupo-gad --follow
```

---

## 📚 FILES BY PURPOSE

| Purpose | File |
|---------|------|
| Understand now | STATE_OF_REPO.md |
| Database setup | setup-db.sh |
| Next steps | NEXT_ITERATION.md |
| Architecture | EXECUTIVE_SUMMARY.md |
| All docs | DOCUMENTATION_INDEX.md |
| Fly.io details | FLY_DEPLOYMENT_GUIDE.md |

---

## 🎖️ SESSION SUMMARY

- **Duration**: 2.5 hours
- **Commits**: 14 new
- **Documentation**: 10 new files (1,900+ lines)
- **Status**: 🟢 LIVE IN PRODUCTION
- **Next**: Database setup (20 min)

---

## 📌 REMEMBER

1. App is LIVE now ✅
2. Just needs database 🔄
3. Then full production 🎯
4. Estimated: 20 min more ⏱️

**Everything is prepared and documented.**  
**Just run `bash setup-db.sh` to continue!** 🚀

---

## 🆘 EMERGENCY COMMANDS

```bash
# If everything breaks
flyctl machines restart -a grupo-gad

# If logs are wrong
flyctl logs -a grupo-gad --clear

# If stuck, check status
flyctl status -a grupo-gad

# If need to cancel deploy
# Just let it finish or use Ctrl+C in terminal
```

---

**Last Updated**: 2025-10-20 04:50 UTC  
**Keep this file bookmarked!** 📌

---

## 🚀 Ready to continue?

**Next action**:
```bash
bash setup-db.sh
```

That's it! The script will guide you through database setup automatically. ✨
