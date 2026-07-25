from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import Base, engine
from app.models import *

from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.pickup_slot import router as pickup_router
from app.api import admin_pickup_slots
from app.api import menu_item, orders, admin_orders, stall, webhook
from app.api import admin_registration, admin_profile


# Base.metadata.create_all(bind=engine)

tags_metadata = [
    {
        "name": "Auth",
        "description": "Authentication and registration.",
    },
    {
        "name": "Users",
        "description": "User profile management.",
    },
    {
        "name": "Food Stalls",
        "description": "View food stalls.",
    },
    {
        "name": "Menu Items",
        "description": "Manage and view menu items.",
    },
    {
        "name": "Orders",
        "description": "Student order management.",
    },
    {
        "name": "Admin Orders",
        "description": "Admin workflow for managing orders.",
    },
    {
        "name": "Pickup Slots",
        "description": "Manage pickup slots for order distribution.",
    },
    {
        "name": "WhatsApp Webhook",
        "description": "Receive and respond to WhatsApp messages.",
    },
]

app = FastAPI(
    title="MunchBot API",
    description="This API powers MunchBot — the WhatsApp-based canteen food pre-ordering system.",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")

# Automatically apply Alembic migrations for existing tables
try:
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Database migrations applied successfully!")
except Exception as e:
    print(f"Database migration note: {e}")

from app.database import SessionLocal
from app.models.user import User
from app.enums.user_role import UserRole
from app.utils.security import hash_password

try:
    db = SessionLocal()
    if not db.query(User).filter(User.email == "admin@test.com").first():
        admin = User(
            registration_number="AD000001",
            name="Admin",
            email="admin@test.com",
            phone_number="9999999999",
            password_hash=hash_password("Admin@123"),
            role=UserRole.ADMIN,
            profile_complete=True,
        )
        db.add(admin)
        db.commit()
    else:
        seeded = db.query(User).filter(User.email == "admin@test.com").first()
        if seeded and not seeded.profile_complete:
            seeded.profile_complete = True
            db.commit()
    db.close()
except Exception as e:
    print(f"Error seeding admin user: {e}")

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = exc.errors()
    error_msg = {"error": {"message": "Validation Error", "details": details}}
    return JSONResponse(status_code=422, content=error_msg)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    error_msg = {"error": {"message": exc.detail}}
    return JSONResponse(status_code=exc.status_code, content=error_msg)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = {"error": {"message": "An internal server error occurred."}}
    # In production, log the exception here
    return JSONResponse(status_code=500, content=error_msg)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(pickup_router)
app.include_router(stall.router)
app.include_router(menu_item.router)
app.include_router(orders.router)
app.include_router(admin_orders.router)
app.include_router(webhook.router)
app.include_router(admin_pickup_slots.router)
app.include_router(admin_registration.router)
app.include_router(admin_profile.router)


@app.get("/")
def root():
    return RedirectResponse(url="/admin-dashboard/login.html")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": "MunchBot API",
    }

# ── Serve Admin Frontend ───────────────────────────────────────────────────────
# Mount AFTER all API routes so API routes take priority
app.mount(
    "/admin-dashboard",
    StaticFiles(directory="frontend", html=True),
    name="admin-dashboard",
)