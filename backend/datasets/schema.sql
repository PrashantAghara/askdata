DROP SCHEMA IF EXISTS demo CASCADE;
CREATE SCHEMA demo;

CREATE TABLE demo.customers (
    customer_id   integer PRIMARY KEY,
    full_name     text NOT NULL,
    email         text NOT NULL UNIQUE,
    phone         text,
    city          text,
    state         text,
    signup_date   date NOT NULL,
    cust_stat_cd  char(1) NOT NULL
);

CREATE TABLE demo.categories (
    category_id         integer PRIMARY KEY,
    name                text NOT NULL,
    parent_category_id  integer REFERENCES demo.categories (category_id)
);

CREATE TABLE demo.products (
    product_id   integer PRIMARY KEY,
    category_id  integer NOT NULL REFERENCES demo.categories (category_id),
    name         text NOT NULL,
    sku          text NOT NULL UNIQUE,
    unit_price   numeric(10, 2) NOT NULL,
    cost_amt     numeric(10, 2) NOT NULL,
    is_active    boolean NOT NULL
);

CREATE TABLE demo.orders (
    order_id      integer PRIMARY KEY,
    customer_id   integer NOT NULL REFERENCES demo.customers (customer_id),
    order_date    timestamptz NOT NULL,
    ord_sts       char(1) NOT NULL,
    channel       text NOT NULL,
    total_amount  numeric(12, 2) NOT NULL
);

CREATE TABLE demo.order_items (
    order_item_id  integer PRIMARY KEY,
    order_id       integer NOT NULL REFERENCES demo.orders (order_id),
    product_id     integer NOT NULL REFERENCES demo.products (product_id),
    qty            integer NOT NULL,
    unit_price     numeric(10, 2) NOT NULL,
    disc_pct       numeric(5, 2) NOT NULL
);

CREATE TABLE demo.payments (
    payment_id  integer PRIMARY KEY,
    order_id    integer NOT NULL REFERENCES demo.orders (order_id),
    method      text NOT NULL,
    paid_amt    numeric(12, 2) NOT NULL,
    paid_at     timestamptz,
    pmt_sts     char(1) NOT NULL
);

CREATE TABLE demo.reviews (
    review_id    integer PRIMARY KEY,
    product_id   integer NOT NULL REFERENCES demo.products (product_id),
    customer_id  integer NOT NULL REFERENCES demo.customers (customer_id),
    rating       smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text  text,
    created_at   timestamptz NOT NULL
);

CREATE INDEX ON demo.orders (customer_id);
CREATE INDEX ON demo.orders (order_date);
CREATE INDEX ON demo.order_items (order_id);
CREATE INDEX ON demo.order_items (product_id);
CREATE INDEX ON demo.payments (order_id);
CREATE INDEX ON demo.reviews (product_id);