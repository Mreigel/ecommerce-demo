from flask import Flask, render_template, session, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.sqlite import JSON
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy import or_, func
import os

def clean_identifier(identifier):
    """Normalize input: lowercase and strip leading 'www.' if present."""
    identifier = identifier.strip().lower()
    if identifier.startswith('www.'):
        identifier = identifier[4:]
    return identifier

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'store.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(120))
    sizes = db.Column(JSON, nullable=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    street = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip = db.Column(db.String(10))
    country = db.Column(db.String(50))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='orders', lazy=True)
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    size = db.Column(db.String(10), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    product = db.relationship('Product', lazy=True)


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/products')
def products_page():
    products = Product.query.all()
    return render_template('products.html', products=products)


@app.route('/signin')
def signin():
    return "Sign In page coming soon!"


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Normalize username and email
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        if email.startswith('www.'):
            email = email[4:]

        # Check for duplicate username/email
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already in use.", "error")
            return redirect(url_for('register'))

        # Get the rest of the form fields
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        street = request.form.get('street')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip')
        country = request.form.get('country')

        # Create the user
        new_user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            street=street,
            city=city,
            state=state,
            zip=zip_code,
            country=country
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template("sign-up.html")



@app.route('/coming-soon')
def coming_soon():
    return render_template('coming_soon.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        raw_identifier = request.form.get('username')
        password = request.form.get('password')
        identifier = clean_identifier(raw_identifier)

        user = User.query.filter(
            or_(
                func.lower(User.username) == identifier,
                func.lower(User.email) == identifier
            )
        ).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('home'))
        else:
            flash('Invalid username/email or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/login_from_dropdown', methods=['POST'])
def login_from_dropdown():
    raw_identifier = request.form.get('username')
    password = request.form.get('password')
    identifier = clean_identifier(raw_identifier)

    user = User.query.filter(
        or_(
            func.lower(User.username) == identifier,
            func.lower(User.email) == identifier
        )
    ).first()

    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        flash(f"Welcome back, {user.username}!", "success")
    else:
        flash("Invalid username or password.", "error")

    return redirect(url_for('home'))

@app.route('/account')
def account():
    if 'user_id' not in session:
        flash("You must be logged in to access account settings.", "warning")
        return redirect(url_for('home'))

    user = User.query.get(session['user_id'])
    return render_template('account.html', user=user)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)  # <-- Remove username from session
    flash('Logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return "Product not found", 404

    return render_template('product_detail.html', product=product)



@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    subtotal = 0

    for product_id_str, sizes_or_qty in cart.items():
        product = Product.query.get(int(product_id_str))
        if not product:
            continue

        if isinstance(sizes_or_qty, dict):
            for size, quantity in sizes_or_qty.items():
                total_price = product.price * quantity
                subtotal += total_price
                cart_items.append({
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'price': product.price,
                    'image': product.image,
                    'size': size,
                    'quantity': quantity,
                    'total_price': total_price
                })
        else:
            quantity = sizes_or_qty
            total_price = product.price * quantity
            subtotal += total_price
            cart_items.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'image': product.image,
                'size': None,
                'quantity': quantity,
                'total_price': total_price
            })

    shipping = 5.99 if cart_items else 0
    total = subtotal + shipping

    cart_product_ids = {int(pid) for pid in cart.keys()}
    recommended_products = Product.query.filter(~Product.id.in_(cart_product_ids)).limit(4).all()

    return render_template('cart.html',
                           cart_items=cart_items,
                           subtotal=subtotal,
                           shipping=shipping,
                           total=total,
                           recommended_products=recommended_products)


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    size = request.form.get('size')
    product = Product.query.get(product_id)
    if not product:
        return "Product not found", 404

    if product.sizes == "Out of Stock":
        return "Sorry, this product is out of stock.", 400

    if not size or size == "Out of Stock":
        return "Please select a valid size.", 400

    cart = session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str not in cart or not isinstance(cart[product_id_str], dict):
        cart[product_id_str] = {}

    cart[product_id_str][size] = cart[product_id_str].get(size, 0) + 1
    session['cart'] = cart

    flash(f"{product.name} ({size}) added to cart.", "success")
    return redirect(request.referrer or url_for('products_page'))


