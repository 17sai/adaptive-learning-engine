# Adaptive Learning System - Architecture Documentation

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                           │
├─────────────────────────────────────────────────────────────────┤
│  Student Dashboard (Streamlit)  │  Teacher Dashboard (Streamlit) │
│  - Learning path visualization  │  - Cohort monitoring           │
│  - Real-time recommendation     │  - Override interface          │
│  - Progress tracking            │  - Analytics dashboard         │
└──────────────┬────────────────────────────┬─────────────────────┘
               │                            │
               │         HTTP/REST         │
               └────────┬───────────────────┘
                        │
           ┌────────────▼────────────────┐
           │     FastAPI Backend         │
           │   (Python + Uvicorn)        │
           │                             │
           │  ┌──────────────────────┐   │
           │  │  API Routes          │   │
           │  │  - Recommendations   │   │
           │  │  - Path Management   │   │
           │  │  - Data Ingestion    │   │
           │  │  - Calibration       │   │
           │  └──────────────────────┘   │
           │           ▲                  │
           │           │                  │
           │  ┌────────┴─────────────┐   │
           │  │  Core Engines        │   │
           │  │                      │   │
           │  │ ┌─────────────────┐  │   │
           │  │ │ Knowledge State │  │   │
           │  │ │ Model           │  │   │
           │  │ └─────────────────┘  │   │
           │  │                      │   │
           │  │ ┌─────────────────┐  │   │
           │  │ │ Recommendation  │  │   │
           │  │ │ Engine          │  │   │
           │  │ └─────────────────┘  │   │
           │  │                      │   │
           │  │ ┌─────────────────┐  │   │
           │  │ │ Data Ingestion  │  │   │
           │  │ │ Pipeline        │  │   │
           │  │ └─────────────────┘  │   │
           │  └──────────────────────┘   │
           │                             │
           └────────────┬────────────────┘
                        │
        ┌───────────────┴──────────────┐
        │                              │
   ┌────▼──────┐            ┌─────────▼──────┐
   │ SQLite DB                │  External Data │
   │ (File-based)             │  Sources       │
   │                          │                │
   │ - Student profiles       │  - Platform    │
   │ - Topics                 │    modules     │
   │ - Assessments            │  - Engagement  │
   │ - Knowledge states       │  - Doubts      │
   │ - Learning paths         │  - Attendance  │
   │ - Path decisions         │                │
   │ - Audit trail            │                │
   └────────────┘             └────────────────┘
```

## Core Module Interactions

### 1. Data Flow: Assessment → Knowledge Update → Recommendation

```
┌──────────────────────────────┐
│ Assessment Result Ingestion  │
│ (POST /ingest/assessment)    │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ Data Ingestion Pipeline      │
│ - Validate input             │
│ - Create AssessmentResult    │
│ - Trigger knowledge update   │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ Knowledge State Model        │
│ - Apply exponential moving   │
│   average to mastery         │
│ - Calculate learning velocity│
│ - Update confidence          │
│ - Apply decay factor         │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ Recommendation Engine        │
│ - Score candidate topics     │
│ - Check prerequisites        │
│ - Recommend difficulty       │
│ - Generate explanation       │
└──────────────────────────────┘
```

### 2. Real-time Inference Flow

```
Student Portal Request
    │
    ▼
/api/students/{id}/recommendation
    │
    ├─ [<100ms] Load knowledge state from DB
    │
    ├─ [<200ms] Apply decay to mastery levels
    │
    ├─ [<300ms] Score all topics using:
    │   - Mastery gaps
    │   - Learning velocity
    │   - Engagement metrics
    │   - Prerequisite checks
    │
    ├─ [<150ms] Determine difficulty level
    │
    ├─ [<50ms] Generate explanation
    │
    └─ Response (< 1 second total)
```

## Database Schema (Key Entities)

```
STUDENTS
├── id (PK)
├── name, email
├── cohort_id (FK)
└── timestamps

TOPICS
├── id (PK)
├── name, description
├── difficulty_level
├── prerequisites (JSON)
└── avg_study_time

ASSESSMENT_RESULTS
├── id (PK)
├── student_id (FK)
├── assessment_id (FK)
├── score
├── time_spent
├── error_patterns (JSON)
└── completed_at (indexed)

KNOWLEDGE_STATES
├── id (PK)
├── student_id (FK)
├── topic_id (FK)
├── mastery_level (0.0-1.0)
├── confidence (model confidence)
├── learning_velocity
└── last_updated (indexed)

LEARNING_PATHS
├── id (PK)
├── student_id (FK, unique)
├── current_topic_id (FK)
├── current_difficulty
├── planned_topics (JSON)
├── completed_topics (JSON)
├── path_version
└── last_updated (indexed)

