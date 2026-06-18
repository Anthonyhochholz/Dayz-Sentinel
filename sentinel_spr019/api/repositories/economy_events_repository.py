import logging
from typing import List, Optional

from sentinel_spr019.api.database import get_connection, dict_factory

LOGGER = logging.getLogger(__name__)

_SELECT_EVENT = (
    "SELECT event_name, nominal, min_count, max_count, lifetime, restock,"
    " saferadius, distanceradius, cleanupradius, position_mode, limit_mode, active"
    " FROM economy_events"
)


class EconomyEventsRepository:
    """Repository for economy events database operations"""

    @staticmethod
    def get_all(limit: int = 100, offset: int = 0, active_only: bool = False) -> tuple[List[dict], int]:
        """
        Get all economy events with pagination.

        Args:
            limit: Number of events to return
            offset: Number of events to skip
            active_only: Filter for active events only

        Returns:
            Tuple of (events list, total count)
        """
        conn = None
        try:
            conn = get_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT COUNT(*) as count FROM economy_events WHERE active = 1")
                total = cursor.fetchone()["count"]
                cursor.execute(
                    _SELECT_EVENT + " WHERE active = 1 ORDER BY event_name ASC LIMIT ? OFFSET ?",
                    (limit, offset),
                )
            else:
                cursor.execute("SELECT COUNT(*) as count FROM economy_events")
                total = cursor.fetchone()["count"]
                cursor.execute(
                    _SELECT_EVENT + " ORDER BY event_name ASC LIMIT ? OFFSET ?",
                    (limit, offset),
                )
            events = cursor.fetchall()
        finally:
            if conn is not None:
                conn.close()
        return events, total

    @staticmethod
    def get_by_name(name: str) -> Optional[dict]:
        """
        Get a specific economy event by name.

        Args:
            name: Event name

        Returns:
            Event dict or None
        """
        conn = None
        try:
            conn = get_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute(
                _SELECT_EVENT + " WHERE event_name = ?",
                (name,),
            )
            event = cursor.fetchone()
        finally:
            if conn is not None:
                conn.close()
        return event

    @staticmethod
    def search(query: str, limit: int = 50, offset: int = 0, active_only: bool = False) -> List[dict]:
        """
        Search events by name (case-insensitive).

        Args:
            query: Search query
            limit: Maximum results
            offset: Number of results to skip
            active_only: Filter for active events only

        Returns:
            List of matching events
        """
        conn = None
        try:
            conn = get_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            if active_only:
                cursor.execute(
                    _SELECT_EVENT
                    + " WHERE event_name LIKE ? AND active = 1"
                    " ORDER BY event_name ASC LIMIT ? OFFSET ?",
                    (f"%{query}%", limit, offset),
                )
            else:
                cursor.execute(
                    _SELECT_EVENT
                    + " WHERE event_name LIKE ?"
                    " ORDER BY event_name ASC LIMIT ? OFFSET ?",
                    (f"%{query}%", limit, offset),
                )
            events = cursor.fetchall()
        finally:
            if conn is not None:
                conn.close()
        return events

    @staticmethod
    def get_count(active_only: bool = False) -> int:
        """Get total count of events."""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT COUNT(*) FROM economy_events WHERE active = 1")
            else:
                cursor.execute("SELECT COUNT(*) FROM economy_events")
            count = cursor.fetchone()[0]
        finally:
            if conn is not None:
                conn.close()
        return count

    @staticmethod
    def toggle_active(name: str) -> bool:
        """
        Toggle active status of an event.

        Args:
            name: Event name

        Returns:
            New active status
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT active FROM economy_events WHERE event_name = ?", (name,))
            result = cursor.fetchone()
            if not result:
                raise Exception(f"Event {name} not found")
            new_status = 1 - result[0]
            cursor.execute(
                "UPDATE economy_events SET active = ? WHERE event_name = ?",
                (new_status, name),
            )
            conn.commit()
        finally:
            if conn is not None:
                conn.close()
        return bool(new_status)
