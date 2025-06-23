import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from typing import List

# Load environment variables first
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from config import config

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE) if config.LOG_FILE else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

# Вывод конфигурации при запуске
if config.DEBUG or config.ENVIRONMENT == "development":
    config.print_config()
else:
    logger.info(f"🚀 Smart Call Center {config.ENVIRONMENT.upper()} mode started")
    logger.info(f"📡 Connecting to Asterisk: {config.DEFAULT_ASTERISK_HOST}:{config.DEFAULT_ASTERISK_PORT}")
    logger.info(f"🗄️  Database: {config.DB_NAME}")

from fastapi import FastAPI, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

# Import models and database
from models import *
from database import DatabaseManager
from auth import get_current_active_user
from db import get_db, set_db

# Import route modules
from routes.auth_routes import router as auth_router
from routes.call_routes import router as call_router
from routes.operator_routes import router as operator_router
from routes.queue_routes import router as queue_router
from routes.admin_routes import router as admin_router
from routes.dashboard_routes import router as dashboard_router
from routes.asterisk_routes import router as asterisk_router

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ.get('DB_NAME', 'callcenter')

# Global database manager
db_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    global db_manager
    
    # Startup
    db_manager = DatabaseManager(mongo_url, db_name)
    set_db(db_manager)
    await db_manager.create_indexes()
    
    # Initialize default data if needed
    await initialize_default_data(db_manager)
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    if db_manager:
        await db_manager.close()
    logger.info("Application shut down")

# Create the main app
app = FastAPI(
    title="CallCenter Analytics API",
    description="API for call center analytics and management",
    version="1.0.0",
    lifespan=lifespan
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Dependency to get database manager
def get_database() -> DatabaseManager:
    return get_db()

# Health check endpoints
@api_router.get("/")
async def root():
    return {"message": "CallCenter Analytics API v1.0.0"}

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        await db_manager.users.count_documents({})
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(call_router)
api_router.include_router(operator_router)
api_router.include_router(queue_router)
api_router.include_router(admin_router)
api_router.include_router(dashboard_router)
api_router.include_router(asterisk_router)

# Include WebSocket routes
from routes.websocket_routes import router as websocket_router
app.include_router(websocket_router)

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def initialize_default_data(db: DatabaseManager):
    """Initialize only essential admin user and system settings"""
    try:
        # Check if admin user exists
        admin_user = await db.get_user_by_username("admin")
        
        if not admin_user:
            logger.info("Initializing admin user...")
            
            from auth import get_password_hash
            
            # Create only admin user
            admin_user_data = User(
                username="admin",
                email="admin@callcenter.com",
                name="Системный администратор",
                password_hash=get_password_hash("admin"),
                role=UserRole.ADMIN
            )
            await db.users.insert_one(admin_user_data.dict())
            
            # Create minimal system settings
            default_settings = SystemSettings(
                call_recording=True,
                auto_answer_delay=3,
                max_call_duration=3600,
                queue_timeout=300,
                callback_enabled=True,
                sms_notifications=False,
                email_notifications=True,
                updated_by=admin_user_data.id
            )
            await db.settings.insert_one(default_settings.dict())
            
            logger.info("Admin user and basic settings initialized successfully")
            logger.info("All operational data will be loaded from Asterisk ARI")
        
    except Exception as e:
        logger.error(f"Error initializing admin data: {e}")

# Legacy endpoints for backward compatibility
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db_manager.db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db_manager.db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]