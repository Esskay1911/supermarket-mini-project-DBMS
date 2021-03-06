import os
from flask import Flask, render_template, url_for, request, flash, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import timedelta
from utils import *
from werkzeug.local import LocalProxy


app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = "enSecretGuru"
app.config['UPLOAD_FOLDER'] = "./static/uploads"
app.permanent_session_lifetime = timedelta(days=3)


cur = LocalProxy(get_cur)


@app.teardown_appcontext
def teardown_db(exception):
    if 'db' in g:
        db = g.pop('db', None)
        g.pop('cur')

        if db is not None:
            db.close()
            print("Connection closed")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # connection = dbConnection()
        # cur = connection.cursor()
        if request.form.get("email") == "admin@abc" and request.form.get("password") == "dbmsmini":
            create_session('admin', 'admin@abc')
            return redirect(url_for("home_admin"))
        next_url = request.args.get("next")
        if 'register' in request.form:
            name = request.form['name']
            email = request.form['email']
            password = generate_password_hash(request.form['password'])
            cur.execute(f"SELECT * FROM Users WHERE email='{email}'")
            if cur.fetchone():
                flash("User already exist. Pleast try to login.", "error")
                # # close_connection()
                # connection.close()
                return render_template("login.html")
            else:
                cur.execute(
                    f"""
                    INSERT INTO Users (name, email, password)
                    VALUES('{name}','{email}','{password}')
                    """
                )
                create_session(name, email)
                flash("Registered Successfully!")
                flash(f"Hello {name}, Welcome to the Supermarket!")
                if next_url:
                    # close_connection()
                    # connection.close()
                    return redirect(next_url)
                # close_connection()
                # connection.close()
                return render_template("home.html")
        elif 'login' in request.form:
            email = request.form['email']
            password = request.form['password']
            cur.execute(f"SELECT * FROM Users WHERE email='{email}'")
            user = cur.fetchone()
            if user:
                password_hash = user['password']
                if check_password_hash(password_hash, password):
                    create_session(user['name'], user['email'])
                    flash("Logged in successfully")
                    flash(
                        f"Hello {session['user']}, Welcome to the Supermarket!", "info")
                    if next_url:
                        # close_connection()
                        # connection.close()
                        return redirect(request.args.get("next"))
                    # close_connection()
                    # connection.close()
                    return redirect(url_for("home"))
                else:
                    flash("Incorrect password", "error")
            else:
                flash("User not found", "error")
            # close_connection()
            # connection.close()
            return render_template("login.html")
    else:
        # close_connection()
        return render_template("login.html")


@app.route("/profile_edit", methods=['GET', 'POST'])
@login_required
def profile_edit():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        cur.execute(
            f"""SELECT password FROM Users WHERE email = '{session["email"]}';""")
        if check_password_hash(cur.fetchone()['password'], old_password):
            name = request.form.get('name')
            email = request.form.get('email')
            new_password = generate_password_hash(
                request.form.get('new_password'))
            phone = request.form.get('phone')
            address = request.form.get('address')
            cur.execute(
                f"""
                UPDATE Users
                SET  name='{name}', email='{email}', password='{new_password}', phone='{phone}', address='{address}'
                WHERE email='{email}'
                """
            )
            flash("Changes applied Successfully")
            redirect(url_for('home'))
        else:
            flash("Incorrect current password", "error")
    return render_template("profile_edit.html")


@app.route("/home")
@login_required
def home():
    if session['email'] == 'admin@abc':
        return redirect(url_for('home_admin'))
    return render_template("home.html")


@app.route("/admin/home")
@admin_login_required
def home_admin():
    return render_template("home_admin.html")


