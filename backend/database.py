from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
from models import *
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, mongo_url: str, db_name: str):
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[db_name]
        
        # Collections
        self.users = self.db.users
        self.groups = self.db.groups
        self.queues = self.db.queues
        self.operators = self.db.operators
        self.calls = self.db.calls
        self.customers = self.db.customers
        self.settings = self.db.settings
        
    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users indexes
            await self.users.create_index("username", unique=True)
            await self.users.create_index("email", unique=True)
            await self.users.create_index("role")
            
            # Operators indexes
            await self.operators.create_index("user_id", unique=True)
            await self.operators.create_index("status")
            await self.operators.create_index("group_id")
            
            # Calls indexes
            await self.calls.create_index("caller_number")
            await self.calls.create_index("queue_id")
            await self.calls.create_index("operator_id")
            await self.calls.create_index("status")
            await self.calls.create_index("start_time")
            await self.calls.create_index([("start_time", -1)])  # Descending for recent calls
            
            # Customers indexes
            await self.customers.create_index("phone_number", unique=True)
            
            # Queues indexes
            await self.queues.create_index("name", unique=True)
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    # User operations
    async def create_user(self, user_data: UserCreate) -> User:
        user = User(**user_data.dict())
        result = await self.users.insert_one(user.dict())
        return user
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        user_data = await self.users.find_one({"username": username})
        if user_data:
            return User(**user_data)
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        user_data = await self.users.find_one({"id": user_id})
        if user_data:
            return User(**user_data)
        return None
    
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        cursor = self.users.find().skip(skip).limit(limit)
        users = []
        async for user_data in cursor:
            users.append(User(**user_data))
        return users
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        updates["updated_at"] = datetime.utcnow()
        result = await self.users.update_one({"id": user_id}, {"$set": updates})
        return result.modified_count > 0
    
    async def delete_user(self, user_id: str) -> bool:
        result = await self.users.delete_one({"id": user_id})
        return result.deleted_count > 0
    
    # Group operations
    async def create_group(self, group_data: GroupCreate) -> Group:
        group = Group(**group_data.dict())
        await self.groups.insert_one(group.dict())
        return group
    
    async def get_groups(self) -> List[Group]:
        cursor = self.groups.find()
        groups = []
        async for group_data in cursor:
            groups.append(Group(**group_data))
        return groups
    
    async def get_group_by_id(self, group_id: str) -> Optional[Group]:
        group_data = await self.groups.find_one({"id": group_id})
        if group_data:
            return Group(**group_data)
        return None
    
    # Queue operations
    async def create_queue(self, queue_data: QueueCreate) -> Queue:
        queue = Queue(**queue_data.dict())
        await self.queues.insert_one(queue.dict())
        return queue
    
    async def get_queues(self) -> List[Queue]:
        cursor = self.queues.find({"is_active": True})
        queues = []
        async for queue_data in cursor:
            queues.append(Queue(**queue_data))
        return queues
    
    async def get_queue_by_id(self, queue_id: str) -> Optional[Queue]:
        queue_data = await self.queues.find_one({"id": queue_id})
        if queue_data:
            return Queue(**queue_data)
        return None
    
    # Operator operations
    async def create_operator(self, operator_data: OperatorCreate) -> Operator:
        operator = Operator(**operator_data.dict())
        await self.operators.insert_one(operator.dict())
        return operator
    
    async def get_operators(self, group_id: Optional[str] = None) -> List[Operator]:
        filter_query = {}
        if group_id:
            filter_query["group_id"] = group_id
            
        cursor = self.operators.find(filter_query)
        operators = []
        async for operator_data in cursor:
            operators.append(Operator(**operator_data))
        return operators
    
    async def get_operator_by_user_id(self, user_id: str) -> Optional[Operator]:
        operator_data = await self.operators.find_one({"user_id": user_id})
        if operator_data:
            return Operator(**operator_data)
        return None
    
    async def update_operator_status(self, operator_id: str, status: OperatorStatus) -> bool:
        updates = {
            "status": status,
            "last_activity": datetime.utcnow()
        }
        result = await self.operators.update_one({"id": operator_id}, {"$set": updates})
        return result.modified_count > 0
    
    # Call operations
    async def create_call(self, call_data: CallCreate) -> Call:
        call = Call(**call_data.dict())
        await self.calls.insert_one(call.dict())
        return call
    
    async def get_calls(self, filters: CallFilters, skip: int = 0, limit: int = 100) -> List[Call]:
        filter_query = {}
        
        if filters.start_date and filters.end_date:
            filter_query["start_time"] = {
                "$gte": filters.start_date,
                "$lte": filters.end_date
            }
        elif filters.start_date:
            filter_query["start_time"] = {"$gte": filters.start_date}
        elif filters.end_date:
            filter_query["start_time"] = {"$lte": filters.end_date}
            
        if filters.status:
            filter_query["status"] = filters.status
        if filters.queue_id:
            filter_query["queue_id"] = filters.queue_id
        if filters.operator_id:
            filter_query["operator_id"] = filters.operator_id
        if filters.caller_number:
            filter_query["caller_number"] = {"$regex": filters.caller_number, "$options": "i"}
        if filters.category:
            filter_query["category"] = filters.category
            
        cursor = self.calls.find(filter_query).sort("start_time", -1).skip(skip).limit(limit)
        calls = []
        async for call_data in cursor:
            calls.append(Call(**call_data))
        return calls
    
    async def get_call_by_id(self, call_id: str) -> Optional[Call]:
        call_data = await self.calls.find_one({"id": call_id})
        if call_data:
            return Call(**call_data)
        return None
    
    async def update_call(self, call_id: str, updates: CallUpdate) -> bool:
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        result = await self.calls.update_one({"id": call_id}, {"$set": update_dict})
        return result.modified_count > 0
    
    async def get_calls_count(self, filters: CallFilters) -> int:
        filter_query = {}
        
        if filters.start_date and filters.end_date:
            filter_query["start_time"] = {
                "$gte": filters.start_date,
                "$lte": filters.end_date
            }
        if filters.status:
            filter_query["status"] = filters.status
        if filters.queue_id:
            filter_query["queue_id"] = filters.queue_id
        if filters.operator_id:
            filter_query["operator_id"] = filters.operator_id
            
        return await self.calls.count_documents(filter_query)
    
    # Group operations
    async def get_groups(self) -> List[Group]:
        """Get all groups"""
        cursor = self.groups.find({})
        groups = await cursor.to_list(None)
        return [Group(**group) for group in groups]
    
    # Settings operations
    async def get_system_settings(self) -> Optional[SystemSettings]:
        settings_data = await self.settings.find_one()
        if settings_data:
            return SystemSettings(**settings_data)
        return None
    
    async def update_system_settings(self, settings: SystemSettingsUpdate, updated_by: str) -> SystemSettings:
        existing_settings = await self.get_system_settings()
        
        if existing_settings:
            # Update existing settings
            update_dict = {k: v for k, v in settings.dict().items() if v is not None}
            update_dict["updated_at"] = datetime.utcnow()
            update_dict["updated_by"] = updated_by
            
            await self.settings.update_one({}, {"$set": update_dict})
            
            # Return updated settings
            updated_settings_data = await self.settings.find_one()
            return SystemSettings(**updated_settings_data)
        else:
            # Create new settings
            new_settings = SystemSettings(
                **settings.dict(exclude_unset=True),
                updated_by=updated_by
            )
            await self.settings.insert_one(new_settings.dict())
            return new_settings
    
    # Statistics operations
    async def get_call_stats(self, query: StatsQuery) -> CallStats:
        """Calculate call statistics based on query parameters"""
        filter_query = {}
        
        # Date filtering based on period
        now = datetime.utcnow()
        if query.period == "today":
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            filter_query["start_time"] = {"$gte": start_of_day}
        elif query.period == "yesterday":
            start_of_yesterday = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_yesterday = now.replace(hour=0, minute=0, second=0, microsecond=0)
            filter_query["start_time"] = {"$gte": start_of_yesterday, "$lt": end_of_yesterday}
        elif query.period == "week":
            start_of_week = now - timedelta(days=7)
            filter_query["start_time"] = {"$gte": start_of_week}
        elif query.period == "month":
            start_of_month = now - timedelta(days=30)
            filter_query["start_time"] = {"$gte": start_of_month}
        elif query.period == "custom" and query.start_date and query.end_date:
            filter_query["start_time"] = {"$gte": query.start_date, "$lte": query.end_date}
        
        # Additional filters
        if query.queue_id:
            filter_query["queue_id"] = query.queue_id
        if query.operator_id:
            filter_query["operator_id"] = query.operator_id
        
        # Aggregate pipeline for statistics
        pipeline = [
            {"$match": filter_query},
            {
                "$group": {
                    "_id": None,
                    "total_calls": {"$sum": 1},
                    "answered_calls": {
                        "$sum": {"$cond": [{"$eq": ["$status", "answered"]}, 1, 0]}
                    },
                    "missed_calls": {
                        "$sum": {"$cond": [{"$eq": ["$status", "missed"]}, 1, 0]}
                    },
                    "abandoned_calls": {
                        "$sum": {"$cond": [{"$eq": ["$status", "abandoned"]}, 1, 0]}
                    },
                    "total_wait_time": {"$sum": "$wait_time"},
                    "total_talk_time": {"$sum": "$talk_time"},
                    "total_hold_time": {"$sum": "$hold_time"},
                    "calls_answered_within_20s": {
                        "$sum": {"$cond": [{"$lte": ["$wait_time", 20]}, 1, 0]}
                    }
                }
            }
        ]
        
        result = await self.calls.aggregate(pipeline).to_list(1)
        
        if result:
            data = result[0]
            total_calls = data.get("total_calls", 0)
            answered_calls = data.get("answered_calls", 0)
            
            avg_wait_time = data.get("total_wait_time", 0) / total_calls if total_calls > 0 else 0
            avg_talk_time = data.get("total_talk_time", 0) / answered_calls if answered_calls > 0 else 0
            avg_hold_time = data.get("total_hold_time", 0) / answered_calls if answered_calls > 0 else 0
            service_level = (data.get("calls_answered_within_20s", 0) / total_calls * 100) if total_calls > 0 else 0
            answer_rate = (answered_calls / total_calls * 100) if total_calls > 0 else 0
            
            return CallStats(
                total_calls=total_calls,
                answered_calls=answered_calls,
                missed_calls=data.get("missed_calls", 0),
                abandoned_calls=data.get("abandoned_calls", 0),
                avg_wait_time=round(avg_wait_time, 2),
                avg_talk_time=round(avg_talk_time, 2),
                avg_hold_time=round(avg_hold_time, 2),
                service_level=round(service_level, 2),
                answer_rate=round(answer_rate, 2)
            )
        
        return CallStats()
    
    async def get_operator_stats(self, query: StatsQuery) -> List[OperatorStats]:
        """Calculate operator statistics"""
        filter_query = {}
        
        # Apply date filters (same logic as call_stats)
        now = datetime.utcnow()
        if query.period == "today":
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            filter_query["start_time"] = {"$gte": start_of_day}
        elif query.period == "week":
            start_of_week = now - timedelta(days=7)
            filter_query["start_time"] = {"$gte": start_of_week}
        # Add other periods as needed
        
        if query.group_id:
            # Get operators in the group first
            operators = await self.get_operators(group_id=query.group_id)
            operator_ids = [op.id for op in operators]
            filter_query["operator_id"] = {"$in": operator_ids}
        elif query.operator_id:
            filter_query["operator_id"] = query.operator_id
        
        # Aggregate pipeline for operator statistics
        pipeline = [
            {"$match": filter_query},
            {
                "$group": {
                    "_id": "$operator_id",
                    "total_calls": {"$sum": 1},
                    "answered_calls": {
                        "$sum": {"$cond": [{"$eq": ["$status", "answered"]}, 1, 0]}
                    },
                    "missed_calls": {
                        "$sum": {"$cond": [{"$eq": ["$status", "missed"]}, 1, 0]}
                    },
                    "total_talk_time": {"$sum": "$talk_time"},
                    "total_hold_time": {"$sum": "$hold_time"}
                }
            }
        ]
        
        results = await self.calls.aggregate(pipeline).to_list(None)
        
        operator_stats = []
        for result in results:
            operator_id = result["_id"]
            if not operator_id:
                continue
                
            # Get operator details
            operator = await self.operators.find_one({"id": operator_id})
            if not operator:
                continue
                
            user = await self.get_user_by_id(operator["user_id"])
            group = await self.get_group_by_id(operator.get("group_id")) if operator.get("group_id") else None
            
            total_calls = result.get("total_calls", 0)
            answered_calls = result.get("answered_calls", 0)
            
            avg_talk_time = result.get("total_talk_time", 0) / answered_calls if answered_calls > 0 else 0
            avg_hold_time = result.get("total_hold_time", 0) / answered_calls if answered_calls > 0 else 0
            efficiency = (answered_calls / total_calls * 100) if total_calls > 0 else 0
            
            operator_stats.append(OperatorStats(
                operator_id=operator_id,
                operator_name=user.name if user else "Unknown",
                group_name=group.name if group else None,
                total_calls=total_calls,
                answered_calls=answered_calls,
                missed_calls=result.get("missed_calls", 0),
                avg_talk_time=round(avg_talk_time, 2),
                avg_hold_time=round(avg_hold_time, 2),
                total_talk_time=result.get("total_talk_time", 0),
                efficiency=round(efficiency, 2)
            ))
        
        return operator_stats
    
    async def get_queue_stats(self, query: StatsQuery) -> List[QueueStats]:
        """Calculate queue statistics"""
        filter_query = {}
        
        # Apply date filters
        now = datetime.utcnow()
        if query.period == "today":
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            filter_query["start_time"] = {"$gte": start_of_day}
        elif query.period == "week":
            start_of_week = now - timedelta(days=7)
            filter_query["start_time"] = {"$gte": start_of_week}
        
        if query.queue_id:
            filter_query["queue_id"] = query.queue_id
        
        # Aggregate pipeline for queue statistics
        pipeline = [
            {"$match": filter_query},
            {
                "$group": {
                    "_id": "$queue_id",
                    "total_calls": {"$sum": 1},
                    "answered_calls": {
                        "$sum": {"$cond": [{"$eq": ["$status", "answered"]}, 1, 0]}
                    },
                    "missed_calls": {
                        "$sum": {"$cond": [{"$eq": ["$status", "missed"]}, 1, 0]}
                    },
                    "abandoned_calls": {
                        "$sum": {"$cond": [{"$eq": ["$status", "abandoned"]}, 1, 0]}
                    },
                    "total_wait_time": {"$sum": "$wait_time"},
                    "total_talk_time": {"$sum": "$talk_time"},
                    "calls_answered_within_20s": {
                        "$sum": {"$cond": [{"$lte": ["$wait_time", 20]}, 1, 0]}
                    }
                }
            }
        ]
        
        results = await self.calls.aggregate(pipeline).to_list(None)
        
        queue_stats = []
        for result in results:
            queue_id = result["_id"]
            queue = await self.get_queue_by_id(queue_id)
            
            total_calls = result.get("total_calls", 0)
            answered_calls = result.get("answered_calls", 0)
            
            avg_wait_time = result.get("total_wait_time", 0) / total_calls if total_calls > 0 else 0
            avg_talk_time = result.get("total_talk_time", 0) / answered_calls if answered_calls > 0 else 0
            service_level = (result.get("calls_answered_within_20s", 0) / total_calls * 100) if total_calls > 0 else 0
            answer_rate = (answered_calls / total_calls * 100) if total_calls > 0 else 0
            
            queue_stats.append(QueueStats(
                queue_id=queue_id,
                queue_name=queue.name if queue else "Unknown Queue",
                total_calls=total_calls,
                answered_calls=answered_calls,
                missed_calls=result.get("missed_calls", 0),
                abandoned_calls=result.get("abandoned_calls", 0),
                avg_wait_time=round(avg_wait_time, 2),
                avg_talk_time=round(avg_talk_time, 2),
                service_level=round(service_level, 2),
                answer_rate=round(answer_rate, 2)
            ))
        
        return queue_stats
    
    async def close(self):
        """Close database connection"""
        self.client.close()