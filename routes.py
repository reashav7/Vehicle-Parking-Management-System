from flask import Flask, render_template, request, redirect, url_for, flash, session
from app import app
from models import db, User, Parking_Lot, Parking_Spot, Reservation
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    name = request.form.get('name')
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    if not name or not username or not password or not confirm_password:
        flash('All fields are required', 'danger')
        return render_template('register.html')
    
    if password != confirm_password:
        flash('Passwords do not match', 'danger')
        return render_template('register.html')
    
    user = User.query.filter_by(username=username).first()
        
    if user:
        flash('Username already exists', 'danger')
        return render_template('register.html')
    
    password_hash = generate_password_hash(password)
    new_user = User(username=username, passhash=password_hash, name=name)
    db.session.add(new_user)
    db.session.commit()
    flash('Registration successful! Please log in.', 'success')
    return redirect(url_for('user_login'))
    


@app.route('/user-login')
def user_login():
    return render_template('user_login.html')

@app.route('/user-login', methods=['POST'])
def user_login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Username and password are required', 'danger')
        return render_template('user_login.html')
    
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.passhash, password):
        flash('Invalid username or password', 'danger')
        return render_template('user_login.html')
    
    session['user_id'] = user.id  # Store user ID in session
    flash('Login successful!', 'success')
    return redirect(url_for('user_dashboard', user_id=user.id))


@app.route('/admin-login')
def admin_login():
    return render_template('admin_login.html')


@app.route('/admin-login', methods=['POST'])
def admin_login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Username and password are required', 'danger')
        return render_template('admin_login.html')
    
    user = User.query.filter_by(username=username, is_admin=True).first()
    if not user or not check_password_hash(user.passhash, password):
        flash('Invalid username or password', 'danger')
        return render_template('admin_login.html')
    
    session['user_id'] = user.id  # Store admin user ID in session
    flash('Admin login successful!', 'success')
    return redirect(url_for('admin_dashboard', user_id=user.id))




##-------------decorator for auth required-----------------##
def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('You need to log in first', 'danger')
            return redirect(url_for('user_login'))
    return inner
##-------------------------------------------------------------##



@app.route('/user-dashboard/<int:user_id>')
@auth_required
def user_dashboard(user_id):
        user = User.query.get(session['user_id'])
        return render_template('user_dashboard.html', user=user)

@app.route('/admin-dashboard/<int:user_id>')
@auth_required
def admin_dashboard(user_id):
        user = User.query.get(session['user_id'])
        return render_template('admin_dashboard.html', user=user)
    


    
    
    
    
    
    
    
    
    