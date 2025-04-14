from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import util
import bcrypt
import json
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

USER_DATA_FILE = "users.json"

# Load user data from the JSON file
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save user data to the JSON file
def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

# Middleware to protect routes
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

# Clear session on app restart (development/debug use)
@app.before_request
def enforce_fresh_session():
    if 'logged_in' not in session and request.endpoint not in ('login', 'register', 'static'):
        session.clear()

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match. Please try again.")
            return render_template('register.html')

        users = load_users()

        for user_data in users.values():
            if user_data['username'] == username:
                flash("Username already exists.")
                return render_template('register.html')
            if user_data['email'] == email:
                flash("Email already exists.")
                return render_template('register.html')

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        users[email] = {
            'username': username,
            'email': email,
            'password': hashed_pw.decode('utf-8')
        }

        save_users(users)

        return redirect(url_for('register', success='true'))

    success = request.args.get('success')
    return render_template('register.html', success=success)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        users = load_users()
        for user_data in users.values():
            if user_data.get('username') == username:
                if bcrypt.checkpw(password, user_data['password'].encode('utf-8')):
                    session['logged_in'] = True
                    session['username'] = username
                    return redirect(url_for('home'))
                else:
                    flash("Incorrect password.")
                    break
        flash("Invalid username or password.")
    return render_template('loginPage.html')


# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Home route
@app.route('/')
@login_required
def home():
    return render_template('index.html')

# Price prediction route (protected)
@app.route('/price-prediction', methods=['GET'], endpoint='price_prediction')  # Explicit endpoint name
@login_required
def render_price():
    return render_template('app.html')

# Existing routes remain unchanged
@app.route('/get_location_names', methods=['GET'])
def get_location_names():
    response = jsonify({
        'locations': util.get_location_names()
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/predict_home_price', methods=['GET', 'POST'])
def predict_home_price():
    total_sqft = float(request.form['total_sqft'])
    location = request.form['location']
    bedroom = int(request.form['bedroom'])
    bath = int(request.form['bath'])
    balcony = int(request.form['balcony'])

    response = jsonify({
        'estimated_price': util.get_estimated_price(location, total_sqft, bedroom, bath, balcony)
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

if __name__ == "__main__":
    print("Starting Python Flask Server For Home Price Prediction...")
    util.load_saved_artifacts()
    app.run(debug=True)