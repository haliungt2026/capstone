import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SCHEMA = """
fact_orders       (id, customer_id, products, is_prepaid, customer_fee, delivery_fee,
                   delivery_phone_number, hot_aimag, sum_duureg, address,
                   effective_date, expiry_date, created_at, is_current)
                   -- products нь JSON array: [{"name": "...", "qty": 1, "price": 15000.0}]
                   -- задлахад: jsonb_array_elements(products::jsonb) AS p
                   -- нэр гаргахад: p->>'name'
                   -- тоо гаргахад: (p->>'qty')::numeric

fact_order_status (id, order_id, driver_id, status, note,
                   effective_date, expiry_date, created_at, is_current)

dim_customers     (id, customer_name, registry_number, phone_number, email,
                   effective_date, expiry_date, created_at, is_current)

dim_drivers       (id, firstname, lastname, registry_number, phone_number, email,
                   plate_number, bank_account, birthday,
                   effective_date, expiry_date, created_at, is_current)

Тэмдэглэл:
- is_current = true байвал идэвхтэй бичлэг
- fact_order_status.status утгууд: 'шинэ', 'хүргэсэн', 'хойшилсон', 'цуцалсан', 'бусад'
- fact_orders болон fact_order_status: fact_orders.id = fact_order_status.order_id
- fact_orders болон dim_customers: customer_id-аар холбогдоно
- fact_order_status болон dim_drivers: driver_id-аар холбогдоно
"""

def _build_history(history: list) -> list:
    messages = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
    return messages

def generate_sql(question: str, history: list = []) -> str:
    messages = _build_history(history)
    messages.append({"role": "user", "content": question})

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=f"""Та PostgreSQL мэдээллийн сангийн SQL бичигч юм.
Зөвхөн цэвэр SQL query буцаана. Markdown, тайлбар, тайлал огт хэрэггүй.

Schema:
{SCHEMA}""",
        messages=messages
    )
    sql = message.content[0].text.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

def generate_response(question: str, sql: str, result: dict, history: list = []) -> str:
    messages = _build_history(history)
    messages.append({
        "role": "user",
        "content": f"""Асуулт: {question}
SQL: {sql}
Үр дүн: {result}
Хэрэглэгчид ойлгомжтой монгол хэлээр хариулна уу."""
    })

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system="Та хүргэлтийн компанийн мэдээллийн шинжээч юм. Монгол хэлээр товч, ойлгомжтой хариулна уу.",
        messages=messages
    )
    return message.content[0].text.strip()
