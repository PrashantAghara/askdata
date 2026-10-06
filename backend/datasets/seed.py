import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import psycopg
from faker import Faker
from psycopg import sql
from sqlalchemy.engine import make_url

from app.config import get_settings

SEED = 42
N_CUSTOMERS = 500
N_PRODUCTS = 120
N_ORDERS = 3000
START = datetime(2025, 1, 1, tzinfo=timezone.utc)
END = datetime(2026, 9, 30, tzinfo=timezone.utc)
HERE = Path(__file__).parent

random.seed(SEED)
Faker.seed(SEED)
fake = Faker("en_IN")

# ---------- categories ----------
TOP = ["Electronics", "Fashion", "Home & Kitchen", "Books", "Sports"]
CHILDREN = {
    "Electronics": ["Mobiles", "Laptops", "Audio"],
    "Fashion": ["Men's Wear", "Women's Wear"],
    "Home & Kitchen": ["Appliances", "Furniture"],
    "Books": ["Fiction", "Non-fiction"],
    "Sports": ["Fitness"],
}
CATALOG = {  # leaf category -> (product nouns, price range in INR)
    "Mobiles": (["Smartphone", "5G Phone", "Feature Phone"], (6999, 79999)),
    "Laptops": (["Laptop", "Ultrabook", "Gaming Laptop"], (29999, 149999)),
    "Audio": (["Earbuds", "Headphones", "Bluetooth Speaker"], (799, 14999)),
    "Men's Wear": (["Shirt", "Jeans", "Jacket"], (499, 4999)),
    "Women's Wear": (["Kurta", "Dress", "Saree"], (599, 7999)),
    "Appliances": (["Mixer Grinder", "Air Fryer", "Microwave"], (1999, 19999)),
    "Furniture": (["Office Chair", "Bookshelf", "Sofa"], (2499, 39999)),
    "Fiction": (["Novel", "Thriller", "Short Stories"], (199, 799)),
    "Non-fiction": (["Biography", "Self-help Book", "History Book"], (249, 999)),
    "Fitness": (["Yoga Mat", "Dumbbell Set", "Running Shoes"], (399, 6999)),
}
BRANDS = ["Aurora", "Nimbus", "Vertex", "Zenith", "Orbit", "Pinnacle", "Lumen", "Crest"]
REVIEW_TEXT = {
    5: [
        "Excellent quality, totally worth it.",
        "Loved it, would buy again.",
        "Fast delivery and great product.",
    ],
    4: ["Good product, minor issues only.", "Value for money.", "Works well, happy with it."],
    3: ["Average, does the job.", "Okay for the price.", "Nothing special."],
    2: ["Not as described.", "Quality could be better.", "Disappointed with the finish."],
    1: ["Stopped working quickly.", "Poor quality, would not recommend.", "Waste of money."],
}


def rand_dt(lo: datetime, hi: datetime) -> datetime:
    return lo + timedelta(seconds=random.randint(0, int((hi - lo).total_seconds())))