@app.route("/shop", methods=['GET', 'POST'])
def shop():
    addedItem = request.args.get('addedItem')
    email = session["email"]
    if addedItem:
        cur.execute(
            f"SELECT * from Cart WHERE customerId = (SELECT id FROM Users WHERE email = '{email}') AND itemId = {addedItem}")
        if cur.fetchone():
            cur.execute(
                f"UPDATE Cart SET quantity = quantity+1 WHERE itemId = {addedItem}")
        else:
            cur.execute(
                f"INSERT INTO Cart(customerId,itemId) VALUES((SELECT id FROM Users WHERE email = '{email}'), {addedItem})")
        flash("Item added successfully. To edit quantity, visit cart.")

    cur.execute(
        f"SELECT * from Cart WHERE customerId = (SELECT id FROM Users WHERE email = '{email}')")
    cart = cur.fetchall()
    cartsize = len(cart)
    print(cartsize)
    cur.execute("SELECT * from Items")
    cur.execute(
        f"""SELECT *
        FROM Items
        LEFT JOIN(SELECT * FROM Cart WHERE customerId=(SELECT id FROM Users WHERE email='{email}')) AS T
        ON Items.id=T.itemId;
        """)
    items = cur.fetchall()
    return render_template("shop.html", items=items, cartsize=cartsize)


@app.route("/cart")
def cart():
    email = session["email"]
    cur.execute(
        f"SELECT * from Cart WHERE customerId = (SELECT id FROM Users WHERE email = '{email}')")
    cart = cur.fetchall()
    return render_template("cart.html", items=cart)


@app.route("/remove_item_from_cart")
def remove_item():
    itemId = request.args.get['id']


@app.route("/previous_cart")
def previous_cart():
    return render_template("previous_cart.html")


@app.route("/explore")
def explore():
    return render_template("explore.html")


@app.route("/admin")
@admin_login_required
def admin():
    # if request.method == 'POST'
    return render_template("admin.html")


@app.route("/admin/add_item", methods=['GET', 'POST'])
@admin_login_required
def add_item():

    cur.execute("SELECT category FROM Categories ORDER BY category;")
    categories = cur.fetchall()
    cur.execute("SELECT brand FROM Brands ORDER BY brand;")
    brands = cur.fetchall()
    # print("Categories")
    # for category in categories:
    #     print(category['category'])
    if request.method == 'POST':
        name = request.form['name']
        cur.execute(f"SELECT id,name from Items where name = '{name}'")
        if cur.fetchone():
            flash("Item with that name already exist. Please try again")
        else:
            category = request.form["category"]
            brand = request.form['brand']
            mrp = request.form['mrp']
            sale_rate = request.form['sale_rate']
            if category == 'Other':
                category = request.form['new_category']
                cur.execute(
                    f"INSERT INTO Categories(category) VALUES('{category}');")
            if brand == 'Other':
                brand = request.form['new_brand']
                cur.execute(f"INSERT INTO Brands(brand) VALUES('{brand}');")
            cur.execute(
                f"""
                INSERT INTO Items (categoryId,brandId,name,mrp,sale_rate)
                VALUES ((SELECT id from Categories WHERE category = '{category}'),(SELECT id from Brands WHERE brand = '{brand}'),'{name}',{mrp},{sale_rate}); 
                """
            )
            cur.execute(f"SELECT id FROM Items WHERE name = '{name}'")
            item_id = cur.fetchone()["id"]
            image = request.files.get("image")
            if image:
                image.save(app.config['UPLOAD_FOLDER'] +
                           "/" + f"{item_id}.png")

    return render_template("add_item.html", categories=categories, brands=brands)


@app.route("/admin/edit_item", methods=['GET', 'POST'])
@admin_login_required
def edit_item():
    return render_template('edit_item.html')


@app.route("/contact_us")
def contact_us():
    return render_template("contact_us.html")


@ app.route("/logout")
def logout():
    flash(f"{session['user']} have been logged out successfully")
    clear_session()
    return redirect(url_for('index'))


@ app.route("/clearsession")
def clearsession():
    clear_session()
    return "Cleared"


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
