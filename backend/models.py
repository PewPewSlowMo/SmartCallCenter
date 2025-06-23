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

# ===== OPERATOR MODELS =====
class Operator(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    extension: str
    status: OperatorStatus = OperatorStatus.OFFLINE
    group_id: Optional[str] = None
    skills: List[str] = ["general"]
    max_concurrent_calls: int = 1
    current_calls: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    # Статистика работы
    total_login_time: int = 0  # секунды
    pause_time: int = 0        # секунды на паузе
    calls_offered: int = 0     # предложенные звонки
    calls_answered: int = 0    # отвеченные звонки
    calls_missed: int = 0      # пропущенные звонки

class OperatorCreate(BaseModel):
    user_id: str
    extension: str
    group_id: Optional[str] = None
    skills: List[str] = ["general"]
    max_concurrent_calls: int = 1

class OperatorUpdate(BaseModel):
    extension: Optional[str] = None
    status: Optional[OperatorStatus] = None
    group_id: Optional[str] = None
    skills: Optional[List[str]] = None
    max_concurrent_calls: Optional[int] = None

# ===== CALL MODELS =====
class Call(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    caller_number: str
    called_number: Optional[str] = None
    operator_id: Optional[str] = None
    queue_name: Optional[str] = None
    channel_id: Optional[str] = None
    uniqueid: Optional[str] = None
    
    # Временные метки
    start_time: datetime
    answer_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Длительности (в секундах)
    wait_time: Optional[int] = None      # время ожидания в очереди
    ring_time: Optional[int] = None      # время звонка оператору
    talk_time: Optional[int] = None      # время разговора
    
    # Статус и классификация
    status: CallStatus
    call_type: CallType = CallType.INCOMING_QUEUE
    category: CallCategory = CallCategory.GENERAL
    priority: CallPriority = CallPriority.NORMAL
    
    # Дополнительная информация
    description: Optional[str] = None
    resolution: Optional[str] = None
    notes: Optional[str] = None
    follow_up_required: bool = False
    customer_satisfaction: Optional[int] = None  # 1-5
    
    # Очередь
    queue_position: Optional[int] = None
    abandon_reason: Optional[str] = None
    
    # Метаданные
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CallCreate(BaseModel):
    caller_number: str
    called_number: Optional[str] = None
    operator_id: Optional[str] = None
    queue_name: Optional[str] = None
    channel_id: Optional[str] = None
    uniqueid: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    status: CallStatus = CallStatus.RINGING
    call_type: CallType = CallType.INCOMING_QUEUE
    category: CallCategory = CallCategory.GENERAL
    priority: CallPriority = CallPriority.NORMAL
    queue_position: Optional[int] = None

class CallUpdate(BaseModel):
    operator_id: Optional[str] = None
    answer_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    wait_time: Optional[int] = None
    ring_time: Optional[int] = None
    talk_time: Optional[int] = None
    status: Optional[CallStatus] = None
    category: Optional[CallCategory] = None
    priority: Optional[CallPriority] = None
    description: Optional[str] = None
    resolution: Optional[str] = None
    notes: Optional[str] = None
    follow_up_required: Optional[bool] = None
    customer_satisfaction: Optional[int] = None
    abandon_reason: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CallDetails(BaseModel):
    description: Optional[str] = None
    category: CallCategory = CallCategory.GENERAL
    priority: CallPriority = CallPriority.NORMAL
    resolution: Optional[str] = None
    follow_up_required: bool = False
    customer_satisfaction: Optional[int] = None
    notes: Optional[str] = None

class CallFilters(BaseModel):
    operator_id: Optional[str] = None
    queue_name: Optional[str] = None
    status: Optional[CallStatus] = None
    call_type: Optional[CallType] = None
    category: Optional[CallCategory] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# ===== QUEUE MODELS =====
class Queue(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    name: str
    description: Optional[str] = None
    strategy: str = "leastrecent"  # leastrecent, fewestcalls, linear, etc.
    max_wait_time: int = 300  # секунды
    priority: int = 1
    music_on_hold: Optional[str] = None
    announce_frequency: int = 60
    announce_position: bool = True
    operator_ids: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class QueueCreate(BaseModel):
    name: str
    description: Optional[str] = None
    strategy: str = "leastrecent"
    max_wait_time: int = 300
    priority: int = 1
    operator_ids: List[str] = []

class QueueUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    strategy: Optional[str] = None
    max_wait_time: Optional[int] = None
    priority: Optional[int] = None
    operator_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None

# ===== ASTERISK CONFIG =====
class AsteriskConfig(BaseModel):
    host: str = "localhost"
    port: int = 8088
    username: str = "asterisk"
    password: str = "asterisk"
    protocol: str = "ARI"
    timeout: int = 30
    enabled: bool = True
    use_ssl: bool = False

# ===== SYSTEM SETTINGS =====
class SystemSettings(BaseModel):
    call_recording: bool = True
    auto_answer_delay: int = 3
    max_call_duration: int = 3600
    queue_timeout: int = 300
    callback_enabled: bool = True
    sms_notifications: bool = False
    email_notifications: bool = True
    asterisk_config: Optional[AsteriskConfig] = None
    asterisk_database_config: Optional[AsteriskDatabaseConfig] = None
    updated_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SystemSettingsUpdate(BaseModel):
    call_recording: Optional[bool] = None
    auto_answer_delay: Optional[int] = None
    max_call_duration: Optional[int] = None
    queue_timeout: Optional[int] = None
    callback_enabled: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None
    asterisk_config: Optional[AsteriskConfig] = None
    asterisk_database_config: Optional[AsteriskDatabaseConfig] = None

# ===== STATISTICS MODELS =====
class StatsQuery(BaseModel):
    period: str = "today"  # today, week, month, custom
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    group_id: Optional[str] = None
    operator_id: Optional[str] = None
    queue_name: Optional[str] = None

class CallStats(BaseModel):
    total_calls: int = 0
    answered_calls: int = 0
    missed_calls: int = 0
    abandoned_calls: int = 0
    avg_wait_time: float = 0.0
    avg_talk_time: float = 0.0
    service_level: float = 0.0  # % calls answered within threshold
    answer_rate: float = 0.0    # % calls answered vs total

class OperatorStats(BaseModel):
    operator_id: str
    operator_name: str
    group_name: Optional[str] = None
    total_calls: int = 0
    answered_calls: int = 0
    missed_calls: int = 0
    offered_calls: int = 0      # НОВОЕ: предложенные звонки
    avg_talk_time: float = 0.0
    avg_hold_time: float = 0.0
    total_talk_time: int = 0
    efficiency: float = 0.0
    online_time: int = 0        # НОВОЕ: время онлайн
    pause_time: int = 0         # НОВОЕ: время на паузе

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
    max_wait_time: float = 0.0

# ===== GROUP MODELS =====
class Group(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    name: str
    description: Optional[str] = None
    supervisor_id: Optional[str] = None
    operator_ids: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    supervisor_id: Optional[str] = None

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    supervisor_id: Optional[str] = None
    is_active: Optional[bool] = None

# ===== RESPONSE MODELS =====
class UserResponse(BaseModel):
    """User response model (без пароля)"""
    id: str
    username: str
    email: EmailStr
    name: str
    role: UserRole
    is_active: bool
    group_id: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

# ===== API RESPONSE =====
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# ===== TOKEN =====
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User