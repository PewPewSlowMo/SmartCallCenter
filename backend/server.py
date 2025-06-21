import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, APIRouter, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Import models and database
from models import *
from database import DatabaseManager
from auth import get_current_active_user

# Import route modules
from routes.auth_routes import router as auth_router
from routes.call_routes import router as call_router
from routes.operator_routes import router as operator_router
from routes.queue_routes import router as queue_router
from routes.admin_routes import router as admin_router
from routes.dashboard_routes import router as dashboard_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ.get('DB_NAME', 'callcenter')

# Global database manager
db_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    global db_manager, _db_manager
    
    # Startup
    db_manager = DatabaseManager(mongo_url, db_name)
    _db_manager = db_manager
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
    return _db_manager

# Global database instance
_db_manager = None

def get_db():
    return _db_manager

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
    """Initialize default data if database is empty"""
    try:
        # Check if admin user exists
        admin_user = await db.get_user_by_username("admin@callcenter.com")
        
        if not admin_user:
            logger.info("Initializing default data...")
            
            # Create default groups
            support_group = await db.create_group(GroupCreate(
                name="Группа поддержки",
                description="Техническая поддержка клиентов"
            ))
            
            sales_group = await db.create_group(GroupCreate(
                name="Группа продаж", 
                description="Отдел продаж"
            ))
            
            vip_group = await db.create_group(GroupCreate(
                name="VIP группа",
                description="Обслуживание VIP клиентов"
            ))
            
            # Create default users
            from auth import get_password_hash
            
            # Admin user
            admin_user_data = User(
                username="admin@callcenter.com",
                email="admin@callcenter.com",
                name="Администратор",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN
            )
            await db.users.insert_one(admin_user_data.dict())
            
            # Manager user
            manager_user_data = User(
                username="manager@callcenter.com",
                email="manager@callcenter.com", 
                name="Менеджер Иван",
                password_hash=get_password_hash("manager123"),
                role=UserRole.MANAGER
            )
            await db.users.insert_one(manager_user_data.dict())
            
            # Supervisor user
            supervisor_user_data = User(
                username="supervisor@callcenter.com",
                email="supervisor@callcenter.com",
                name="Супервайзер Анна",
                password_hash=get_password_hash("supervisor123"),
                role=UserRole.SUPERVISOR,
                group_id=support_group.id
            )
            await db.users.insert_one(supervisor_user_data.dict())
            
            # Operator user
            operator_user_data = User(
                username="operator@callcenter.com",
                email="operator@callcenter.com",
                name="Оператор Петр",
                password_hash=get_password_hash("operator123"),
                role=UserRole.OPERATOR,
                group_id=support_group.id
            )
            await db.users.insert_one(operator_user_data.dict())
            
            # Create default queues
            main_queue = await db.create_queue(QueueCreate(
                name="Основная очередь",
                description="Основная очередь для входящих звонков",
                max_wait_time=300,
                priority=1
            ))
            
            support_queue = await db.create_queue(QueueCreate(
                name="Техподдержка",
                description="Очередь технической поддержки",
                max_wait_time=180,
                priority=2
            ))
            
            sales_queue = await db.create_queue(QueueCreate(
                name="Продажи",
                description="Очередь отдела продаж",
                max_wait_time=120,
                priority=3
            ))
            
            vip_queue = await db.create_queue(QueueCreate(
                name="VIP клиенты",
                description="Приоритетная очередь для VIP клиентов",
                max_wait_time=60,
                priority=5
            ))
            
            # Create operator records
            await db.create_operator(OperatorCreate(
                user_id=operator_user_data.id,
                extension="1001",
                group_id=support_group.id,
                skills=["support", "technical"]
            ))
            
            # Create default system settings
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
            
            logger.info("Default data initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing default data: {e}")

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