def build_data():
    categories, cat_id = [], {}
    for name in TOP:
        cat_id[name] = len(categories) + 1
        categories.append((cat_id[name], name, None))
    for parent in TOP:
        for name in CHILDREN[parent]:
            cat_id[name] = len(categories) + 1
            categories.append((cat_id[name], name, cat_id[parent]))

    leaves = list(CATALOG)
    products = []
    for pid in range(1, N_PRODUCTS + 1):
        leaf = leaves[(pid - 1) % len(leaves)]
        nouns, (lo, hi) = CATALOG[leaf]
        price = Decimal(random.randint(lo, hi) // 10 * 10 + 9)
        cost = (price * Decimal(str(round(random.uniform(0.55, 0.8), 2)))).quantize(Decimal("0.01"))
        name = f"{random.choice(BRANDS)} {random.choice(nouns)} {random.randint(100, 999)}"
        products.append(
            (pid, cat_id[leaf], name, f"SKU-{pid:05d}", price, cost, random.random() > 0.05)
        )

    customers = []
    for cid in range(1, N_CUSTOMERS + 1):
        signup = fake.date_between(start_date=date(2024, 1, 1), end_date=date(2026, 8, 31))
        customers.append(
            (
                cid,
                fake.name(),
                f"user{cid}@example.com",
                fake.phone_number(),
                fake.city(),
                fake.state(),
                signup,
                random.choices("AIB", weights=[85, 10, 5])[0],
            )
        )
    weights = [random.paretovariate(1.4) for _ in customers]  # a few heavy buyers

    orders, items, payments, reviews = [], [], [], []
    item_id = pay_id = rev_id = 0
    for oid in range(1, N_ORDERS + 1):
        cust = random.choices(customers, weights=weights)[0]
        signup_dt = datetime.combine(cust[6], datetime.min.time(), tzinfo=timezone.utc)
        odt = rand_dt(max(START, signup_dt), END)

        if (END - odt).days < 10:
            status = random.choices("PSD", weights=[40, 40, 20])[0]
        else:
            status = random.choices("DCR", weights=[80, 12, 8])[0]

        n_items = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
        total = Decimal("0")
        order_products = []
        for p in random.sample(products, n_items):
            item_id += 1
            qty = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
            disc = Decimal(random.choice([0, 0, 0, 5, 10, 15, 20]))
            total += p[4] * qty * (Decimal(100) - disc) / Decimal(100)
            items.append((item_id, oid, p[0], qty, p[4], disc))
            order_products.append(p[0])
        total = total.quantize(Decimal("0.01"))
        channel = random.choices(["web", "app", "marketplace"], weights=[45, 40, 15])[0]
        orders.append((oid, cust[0], odt, status, channel, total))

        method = random.choices(["UPI", "card", "COD", "wallet"], weights=[45, 30, 15, 10])[0]
        paid_at = odt + timedelta(minutes=random.randint(1, 90))
        if status in ("D", "S"):
            pay_id += 1
            payments.append((pay_id, oid, method, total, paid_at, "S"))
        elif status == "R":
            pay_id += 1
            payments.append((pay_id, oid, method, total, paid_at, "R"))
        elif status == "C":
            pay_id += 1
            if random.random() < 0.5:
                payments.append((pay_id, oid, method, Decimal("0.00"), paid_at, "F"))
            else:
                payments.append((pay_id, oid, method, total, paid_at, "R"))
        # pending orders have no payment yet

        if status == "D":
            for prod_id in order_products:
                if random.random() < 0.25:
                    rev_id += 1
                    rating = random.choices([1, 2, 3, 4, 5], weights=[5, 7, 15, 33, 40])[0]
                    created = min(END, odt + timedelta(days=random.randint(3, 20)))
                    reviews.append(
                        (
                            rev_id,
                            prod_id,
                            cust[0],
                            rating,
                            random.choice(REVIEW_TEXT[rating]),
                            created,
                        )
                    )

    return {
        "categories": categories,
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": items,
        "payments": payments,
        "reviews": reviews,
    }


COLUMNS = {
    "categories": ["category_id", "name", "parent_category_id"],
    "customers": [
        "customer_id",
        "full_name",
        "email",
        "phone",
        "city",
        "state",
        "signup_date",
        "cust_stat_cd",
    ],
    "products": ["product_id", "category_id", "name", "sku", "unit_price", "cost_amt", "is_active"],
    "orders": ["order_id", "customer_id", "order_date", "ord_sts", "channel", "total_amount"],
    "order_items": ["order_item_id", "order_id", "product_id", "qty", "unit_price", "disc_pct"],
    "payments": ["payment_id", "order_id", "method", "paid_amt", "paid_at", "pmt_sts"],
    "reviews": ["review_id", "product_id", "customer_id", "rating", "review_text", "created_at"],
}
LOAD_ORDER = ["categories", "customers", "products", "orders", "order_items", "payments", "reviews"]


def load(cur, table: str, rows: list) -> None:
    stmt = sql.SQL("COPY demo.{} ({}) FROM STDIN").format(
        sql.Identifier(table), sql.SQL(", ").join(map(sql.Identifier, COLUMNS[table]))
    )
    with cur.copy(stmt) as copy:
        for row in rows:
            copy.write_row(row)


def main() -> None:
    settings = get_settings()
    if not settings.demo_database_url:
        raise SystemExit("Set DEMO_DATABASE_URL in backend/.env first")

    owner = make_url(settings.database_url)
    ro = make_url(settings.demo_database_url)
    owner_role = owner.username.split(".")[0]
    role = ro.username.split(".")[0]
    password = ro.password

    if role == owner_role:
        raise SystemExit(
            f"DEMO_DATABASE_URL uses the same role as DATABASE_URL ('{role}'). "
            "Use a separate read-only role such as askdata_ro, otherwise this script "
            "would change the permissions of your main role."
        )
    if not password:
        raise SystemExit("DEMO_DATABASE_URL needs a password for the read-only role")

    owner_conninfo = owner.set(drivername="postgresql").render_as_string(hide_password=False)
    data = build_data()

    with psycopg.connect(owner_conninfo) as conn, conn.cursor() as cur:
        cur.execute((HERE / "schema.sql").read_text(encoding="utf-8"))
        for table in LOAD_ORDER:
            load(cur, table, data[table])
            cur.execute(sql.SQL("ANALYZE demo.{}").format(sql.Identifier(table)))

        # read-only role
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,))
        if cur.fetchone() is None:
            cur.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(role)))
        r = sql.Identifier(role)
        cur.execute(
            sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(r, sql.Literal(password))
        )
        for stmt in [
            "GRANT USAGE ON SCHEMA demo TO {r}",
            "GRANT SELECT ON ALL TABLES IN SCHEMA demo TO {r}",
            "ALTER DEFAULT PRIVILEGES IN SCHEMA demo GRANT SELECT ON TABLES TO {r}",
            "ALTER ROLE {r} SET default_transaction_read_only = on",
            "ALTER ROLE {r} SET statement_timeout = '15s'",
            "ALTER ROLE {r} SET search_path = demo",
        ]:
            cur.execute(sql.SQL(stmt).format(r=r))

        print("loaded:")
        for table in LOAD_ORDER:
            cur.execute(sql.SQL("SELECT count(*) FROM demo.{}").format(sql.Identifier(table)))
            print(f"  {table:12s} {cur.fetchone()[0]}")
        print(f"read-only role: {role}")


if __name__ == "__main__":
    main()
