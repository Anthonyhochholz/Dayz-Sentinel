from sentinel_spr019.api.database import get_connection
from sentinel_spr019.api.models.economy_item import EconomyItem, EconomyItemResponse
from typing import List, Optional


class EconomyItemsRepository:
    """Repository for economy items database operations"""

    @staticmethod
    def get_all(limit: int = 50, offset: int = 0) -> tuple[List[dict], int]:
        """
        Get all economy items with pagination
        
        Args:
            limit: Number of items to return
            offset: Number of items to skip
            
        Returns:
            Tuple of (items list, total count)
        """
        try:
            conn = get_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute("SELECT COUNT(*) as count FROM economy_items")
            total = cursor.fetchone()["count"]
            
            # Get paginated items
            cursor.execute(
                """
                SELECT name, nominal, min_value, max_value, restock, lifetime
                FROM economy_items
                ORDER BY name ASC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )
            items = cursor.fetchall()
            conn.close()
            
            return items, total
        except Exception as e:
            raise Exception(f"Error fetching economy items: {str(e)}")

    @staticmethod
    def get_by_name(name: str) -> Optional[dict]:
        """
        Get a specific economy item by name
        
        Args:
            name: Item name
            
        Returns:
            Item dict or None
        """
        try:
            conn = get_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT name, nominal, min_value, max_value, restock, lifetime
                FROM economy_items
                WHERE name = ?
                """,
                (name,)
            )
            item = cursor.fetchone()
            conn.close()
            
            return item
        except Exception as e:
            raise Exception(f"Error fetching item {name}: {str(e)}")

    @staticmethod
    def search(query: str, limit: int = 50) -> List[dict]:
        """
        Search items by name (case-insensitive)
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching items
        """
        try:
            conn = get_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT name, nominal, min_value, max_value, restock, lifetime
                FROM economy_items
                WHERE name LIKE ?
                ORDER BY name ASC
                LIMIT ?
                """,
                (f"%{query}%", limit)
            )
            items = cursor.fetchall()
            conn.close()
            
            return items
        except Exception as e:
            raise Exception(f"Error searching items: {str(e)}")

    @staticmethod
    def get_count() -> int:
        """Get total count of items"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM economy_items")
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
        except Exception as e:
            raise Exception(f"Error getting item count: {str(e)}")


def dict_factory(cursor, row):
    """Convert database rows to dictionaries"""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}
