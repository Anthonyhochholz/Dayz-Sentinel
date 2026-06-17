from sentinel_spr019.api.database import get_connection
from sentinel_spr019.api.models.economy_event import EconomyEvent, EconomyEventResponse
from typing import List, Optional


class EconomyEventsRepository:
    """Repository for economy events database operations"""

    @staticmethod
    def get_all(limit: int = 100, offset: int = 0, active_only: bool = False) -> tuple[List[dict], int]:
        """
        Get all economy events with pagination
        
        Args:
            limit: Number of events to return
            offset: Number of events to skip
            active_only: Filter for active events only
            
        Returns:
            Tuple of (events list, total count)
        """
        try:
            conn = get_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            where_clause = "WHERE active = 1" if active_only else ""
            
            # Get total count
            cursor.execute(f"SELECT COUNT(*) as count FROM economy_events {where_clause}")
            total = cursor.fetchone()["count"]
            
            # Get paginated events
            cursor.execute(
                f"""
                SELECT event_name, nominal, min_count, max_count, lifetime, restock,
                       saferadius, distanceradius, cleanupradius, position_mode, limit_mode, active
                FROM economy_events
                {where_clause}
                ORDER BY event_name ASC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )
            events = cursor.fetchall()
            conn.close()
            
            return events, total
        except Exception as e:
            raise Exception(f"Error fetching economy events: {str(e)}")

    @staticmethod
    def get_by_name(name: str) -> Optional[dict]:
        """
        Get a specific economy event by name
        
        Args:
            name: Event name
            
        Returns:
            Event dict or None
        """
        try:
            conn = get_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT event_name, nominal, min_count, max_count, lifetime, restock,
                       saferadius, distanceradius, cleanupradius, position_mode, limit_mode, active
                FROM economy_events
                WHERE event_name = ?
                """,
                (name,)
            )
            event = cursor.fetchone()
            conn.close()
            
            return event
        except Exception as e:
            raise Exception(f"Error fetching event {name}: {str(e)}")

    @staticmethod
    def search(query: str, limit: int = 50, active_only: bool = False) -> List[dict]:
        """
        Search events by name (case-insensitive)
        
        Args:
            query: Search query
            limit: Maximum results
            active_only: Filter for active events only
            
        Returns:
            List of matching events
        """
        try:
            conn = get_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            where_clause = "AND active = 1" if active_only else ""
            
            cursor.execute(
                f"""
                SELECT event_name, nominal, min_count, max_count, lifetime, restock,
                       saferadius, distanceradius, cleanupradius, position_mode, limit_mode, active
                FROM economy_events
                WHERE event_name LIKE ? {where_clause}
                ORDER BY event_name ASC
                LIMIT ?
                """,
                (f"%{query}%", limit)
            )
            events = cursor.fetchall()
            conn.close()
            
            return events
        except Exception as e:
            raise Exception(f"Error searching events: {str(e)}")

    @staticmethod
    def get_count(active_only: bool = False) -> int:
        """Get total count of events"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            where_clause = "WHERE active = 1" if active_only else ""
            cursor.execute(f"SELECT COUNT(*) FROM economy_events {where_clause}")
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
        except Exception as e:
            raise Exception(f"Error getting event count: {str(e)}")

    @staticmethod
    def toggle_active(name: str) -> bool:
        """
        Toggle active status of an event
        
        Args:
            name: Event name
            
        Returns:
            New active status
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get current status
            cursor.execute("SELECT active FROM economy_events WHERE event_name = ?", (name,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                raise Exception(f"Event {name} not found")
            
            current_status = result[0]
            new_status = 1 - current_status
            
            # Update status
            cursor.execute(
                "UPDATE economy_events SET active = ? WHERE event_name = ?",
                (new_status, name)
            )
            conn.commit()
            conn.close()
            
            return bool(new_status)
        except Exception as e:
            raise Exception(f"Error toggling event status: {str(e)}")


def dict_factory(cursor, row):
    """Convert database rows to dictionaries"""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}
