from flask import Flask, render_template, session, redirect, request, url_for

products = {
    1: {"id": 1, "name": "Cotton Tee", "description": "Comfortable cotton t-shirt", "price": 19.99, "image": "product1.jpg", "sizes": ["S", "M", "L", "XL"]},
    2: {"id": 2, "name": "Black Heavy Duty Tee", "description": "Stylish plain black tee", "price": 24.99, "image": "product2.jpg", "sizes": ["S", "M", "L", "XL"]},
    3: {"id": 3, "name": "Kid's Orange Tee", "description": "Vibrant and stylish", "price": 29.99, "image": "product3.jpg", "sizes": ["S", "M", "L"]},
    4: {"id": 4, "name": "Men's Sun Hat", "description": "Authentic Sun Hat", "price": 19.99, "image": "product4.jpg", "sizes": ["Out of Stock"]},
    5: {"id": 5, "name": "Woman's Summer Hat", "description": "Woman's Summer Hat", "price": 24.99, "image": "product5.jpg", "sizes": ["Out of Stock"]},
    6: {"id": 6, "name": "Mens White Tee", "description": "Mens White Tee", "price": 9.99, "image": "product6.jpg", "sizes": ["S", "M", "L", "XL"]},
    7: {"id": 7, "name": "Men's Swim Trunks", "description": "Mens Summer Trunks", "price": 19.99, "image": "product7.jpg", "sizes": ["M", "L", "XL"]},
    8: {"id": 8, "name": "Woman's Swim Suit", "description": "Woman's Swim Suit 2 Piece", "price": 22.99, "image": "product8.jpg", "sizes": ["S", "M", "L"]},
    9: {"id": 9, "name": "Mystery Pack", "description": "Includes Shoes, Shirt, and Pants!", "price": 150.99, "image": "product9.jpg", "sizes": ["Out of Stock"]}
}

users = {
    "testuser": {"password": "testpass"}  # Example user; replace with real user DB in production
}

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'  # Change this to a secure key


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/products')
def products_page():
    return render_template('products.html', products=products)


@app.route('/signin')
def signin():
    return "Sign In page coming soon!"


@app.route('/register')
def register():
    return render_template("sign-up.html")


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = products.get(product_id)
    if not product:
        return "Product not found", 404
    return render_template('product_detail.html', product=product)

@app.route('/coming-soon')
def coming_soon():
    return render_template('coming_soon.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = users.get(username)
        if user and user['password'] == password:
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('home'))
    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    subtotal = 0

    for product_id_str, sizes_or_qty in cart.items():
        product_id = int(product_id_str)
        product = products.get(product_id)
        if not product:
            continue

        if isinstance(sizes_or_qty, dict):
            for size, quantity in sizes_or_qty.items():
                total_price = product['price'] * quantity
                subtotal += total_price
                cart_items.append({
                    'id': product_id,
                    'name': product['name'],
                    'description': product['description'],
                    'price': product['price'],
                    'image': product['image'],
                    'size': size,
                    'quantity': quantity,
                    'total_price': total_price
                })
        else:
            quantity = sizes_or_qty
            total_price = product['price'] * quantity
            subtotal += total_price
            cart_items.append({
                'id': product_id,
                'name': product['name'],
                'description': product['description'],
                'price': product['price'],
                'image': product['image'],
                'size': None,
                'quantity': quantity,
                'total_price': total_price
            })

    shipping = 5.99 if cart_items else 0
    total = subtotal + shipping

    # Prepare recommended products — pick first 4 products NOT already in cart
    cart_product_ids = {int(pid) for pid in cart.keys()}
    recommended_products = [p for pid, p in products.items() if pid not in cart_product_ids][:4]

    return render_template('cart.html',
                           cart_items=cart_items,
                           subtotal=subtotal,
                           shipping=shipping,
                           total=total,
                           recommended_products=recommended_products)




@app.route('/checkout')
def checkout():
    return "<h2>Checkout Coming Soon!</h2><p>Stay tuned for this feature.</p>"


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
                if not cart[product_id_str]:  # Remove product if no sizes left
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


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    size = request.form.get('size')

    product = products.get(product_id)
    if not product:
        return "Product not found", 404

    if product.get('sizes') == ["Out of Stock"]:
        return "Sorry, this product is out of stock.", 400

    if not size or size == "Out of Stock":
        return "Please select a valid size.", 400

    cart = session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str not in cart or not isinstance(cart[product_id_str], dict):
        cart[product_id_str] = {}

    cart[product_id_str][size] = cart[product_id_str].get(size, 0) + 1
    session['cart'] = cart

    return redirect(request.referrer or url_for('products_page'))




@app.context_processor
def cart_item_count():
    cart = session.get('cart', {})
    total_items = 0
    for sizes in cart.values():
        if isinstance(sizes, dict):
            total_items += sum(sizes.values())
        else:
            total_items += sizes
    return dict(cart_item_count=total_items)


if __name__ == '__main__':
    app.run(debug=True)
