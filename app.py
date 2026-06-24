# app.py - ASHWIN VIP PANNEL
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
import string
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'ashwin-vip-panel-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ashwin_vip_panel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Pricing (INR) per key by validity type — adjustable
PRICES = {
    'day': 75,
    'week': 400,
    'month': 1500,
    'session': 25
}
# ------------------- MODELS -------------------
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
    referred_user = db.relationship('User', foreign_keys=[referred_id], lazy='joined')


class SellerPermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    allowed = db.Column(db.Boolean, default=False)

# Create tables and admin user
with app.app_context():
    db.create_all()
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

# ------------------- HELPERS -------------------
def generate_key(length=16):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def calculate_expiry(validity_type):
    if validity_type == 'day':
        return datetime.utcnow() + timedelta(days=1)
    elif validity_type == 'week':
        return datetime.utcnow() + timedelta(weeks=1)
    elif validity_type == 'month':
        return datetime.utcnow() + timedelta(days=30)
    elif validity_type == 'session':
        return datetime.utcnow() + timedelta(hours=24)
    return datetime.utcnow() + timedelta(days=1)

# ------------------- ROUTES -------------------
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

@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for Android app login - KEY ONLY"""
    key_str = request.form.get('key') or (request.json.get('key') if request.json else None)
    
    if not key_str:
        return jsonify({'success': False, 'error': 'License key required'}), 400
    
    # Validate key
    key = Key.query.filter_by(key=key_str).first()
    if not key:
        return jsonify({'success': False, 'error': 'Invalid key'}), 401
    if not key.is_active:
        return jsonify({'success': False, 'error': 'Key is inactive'}), 403
    if key.is_used:
        return jsonify({'success': False, 'error': 'Key already used'}), 403
    if key.expires_at < datetime.utcnow():
        return jsonify({'success': False, 'error': 'Key has expired'}), 403
    
    # Log in user associated with this key (key owner or default ASHWIN)
    if key.user_id:
        user = User.query.get(key.user_id)
    else:
        user = User.query.filter_by(username='ASHWIN').first()
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    if user.is_banned:
        return jsonify({'success': False, 'error': 'Account banned'}), 403
    
    # Set session
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    
    return jsonify({
        'success': True,
        'message': 'Login successful - Key validated',
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'balance': user.balance
        }
    }), 200

@app.route('/apk_login', methods=['POST'])
def apk_login():
    """APK Login endpoint - Validates license key and returns key details"""
    data = request.get_json()
    if not data or 'key' not in data:
        return jsonify({'success': False, 'message': 'Key required'}), 400
    
    key_str = data['key'].strip()
    key = Key.query.filter_by(key=key_str).first()
    
    if not key:
        return jsonify({'success': False, 'message': 'Invalid key'}), 404
    
    if not key.is_active:
        return jsonify({'success': False, 'message': 'Key is inactive'}), 403
    
    if key.is_used:
        return jsonify({'success': False, 'message': 'Key already used'}), 403
    
    if key.expires_at < datetime.utcnow():
        return jsonify({'success': False, 'message': 'Key has expired'}), 403
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'data': {
            'key': key.key,
            'type': key.validity_type,
            'expires': key.expires_at.isoformat()
        }
    }), 200

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.is_banned:
        session.clear()
        return redirect(url_for('login'))

    total_users = User.query.count()
    active_keys = Key.query.filter_by(is_active=True, is_used=False).count()
    total_keys = Key.query.count()
    user_keys = Key.query.filter_by(user_id=user.id).order_by(Key.created_at.desc()).all()
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.created_at.desc()).limit(10).all()

    return render_template('dashboard.html',
                           user=user,
                           total_users=total_users,
                           active_keys=active_keys,
                           total_keys=total_keys,
                           user_keys=user_keys,
                           transactions=transactions,
                           prices=PRICES,
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

    # Cost for non-admin users (based on validity type)
    price_per_key = PRICES.get(validity_type, PRICES['day'])
    if user.role != 'admin':
        cost = quantity * price_per_key
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

    if user.role != 'admin':
        transaction = Transaction(
            user_id=user.id,
            amount=-cost,
            type='debit',
            description=f'Generated {quantity} key(s) ({validity_type})'
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
    return render_template('users.html', users=users, user=user, now=datetime.utcnow())

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
        return jsonify({'success': True, 'message': f'User {user.username} banned'})
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
        return jsonify({'success': True, 'message': f'User {user.username} unbanned'})
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
        return jsonify({'success': True, 'message': 'Key deleted'})
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
        key.expires_at = key.expires_at + timedelta(days=30)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Key extended by 30 days'})
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

    key.is_used = True
    key.used_by = user.id
    key.used_at = datetime.utcnow()
    user.balance += 100  # Reward for using key
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
    return render_template('referrals.html', user=user, referrals=referrals, now=datetime.utcnow())

@app.route('/create_referral', methods=['POST'])
@app.route('/create_referral/', methods=['POST'])
def create_referral():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user or user.role != 'admin':
        return redirect(url_for('dashboard'))

    username = request.form.get('username')
    new_user = User.query.filter_by(username=username).first()
    if not new_user:
        return redirect(url_for('manage_referrals'))

    existing = Referral.query.filter_by(referred_id=new_user.id).first()
    if existing:
        return redirect(url_for('manage_referrals'))

    referral = Referral(referrer_id=user.id, referred_id=new_user.id)
    db.session.add(referral)
    db.session.commit()
    return redirect(url_for('manage_referrals'))

@app.route('/authorize_seller', methods=['POST'])
@app.route('/authorize_seller/', methods=['POST'])
def authorize_seller():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    owner = User.query.get(session['user_id'])
    if not owner or owner.username != 'ASHWIN':
        return jsonify({'error': 'Unauthorized'}), 403

    admin_username = request.form.get('admin_username')
    allow = request.form.get('allow', '0')
    target = User.query.filter_by(username=admin_username).first()
    if not target:
        return jsonify({'error': 'User not found'}), 404
    if target.role != 'admin':
        return jsonify({'error': 'Target user is not an admin'}), 400

    perm = SellerPermission.query.filter_by(user_id=target.id).first()
    if not perm:
        perm = SellerPermission(user_id=target.id, allowed=(allow == '1'))
        db.session.add(perm)
    else:
        perm.allowed = (allow == '1')
    db.session.commit()
    return redirect(url_for('manage_referrals'))

@app.route('/create_user', methods=['POST'])
@app.route('/create_user/', methods=['POST'])
def create_user():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    owner = User.query.get(session['user_id'])
    if not owner or owner.username != 'ASHWIN':
        return redirect(url_for('dashboard'))

    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    balance = float(request.form.get('balance', 0.0))
    
    if not username or not password:
        return redirect(url_for('manage_referrals'))
    existing = User.query.filter_by(username=username).first()
    if existing:
        return redirect(url_for('manage_referrals'))

    new_user = User(
        username=username,
        password=generate_password_hash(password),
        role=role,
        balance=balance
    )
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('manage_referrals'))

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
    return jsonify({
        'status': 'active',
        'panel': 'ASHWIN VIP PANNEL',
        'version': '2.1',
        'api_endpoints': {
            'check_key': '/check_key',
            'use_key': '/use_key',
            'stats': '/api/stats',
            'apk_login': '/apk_login'
        },
        'server_time': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 2487))
    app.run(debug=False, host='0.0.0.0', port=port)

