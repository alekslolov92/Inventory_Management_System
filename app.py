from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = "inventory_secret_key_2024"

with app.app_context():
    init_db()


@app.route("/")
def dashboard():
    conn = get_db()
    products = conn.execute("""
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.name ASC
    """).fetchall()
    
    total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    low_stock_items = conn.execute(
        "SELECT COUNT(*) FROM products WHERE stock_quantity <= low_stock_threshold"
    ).fetchone()[0]
    total_sales = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    revenue = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales").fetchone()[0]
    conn.close()

    return render_template("dashboard.html",
        products=products,
        total_products=total_products,
        low_stock_items=low_stock_items,
        total_sales=total_sales,
        revenue=revenue
    )


@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    conn = get_db()
    if request.method == "POST":
        name = request.form["name"].strip()
        category_id = request.form["category_id"]
        price = request.form["price"]
        stock_quantity = request.form["stock_quantity"]
        low_stock_threshold = request.form["low_stock_threshold"]

        if not name or not price or not stock_quantity:
            flash("Name, Price, and Stock Quantity are required.", "danger")
            categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
            conn.close()
            return render_template("add_product.html", categories=categories)

        conn.execute("""
            INSERT INTO products (name, category_id, price, stock_quantity, low_stock_threshold)
            VALUES (?, ?, ?, ?, ?)
        """, (name, category_id or None, float(price), int(stock_quantity), int(low_stock_threshold)))
        conn.commit()
        conn.close()
        flash(f'Product "{name}" added successfully!', "success")
        return redirect(url_for("dashboard"))

    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return render_template("add_product.html", categories=categories)


@app.route("/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    if not product:
        flash("Product not found.", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form["name"].strip()
        category_id = request.form["category_id"]
        price = request.form["price"]
        stock_quantity = request.form["stock_quantity"]
        low_stock_threshold = request.form["low_stock_threshold"]

        conn.execute("""
            UPDATE products
            SET name=?, category_id=?, price=?, stock_quantity=?, low_stock_threshold=?
            WHERE id=?
        """, (name, category_id or None, float(price), int(stock_quantity), int(low_stock_threshold), product_id))
        conn.commit()
        conn.close()
        flash(f'Product "{name}" updated successfully!', "success")
        return redirect(url_for("dashboard"))

    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return render_template("edit_product.html", product=product, categories=categories)


@app.route("/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    conn = get_db()
    product = conn.execute("SELECT name FROM products WHERE id = ?", (product_id,)).fetchone()
    if product:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        flash(f'Product "{product["name"]}" deleted.', "warning")
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/record-sale", methods=["GET", "POST"])
def record_sale():
    conn = get_db()
    if request.method == "POST":
        product_id = request.form["product_id"]
        quantity_sold = int(request.form["quantity_sold"])

        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

        if not product:
            flash("Product not found.", "danger")
            conn.close()
            return redirect(url_for("record_sale"))

        if quantity_sold <= 0:
            flash("Quantity must be greater than 0.", "danger")
            conn.close()
            return redirect(url_for("record_sale"))

        if quantity_sold > product["stock_quantity"]:
            flash(f'Insufficient stock. Only {product["stock_quantity"]} units available.', "danger")
            conn.close()
            return redirect(url_for("record_sale"))

        total_amount = quantity_sold * product["price"]

        conn.execute("""
            INSERT INTO sales (product_id, quantity_sold, sale_price, total_amount)
            VALUES (?, ?, ?, ?)
        """, (product_id, quantity_sold, product["price"], total_amount))

        conn.execute("""
            UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?
        """, (quantity_sold, product_id))

        conn.commit()
        conn.close()
        flash(f'Sale recorded! {quantity_sold} units sold for ₹{total_amount:.2f}.', "success")
        return redirect(url_for("sales"))

    products = conn.execute(
        "SELECT * FROM products WHERE stock_quantity > 0 ORDER BY name"
    ).fetchall()
    conn.close()
    return render_template("record_sale.html", products=products)


@app.route("/sales")
def sales():
    conn = get_db()
    sales_data = conn.execute("""
        SELECT s.*, p.name as product_name
        FROM sales s
        JOIN products p ON s.product_id = p.id
        ORDER BY s.sale_date DESC
    """).fetchall()
    total_revenue = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales").fetchone()[0]
    conn.close()
    return render_template("sales.html", sales=sales_data, total_revenue=total_revenue)


@app.route("/categories", methods=["GET", "POST"])
def categories():
    conn = get_db()
    if request.method == "POST":
        name = request.form["name"].strip()
        if name:
            try:
                conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                conn.commit()
                flash(f'Category "{name}" added.', "success")
            except:
                flash(f'Category "{name}" already exists.', "danger")
        conn.close()
        return redirect(url_for("categories"))

    all_categories = conn.execute("""
        SELECT c.*, COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id
        GROUP BY c.id
        ORDER BY c.name
    """).fetchall()
    conn.close()
    return render_template("categories.html", categories=all_categories)


@app.route("/delete-category/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    conn = get_db()
    conn.execute("UPDATE products SET category_id = NULL WHERE category_id = ?", (category_id,))
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()
    flash("Category deleted.", "warning")
    return redirect(url_for("categories"))


if __name__ == "__main__":
    app.run(debug=True)