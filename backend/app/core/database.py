from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Database connection
if settings.database_url.startswith("sqlite"):
    # SQLite specific settings for production
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args={
            "check_same_thread": False,  # Allow multi-threaded access
            "timeout": 10,  # Wait 10s if database is locked
        },
    )
    
    # Enable WAL mode (Write-Ahead Logging) for better concurrency
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        # Enable WAL mode for concurrent reads/writes
        cursor.execute("PRAGMA journal_mode=WAL")
        # Optimize for faster writes
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Increase cache size for better performance
        cursor.execute("PRAGMA cache_size=10000")
        # Foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # Other database types (PostgreSQL, MySQL, etc.)
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,  # Test connections before using them
        pool_size=10,  # Connection pool size
        max_overflow=20,  # Additional connections beyond pool_size
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base for all models
Base = declarative_base()

def get_db():
    """Dependency for getting a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
