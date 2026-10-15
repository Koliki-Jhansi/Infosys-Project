import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.core.security import hash_password
from app.db.session import engine, Base, SessionLocal
from app.models import User, UserRole, AppSetting
from app.api.v1.auth import router as auth_router
from app.api.v1.tickets import router as tickets_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.settings import router as settings_router, ensure_default_settings

# Application API Routers
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.jira import router as jira_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.ai_solution import router as ai_solution_router

def init_db_and_seed():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        ensure_default_settings(db)
        
        # Seed default Demo Accounts if none exist
        admin = db.query(User).filter(User.email == "admin@aeroassistant.com").first()
        if not admin:
            admin_user = User(
                email="admin@aeroassistant.com",
                hashed_password=hash_password("AdminPass123!"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)

            support_user = User(
                email="engineer@aeroassistant.com",
                hashed_password=hash_password("EngineerPass123!"),
                full_name="Sarah Connor (Lead Support Agent)",
                role=UserRole.SUPPORT_AGENT,
                is_active=True
            )
            db.add(support_user)

            requester_user = User(
                email="requester@aeroassistant.com",
                hashed_password=hash_password("RequesterPass123!"),
                full_name="Emily Watson (Passenger)",
                role=UserRole.PASSENGER,
                is_active=True
            )
            db.add(requester_user)

            db.commit()
            logger.info("Demo accounts seeded: admin@aeroassistant.com, engineer@aeroassistant.com, requester@aeroassistant.com")
        
        # Ensure agent@ and passenger@ aliases exist for convenience
        agent_alias = db.query(User).filter(User.email == "agent@aeroassistant.com").first()
        if not agent_alias:
            db.add(User(
                email="agent@aeroassistant.com",
                hashed_password=hash_password("AgentPass123!"),
                full_name="Alex Rivera (Support Agent)",
                role=UserRole.SUPPORT_AGENT,
                is_active=True
            ))
            db.add(User(
                email="passenger@aeroassistant.com",
                hashed_password=hash_password("PassengerPass123!"),
                full_name="Marcus Vance (Frequent Flyer)",
                role=UserRole.PASSENGER,
                is_active=True
            ))
            db.commit()
    finally:
        db.close()

from app.api.v1.knowledge import router as knowledge_router, auto_seed_sample_documents

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Aero Assistant API...")
    init_db_and_seed()
    db = SessionLocal()
    try:
        await auto_seed_sample_documents(db)
    except Exception as e:
        logger.warning(f"Auto-seed sample knowledge docs: {e}")
    finally:
        db.close()
    yield
    logger.info("Shutting down Aero Assistant API...")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Intelligent IT Ticket Automation Platform with RAG, Multi-Agent Orchestration, and Jira Integration",
    lifespan=lifespan
)

from fastapi.exceptions import RequestValidationError

# CORS
cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
]
for origin in settings.cors_origins_list:
    if origin not in cors_origins:
        cors_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_messages = []
    for err in errors:
        loc = [str(x) for x in err.get("loc", []) if x != "body"]
        field = ".".join(loc)
        msg = err.get("msg", "Invalid value")
        error_messages.append(f"{field}: {msg}" if field else msg)
    summary_msg = "; ".join(error_messages)
    return JSONResponse(
        status_code=422,
        content={
            "detail": errors,
            "message": summary_msg,
            "error": summary_msg
        }
    )

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", os.urandom(8).hex())
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# Mount API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(tickets_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(workflows_router, prefix="/api")
app.include_router(jira_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(ai_solution_router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "ai_mock_mode": settings.AI_MOCK_MODE,
        "jira_mock_mode": settings.JIRA_MOCK_MODE,
        "default_confidence_threshold": settings.CONFIDENCE_THRESHOLD
    }
