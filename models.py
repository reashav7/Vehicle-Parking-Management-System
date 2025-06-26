from app import app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    
class Parking_Lot(db.Model):
    __tablename__ = 'parking_lot'
    
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(128), nullable=False)
    pin_code = db.Column(db.String(6), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    maximum_spots = db.Column(db.Integer, nullable=False)
    
    parking_spots = db.relationship('Parking_Spot', backref='parking_lot', lazy=True)

    
class Parking_Spot(db.Model):  
    __tablename__ = 'parking_spot'
    
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(1), default='A', nullable=False)  
    
    reservations = db.relationship('Reservation', backref='parking_spot', lazy=True)
    
class Reservation(db.Model):
    __tablename__ = 'reservation'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False)
    hours_parked = db.Column(db.Integer, nullable=False)
    parking_cost_per_hour = db.Column(db.Float, nullable=False)
    total_parking_cost = db.Column(db.Float, nullable=False)
    
    
    
with app.app_context():
    db.create_all()
    
