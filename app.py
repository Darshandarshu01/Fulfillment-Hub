from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)


# =========================
# DATABASE CONNECTION
# =========================

def get_db_connection():
    connection = sqlite3.connect("fulfillment.db")
    connection.row_factory = sqlite3.Row
    return connection


# =========================
# DASHBOARD
# =========================

@app.route("/")
def dashboard():

    connection = get_db_connection()

    orders = connection.execute(
        "SELECT * FROM orders"
    ).fetchall()

    inventory = connection.execute(
        "SELECT * FROM inventory"
    ).fetchall()

    connection.close()

    total_orders = len(orders)

    priority_orders = sum(
        1 for order in orders
        if order["priority"] == "Priority"
    )

    delayed_orders = 0

    ready_to_ship = sum(
        1 for order in orders
        if order["status"] == "Staged"
    )

    low_stock = sum(
        1 for item in inventory
        if item["main_stock"] <= item["minimum_stock"]
    )

    return render_template(
        "dashboard.html",
        orders=orders,
        total_orders=total_orders,
        priority_orders=priority_orders,
        delayed_orders=delayed_orders,
        ready_to_ship=ready_to_ship,
        low_stock=low_stock
    )


# =========================
# ORDERS
# =========================

@app.route("/orders")
def orders():

    connection = get_db_connection()

    orders = connection.execute(
        """
        SELECT *
        FROM orders
        ORDER BY priority DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "orders.html",
        orders=orders
    )


@app.route("/update-order/<int:order_id>", methods=["POST"])
def update_order(order_id):

    new_status = request.form.get("status")

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        (new_status, order_id)
    )

    connection.commit()
    connection.close()

    return redirect("/orders")


# =========================
# INVENTORY
# =========================

@app.route("/inventory")
def inventory():

    connection = get_db_connection()

    inventory = connection.execute(
        "SELECT * FROM inventory"
    ).fetchall()

    connection.close()

    return render_template(
        "inventory.html",
        inventory=inventory
    )


@app.route("/transfer-stock/<int:item_id>", methods=["POST"])
def transfer_stock(item_id):

    quantity = request.form.get("quantity")

    try:
        quantity = int(quantity)
    except:
        return redirect("/inventory")

    connection = get_db_connection()

    item = connection.execute(
        """
        SELECT *
        FROM inventory
        WHERE id = ?
        """,
        (item_id,)
    ).fetchone()

    if item:

        if quantity > 0 and quantity <= item["secondary_stock"]:

            new_main_stock = (
                item["main_stock"] + quantity
            )

            new_secondary_stock = (
                item["secondary_stock"] - quantity
            )

            connection.execute(
                """
                UPDATE inventory
                SET main_stock = ?,
                    secondary_stock = ?
                WHERE id = ?
                """,
                (
                    new_main_stock,
                    new_secondary_stock,
                    item_id
                )
            )

            connection.commit()

    connection.close()

    return redirect("/inventory")


# =========================
# PICKING
# =========================

@app.route("/picking")
def picking():

    connection = get_db_connection()

    picking_items = connection.execute(
        """
        SELECT
            picking.id,
            picking.product_name,
            picking.variant,
            picking.required_quantity,
            picking.picked_quantity,
            picking.status,
            orders.order_number,
            orders.priority
        FROM picking
        JOIN orders
        ON picking.order_id = orders.id
        ORDER BY orders.priority DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "picking.html",
        picking_items=picking_items
    )


@app.route("/confirm-pick/<int:item_id>", methods=["POST"])
def confirm_pick(item_id):

    quantity = request.form.get("quantity")

    try:
        quantity = int(quantity)
    except:
        return redirect("/picking")

    connection = get_db_connection()

    item = connection.execute(
        """
        SELECT *
        FROM picking
        WHERE id = ?
        """,
        (item_id,)
    ).fetchone()

    if item:

        if quantity == item["required_quantity"]:

            connection.execute(
                """
                UPDATE picking
                SET picked_quantity = ?,
                    status = 'Picked'
                WHERE id = ?
                """,
                (quantity, item_id)
            )

            connection.commit()

    connection.close()

    return redirect("/picking")


# =========================
# PACKING
# =========================

@app.route("/packing")
def packing():

    connection = get_db_connection()

    packing_orders = connection.execute(
        """
        SELECT
            packing.id AS packing_id,
            packing.box_type,
            packing.packed_by,
            packing.status,

            orders.id AS order_id,
            orders.order_number,
            orders.customer_name,
            orders.priority,

            COALESCE(
                (
                    SELECT
                        CASE
                            WHEN COUNT(*) =
                                SUM(
                                    CASE
                                        WHEN picking.status = 'Picked'
                                        THEN 1
                                        ELSE 0
                                    END
                                )
                            THEN 'Picked'
                            ELSE 'Pending'
                        END
                    FROM picking
                    WHERE picking.order_id = orders.id
                ),
                'Pending'
            ) AS picking_status

        FROM packing

        JOIN orders
        ON packing.order_id = orders.id

        ORDER BY orders.priority DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "packing.html",
        packing_orders=packing_orders
    )


@app.route("/pack-order/<int:packing_id>", methods=["POST"])
def pack_order(packing_id):

    box_type = request.form.get("box_type")
    packed_by = request.form.get("packed_by")

    connection = get_db_connection()

    packing_item = connection.execute(
        """
        SELECT
            packing.id,
            packing.order_id
        FROM packing
        WHERE packing.id = ?
        """,
        (packing_id,)
    ).fetchone()

    if packing_item:

        order_id = packing_item["order_id"]

        pending_items = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM picking
            WHERE order_id = ?
            AND status != 'Picked'
            """,
            (order_id,)
        ).fetchone()

        if pending_items["count"] == 0:

            connection.execute(
                """
                UPDATE packing
                SET box_type = ?,
                    packed_by = ?,
                    status = 'Packed'
                WHERE id = ?
                """,
                (
                    box_type,
                    packed_by,
                    packing_id
                )
            )

            connection.execute(
                """
                UPDATE orders
                SET status = 'Packing'
                WHERE id = ?
                """,
                (order_id,)
            )

            connection.commit()

    connection.close()

    return redirect("/packing")


