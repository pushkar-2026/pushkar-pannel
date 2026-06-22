# app.py - Main Flask Application
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
import string
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
app.secret_key = 'pushkar-vvip-panel-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pushkar_vvip_panel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, reseller, user
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_banned = db.Column(db.Boolean, default=False)
    referred_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
class Key(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    validity_type = db.Column(db.String(20))  # day, week, month, session
    validity_days = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float)
    type = db.Column(db.String(20))  # credit, debit
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Referral(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    referred_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

# Create tables
with app.app_context():
    db.create_all()
    
    # Create admin user if not exists
    admin = User.query.filter_by(username='ASHWIN').first()
    if not admin:
        admin = User(
            username='ASHWIN',
            password=generate_password_hash('PUSHKAR2006'),
            role='admin',
            balance=1000000.0
        )
        db.session.add(admin)
        db.session.commit()

# Helper Functions
def generate_key(length=16):
    """Generate a random key"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def calculate_expiry(validity_type):
    """Calculate expiry date based on validity type"""
    if validity_type == 'day':
        return datetime.utcnow() + timedelta(days=1)
    elif validity_type == 'week':
        return datetime.utcnow() + timedelta(weeks=1)
    elif validity_type == 'month':
        return datetime.utcnow() + timedelta(days=30)
    elif validity_type == 'session':
        return datetime.utcnow() + timedelta(hours=24)
    return datetime.utcnow() + timedelta(days=1)

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            if user.is_banned:
                return render_template('login.html', error='Your account has been banned')
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if user.is_banned:
        session.clear()
        return redirect(url_for('login'))
    
    # Get stats
    total_users = User.query.count()
    active_keys = Key.query.filter_by(is_active=True, is_used=False).count()
    total_keys = Key.query.count()
    
    # Recent transactions
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.created_at.desc()).limit(10).all()
    
    # User's keys
    user_keys = Key.query.filter_by(user_id=user.id).order_by(Key.created_at.desc()).all()
    
    return render_template('dashboard.html', 
                         user=user, 
                         total_users=total_users,
                         active_keys=active_keys,
                         total_keys=total_keys,
                         transactions=transactions,
                         user_keys=user_keys,
                         now=datetime.utcnow())

@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.get(session['user_id'])
    if user.is_banned:
        return jsonify({'error': 'User is banned'}), 403
    
    quantity = int(request.form.get('quantity', 1))
    validity_type = request.form.get('validity_type')
    
    # Check if user has enough balance (admin can generate free)
    if user.role != 'admin':
        cost = quantity * 10  # Example: 10 per key
        if user.balance < cost:
            return jsonify({'error': 'Insufficient balance'}), 400
        user.balance -= cost
    
    keys_generated = []
    for _ in range(quantity):
        key_str = generate_key()
        expiry = calculate_expiry(validity_type)
        
        new_key = Key(
            key=key_str,
            user_id=user.id,
            validity_type=validity_type,
            validity_days=1 if validity_type == 'day' else 7 if validity_type == 'week' else 30 if validity_type == 'month' else 1,
            expires_at=expiry
        )
        db.session.add(new_key)
        keys_generated.append(key_str)
    
    # Log transaction
    if user.role != 'admin':
        transaction = Transaction(
            user_id=user.id,
            amount=-quantity * 10,
            type='debit',
            description=f'Generated {quantity} key(s)'
        )
        db.session.add(transaction)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'keys': keys_generated,
        'message': f'Generated {quantity} key(s) successfully'
    })

@app.route('/keys')
def view_keys():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        keys = Key.query.all()
    else:
        keys = Key.query.filter_by(user_id=user.id).all()
    
    return render_template('keys.html', keys=keys, user=user, now=datetime.utcnow())

@app.route('/users')
def manage_users():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('users.html', users=users, user=user)

@app.route('/ban_user/<int:user_id>', methods=['POST'])
def ban_user(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    admin = User.query.get(session['user_id'])
    if admin.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if user:
        user.is_banned = True
        db.session.commit()
        return jsonify({'success': True, 'message': f'User {user.username} has been banned'})
    
    return jsonify({'error': 'User not found'}), 404

@app.route('/unban_user/<int:user_id>', methods=['POST'])
def unban_user(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    admin = User.query.get(session['user_id'])
    if admin.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if user:
        user.is_banned = False
        db.session.commit()
        return jsonify({'success': True, 'message': f'User {user.username} has been unbanned'})
    
    return jsonify({'error': 'User not found'}), 404

@app.route('/delete_key/<int:key_id>', methods=['POST'])
def delete_key(key_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    key = Key.query.get(key_id)
    if key:
        db.session.delete(key)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Key deleted successfully'})
    
    return jsonify({'error': 'Key not found'}), 404

@app.route('/extend_key/<int:key_id>', methods=['POST'])
def extend_key(key_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    key = Key.query.get(key_id)
    if key:
        # Extend by 30 days
        key.expires_at = key.expires_at + timedelta(days=30)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Key extended successfully'})
    
    return jsonify({'error': 'Key not found'}), 404

@app.route('/check_key', methods=['POST'])
def check_key():
    key_str = request.form.get('key')
    key = Key.query.filter_by(key=key_str).first()
    
    if not key:
        return jsonify({'valid': False, 'message': 'Invalid key'})
    
    if not key.is_active:
        return jsonify({'valid': False, 'message': 'Key is inactive'})
    
    if key.is_used:
        return jsonify({'valid': False, 'message': 'Key already used'})
    
    if key.expires_at < datetime.utcnow():
        return jsonify({'valid': False, 'message': 'Key has expired'})
    
    return jsonify({
        'valid': True,
        'key': key.key,
        'validity_type': key.validity_type,
        'expires_at': key.expires_at.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/use_key', methods=['POST'])
def use_key():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.get(session['user_id'])
    if user.is_banned:
        return jsonify({'error': 'User is banned'}), 403
    
    key_str = request.form.get('key')
    key = Key.query.filter_by(key=key_str).first()
    
    if not key:
        return jsonify({'valid': False, 'message': 'Invalid key'})
    
    if not key.is_active:
        return jsonify({'valid': False, 'message': 'Key is inactive'})
    
    if key.is_used:
        return jsonify({'valid': False, 'message': 'Key already used'})
    
    if key.expires_at < datetime.utcnow():
        return jsonify({'valid': False, 'message': 'Key has expired'})
    
    # Use the key
    key.is_used = True
    key.used_by = user.id
    key.used_at = datetime.utcnow()
    
    # Add balance to user (example: 100 per key)
    user.balance += 100
    
    transaction = Transaction(
        user_id=user.id,
        amount=100,
        type='credit',
        description=f'Used key: {key.key}'
    )
    db.session.add(transaction)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Key used successfully!',
        'balance': user.balance
    })

@app.route('/referrals')
def manage_referrals():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    referrals = Referral.query.filter_by(referrer_id=user.id).all()
    
    return render_template('referrals.html', user=user, referrals=referrals)

@app.route('/create_referral', methods=['POST'])
def create_referral():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    username = request.form.get('username')
    new_user = User.query.filter_by(username=username).first()
    
    if not new_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if already referred
    existing = Referral.query.filter_by(referred_id=new_user.id).first()
    if existing:
        return jsonify({'error': 'User already has a referrer'}), 400
    
    referral = Referral(
        referrer_id=user.id,
        referred_id=new_user.id
    )
    db.session.add(referral)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Referral created successfully'})

@app.route('/api/stats')
def api_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_banned=False).count(),
        'total_keys': Key.query.count(),
        'active_keys': Key.query.filter_by(is_active=True, is_used=False).count(),
        'used_keys': Key.query.filter_by(is_used=True).count(),
        'total_balance': db.session.query(db.func.sum(User.balance)).scalar() or 0,
        'total_transactions': Transaction.query.count()
    }
    
    return jsonify(stats)

@app.route('/update_balance', methods=['POST'])
def update_balance():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    admin = User.query.get(session['user_id'])
    if admin.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user_id = request.form.get('user_id')
    amount = float(request.form.get('amount'))
    
    user = User.query.get(user_id)
    if user:
        user.balance += amount
        transaction = Transaction(
            user_id=user.id,
            amount=amount,
            type='credit' if amount > 0 else 'debit',
            description=f'Balance update by admin: {amount}'
        )
        db.session.add(transaction)
        db.session.commit()
        return jsonify({'success': True, 'new_balance': user.balance})
    
    return jsonify({'error': 'User not found'}), 404

@app.route('/apk_connect')
def apk_connect():
    """APK Connection endpoint for app integration"""
    return jsonify({
        'status': 'active',
        'panel': 'PUSHKAR VVIP PANNEL',
        'version': '2.0',
        'api_endpoints': {
            'check_key': '/check_key',
            'use_key': '/use_key',
            'stats': '/api/stats'
        },
        'server_time': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
