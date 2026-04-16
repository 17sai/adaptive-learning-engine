# Adaptive Learning Path Engine

AI-powered personalized learning system that dynamically adapts to each student's performance, engagement, and learning velocity.

## 🎯 Project Overview

This is a production-complexity adaptive learning platform with:

- **Backend**: FastAPI + SQLite + scikit-learn ML models
- **Frontend**: Streamlit dashboards (Student + Teacher)
- **Real-time Inference**: Recommendations update within seconds
- **Knowledge Modeling**: Continuous tracking of student mastery with forgetting curves
- **Recommendation Engine**: Context-aware topic selection with difficulty calibration
- **Audit Trail**: Complete history of all path decisions for compliance

## 📁 Project Structure

```
Project(Adaptive_Learning)/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # API endpoints
│   │   ├── models/
│   │   │   └── models.py          # SQLAlchemy ORM models
│   │   ├── schemas/
│   │   │   └── schemas.py         # Pydantic validation schemas
│   │   ├── engines/
│   │   │   ├── knowledge_state_model.py      # Student knowledge tracking
│   │   │   └── recommendation_engine.py      # ML recommendation logic
│   │   ├── pipelines/
│   │   │   └── data_ingestion.py  # Real-time data ingestion
│   │   ├── core/
│   │   │   ├── config.py          # Configuration management
│   │   │   └── database.py        # Database setup
│   │   ├── utils/
│   │   │   └── helpers.py         # Utility functions
│   │   └── main.py                # FastAPI app entry point
│   └── requirements.txt           # Backend dependencies
│
├── frontend/
│   ├── student_dashboard.py       # Student learning interface
│   ├── teacher_dashboard.py       # Teacher monitoring & override
│   └── requirements.txt           # Frontend dependencies
│
├── database/                      # Migration scripts (future)
├── .env.example
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- pip

(No database installation needed - SQLite is included with Python)

### 1. Setup Environment

```bash
# Clone/navigate to project
cd Project(Adaptive_Learning)

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 3. Configure Database

Copy the example config:

```bash
copy .env.example .env
```

No credentials needed - SQLite is file-based and auto-creates the database.

### 4. Initialize Database

```bash
# Tables and sample data auto-create on first run
cd backend
python init_db.py
```

### 5. Start Backend Server

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

### 6. Start Frontend (Streamlit)

In a new terminal:

```bash
cd frontend

# Student dashboard
streamlit run student_dashboard.py --server.port=8501

# Teacher dashboard (different port)
streamlit run teacher_dashboard.py --server.port=8502
```

**Access:**
- Student Dashboard: `http://localhost:8501`
- Teacher Dashboard: `http://localhost:8502`

## 📊 Core Modules

### Knowledge State Model (`backend/app/engines/knowledge_state_model.py`)

Maintains continuous representation of student knowledge:

- **Mastery Levels**: 0.0-1.0 for each topic
- **Confidence**: Model confidence in the estimate (affects recommendations)
- **Learning Velocity**: Rate of improvement (helps personalize pace)
- **Forgetting Curves**: Knowledge decay without practice (Ebbinghaus-inspired)

**Key Methods:**
- `initialize_student_knowledge()` - Setup for new students
- `update_from_assessment()` - Update after each quiz/test
- `apply_decay()` - Calculate decayed mastery for idle topics
- `get_weak_areas()` - Find topics needing review

### Recommendation Engine (`backend/app/engines/recommendation_engine.py`)

Determines next topic and difficulty:

**Scoring Factors:**
- Mastery gaps (primary)
- Learning velocity
- Engagement levels
- Prerequisites completion

**Features:**
- Difficulty calibration (50-70% success target)  
- Prerequisite validation
- Explanation generation ("Why am I learning this?")

### Data Ingestion Pipeline (`backend/app/pipelines/data_ingestion.py`)

Real-time processing of:
- Assessment results → Knowledge state updates
- Engagement metrics
- Student doubts/questions
- Difficulty calibration

## 🔌 API Endpoints

### Core Recommendation
- `GET /api/students/{student_id}/recommendation` - Get next topic
- `GET /api/students/{student_id}/weak-areas` - Identify gaps
- `GET /api/students/{student_id}/knowledge-state` - Full knowledge map