# =========================
# STAGING & SHIPPING
# =========================

@app.route("/staging")
def staging():

    connection = get_db_connection()

    staging_orders = connection.execute(
        """
        SELECT
            staging.id AS staging_id,
            staging.staging_location,
            staging.courier,
            staging.pickup_time,
            staging.status,

            orders.id AS order_id,
            orders.order_number,
            orders.customer_name,
            orders.priority,

            packing.status AS packing_status

        FROM staging

        JOIN orders
        ON staging.order_id = orders.id

        JOIN packing
        ON packing.order_id = orders.id

        ORDER BY orders.priority DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "staging.html",
        staging_orders=staging_orders
    )


@app.route("/stage-order/<int:staging_id>", methods=["POST"])
def stage_order(staging_id):

    staging_location = request.form.get(
        "staging_location"
    )

    courier = request.form.get(
        "courier"
    )

    pickup_time = request.form.get(
        "pickup_time"
    )

    connection = get_db_connection()

    staging_item = connection.execute(
        """
        SELECT order_id
        FROM staging
        WHERE id = ?
        """,
        (staging_id,)
    ).fetchone()

    if staging_item:

        order_id = staging_item["order_id"]

        packing_item = connection.execute(
            """
            SELECT status
            FROM packing
            WHERE order_id = ?
            """,
            (order_id,)
        ).fetchone()

        if (
            packing_item
            and packing_item["status"] == "Packed"
        ):

            connection.execute(
                """
                UPDATE staging
                SET staging_location = ?,
                    courier = ?,
                    pickup_time = ?,
                    status = 'Staged'
                WHERE id = ?
                """,
                (
                    staging_location,
                    courier,
                    pickup_time,
                    staging_id
                )
            )

            connection.execute(
                """
                UPDATE orders
                SET status = 'Staged'
                WHERE id = ?
                """,
                (order_id,)
            )

            connection.commit()

    connection.close()

    return redirect("/staging")


@app.route("/ship-order/<int:staging_id>", methods=["POST"])
def ship_order(staging_id):

    connection = get_db_connection()

    staging_item = connection.execute(
        """
        SELECT
            order_id,
            status
        FROM staging
        WHERE id = ?
        """,
        (staging_id,)
    ).fetchone()

    if staging_item:

        order_id = staging_item["order_id"]

        if staging_item["status"] == "Staged":

            connection.execute(
                """
                UPDATE staging
                SET status = 'Shipped'
                WHERE id = ?
                """,
                (staging_id,)
            )

            connection.execute(
                """
                UPDATE orders
                SET status = 'Shipped'
                WHERE id = ?
                """,
                (order_id,)
            )

            connection.commit()

    connection.close()

    return redirect("/staging")


# =========================
# EXCEPTIONS / ISSUE MANAGEMENT
# =========================

@app.route("/exceptions")
def exceptions():

    connection = get_db_connection()

    # Get orders for the issue reporting form
    orders = connection.execute(
        """
        SELECT *
        FROM orders
        ORDER BY priority DESC
        """
    ).fetchall()

    # Get existing exceptions
    exception_items = connection.execute(
        """
        SELECT
            exceptions.id,
            exceptions.issue_type,
            exceptions.description,
            exceptions.priority,
            exceptions.status,
            exceptions.created_at,
            orders.order_number

        FROM exceptions

        JOIN orders
        ON exceptions.order_id = orders.id

        ORDER BY
            CASE
                WHEN exceptions.status = 'Open'
                THEN 0
                ELSE 1
            END,
            exceptions.id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "exceptions.html",
        orders=orders,
        exceptions=exception_items
    )


@app.route("/add-exception", methods=["POST"])
def add_exception():

    order_id = request.form.get(
        "order_id"
    )

    issue_type = request.form.get(
        "issue_type"
    )

    description = request.form.get(
        "description"
    )

    priority = request.form.get(
        "priority"
    )

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M"
    )

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO exceptions
        (
            order_id,
            issue_type,
            description,
            priority,
            status,
            created_at
        )

        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            'Open',
            ?
        )
        """,
        (
            order_id,
            issue_type,
            description,
            priority,
            created_at
        )
    )

    connection.commit()
    connection.close()

    return redirect("/exceptions")


@app.route(
    "/resolve-exception/<int:exception_id>",
    methods=["POST"]
)
def resolve_exception(exception_id):

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE exceptions
        SET status = 'Resolved'
        WHERE id = ?
        """,
        (exception_id,)
    )

    connection.commit()
    connection.close()

    return redirect("/exceptions")


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    app.run(debug=True)