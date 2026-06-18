import logging
from typing import List, Optional

from sentinel_spr019.api.database import get_connection, dict_factory

LOGGER = logging.getLogger(__name__)


class EconomyItemsRepository:
    """Repository for economy items database operations"""

    @staticmethod
    def get_all(limit: int = 50, offset: int = 0) -> tuple[List[dict], int]:
        """
        Get all economy items with pagination.

        Args:
            limit: Number of items to return
            offset: Number of items to skip

        Returns:
            Tuple of (items list, total count)
        """
        conn = None
        try:
            conn = get_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM economy_items")
            total = cursor.fetchone()["count"]
            cursor.execute(
                """
                SELECT name, nominal, min_value, max_value, restock, lifetime
                FROM economy_items
                ORDER BY name ASC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            items = cursor.fetchall()
        finally:
            if conn is not None:
                conn.close()
        return items, total

    @staticmethod
    def get_by_name(name: str) -> Optional[dict]:
        """
        Get a specific economy item by name.

        Args:
            name: Item name

        Returns:
            Item dict or None
        """
        conn = None
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
                (name,),
            )
            item = cursor.fetchone()
        finally:
            if conn is not None:
                conn.close()
        return item

    @staticmethod
    def search(query: str, limit: int = 50, offset: int = 0) -> List[dict]:
        """
        Search items by name (case-insensitive).

        Args:
            query: Search query
            limit: Maximum results
            offset: Number of results to skip

        Returns:
            List of matching items
        """
        conn = None
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
                LIMIT ? OFFSET ?
                """,
                (f"%{query}%", limit, offset),
            )
            items = cursor.fetchall()
        finally:
            if conn is not None:
                conn.close()
        return items

    @staticmethod
    def get_count() -> int:
        """Get total count of items."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM economy_items")
            count = cursor.fetchone()[0]
        finally:
            if conn is not None:
                conn.close()
        return count
