from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid

def generate_uuid():
    return str(uuid.uuid4())

# ===== ENUMS =====
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    OPERATOR = "operator"

class CallStatus(str, Enum):
    WAITING = "waiting"        # В очереди ожидания
    RINGING = "ringing"        # Звонит оператору
    ANSWERED = "answered"      # Отвечен оператором
    COMPLETED = "completed"    # Завершен
    MISSED = "missed"          # Пропущен
    ABANDONED = "abandoned"    # Брошен звонящим
    TRANSFERRED = "transferred" # Переведен
    FAILED = "failed"          # Ошибка

class CallType(str, Enum):
    INCOMING_QUEUE = "incoming_queue"    # Входящий в очередь
    INCOMING_DIRECT = "incoming_direct"  # Входящий напрямую
    OUTGOING = "outgoing"               # Исходящий
    INTERNAL = "internal"               # Внутренний

class CallCategory(str, Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    SALES = "sales"
    SUPPORT = "support"
    COMPLAINT = "complaint"
    VIP = "vip"

class CallPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class OperatorStatus(str, Enum):
    OFFLINE = "offline"
    AVAILABLE = "available"
    BUSY = "busy"
    PAUSED = "paused"
    IN_CALL = "in_call"

# ===== ASTERISK DATABASE CONFIG =====
class AsteriskDatabaseConfig(BaseModel):
    """Конфигурация подключения к БД Asterisk"""
    host: str = "localhost"
    port: int = 3306
    username: str = "asterisk"
    password: str = "password"
    database: str = "asteriskcdrdb"
    db_type: str = "mysql"  # mysql или postgresql
    enabled: bool = False
    ssl_mode: str = "disabled"
    charset: str = "utf8mb4"
    connection_timeout: int = 30
    pool_size: int = 10

# ===== USER MODELS =====
class User(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    username: str
    email: EmailStr
    name: str
    password_hash: str
    role: UserRole
    is_active: bool = True
    group_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    name: str
    password: str
    role: UserRole
    group_id: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    group_id: Optional[str] = None
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    username: str
    password: str

# Group Models
class Group(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    supervisor_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    supervisor_id: Optional[str] = None

# Queue Models
class Queue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    max_wait_time: int = 300  # seconds
    priority: int = 1
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class QueueCreate(BaseModel):
    name: str
    description: Optional[str] = None
    max_wait_time: int = 300
    priority: int = 1

# Operator Models
class Operator(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    extension: Optional[str] = None
    status: OperatorStatus = OperatorStatus.OFFLINE
    group_id: Optional[str] = None
    skills: List[str] = []
    max_concurrent_calls: int = 1
    current_calls: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)

class OperatorCreate(BaseModel):
    user_id: str
    extension: Optional[str] = None
    group_id: Optional[str] = None
    skills: List[str] = []
    max_concurrent_calls: int = 1

class OperatorStatusUpdate(BaseModel):
    status: OperatorStatus

# Call Models
class Call(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caller_number: str
    called_number: Optional[str] = None
    queue_id: str
    operator_id: Optional[str] = None
    status: CallStatus
    start_time: datetime = Field(default_factory=datetime.utcnow)
    answer_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    wait_time: int = 0  # seconds
    talk_time: int = 0  # seconds
    hold_time: int = 0  # seconds
    recording_url: Optional[str] = None
    caller_region: Optional[str] = None
    
    # Call details filled by operator
    description: Optional[str] = None
    category: Optional[CallCategory] = None
    priority: CallPriority = CallPriority.MEDIUM
    resolution: Optional[str] = None
    follow_up_required: bool = False
    customer_satisfaction: Optional[str] = None
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CallCreate(BaseModel):
    caller_number: str
    called_number: Optional[str] = None
    queue_id: str
    caller_region: Optional[str] = None

class CallUpdate(BaseModel):
    operator_id: Optional[str] = None
    status: Optional[CallStatus] = None
    answer_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    wait_time: Optional[int] = None
    talk_time: Optional[int] = None
    hold_time: Optional[int] = None
    description: Optional[str] = None
    category: Optional[CallCategory] = None
    priority: Optional[CallPriority] = None
    resolution: Optional[str] = None
    follow_up_required: Optional[bool] = None
    customer_satisfaction: Optional[str] = None
    notes: Optional[str] = None

class CallDetails(BaseModel):
    description: str
    category: CallCategory
    priority: CallPriority = CallPriority.MEDIUM
    resolution: Optional[str] = None
    follow_up_required: bool = False
    customer_satisfaction: Optional[str] = None
    notes: Optional[str] = None

# Customer Models
class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phone_number: str
    name: Optional[str] = None
    email: Optional[str] = None
    is_vip: bool = False
    region: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CustomerCreate(BaseModel):
    phone_number: str
    name: Optional[str] = None
    email: Optional[str] = None
    is_vip: bool = False
    region: Optional[str] = None
    notes: Optional[str] = None

# System Settings Models
class AsteriskConfig(BaseModel):
    host: str
    port: int = 5038
    username: str
    password: str
    protocol: str = "AMI"
    timeout: int = 30
    enabled: bool = False

class SystemSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    call_recording: bool = True
    auto_answer_delay: int = 3
    max_call_duration: int = 3600
    queue_timeout: int = 300
    callback_enabled: bool = True
    sms_notifications: bool = False
    email_notifications: bool = True
    asterisk_config: Optional[AsteriskConfig] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str

class SystemSettingsUpdate(BaseModel):
    call_recording: Optional[bool] = None
    auto_answer_delay: Optional[int] = None
    max_call_duration: Optional[int] = None
    queue_timeout: Optional[int] = None
    callback_enabled: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None
    asterisk_config: Optional[AsteriskConfig] = None

# Statistics Models
class CallStats(BaseModel):
    total_calls: int = 0
    answered_calls: int = 0
    missed_calls: int = 0
    abandoned_calls: int = 0
    avg_wait_time: float = 0.0
    avg_talk_time: float = 0.0
    avg_hold_time: float = 0.0
    service_level: float = 0.0  # % answered within threshold
    answer_rate: float = 0.0

class OperatorStats(BaseModel):
    operator_id: str
    operator_name: str
    group_name: Optional[str] = None
    total_calls: int = 0
    answered_calls: int = 0
    missed_calls: int = 0
    avg_talk_time: float = 0.0
    avg_hold_time: float = 0.0
    total_talk_time: int = 0
    efficiency: float = 0.0
    online_time: int = 0

class QueueStats(BaseModel):
    queue_id: str
    queue_name: str
    total_calls: int = 0
    answered_calls: int = 0
    missed_calls: int = 0
    abandoned_calls: int = 0
    avg_wait_time: float = 0.0
    avg_talk_time: float = 0.0
    service_level: float = 0.0
    answer_rate: float = 0.0

# Response Models
class APIResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

# Filters and Query Models
class CallFilters(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[CallStatus] = None
    queue_id: Optional[str] = None
    operator_id: Optional[str] = None
    caller_number: Optional[str] = None
    category: Optional[CallCategory] = None
    
class StatsQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    period: str = "today"  # today, yesterday, week, month, custom
    group_id: Optional[str] = None
    operator_id: Optional[str] = None
    queue_id: Optional[str] = None