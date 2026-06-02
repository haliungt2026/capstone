import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SCHEMA = """
fact_orders       (id, customer_id, products, is_prepaid, customer_fee, delivery_fee,
                   delivery_phone_number, hot_aimag, sum_duureg, address,
                   effective_date, expiry_date, created_at, is_current)

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
- fact_orders болон fact_order_status: order_id-аар холбогдоно
- fact_orders болон dim_customers: customer_id-аар холбогдоно
- fact_order_status болон dim_drivers: driver_id-аар холбогдоно
"""

def generate_sql(question: str) -> str:
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=512,
        system=f"""Та PostgreSQL мэдээллийн сангийн SQL бичигч юм.
Зөвхөн цэвэр SQL query буцаана. Markdown, тайлбар, тайлал огт хэрэггүй.

Schema:
{SCHEMA}""",
        messages=[{"role": "user", "content": question}]
    )
    sql = message.content[0].text.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

def generate_response(question: str, sql: str, result: dict) -> str:
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=256,
        system="Та хүргэлтийн компанийн мэдээллийн шинжээч юм. Монгол хэлээр товч, ойлгомжтой хариулна уу.",
        messages=[{
            "role": "user",
            "content": f"""Асуулт: {question}
SQL: {sql}
Үр дүн: {result}
Хэрэглэгчид ойлгомжтой монгол хэлээр хариулна уу."""
        }]
    )
    return message.content[0].text.strip()