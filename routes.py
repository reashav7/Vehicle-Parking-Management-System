from flask import Flask, render_template
from app import app

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user-login')
def user_login():
    return render_template('user_login.html')

@app.route('/admin-login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/register')
def register():
    return render_template('register.html')