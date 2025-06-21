"""
Database dependency module to avoid circular imports
"""
from database import DatabaseManager

# Global database instance
_db_manager = None

def get_db():
    """Get the database manager instance"""
    return _db_manager

def set_db(db_manager):
    """Set the global database manager instance"""
    global _db_manager
    _db_manager = db_manager