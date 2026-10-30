CREATE SCHEMA raw;

CREATE TABLE raw.orders_import (
    order_id      text,
    customer_id   text,
    customer_name text,
    email         text,
    phone         text,
    city          text,
    product       text,
    quantity      text,
    unit_price    text,
    amount        text,
    order_date    text,
    ship_date     text,
    status        text,
    age           text
);

COPY raw.orders_import
FROM '/docker-entrypoint-initdb.d/orders.csv'
WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

CREATE TABLE raw.orders (
    order_id      int,
    customer_id   int,
    customer_name text,
    email         text,
    phone         text,
    city          text,
    product       text,
    quantity      int,
    unit_price    numeric(12,2),
    amount        numeric(12,2),
    order_date    date,
    ship_date     date,
    status        text,
    age           int
);

INSERT INTO raw.orders
SELECT
    nullif(btrim(order_id), '')::int,
    nullif(btrim(customer_id), '')::int,
    nullif(btrim(customer_name), ''),
    nullif(btrim(email), ''),
    nullif(btrim(phone), ''),
    nullif(btrim(city), ''),
    nullif(btrim(product), ''),
    nullif(btrim(quantity), '')::int,
    replace(nullif(btrim(unit_price), ''), ',', '.')::numeric,
    replace(nullif(btrim(amount), ''), ',', '.')::numeric,
    nullif(btrim(order_date), '')::date,
    nullif(btrim(ship_date), '')::date,
    nullif(btrim(status), ''),
    nullif(btrim(age), '')::int
FROM raw.orders_import;

DROP TABLE raw.orders_import;