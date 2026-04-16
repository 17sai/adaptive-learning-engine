# Production Readiness Guide - Adaptive Learning System

## 📋 Quick Start

You now have 3 production tools to validate your system:

1. **`PRODUCTION_CHECKLIST.md`** - Deployment verification steps
2. **`monitor.py`** - Real-time system health monitoring
3. **`load_test.py`** - Performance and reliability testing

---

## 🚀 Step-by-Step Production Readiness

### Step 1: Pre-Deployment Validation (5 minutes)

**Verify system is working:**

```bash
# Terminal 1: Start backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 2: Check health
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

---

### Step 2: Monitor System Health (Real-time)

**Start the monitoring dashboard:**

```bash
# Terminal 3: Install psutil if needed
pip install psutil requests

# Run continuous monitoring (updates every 30 seconds)
python monitor.py --watch

# Or single snapshot
python monitor.py

# Export to JSON for analysis
python monitor.py --export health_report.json
```

**What you'll see:**
- ✅ API Status (RUNNING/DOWN)
- 📊 Database file size, row counts, integrity
- 💻 CPU, Memory, Disk usage
- 🚨 Alerts for issues (high CPU, old backups, etc.)

**Example output:**
```
======================================================================
ADAPTIVE LEARNING SYSTEM - MONITORING DASHBOARD
======================================================================
Generated: 2024-04-15 14:32:15

✅ API Backend: RUNNING
   URL: http://localhost:8000

📊 DATABASE STATISTICS:
   File Size: 2.5 MB
   Journal Mode: wal
   Integrity: ok
   Students: 15
   Assessments: 47
   Topics: 5

💻 SYSTEM RESOURCES:
   CPU:    [████░░░░░░░░░░░░░░] 20.5%
   Memory: [██████░░░░░░░░░░░░░] 32.1% (5.12 GB used)
   Disk:   [███████░░░░░░░░░░░░] 35.7% (125.43 GB free)

✅ BACKUPS:
   Latest: adaptive_learning.db.20240415_020000.gz
   Size: 1.2 MB
   Age: 12.5 hours

✅ No alerts
======================================================================
```

---

### Step 3: Load Testing (10-15 minutes)

**Simulate production-like activity:**

```bash
# Basic test: 10 students over 60 seconds
python load_test.py --students 10 --duration 60

# Light load: 50 students over 5 minutes
python load_test.py --students 50 --duration 300

# Production readiness: 100 students over 10 minutes
python load_test.py --students 100 --duration 600

# Export results for reporting
python load_test.py --students 100 --duration 300 --export production_test.json
```

**What it tests:**
- ✅ Registration of new students under load
- ✅ Recommendation endpoint response time
- ✅ Assessment submission processing
- ✅ Concurrent request handling
- ✅ Error rate and stability

**Expected results for production readiness:**

| Metric | ✅ Ready | ⚠️ Monitor | ❌ Not Ready |
|--------|---------|-----------|-------------|
| Success Rate | > 99% | 95-99% | < 95% |
| Avg Response | < 100ms | 100-500ms | > 500ms |
| P95 Response | < 200ms | 200-1000ms | > 1000ms |
| Errors | None | < 5/1000 | > 5/1000 |

**Example output:**
```
======================================================================
LOAD TEST RESULTS
======================================================================

📊 SUMMARY:
   Total Requests: 1,247
   Successful: 1,246
   Failed: 1
   Success Rate: 99.9%

🎯 RECOMMENDATIONS (623 requests):
   Min: 45.23 ms
   Max: 892.15 ms
   Avg: 87.34 ms
   Median: 82.10 ms
   P95: 145.67 ms
   P99: 234.89 ms

📝 ASSESSMENTS (624 requests):
   Min: 52.10 ms
   Max: 756.34 ms
   Avg: 94.56 ms
   Median: 89.23 ms
   P95: 167.89 ms
   P99: 289.34 ms

✅ RECOMMENDATIONS FOR PRODUCTION DEPLOYMENT:
   ✓ Excellent reliability - system ready for production
   ✓ Excellent response time - well under 500ms threshold

======================================================================
```

---

## 🔧 Using Each Tool

### Monitor.py - Ongoing Monitoring

**Single check (snapshot):**
```bash
python monitor.py
```

**Continuous monitoring (background):**
```bash
python monitor.py --watch &
# Shows dashboard every 30 seconds
# Stop with: fg (then Ctrl+C)
```

**Custom database path:**
```bash
python monitor.py --db /var/lib/adaptive_learning/adaptive_learning.db
```

**Export for analysis:**
```bash
python monitor.py --export daily_health.json
# JSON output good for:
# - Email reports
# - Graphing trends
# - Automated alerts
# - Documentation
```

**What each metric means:**

| Metric | What it measures | Production threshold |
|--------|-----------------|---------------------|
| File Size | Database growth | Alert if > 500 MB on SQLite |
| Integrity | Data corruption | Must be "ok" |
| Journal Mode | Concurrency level | Should be "wal" |
| CPU % | Server load | Alert if > 80% sustained |
| Memory % | RAM usage | Alert if > 85% |
| Disk % | Storage space | Alert if > 90% |
| Backup age | Freshness | Alert if > 25 hours |

---

### Load_test.py - Performance Testing

**Minimum production test:**
```bash
# Run 5 different intensity levels
python load_test.py --students 10 --duration 60  # Light
python load_test.py --students 25 --duration 60  # Medium
python load_test.py --students 50 --duration 60  # Heavy
python load_test.py --students 100 --duration 300  # Extended
python load_test.py --students 50 --duration 600  # Long duration
```

**Simulate school scenarios:**

```bash
# Morning scenario: 30 students checking recommendations
python load_test.py --students 30 --duration 300

