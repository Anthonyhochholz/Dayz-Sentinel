from sentinel_spr019.api.database import get_connection

class EconomyRepository:
    def get_items(self, limit=100):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, nominal, lifetime, restock FROM economy_items LIMIT ?", (limit,))
        cols=[d[0] for d in cur.description]
        rows=[dict(zip(cols,row)) for row in cur.fetchall()]
        conn.close()
        return rows