### Path Management
- `GET /api/students/{student_id}/learning-path` - Current path
- `POST /api/students/{student_id}/override-recommendation` - Teacher override
- `POST /api/students/{student_id}/path-decision` - Log decisions

### Data Ingestion
- `POST /api/ingest/assessment-result` - Submit assessment
- `POST /api/ingest/engagement` - Log engagement
- `POST /api/ingest/doubt` - Record question
- `POST /api/ingest/batch-assessments` - Bulk assessments

### Difficulty Calibration
- `POST /api/calibrate/difficulty/{topic_id}` - Recalibrate content

### Teacher Dashboard
- `GET /api/teacher/cohort/{cohort_id}/paths` - Cohort view
- `GET /api/teacher/student/{student_id}/history` - Decision history
- `GET /api/metrics/student/{student_id}` - Performance metrics

## 🔑 Key Design Decisions

### Architecture
- **Separation of Concerns**: Engines, Pipelines, Routes cleanly separated
- **Real-time Inference**: Sub-1s response times via in-memory calculations
- **Audit Trail**: Every decision logged with reasoning for transparency

### ML Approach
- **No external ML service** - Designed to run inference synchronously
- **scikit-learn ready** - Can add clustering, regression models later
- **Bayesian-inspired mastery**: Simple yet effective for personalization

### Database
- **SQLite**: File-based, no server needed, zero configuration
- **JSON fields**: Flexible storage for error patterns, reasoning
- **Indexing**: Student ID, timestamps for fast queries

### Scalability Considerations
- **Horizontal scaling**: Stateless API servers
- **Caching layer ready**: Redis cache patterns designed in
- **Batch processing**: Batch assessment endpoint for bulk ingestion
- **Async option**: Can migrate to async with Celery for large scale

## 🧪 Testing the System

### 1. Create Test Data

```python
# Use the API to create students and topics
curl -X POST http://localhost:8000/api/students \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

### 2. Simulate Student Activity

```python
# Ingest an assessment result
curl -X POST http://localhost:8000/api/ingest/assessment-result \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 1,
    "assessment_id": 1,
    "score": 75,
    "total_time_spent": 1200,
    "correct_answers": 15,
    "wrong_answers": 5,
    "error_patterns": {"concept_misunderstanding": 3, "careless_errors": 2}
  }'
```

### 3. Get Recommendation

Visit: `http://localhost:8000/api/students/1/recommendation`

## 📈 Future Enhancements

1. **Advanced ML Models**
   - Bayesian Knowledge Tracing for deeper modeling
   - Collaborative filtering for peer recommendations
   - Neural networks for pattern detection

2. **Real-time Updates**
   - WebSocket support for live path adjustments
   - Kafka streaming for high-volume ingestion

3. **Explainability**
   - SHAP values for model explanations
   - Confidence intervals on predictions

4. **Scaling Infrastructure**
   - Docker containerization
   - Kubernetes deployment manifests
   - Load testing scripts

5. **Analytics**
   - Retention prediction
   - Learning curve analysis
   - Cohort behavioral clustering

## 🔐 Production Considerations

- Environment variables for secrets
- Database connection pooling
- Rate limiting on API endpoints
- JWT authentication for users
- HTTPS/TLS configuration
- Database backups and recovery
- Monitoring and alerting setup

## 📝 Notes for Interns

As mentioned in the project brief, you're expected to make independent technical decisions. Some considerations:

1. **Model Selection**: Why scikit-learn vs. deep learning?
   - Answer: Interpretability, fast training, resource efficiency for MVP

2. **Database Normalization**: Tradeoffs vs. JSON fields?
   - Answer: JSON for flexibility + ACID compliance for critical data

3. **Real-time Constraints**: How to keep inference < 1s at scale?
   - Answer: In-memory caches, indexed queries, materialized views as scale increases

4. **Privacy**: How to handle student data securely?
   - Answer: Encryption at rest, role-based access, audit logging (implemented)

## 📚 References

- [Ebbinghaus Forgetting Curve](https://en.wikipedia.org/wiki/Forgetting_curve)
- [Bayesian Knowledge Tracing](https://en.wikipedia.org/wiki/Bayesian_knowledge_tracing)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

## 🤝 Contributing

All PRs should include:
- Unit tests for new features
- Updated documentation
- Performance benchmarks for critical paths

## 📄 License

[Add appropriate license]

---

**Happy building! 🎓**