@app.route('/update_cart/<product_id>', methods=['POST'])
def update_cart(product_id):
    product_id_str = str(product_id)
    size = request.form.get('size')
    action = request.form.get('action')
    cart = session.get('cart', {})

    if product_id_str in cart and size in cart[product_id_str]:
        if action == 'increase':
            cart[product_id_str][size] += 1
        elif action == 'decrease':
            cart[product_id_str][size] -= 1
            if cart[product_id_str][size] <= 0:
                del cart[product_id_str][size]
                if not cart[product_id_str]:
                    del cart[product_id_str]

    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/remove_from_cart/<product_id>', methods=['POST'])
def remove_from_cart(product_id):
    product_id_str = str(product_id)
    size = request.form.get('size')
    cart = session.get('cart', {})

    if product_id_str in cart and size in cart[product_id_str]:
        del cart[product_id_str][size]
        if not cart[product_id_str]:
            del cart[product_id_str]

    session['cart'] = cart
    return redirect(url_for('cart'))


from datetime import datetime

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash("Please log in to check out.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    cart = session.get('cart', {})
    cart_items = []
    subtotal = 0

    for product_id_str, sizes_or_qty in cart.items():
        product = Product.query.get(int(product_id_str))
        if not product:
            continue

        if isinstance(sizes_or_qty, dict):
            for size, quantity in sizes_or_qty.items():
                total_price = product.price * quantity
                subtotal += total_price
                cart_items.append({
                    'product': product,
                    'name': product.name,
                    'size': size,
                    'quantity': quantity,
                    'total_price': total_price
                })

    shipping = 5.99 if cart_items else 0
    total = subtotal + shipping

    if request.method == 'POST':
        new_order = Order(user_id=user.id, total=total)
        db.session.add(new_order)
        db.session.flush()  # Get order ID before committing

        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item['product'].id,
                size=item['size'],
                quantity=item['quantity'],
                price=item['product'].price
            )
            db.session.add(order_item)

        db.session.commit()
        session['cart'] = {}
        flash("✅ Order placed successfully!", "success")
        return redirect(url_for('order_confirmation'))

    return render_template('checkout.html',
                           cart_items=cart_items,
                           total=total,
                           current_user=user)



@app.route('/test-products')
def test_products():
    products = Product.query.all()
    return '<br>'.join([f"{p.id}: {p.name} - ${p.price}" for p in products])


@app.context_processor
def inject_globals():
    cart = session.get('cart', {})
    total_items = 0
    for sizes in cart.values():
        if isinstance(sizes, dict):
            total_items += sum(sizes.values())
        else:
            total_items += sizes

    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    return dict(cart_item_count=total_items, current_user=user)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Product.query.first():
            product_data = [
                {"name": "Cotton Tee", "description": "Comfortable cotton t-shirt", "price": 19.99, "image": "product1.jpg", "sizes": ["S", "M", "L", "XL"]},
                {"name": "Black Heavy Duty Tee", "description": "Stylish plain black tee", "price": 24.99, "image": "product2.jpg", "sizes": ["S", "M", "L", "XL"]},
                {"name": "Kid's Orange Tee", "description": "Vibrant and stylish", "price": 29.99, "image": "product3.jpg", "sizes": ["S", "M", "L"]},
                {"name": "Men's Sun Hat", "description": "Authentic Sun Hat", "price": 19.99, "image": "product4.jpg", "sizes": []},
                {"name": "Woman's Summer Hat", "description": "Woman's Summer Hat", "price": 24.99, "image": "product5.jpg", "sizes": []},
                {"name": "Mens White Tee", "description": "Mens White Tee", "price": 9.99, "image": "product6.jpg", "sizes": ["S", "M", "L", "XL"]},
                {"name": "Men's Swim Trunks", "description": "Mens Summer Trunks", "price": 19.99, "image": "product7.jpg", "sizes": ["M", "L", "XL"]},
                {"name": "Woman's Swim Suit", "description": "Woman's Swim Suit 2 Piece", "price": 22.99, "image": "product8.jpg", "sizes": ["S", "M", "L"]},
                {"name": "Mystery Pack", "description": "Includes Shoes, Shirt, and Pants!", "price": 150.99, "image": "product9.jpg", "sizes": []},
            ]
            for p in product_data:
                db.session.add(Product(**p))
            db.session.commit()
            print("✅ Seeded products into database.")

    app.run(debug=True)
