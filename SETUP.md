# SETUP GUIDE - Adaptive Learning System

Complete step-by-step guide to get the system running locally.

## ⚡ Quick Start (5 minutes)

### 1. Verify Project Setup
```bash
cd Project(Adaptive_Learning)
python verify_setup.py
```

### 2. Copy Environment Config
```bash
# Copy template (SQLite - no credentials needed)
copy .env.example .env
```

### 3. Run Setup Script
```bash
python quickstart.py
```

This will:
- Create Python virtual environment
- Install all backend dependencies
- Install all frontend dependencies

### 4. Initialize Database

```bash
# Activate virtual environment
venv\Scripts\activate  # or source venv/bin/activate on Mac/Linux

# Initialize with sample data (auto-creates SQLite database)
cd backend
python init_db.py
```

### 5. Start Servers (3 Terminal Windows)

**Terminal 1 - Backend API:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python -m uvicorn app.main:app --reload
```
✓ Visit: http://localhost:8000/docs

**Terminal 2 - Student Dashboard:**
```bash
cd frontend
source venv/bin/activate
streamlit run student_dashboard.py
```
✓ Visit: http://localhost:8501

**Terminal 3 - Teacher Dashboard:**
```bash
cd frontend
source venv/bin/activate
streamlit run teacher_dashboard.py --server.port 8502
```
✓ Visit: http://localhost:8502

## 🔧 Detailed Configuration

### SQLite Setup (No Installation Needed)

SQLite is included with Python, so no installation is required. The database file (`adaptive_learning.db`) will be automatically created in the `backend` directory when you run `python init_db.py`.

Your `.env` file is already configured with SQLite - no changes needed.

### Python Virtual Environment

#### Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

## 🧪 Verify Installation

### 1. Check Backend Health
```bash
curl http://localhost:8000/health
# Response: {"status": "healthy", "service": "Adaptive Learning Engine"}
```

### 2. Check Database Connection
```bash
# Check if database file was created
# Windows
dir backend\adaptive_learning.db

# macOS/Linux
ls backend/adaptive_learning.db

# Should exist after running init_db.py
```

### 3. Test API Documentation
- Visit: http://localhost:8000/docs
- You should see all API endpoints listed
- Try "GET /health" endpoint

### 4. Test Student Dashboard
- Visit: http://localhost:8501
- Sidebar should show "Profile" section
- Enter Student ID 1
- Should load sample recommendation

### 5. Test Teacher Dashboard  
- Visit: http://localhost:8502
- Select different view modes (Cohort Overview, etc.)
- Should render without errors

## 🚀 First Test Workflow

### 1. Create Test Data
```bash
# Option A: Use the included init_db.py
cd backend
python init_db.py
# Creates 4 sample students, 5 topics, 4 assessments

# Option B: Manually via API
curl -X POST http://localhost:8000/api/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Student","email":"test@test.com"}'
```

### 2. Submit Assessment Result
```bash
curl -X POST http://localhost:8000/api/ingest/assessment-result \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 1,
    "assessment_id": 1,
    "score": 85,
    "total_time_spent": 1200,
    "correct_answers": 8,
    "wrong_answers": 2,
    "error_patterns": {"concept_gap": 2}
  }'
```

### 3. Get Recommendation
```bash
curl http://localhost:8000/api/students/1/recommendation
# Response: {"student_id": 1, "recommended_topic_id": 3, "recommended_difficulty": 2, ...}
```

### 4. View in Dashboard
- Open Student Dashboard: http://localhost:8501
- Enter Student ID: 1
- Click "Refresh Data"
- Should see recommendation and knowledge state

## 📊 Running Tests

### Unit & Integration Tests
```bash
cd backend

# Install pytest
pip install pytest

# Run tests
pytest tests.py -v

# Run specific test
pytest tests.py::test_knowledge_state_initialization -v
```

### Performance Testing
```bash
# Install load testing tools
pip install locust

