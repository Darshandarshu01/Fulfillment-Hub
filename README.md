# Fulfillment Hub

A lightweight web-based fulfillment management system designed for small e-commerce businesses to manage orders, inventory, picking, packing, staging, shipping, and exceptions in one place.

---

## Project Overview

Small e-commerce businesses may receive hundreds of orders every day. Managing priority orders, warehouse inventory, picking, packing, courier pickups, and exceptions manually can lead to delays and mistakes.

**Fulfillment Hub** provides a simple centralized system to track the complete fulfillment workflow.

The system follows this process:

**Order Received → Processing → Picking → Packing → Staging → Shipping**

It also supports priority order tracking, stock transfers between warehouses, and exception management.

---

## Features

### 1. Dashboard

The dashboard provides a quick overview of fulfillment operations.

It displays:

- Total orders
- Priority orders
- Ready-to-ship orders
- Low-stock items
- Order status overview
- Inventory alerts
- Quick navigation to different modules

---

### 2. Order Management

The Orders module allows the team to:

- View all orders
- Identify priority orders
- Track order status
- Update the current fulfillment status

Priority orders are displayed before normal orders.

---

### 3. Inventory Management

The Inventory module tracks stock in:

- Main warehouse
- Secondary warehouse

It also displays minimum stock levels.

The system supports transferring stock from the secondary warehouse to the main warehouse when additional stock is required.

Example:

```text
Secondary Warehouse
        ↓
   Stock Transfer
        ↓
Main Warehouse
        ↓
     Picking