# Assessment day: 100 students submitting results over 2 hours
python load_test.py --students 100 --duration 7200

# Peak load test: Can your system handle 200 concurrent?
python load_test.py --students 200 --duration 600
```

**Batch testing script:**
```bash
#!/bin/bash
echo "Running production readiness tests..."

python load_test.py --students 10 --duration 60 --export test_10std_60sec.json
python load_test.py --students 50 --duration 300 --export test_50std_300sec.json
python load_test.py --students 100 --duration 600 --export test_100std_600sec.json

echo "All tests completed. Check JSON files for detailed results."
```

---

### PRODUCTION_CHECKLIST.md - Deployment Verification

**Use this during deployment:**

```bash
# Print the checklist
cat PRODUCTION_CHECKLIST.md

# Check off each section as you complete:
# ☑️ Pre-Deployment
# ☑️ Deployment Day
# ☑️ Post-Deployment
# ☑️ Ongoing Maintenance
```

**Key sections:**

1. **Pre-Deployment** (Do these first)
   - [ ] Run load tests
   - [ ] Verify backups work
   - [ ] Document procedures

2. **Deployment Day** (Do these before launching)
   - [ ] Set up Linux service file
   - [ ] Configure backup scheduling
   - [ ] Set up monitoring
   - [ ] Test all endpoints

3. **Post-Deployment** (Do these after launch)
   - [ ] Verify first backup completes
   - [ ] Monitor for 24 hours
   - [ ] Document any issues

4. **Ongoing Maintenance** (Do monthly)
   - [ ] Update packages
   - [ ] Check disk space
   - [ ] Verify backups

---

## 📊 Recommended Testing Schedule

### Before First Deployment

```
Week 1:
├─ Mon: Run load_test.py with 10 students
├─ Tue: Run load_test.py with 50 students
├─ Wed: Run load_test.py with 100 students
├─ Thu: Extended 10-minute test with 50 students
├─ Fri: Full checklist walkthrough
└─ Review all test results

Week 2:
├─ Staging environment deployment
├─ Production checklist verification
├─ Monitor for 7 days
└─ Go/no-go decision
```

### First Production Month

```
Daily:
├─ Check monitor.py output
├─ Review any alerts
└─ Verify backup completion

Weekly:
├─ Test backup restoration
├─ Review API logs
└─ Check system growth rate

Monthly:
├─ Full load test (100 students)
├─ Database optimization (VACUUM/ANALYZE)
├─ Security review
└─ Plan for scaling
```

---

## 🚨 Common Issues & Fixes

### Issue: "database is locked"

**Cause:** Too many concurrent writes, SQLite timeout too short

**Fix:**
```python
# In backend/app/core/database.py, increase timeout:
connect_args={"timeout": 30}  # Changed from 10 to 30 seconds
```

### Issue: Slow recommendations (> 500ms)

**Cause:** Database size growing, indexes missing, or server under-resourced

**Check:**
```bash
# Check database size
ls -lh backend/adaptive_learning.db

# Optimize database
sqlite3 backend/adaptive_learning.db "VACUUM;"
sqlite3 backend/adaptive_learning.db "ANALYZE;"

# Check if queries use indexes
sqlite3 backend/adaptive_learning.db "EXPLAIN QUERY PLAN SELECT * FROM students WHERE id=1;"
```

### Issue: Disk space filling up

**Cause:** Database file growing too large or backups not cleaning up

**Fix:**
```bash
# Check what's using space
du -sh backend/
du -sh /var/backups/adaptive_learning/

# Clean old backups
find /var/backups/adaptive_learning/ -mtime +30 -delete

# Vacuum database
sqlite3 backend/adaptive_learning.db "VACUUM;"
```

### Issue: Load test shows "connection refused"

**Cause:** API backend not running, wrong URL, or firewall

**Fix:**
```bash
# Terminal 1: Ensure backend is running
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Test connection
curl http://localhost:8000/health

# If on remote server:
python load_test.py --api http://your-server-ip:8000
```

---

## ✅ Production Readiness Sign-Off

You are **ready for production** when:

- ✅ `load_test.py` with 100 students shows > 99% success rate
- ✅ Average response time < 300ms  
- ✅ P95 response time < 1000ms
- ✅ `monitor.py` shows "Integrity: ok"
- ✅ Backup script runs successfully daily
- ✅ All checklist items completed
- ✅ You can restore from backup in < 5 minutes
- ✅ Team trained on monitoring and incident response

---

## 📞 Support & Escalation

**If you see these issues:**

| Issue | Severity | Action |
|-------|----------|--------|
| Success rate < 95% | CRITICAL | Wait, don't deploy. Investigate errors. |
| Response time > 1s | CRITICAL | Database optimization or server upgrade needed. |
| Backup missing | CRITICAL | Fix backup script before deploying. |
| CPU > 90% sustained | HIGH | Need more server resources. |
| Memory > 85% sustained | HIGH | Increase server RAM. |
| Avg response 300-500ms | MEDIUM | Monitor in production, optimize if needed. |
| Old backup (>25hrs) | MEDIUM | Check cron job, restart backup scheduler. |
| Any database corruption | CRITICAL | Restore from backup immediately. |

---

## 📚 Additional Resources

- **Database optimization:** See `SQLITE_VS_PRODUCTION.md`
- **Student management:** See `SCALABILITY_GUIDE.md`
- **Teacher features:** See `TEACHER_OVERRIDE_GUIDE.md`
- **Architecture:** See `ARCHITECTURE.md`

---

**Remember:** Your system is production-ready when you're confident it can handle your peak load with room to spare. These tools help you prove that before launch. 🚀