# (Locust script to be added in future)
```

## 🐳 Docker Approach (Alternative)

### Build and Run with Docker Compose
```bash
# From project root
docker-compose up -d

# Wait for services to start (5-10 seconds)
docker ps  # Should show 3 containers: backend, student_dashboard, teacher_dashboard

# Initialize database
docker-compose exec backend python init_db.py

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Access Services
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Student Dashboard: http://localhost:8501
- Teacher Dashboard: http://localhost:8502

## 🛠️ Troubleshooting

### Issue: `FileNotFoundError: adaptive_learning.db not found`
**Solution:**
1. Run `python init_db.py` from the backend directory
2. Check that the database file is created: `ls backend/adaptive_learning.db` (Mac/Linux) or `dir backend\adaptive_learning.db` (Windows)

### Issue: `ModuleNotFoundError: No module named 'app'`
**Solution:**
1. Ensure you're in the `backend` directory
2. Check virtual environment is activated
3. Reinstall: `pip install -r requirements.txt`

### Issue: `Port already in use`
**Solution:**
```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or use different port
python -m uvicorn app.main:app --port 8001
streamlit run student_dashboard.py --server.port 8503
```

### Issue: `Streamlit connection refused`
**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify API_BASE_URL in dashboard code is correct
3. Check firewall not blocking localhost

### Issue: Database reset needed
**Solution:**
```bash
# Delete database file and reinitialize (loses all data)
cd backend
rm adaptive_learning.db  # or del adaptive_learning.db on Windows
python init_db.py
```

## 📝 Development Workflow

### Making Changes

1. **Backend**: Changes auto-reload with `--reload` flag
2. **UI**: Streamlit auto-refreshes on file save

### Adding New Topic
```python
# In backend/app/models/models.py - no changes needed
# Data goes through API instead

# Create via API:
curl -X POST http://localhost:8000/api/topics \
  -H "Content-Type: application/json" \
  -d '{"name":"Statistics","description":"Intro to Stats","difficulty_level":2}'
```

### Adding New Endpoint
1. Write function in `backend/app/api/routes.py`
2. Use FastAPI decorators: `@router.post()`, `@router.get()`, etc.
3. Add Pydantic schema to `backend/app/schemas/schemas.py`
4. Restart backend (auto-reload should pick it up)
5. View in `http://localhost:8000/docs`

## 📚 Useful Commands

```bash
# Activate environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Run backend with specific port
python -m uvicorn app.main:app --port 8001

# Run with debug logging
python -m uvicorn app.main:app --log-level debug

# Check database
psql adaptive_learning -c "SELECT COUNT(*) FROM students;"

# Reset everything
rm -rf venv
dropdb adaptive_learning
python quickstart.py
```

## ✅ Final Checklist

- [ ] SQLite database auto-created (no install needed)
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`requirements.txt`)
- [ ] `.env` file configured with correct DB credentials
- [ ] `init_db.py` ran successfully (creates sample data)
- [ ] Backend starts without errors on port 8000
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Student Dashboard accessible at http://localhost:8501
- [ ] Teacher Dashboard accessible at http://localhost:8502
- [ ] Can fetch recommendation via API for student 1
- [ ] Tests pass: `pytest backend/tests.py`

## 🎓 Next Steps After Setup

1. **Explore API**: Visit http://localhost:8000/docs and try endpoints
2. **Review Code**: Read `ARCHITECTURE.md` for design details
3. **Understand Models**: Study `backend/app/engines/` modules
4. **Add Features**: Extend dashboards, add new recommendation factors
5. **Scale Testing**: Use `docker-compose` to test at larger scale
6. **Implement ML Models**: Integrate scikit-learn into recommendation engine

---

**Having issues? See TROUBLESHOOTING section above or check README.md for more details.**

**Questions? Refer to ARCHITECTURE.md for technical deep-dive.**
