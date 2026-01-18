"""
Candle Edge - AI Trading Signals Platform
Flask application with authentication and Stripe payments
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import os
import stripe

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Stripe configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_test_key')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_your_test_key')
STRIPE_PRICE_ID = os.environ.get('STRIPE_PRICE_ID', 'price_your_price_id')  # $5/month price ID

# Simple in-memory user store (replace with database in production)
users = {}

# ============================================
# Authentication helpers
# ============================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def subscription_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        user = users.get(session['user_email'])
        if not user or not user.get('subscribed'):
            flash('Please subscribe to access the dashboard.', 'error')
            return redirect(url_for('subscribe'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# Routes
# ============================================

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if email in users and users[email]['password'] == password:
            session['user_email'] = email
            flash('Welcome back!', 'success')
            
            # Redirect based on subscription status
            if users[email].get('subscribed'):
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('subscribe'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not name or not email or not password:
            flash('All fields are required.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
        elif email in users:
            flash('An account with this email already exists.', 'error')
        else:
            # Create user
            users[email] = {
                'name': name,
                'email': email,
                'password': password,
                'subscribed': False,
                'stripe_customer_id': None
            }
            session['user_email'] = email
            flash('Account created! Please subscribe to continue.', 'success')
            return redirect(url_for('subscribe'))
    
    return render_template('signup.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.pop('user_email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/subscribe')
@login_required
def subscribe():
    """Subscription page"""
    user = users.get(session['user_email'])
    if user and user.get('subscribed'):
        return redirect(url_for('dashboard'))
    
    return render_template('subscribe.html', 
                         stripe_publishable_key=STRIPE_PUBLISHABLE_KEY)


@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for $5/month subscription"""
    try:
        user_email = session['user_email']
        user = users.get(user_email)
        
        # Create or get Stripe customer
        if not user.get('stripe_customer_id'):
            customer = stripe.Customer.create(
                email=user_email,
                name=user.get('name', '')
            )
            users[user_email]['stripe_customer_id'] = customer.id
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=users[user_email]['stripe_customer_id'],
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Candle Edge Pro',
                        'description': 'AI-powered trading signals - Monthly subscription',
                    },
                    'unit_amount': 500,  # $5.00 in cents
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('subscribe', _external=True),
        )
        
        return redirect(checkout_session.url)
    
    except Exception as e:
        flash(f'Error creating checkout session: {str(e)}', 'error')
        return redirect(url_for('subscribe'))


@app.route('/payment-success')
@login_required
def payment_success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    
    if session_id:
        try:
            # Verify the session with Stripe
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            
            if checkout_session.payment_status == 'paid':
                # Update user subscription status
                user_email = session['user_email']
                if user_email in users:
                    users[user_email]['subscribed'] = True
                    users[user_email]['subscription_id'] = checkout_session.subscription
                
                flash('Payment successful! Welcome to Candle Edge Pro!', 'success')
                return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error verifying payment: {str(e)}', 'error')
    
    return redirect(url_for('subscribe'))


@app.route('/webhook', methods=['POST'])
def webhook():
    """Stripe webhook for subscription events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Handle subscription events
    if event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # Find user by subscription ID and deactivate
        for email, user in users.items():
            if user.get('subscription_id') == subscription['id']:
                users[email]['subscribed'] = False
                break
    
    return 'OK', 200


@app.route('/dashboard')
@subscription_required
def dashboard():
    """Main dashboard (requires subscription)"""
    user = users.get(session['user_email'])
    return render_template('dashboard.html', user=user)


# ============================================
# Run app
# ============================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
