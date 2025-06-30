from flask import Flask, render_template, session, redirect, request, url_for

products = {
    1: {"id": 1, "name": "T-shirt 1", "description": "Comfortable cotton t-shirt", "price": 19.99, "image": "product1.jpg"},
    2: {"id": 2, "name": "T-shirt 2", "description": "Cool graphic tee", "price": 24.99, "image": "product2.png"},
    3: {"id": 3, "name": "T-shirt 3", "description": "Soft and stylish", "price": 29.99, "image": "product3.png"}
}


app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'  # Change to a secure key

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
    return "Register page coming soon!"

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = products.get(product_id)
    if not product:
        return "Product not found", 404
    return render_template('product_detail.html', product=product)

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    print("Current cart session data:", cart)  # Debug print

    cart_items = []
    for product_id, quantity in cart.items():
        product = products.get(product_id)
        if product:
            cart_items.append({
                'id': product_id,
                'name': product['name'],
                'description': product['description'],
                'price': product['price'],
                'image': product['image'],
                'quantity': quantity,
                'total_price': product['price'] * quantity
            })

    return render_template('cart.html', cart_items=cart_items)


@app.route('/update_cart/<product_id>', methods=['POST'])
def update_cart(product_id):
    product_id = int(product_id)
    action = request.form.get('action')
    cart = session.get('cart', {})

    if product_id in cart:
        if action == 'increase':
            cart[product_id] += 1
        elif action == 'decrease':
            cart[product_id] -= 1
            if cart[product_id] <= 0:
                del cart[product_id]

    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/add_to_cart/<product_id>')
def add_to_cart(product_id):
    product_id = int(product_id)  # Convert to int here
    cart = session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + 1
    session['cart'] = cart
    return redirect(request.referrer or url_for('products_page'))

@app.context_processor
def cart_item_count():
    cart = session.get('cart', {})
    total_items = sum(cart.values())  # sums all quantities
    return dict(cart_item_count=total_items)

if __name__ == '__main__':
    app.run(debug=True)
