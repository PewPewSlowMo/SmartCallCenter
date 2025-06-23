from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List
from datetime import datetime

from models import User, APIResponse
from database import DatabaseManager
from auth import get_current_active_user, require_admin
from db import get_db