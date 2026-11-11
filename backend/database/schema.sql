
CREATE DATABASE IF NOT EXISTS queryai_db;
USE queryai_db;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT DEFAULT 0
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    order_total DECIMAL(10,2) NOT NULL,
    order_date DATE NOT NULL,
    status VARCHAR(30) DEFAULT 'Completed',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TEMPORARY TABLE numbers (n INT PRIMARY KEY);

INSERT INTO numbers (n)
SELECT ones.n + tens.n * 10 + hundreds.n * 100 + 1
FROM
(SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL
 SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL
 SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
CROSS JOIN
(SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL
 SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL
 SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) tens
CROSS JOIN
(SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL
 SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL
 SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) hundreds;

INSERT INTO customers (name, email, city)
SELECT
    CONCAT('Customer ', LPAD(n, 3, '0')),
    CONCAT('customer', n, '@example.com'),
    ELT(1 + MOD(n - 1, 6),
        'Hyderabad', 'Vijayawada', 'Chennai',
        'Bangalore', 'Delhi', 'Mumbai')
FROM numbers WHERE n <= 60;

INSERT INTO products (product_name, category, price, stock_quantity)
SELECT
    CONCAT('Product ', LPAD(n, 3, '0')),
    ELT(1 + MOD(n - 1, 5),
        'Electronics', 'Clothing', 'Books',
        'Accessories', 'Home'),
    100 + (n * 25.50),
    MOD(n * 7, 40)
FROM numbers WHERE n <= 60;

INSERT INTO orders (
    customer_id, product_id, quantity,
    order_total, order_date, status
)
SELECT
    1 + MOD(n * 7, 60),
    1 + MOD(n * 11, 60),
    1 + MOD(n, 5),
    p.price * (1 + MOD(n, 5)),
    DATE_SUB(CURDATE(), INTERVAL MOD(n, 90) DAY),
    ELT(1 + MOD(n - 1, 4),
        'Completed', 'Pending', 'Shipped', 'Cancelled')
FROM numbers
JOIN products p
    ON p.product_id = 1 + MOD(n * 11, 60)
WHERE n <= 150;

DROP TEMPORARY TABLE numbers;

SELECT 'customers' AS table_name, COUNT(*) AS total FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders;

SELECT * FROM customers LIMIT 5;
SELECT * FROM products LIMIT 5;
SELECT * FROM orders LIMIT 5;
