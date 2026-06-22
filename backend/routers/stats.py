from fastapi import APIRouter
from database import get_connection
from datetime import date

router = APIRouter(prefix="/api/stats", tags=["Stats"])

@router.get("")
def get_stats():
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Нийт захиалга
        cur.execute("SELECT COUNT(*) FROM fact_orders WHERE is_current = true")
        total_orders = cur.fetchone()[0]

        # Хүргэгдсэн тоо
        cur.execute("""
            SELECT COUNT(*) FROM fact_order_status
            WHERE status = 'хүргэсэн' AND is_current = true
        """)
        delivered = cur.fetchone()[0]

        # Хойшилсон тоо
        cur.execute("""
            SELECT COUNT(*) FROM fact_order_status
            WHERE status = 'хойшилсон' AND is_current = true
        """)
        delayed = cur.fetchone()[0]

        # Цуцалсан тоо
        cur.execute("""
            SELECT COUNT(*) FROM fact_order_status
            WHERE status = 'цуцалсан' AND is_current = true
        """)
        cancelled = cur.fetchone()[0]

        # Өнөөдрийн захиалга
        cur.execute("""
            SELECT COUNT(*) FROM fact_orders
            WHERE DATE(created_at) = CURRENT_DATE AND is_current = true
        """)
        today_orders = cur.fetchone()[0]

        # Хүргэгдсэн хувь
        delivered_pct = round(delivered / total_orders * 100, 1) if total_orders else 0

        cur.close()
        return {
            "total_orders": total_orders,
            "delivered": delivered,
            "delivered_pct": delivered_pct,
            "delayed": delayed,
            "cancelled": cancelled,
            "today_orders": today_orders
        }
    finally:
        conn.close()