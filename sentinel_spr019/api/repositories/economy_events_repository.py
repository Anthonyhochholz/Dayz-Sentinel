from sentinel_spr019.api.database import get_connection


class EconomyEventsRepository:
    def get_events(self, limit: int = 100, active_only: bool = False):
        conn = get_connection()
        cur = conn.cursor()
        if active_only:
            cur.execute(
                "SELECT * FROM economy_events WHERE active = 1 ORDER BY event_name LIMIT ?",
                (limit,)
            )
        else:
            cur.execute(
                "SELECT * FROM economy_events ORDER BY event_name LIMIT ?",
                (limit,)
            )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        conn.close()
        return rows

    def get_event_by_name(self, event_name: str):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM economy_events WHERE event_name = ?",
            (event_name,)
        )
        cols = [d[0] for d in cur.description]
        row = cur.fetchone()
        conn.close()
        return dict(zip(cols, row)) if row else None
