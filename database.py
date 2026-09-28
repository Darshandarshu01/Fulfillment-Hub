import sqlite3

connection = sqlite3.connect("fulfillment.db")


# =========================================================
# ORDERS TABLE
# =========================================================

connection.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT,
    customer_name TEXT,
    priority TEXT,
    status TEXT,
    deadline TEXT
)
""")


# =========================================================
# INVENTORY TABLE
# =========================================================

connection.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT,
    variant TEXT,
    main_stock INTEGER,
    secondary_stock INTEGER,
    minimum_stock INTEGER
)
""")


# =========================================================
# PICKING TABLE
# =========================================================

connection.execute("""
CREATE TABLE IF NOT EXISTS picking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_name TEXT,
    variant TEXT,
    required_quantity INTEGER,
    picked_quantity INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY (order_id) REFERENCES orders(id)
)
""")


# =========================================================
# PACKING TABLE
# =========================================================

connection.execute("""
CREATE TABLE IF NOT EXISTS packing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    box_type TEXT,
    packed_by TEXT,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY (order_id) REFERENCES orders(id)
)
""")


# =========================================================
# STAGING & SHIPPING TABLE
# =========================================================

connection.execute("""
CREATE TABLE IF NOT EXISTS staging (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    staging_location TEXT,
    courier TEXT,
    pickup_time TEXT,
    status TEXT DEFAULT 'Ready for Pickup',
    FOREIGN KEY (order_id) REFERENCES orders(id)
)
""")


# =========================================================
# EXCEPTIONS TABLE
# =========================================================

connection.execute("""
CREATE TABLE IF NOT EXISTS exceptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    issue_type TEXT,
    description TEXT,
    priority TEXT,
    status TEXT DEFAULT 'Open',
    created_at TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(id)
)
""")


# =========================================================
# SAMPLE ORDERS
# =========================================================

orders = [
    ("ORD-1001", "Rahul", "Priority", "Picking", "Today 5:00 PM"),
    ("ORD-1002", "Ananya", "Normal", "Processing", "Tomorrow"),
    ("ORD-1003", "Vikram", "Priority", "Packing", "Today 4:30 PM"),
    ("ORD-1004", "Priya", "Normal", "Staged", "Today 6:00 PM"),
    ("ORD-1005", "Arjun", "Priority", "Processing", "Today 5:30 PM")
]

existing_orders = connection.execute(
    "SELECT COUNT(*) FROM orders"
).fetchone()[0]

if existing_orders == 0:

    connection.executemany("""
        INSERT INTO orders
        (order_number, customer_name, priority, status, deadline)
        VALUES (?, ?, ?, ?, ?)
    """, orders)


# =========================================================
# SAMPLE INVENTORY
# =========================================================

inventory = [
    ("T-Shirt", "Black - M", 25, 10, 15),
    ("T-Shirt", "White - L", 8, 20, 15),
    ("Shoes", "Black - 9", 5, 30, 10),
    ("Shoes", "White - 8", 18, 5, 10),
    ("Headphones", "Wireless", 12, 8, 10),
    ("Backpack", "Blue", 4, 25, 10)
]

existing_inventory = connection.execute(
    "SELECT COUNT(*) FROM inventory"
).fetchone()[0]

if existing_inventory == 0:

    connection.executemany("""
        INSERT INTO inventory
        (product_name, variant, main_stock, secondary_stock, minimum_stock)
        VALUES (?, ?, ?, ?, ?)
    """, inventory)


# =========================================================
# SAMPLE PICKING ITEMS
# =========================================================

picking_items = [
    (1, "T-Shirt", "Black - M", 2, 0, "Pending"),
    (1, "Headphones", "Wireless", 1, 0, "Pending"),
    (2, "Shoes", "White - 8", 1, 0, "Pending"),
    (3, "T-Shirt", "White - L", 2, 0, "Pending"),
    (5, "Backpack", "Blue", 1, 0, "Pending")
]

existing_picking = connection.execute(
    "SELECT COUNT(*) FROM picking"
).fetchone()[0]

if existing_picking == 0:

    connection.executemany("""
        INSERT INTO picking
        (order_id, product_name, variant,
         required_quantity, picked_quantity, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, picking_items)


# =========================================================
# SAMPLE PACKING RECORDS
# =========================================================

packing_items = [
    (1, "Not Selected", "", "Pending"),
    (2, "Not Selected", "", "Pending"),
    (3, "Not Selected", "", "Pending"),
    (4, "Not Selected", "", "Pending"),
    (5, "Not Selected", "", "Pending")
]

existing_packing = connection.execute(
    "SELECT COUNT(*) FROM packing"
).fetchone()[0]

if existing_packing == 0:

    connection.executemany("""
        INSERT INTO packing
        (order_id, box_type, packed_by, status)
        VALUES (?, ?, ?, ?)
    """, packing_items)


# =========================================================
# SAMPLE STAGING RECORDS
# =========================================================

existing_staging = connection.execute(
    "SELECT COUNT(*) FROM staging"
).fetchone()[0]

if existing_staging == 0:

    staging_items = [
        (1, "Zone A", "", "", "Ready for Pickup"),
        (2, "Zone B", "", "", "Ready for Pickup"),
        (3, "Zone A", "", "", "Ready for Pickup"),
        (4, "Zone C", "", "", "Ready for Pickup"),
        (5, "Zone B", "", "", "Ready for Pickup")
    ]

    connection.executemany("""
        INSERT INTO staging
        (order_id, staging_location, courier,
         pickup_time, status)
        VALUES (?, ?, ?, ?, ?)
    """, staging_items)


# =========================================================
# SAVE DATABASE
# =========================================================

connection.commit()
connection.close()

print("Database created successfully!")