PATH_DECISIONS (Audit Trail)
├── id (PK)
├── student_id (FK)
├── recommended_topic_id (FK)
├── recommended_difficulty
├── reasoning (JSON)
├── teacher_override (boolean)
├── created_at (indexed)

ENGAGEMENT_RECORDS
├── id (PK)
├── student_id (FK)
├── topic_id (FK)
├── time_spent
├── interactions
└── recorded_at (indexed)

DOUBTS
├── id (PK)
├── student_id (FK)
├── topic_id (FK)
├── question (text)
├── resolved (boolean)
└── created_at (indexed)
```

## Knowledge State Model Details

### Mastery Calculation

```
New Mastery = α × Score + (1 - α) × Old Mastery

Where:
- α = 0.6 (weight of new assessment)
- Score = normalized assessment score (0-1)
- α = 0.6 makes the model responsive while preserving history
```

### Forgetting Curve

```
Decayed Mastery(t) = M(0) × decay_factor^t

Where:
- M(0) = current mastery level
- decay_factor = 0.95 (5% daily decay)
- t = days since last update

Example: 0.8 mastery decays to:
- After 1 day:  0.76 (0.8 × 0.95)
- After 7 days: 0.56 (0.8 × 0.95^7)
- After 14 days: 0.39 (0.8 × 0.95^14)
```

### Confidence Calculation

```
- Initial: 0.5 (medium)
- Increment: +0.1 per new assessment (max 1.0)
- Purpose: Indicates reliability of mastery estimate
  - Low confidence: Few data points
  - High confidence: Many consistent assessments
```

### Learning Velocity

```
Velocity = Change in Mastery / Time Elapsed

Used for:
- Identifying fast/slow learners
- Personalizing pace recommendations
- Detecting struggles early
```

## Recommendation Engine Details

### Topic Scoring Function

```
Score(topic) = 0.5 × mastery_gap 
             + 0.2 × max(velocity, 0) 
             + 0.3 × engagement_score

Where:
- mastery_gap = 1.0 - current_mastery
- velocity = learning_velocity (0+ = improvement)
- engagement_score = normalized time spent (0-1)

Special cases:
- Skip if mastery > 0.7 (topic mastered)
- Score -2 if prerequisites not met
- Score -1 if already mastered
```

### Difficulty Calibration

```
Target Success Rate: 70%

For each difficulty level:
1. Calculate success rate = (score ≥ 60%) / total attempts
2. Find difficulty closest to 70% success
3. Recommend that difficulty level

Frequency: Recalculated daily or when sample size > 50
```

## Scalability Considerations

### Current Design (MVP)
- Single backend instance
- Direct database queries (indexed)
- Synchronous inference (<1s per request)
- In-memory calculations where possible

### Scaling Path

**Stage 1 (1K-10K students)**
- Add Redis caching for knowledge states
- Implement connection pooling
- Add read replicas for analytics queries

**Stage 2 (10K-100K students)**
- Horizontal scaling with load balancer
- Message queue for data ingestion (Kafka/RabbitMQ)
- Async inference workers for heavy computations
- Separate analytics database

**Stage 3 (100K+ students)**
- Distributed knowledge graph store
- Real-time streaming (Kafka)
- Machine learning model serving layer
- Kubernetes deployment

## High Availability & Disaster Recovery

### Current Implementation
- Database audit trail (PATH_DECISIONS)
- Immutable assessment results
- Version tracking for learning paths

### Future Additions
- Database replication
- Backup and restore procedures
- Failover mechanisms
- Data encryption at rest

## Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| Get Recommendation | <1000ms | ~300ms* |
| Ingest Assessment | <500ms | ~150ms* |
| Batch Ingest (100 items) | <5s | ~1.5s* |
| Knowledge State Load | <200ms | ~80ms* |

*Estimated on single backend instance with indexed queries

## Testing Strategy

1. **Unit Tests** - Individual component tests
2. **Integration Tests** - End-to-end workflows
3. **Performance Tests** - Latency benchmarks
4. **Load Tests** - Concurrent student requests
5. **Chaos Tests** - Database failure scenarios

## Monitoring & Observability

### Key Metrics to Track
- Recommendation latency
- Assessment ingestion success rate
- Knowledge state update accuracy
- Teacher override patterns
- Student learning velocity distributions

### Logging
- All API requests and responses
- Knowledge state updates with deltas
- Teacher overrides with reasoning
- Data pipeline failures and retries

## Security Considerations

1. **Authentication** - JWT tokens (future)
2. **Authorization** - Role-based access control
3. **Data Privacy** - Student data encryption
4. **Audit Trail** - Complete decision history
5. **Rate Limiting** - Prevent API abuse
6. **SQL Injection** - ORM prevents injection
7. **CORS** - Configure for production domains
