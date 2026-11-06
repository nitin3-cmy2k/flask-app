import os
import time
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g
import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_fallback_key")

# Kubernetes environment variables
DB_HOST = os.environ.get("DB_HOST", "mysql-service")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "SecretPassword123")
DB_NAME = os.environ.get("DB_NAME", "inventory_db")

db_pool = None

def init_db():
    """Initializes the database and schema. Safe to call multiple times."""
    for i in range(10):
        try:
            conn = mysql.connector.connect(
                host=DB_HOST, user=DB_USER, password=DB_PASSWORD
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            cursor.execute(f"USE {DB_NAME}")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sku VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(100) NOT NULL,
                    category VARCHAR(50),
                    quantity INT NOT NULL DEFAULT 0,
                    price DECIMAL(10, 2) NOT NULL,
                    is_hidden TINYINT(1) NOT NULL DEFAULT 0
                )
            """)
            conn.commit()
            cursor.close()
            conn.close()
            print("Database schema verified/initialized successfully.")
            return True
        except Error as e:
            print(f"Database initialization attempt {i+1} failed. Retrying in 5s... Error: {e}")
            time.sleep(5)
    return False

def get_db_pool():
    """Thread-safe on-demand pool allocator."""
    global db_pool
    if db_pool is None:
        try:
            db_pool = pooling.MySQLConnectionPool(
                pool_name="inventory_pool",
                pool_size=10,
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            print("Connection pool created successfully.")
        except Error as e:
            print(f"Failed to create connection pool: {e}")
            raise e
    return db_pool

def get_db():
    """Attaches a pool connection to the application context 'g' for the current request."""
    if 'db' not in g:
        pool = get_db_pool()
        g.db = pool.get_connection()
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Automatically returns the connection to the pool at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- ROUTES ---

@app.route('/')
def index():
    """Fetch and display active, hidden, and tracked inventory stats."""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get active items
        cursor.execute("SELECT * FROM inventory WHERE is_hidden = 0")
        active_items = cursor.fetchall()
        
        # Get hidden items
        cursor.execute("SELECT * FROM inventory WHERE is_hidden = 1")
        hidden_items = cursor.fetchall()
        
        # Calculate summary arithmetic values
        cursor.execute("SELECT SUM(quantity) as total_qty, SUM(quantity * price) as total_val FROM inventory")
        stats = cursor.fetchone()
        
        cursor.close()
        
        total_quantity = stats['total_qty'] if stats['total_qty'] else 0
        total_value = stats['total_val'] if stats['total_val'] else 0.0
        
        return render_template(
            'index.html', 
            active_items=active_items, 
            hidden_items=hidden_items,
            total_quantity=total_quantity,
            total_value=total_value
        )
    except Error as e:
        flash(f"Error fetching data: {e}", "danger")
        return render_template('index.html', active_items=[], hidden_items=[], total_quantity=0, total_value=0.0)

@app.route('/add', methods=['POST'])
def add_item():
    """Create a new inventory item."""
    sku = request.form.get('sku')
    name = request.form.get('name')
    category = request.form.get('category')
    quantity = int(request.form.get('quantity', 0))
    price = float(request.form.get('price', 0.0))

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO inventory (sku, name, category, quantity, price) VALUES (%s, %s, %s, %s, %s)",
            (sku, name, category, quantity, price)
        )
        conn.commit()
        cursor.close()
        flash(f"Item '{name}' added successfully! Initial Stock: +{quantity}", "success")
    except Error as e:
        flash(f"Error adding item (check if SKU is unique): {e}", "danger")
    
    return redirect(url_for('index'))

@app.route('/adjust_stock/<int:item_id>', methods=['POST'])
def adjust_stock(item_id):
    """Performs delta arithmetic (+ or -) to add or remove item stock allocations."""
    action = request.form.get('action') # expect 'add' or 'remove'
    amount = int(request.form.get('amount', 0))
    
    if amount <= 0:
        flash("Please enter a valid amount greater than 0.", "warning")
        return redirect(url_for('index'))
        
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Check existing item properties
        cursor.execute("SELECT name, quantity FROM inventory WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        
        if not item:
            flash("Item not found.", "danger")
            cursor.close()
            return redirect(url_for('index'))
            
        current_qty = item['quantity']
        
        if action == 'add':
            new_qty = current_qty + amount
            flash(f"Added {amount} units to {item['name']}.", "success")
        elif action == 'remove':
            if current_qty - amount < 0:
                flash(f"Cannot remove {amount} units. Only {current_qty} left in stock!", "danger")
                cursor.close()
                return redirect(url_for('index'))
            new_qty = current_qty - amount
            flash(f"Removed {amount} units from {item['name']}.", "warning")
        else:
            new_qty = current_qty
            
        cursor.execute("UPDATE inventory SET quantity = %s WHERE id = %s", (new_qty, item_id))
        conn.commit()
        cursor.close()
        
    except Error as e:
        flash(f"Database error during stock adjustment: {e}", "danger")
        
    return redirect(url_for('index'))

@app.route('/hide/<int:item_id>', methods=['POST'])
def hide_item(item_id):
    """Soft delete by archiving the item out of principal view."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE inventory SET is_hidden = 1 WHERE id = %s", (item_id,))
        conn.commit()
        cursor.close()
        flash("Item hidden and moved to the archive list.", "warning")
    except Error as e:
        flash(f"Error hiding item: {e}", "danger")
        
    return redirect(url_for('index'))

@app.route('/unhide/<int:item_id>', methods=['POST'])
def unhide_item(item_id):
    """Restores an archived item back to visible production lists."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE inventory SET is_hidden = 0 WHERE id = %s", (item_id,))
        conn.commit()
        cursor.close()
        flash("Item restored back to active view.", "success")
    except Error as e:
        flash(f"Error restoring item: {e}", "danger")
        
    return redirect(url_for('index'))

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    """Permanently deletes/removes the item from the database record."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
        conn.commit()
        cursor.close()
        flash("Item permanently removed.", "danger")
    except Error as e:
        flash(f"Error permanently removing item: {e}", "danger")
        
    return redirect(url_for('index'))

# --- APPLICATION INITIALIZATION STARTUP ---
if __name__ == '__main__':
    # Force table initialization before starting up the server container loop
    print("Initializing structural database tables...")
    if init_db():
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("CRITICAL: Failed to connect to database. Server halting lifecycle.")

