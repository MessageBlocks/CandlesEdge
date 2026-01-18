# Candle Edge Website

A Flask-based marketing website for Candle Edge AI Trading Signals platform with user authentication and Stripe payment integration.

## Features

- 🏠 **Landing Page** - Modern splash page with features and pricing
- 🔐 **Authentication** - User signup and login
- 💳 **Stripe Payments** - $5/month subscription via Stripe Checkout
- 📊 **Dashboard** - Member area after subscription

## Screenshots

The site uses a modern dark theme inspired by professional trading platforms:
- Background: `#0b0e11`
- Cards: `#1e2329`
- Accent Yellow: `#fcd535`
- Green: `#00e676`
- Red: `#ff5252`

## Quick Start

### 1. Clone and Setup

```bash
cd candle-edge-website
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your actual keys
```

### 3. Get Stripe API Keys

1. Create a Stripe account at https://stripe.com
2. Go to https://dashboard.stripe.com/apikeys
3. Copy your **test** keys (start with `sk_test_` and `pk_test_`)
4. Add them to your `.env` file

### 4. Run the App

```bash
python app.py
```

Visit http://localhost:5000

## Project Structure

```
candle-edge-website/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── templates/
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Landing page
│   ├── login.html        # Login page
│   ├── signup.html       # Signup page
│   ├── subscribe.html    # Subscription/payment page
│   └── dashboard.html    # Member dashboard
└── static/
    └── css/              # Additional CSS (if needed)
```

## Stripe Integration

### How it works:

1. User signs up → Redirected to subscribe page
2. User clicks "Subscribe" → Creates Stripe Checkout Session
3. User completes payment on Stripe → Redirected to success page
4. Success page verifies payment → Grants access to dashboard

### Setting up Stripe Webhooks (Production):

1. Go to https://dashboard.stripe.com/webhooks
2. Add endpoint: `https://yourdomain.com/webhook`
3. Select events: `customer.subscription.deleted`
4. Copy the webhook signing secret to your `.env`

### Testing Payments:

Use Stripe test card numbers:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- Any future expiry date and any CVC

## Deployment

### Deploy to Railway/Render/Heroku:

1. Push code to GitHub
2. Connect your repo to the platform
3. Add environment variables in the dashboard
4. Deploy!

### Using Gunicorn (Production):

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

### Procfile for Heroku/Railway:

```
web: gunicorn app:app
```

## Production Checklist

- [ ] Change `SECRET_KEY` to a secure random string
- [ ] Switch to Stripe **live** keys (`sk_live_` and `pk_live_`)
- [ ] Set up Stripe webhook endpoint
- [ ] Replace in-memory user store with a real database (PostgreSQL, etc.)
- [ ] Add proper password hashing (use `werkzeug.security`)
- [ ] Enable HTTPS
- [ ] Add email verification
- [ ] Add password reset functionality

## Database Migration (Production)

For production, replace the in-memory `users` dict with a proper database:

```python
# Example with SQLAlchemy
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100))
    subscribed = db.Column(db.Boolean, default=False)
    stripe_customer_id = db.Column(db.String(100))
    subscription_id = db.Column(db.String(100))
```

## License

MIT License - feel free to use this for your own projects!

## Support

For questions about Candle Edge, contact support@candleedge.com
