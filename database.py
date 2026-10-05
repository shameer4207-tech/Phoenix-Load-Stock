import sqlite3
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).with_name("phoenix.db")


def connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    con = connect()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT NOT NULL UNIQUE,
            dealer_name TEXT NOT NULL,
            order_date TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            model TEXT NOT NULL,
            order_qty INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS battery_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL UNIQUE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            qty_in INTEGER NOT NULL,
            transaction_date TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS loads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            load_no INTEGER NOT NULL,
            load_date TEXT NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS load_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            load_id INTEGER NOT NULL,
            model TEXT NOT NULL,
            qty_sent INTEGER NOT NULL,
            FOREIGN KEY(load_id) REFERENCES loads(id)
        )
    """)

    con.commit()
    con.close()


def add_model(model):
    model = model.strip()
    if not model:
        return
    con = connect()
    con.execute(
        "INSERT OR IGNORE INTO battery_models(model) VALUES (?)",
        (model,)
    )
    con.commit()
    con.close()


def add_stock(model, qty):
    model = model.strip()
    qty = int(qty)

    if not model:
        raise ValueError("Battery Model enter karein.")
    if qty <= 0:
        raise ValueError("Stock quantity 0 se zyada honi chahiye.")

    add_model(model)

    con = connect()
    try:
        con.execute(
            """INSERT INTO stock_transactions
               (model, qty_in, transaction_date)
               VALUES (?, ?, ?)""",
            (model, qty, date.today().isoformat())
        )
        con.commit()
    finally:
        con.close()


def add_order(order_no, dealer_name, order_date, items):
    order_no = str(order_no).strip()
    dealer_name = str(dealer_name).strip()
    order_date = str(order_date).strip()

    if not order_no:
        raise ValueError("Order No. enter karein.")
    if not dealer_name:
        raise ValueError("Dealer Name enter karein.")
    if not items:
        raise ValueError("Kam az kam ek model enter karein.")

    cleaned = []
    seen = {}

    for model, qty in items:
        model = str(model).strip()
        qty = int(qty)

        if not model:
            continue
        if qty <= 0:
            raise ValueError(f"{model}: quantity 0 se zyada honi chahiye.")

        # Same model accidentally repeated ho to quantities merge ho jayengi.
        seen[model] = seen.get(model, 0) + qty

    cleaned = list(seen.items())

    if not cleaned:
        raise ValueError("Kam az kam ek valid model/quantity enter karein.")

    con = connect()
    cur = con.cursor()

    try:
        existing = cur.execute(
            "SELECT id FROM orders WHERE order_no=?",
            (order_no,)
        ).fetchone()

        if existing:
            raise ValueError(
                f"Order No. {order_no} already maujood hai. "
                "New testing ke liye naya Order No. use karein."
            )

        cur.execute(
            """INSERT INTO orders(order_no, dealer_name, order_date)
               VALUES (?, ?, ?)""",
            (order_no, dealer_name, order_date)
        )
        oid = cur.lastrowid

        for model, qty in cleaned:
            cur.execute(
                "INSERT OR IGNORE INTO battery_models(model) VALUES (?)",
                (model,)
            )
            cur.execute(
                """INSERT INTO order_items(order_id, model, order_qty)
                   VALUES (?, ?, ?)""",
                (oid, model, qty)
            )

        con.commit()
        return oid

    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def get_dashboard_counts():
    con = connect()
    cur = con.cursor()

    total = cur.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    pending_batteries = cur.execute("""
        SELECT COALESCE(SUM(
            oi.order_qty - COALESCE(s.sent, 0)
        ), 0)
        FROM order_items oi
        LEFT JOIN (
            SELECT l.order_id, li.model, SUM(li.qty_sent) sent
            FROM load_items li
            JOIN loads l ON l.id = li.load_id
            GROUP BY l.order_id, li.model
        ) s
        ON s.order_id = oi.order_id AND s.model = oi.model
        WHERE oi.order_qty > COALESCE(s.sent, 0)
    """).fetchone()[0]

    pending_orders = cur.execute("""
        SELECT COUNT(DISTINCT oi.order_id)
        FROM order_items oi
        LEFT JOIN (
            SELECT l.order_id, li.model, SUM(li.qty_sent) sent
            FROM load_items li
            JOIN loads l ON l.id = li.load_id
            GROUP BY l.order_id, li.model
        ) s
        ON s.order_id = oi.order_id AND s.model = oi.model
        WHERE oi.order_qty > COALESCE(s.sent, 0)
    """).fetchone()[0]

    con.close()

    return {
        "total_orders": int(total or 0),
        "pending_orders": int(pending_orders or 0),
        "pending_batteries": int(pending_batteries or 0),
    }


def search_orders(query):
    query = str(query).strip()
    con = connect()

    rows = con.execute("""
        SELECT id, order_no, dealer_name, order_date
        FROM orders
        WHERE order_no LIKE ? OR dealer_name LIKE ?
        ORDER BY id DESC
    """, (f"%{query}%", f"%{query}%")).fetchall()

    con.close()
    return rows


def get_order_status(order_id):
    con = connect()
    cur = con.cursor()

    order = cur.execute("""
        SELECT id, order_no, dealer_name, order_date
        FROM orders WHERE id=?
    """, (order_id,)).fetchone()

    if not order:
        con.close()
        return None

    loads = cur.execute("""
        SELECT id, load_no, load_date
        FROM loads
        WHERE order_id=?
        ORDER BY load_no, id
    """, (order_id,)).fetchall()

    items = cur.execute("""
        SELECT model, order_qty
        FROM order_items
        WHERE order_id=?
        ORDER BY id
    """, (order_id,)).fetchall()

    sent = cur.execute("""
        SELECT li.model, l.load_no, SUM(li.qty_sent)
        FROM load_items li
        JOIN loads l ON l.id=li.load_id
        WHERE l.order_id=?
        GROUP BY li.model, l.load_no
    """, (order_id,)).fetchall()

    con.close()

    sent_map = {(r[0], r[1]): int(r[2] or 0) for r in sent}
    result = []

    for model, order_qty in items:
        load_values = [
            sent_map.get((model, l[1]), 0)
            for l in loads
        ]
        total_sent = sum(load_values)

        result.append({
            "model": model,
            "order_qty": int(order_qty),
            "loads": load_values,
            "total_sent": total_sent,
            "pending": max(int(order_qty) - total_sent, 0),
        })

    return {
        "order": order,
        "loads": loads,
        "items": result,
    }


def get_order_for_load(order_no):
    order_no = str(order_no).strip()

    con = connect()
    cur = con.cursor()

    order = cur.execute("""
        SELECT id, order_no, dealer_name, order_date
        FROM orders
        WHERE order_no=?
    """, (order_no,)).fetchone()

    if not order:
        con.close()
        return None

    items = cur.execute("""
        SELECT model, order_qty
        FROM order_items
        WHERE order_id=?
        ORDER BY id
    """, (order[0],)).fetchall()

    sent_rows = cur.execute("""
        SELECT li.model, COALESCE(SUM(li.qty_sent), 0)
        FROM load_items li
        JOIN loads l ON l.id=li.load_id
        WHERE l.order_id=?
        GROUP BY li.model
    """, (order[0],)).fetchall()

    sent_map = dict(sent_rows)

    stock_rows = cur.execute("""
        SELECT model, COALESCE(SUM(qty_in), 0)
        FROM stock_transactions
        GROUP BY model
    """).fetchall()
    stock_in = dict(stock_rows)

    used_rows = cur.execute("""
        SELECT model, COALESCE(SUM(qty_sent), 0)
        FROM load_items
        GROUP BY model
    """).fetchall()
    used_map = dict(used_rows)

    next_load = cur.execute("""
        SELECT COALESCE(MAX(load_no), 0) + 1
        FROM loads
        WHERE order_id=?
    """, (order[0],)).fetchone()[0]

    con.close()

    result_items = []

    for model, order_qty in items:
        sent = int(sent_map.get(model, 0) or 0)
        stock = (
            int(stock_in.get(model, 0) or 0)
            - int(used_map.get(model, 0) or 0)
        )

        result_items.append({
            "model": model,
            "order_qty": int(order_qty),
            "total_sent": sent,
            "pending": max(int(order_qty) - sent, 0),
            "stock_available": max(stock, 0),
        })

    return {
        "order": order,
        "items": result_items,
        "next_load_no": int(next_load),
    }


def save_load(order_id, load_no, load_date, items):
    """
    Save one load against an EXISTING order.
    This function never inserts a new order.
    """

    con = connect()
    cur = con.cursor()

    try:
        order = cur.execute(
            "SELECT id FROM orders WHERE id=?",
            (order_id,)
        ).fetchone()

        if not order:
            raise ValueError("Order nahi mila.")

        load_no = int(load_no)

        if load_no <= 0:
            raise ValueError("Load No. positive number hona chahiye.")

        if not items:
            raise ValueError("Kam az kam ek model ki quantity enter karein.")

        exists = cur.execute("""
            SELECT 1
            FROM loads
            WHERE order_id=? AND load_no=?
        """, (order_id, load_no)).fetchone()

        if exists:
            raise ValueError(
                f"Load {load_no} is order ke liye already save hai."
            )

        order_rows = cur.execute("""
            SELECT model, order_qty
            FROM order_items
            WHERE order_id=?
        """, (order_id,)).fetchall()

        order_map = dict(order_rows)

        sent_rows = cur.execute("""
            SELECT li.model, COALESCE(SUM(li.qty_sent), 0)
            FROM load_items li
            JOIN loads l ON l.id=li.load_id
            WHERE l.order_id=?
            GROUP BY li.model
        """, (order_id,)).fetchall()

        sent_map = dict(sent_rows)

        stock_rows = cur.execute("""
            SELECT model, COALESCE(SUM(qty_in), 0)
            FROM stock_transactions
            GROUP BY model
        """).fetchall()
        stock_in = dict(stock_rows)

        used_rows = cur.execute("""
            SELECT model, COALESCE(SUM(qty_sent), 0)
            FROM load_items
            GROUP BY model
        """).fetchall()
        used_map = dict(used_rows)

        cleaned_map = {}

        for model, qty in items:
            model = str(model).strip()
            qty = int(qty)

            if not model or qty <= 0:
                continue

            if model not in order_map:
                raise ValueError(f"{model} is order mein nahi hai.")

            cleaned_map[model] = cleaned_map.get(model, 0) + qty

        if not cleaned_map:
            raise ValueError("Kam az kam ek valid quantity enter karein.")

        cleaned = []

        for model, qty in cleaned_map.items():
            pending = (
                int(order_map[model])
                - int(sent_map.get(model, 0) or 0)
            )

            available = (
                int(stock_in.get(model, 0) or 0)
                - int(used_map.get(model, 0) or 0)
            )

            if qty > pending:
                raise ValueError(
                    f"{model}: pending sirf {pending} hai."
                )

            if qty > available:
                raise ValueError(
                    f"{model}: stock available sirf {available} hai."
                )

            cleaned.append((model, qty))

        cur.execute("""
            INSERT INTO loads(order_id, load_no, load_date)
            VALUES (?, ?, ?)
        """, (order_id, load_no, str(load_date).strip()))

        load_id = cur.lastrowid

        for model, qty in cleaned:
            cur.execute("""
                INSERT INTO load_items(load_id, model, qty_sent)
                VALUES (?, ?, ?)
            """, (load_id, model, qty))

        con.commit()
        return load_id

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()


def get_current_stock():
    """
    Global current stock:
    Total Stock In - Total Sent
    model wise.
    """
    con = connect()
    cur = con.cursor()

    rows = cur.execute("""
        SELECT
            m.model,
            COALESCE((
                SELECT SUM(st.qty_in)
                FROM stock_transactions st
                WHERE st.model=m.model
            ), 0) AS stock_in,
            COALESCE((
                SELECT SUM(li.qty_sent)
                FROM load_items li
                WHERE li.model=m.model
            ), 0) AS sent
        FROM battery_models m
        ORDER BY m.model COLLATE NOCASE
    """).fetchall()

    con.close()

    result = []

    for model, stock_in, sent in rows:
        stock_in = int(stock_in or 0)
        sent = int(sent or 0)
        result.append({
            "model": model,
            "stock_in": stock_in,
            "sent": sent,
            "remaining": max(stock_in - sent, 0),
        })

    return result


def get_load_history():
    """
    Every saved load/model entry, newest load records first.
    """
    con = connect()

    rows = con.execute("""
        SELECT
            o.order_no,
            o.dealer_name,
            l.load_no,
            l.load_date,
            li.model,
            li.qty_sent
        FROM load_items li
        JOIN loads l ON l.id=li.load_id
        JOIN orders o ON o.id=l.order_id
        ORDER BY l.id DESC, li.id ASC
    """).fetchall()

    con.close()

    return [
        {
            "order_no": r[0],
            "dealer_name": r[1],
            "load_no": int(r[2]),
            "load_date": r[3],
            "model": r[4],
            "qty_sent": int(r[5]),
        }
        for r in rows
    ]
