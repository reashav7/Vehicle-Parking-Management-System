from flask import Flask, render_template, request, redirect, url_for, flash, session
from app import app
from models import db, User, Parking_Lot, Parking_Spot, Reservation
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import or_, case
from datetime import datetime, timedelta
import pytz
from flask_login import login_required
from sqlalchemy.orm import joinedload
import io
import base64
import os

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
    
    session['user_id'] = user.id  
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
    
    session['user_id'] = user.id
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

##-------------decorator for admin required--------------------##

def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to log in first', 'danger')
            return redirect(url_for('admin_login'))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            flash('You do not have permission to access this page', 'danger')
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)
    return inner

##-------------------------------------------------------------##

  
    
@app.route('/user_dashboard/profile/')
@auth_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user = user)


@app.route('/user_dashboard/profile/', methods=['POST'])
@auth_required
def profile_post():
    name = request.form.get('name')
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    
    if not name or not username or not cpassword:
        flash('All fields are required', 'danger')
        return redirect(url_for('profile'))
    
    user = User.query.get(session['user_id'])
    if not check_password_hash(user.passhash, cpassword):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('profile'))
    
    if username != user.username:
        new_user = User.query.filter_by(username=username).first()
        if new_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('profile'))
        
    user.name = name
    user.username = username
    user.passhash = generate_password_hash(password)
    db.session.commit()
    flash('Profile updated successfully', 'success')
    if user.is_admin:
        return redirect(url_for('admin_dashboard', user_id=user.id))
    else:
        return redirect(url_for('user_dashboard', user_id=user.id))
    
    
    


@app.route('/user_dashboard/logout/')
@auth_required
def user_logout():
    session.pop('user_id')
    flash('You have been logged out', 'success')
    return redirect(url_for('user_login'))

@app.route('/admin_dashboard/logout/')
@admin_required
def admin_logout():
    session.pop('user_id')
    flash('You have been logged out', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin-dashboard/<int:user_id>')
@admin_required
def admin_dashboard(user_id):
        user = User.query.get(session['user_id'])
        parking_lots = Parking_Lot.query.all()
        return render_template('admin_dashboard.html', user=user, parking_lots=parking_lots, name=user.name, username=user.username)
    
    
    
    
@app.route('/admin_dashboard/add_parking_lot')
@admin_required
def add_parking_lot():
    return render_template('add_parking_lot.html')



@app.route('/admin_dashboard/add_parking_lot', methods=['POST'])
@admin_required
def add_parking_lot_post():
    prime_location_name = request.form.get('prime_location_name')
    address = request.form.get('address')
    pin_code = request.form.get('pin_code')
    price_per_hour = request.form.get('price_per_hour')
    maximum_spots = request.form.get('maximum_spots')

    if not prime_location_name or not address or not pin_code or not price_per_hour or not maximum_spots:
        flash('All fields are required', 'danger')
        return render_template('add_parking_lot.html')

    try:
        price_per_hour = float(price_per_hour)
        maximum_spots = int(maximum_spots)
    except ValueError:
        flash("Invalid input for price or maximum spots", "danger")
        return render_template('add_parking_lot.html')


    parking_lot = Parking_Lot(
        prime_location_name=prime_location_name,
        address=address,
        pin_code=pin_code,
        price_per_hour=price_per_hour,
        maximum_spots=maximum_spots
    )
    db.session.add(parking_lot)
    db.session.commit()  

    
    auto_spots = int(maximum_spots * 0.8)
    for _ in range(auto_spots):
        spot = Parking_Spot(lot_id=parking_lot.id, status='A')  
        db.session.add(spot)
    db.session.commit()

    flash(f'Parking lot added with {auto_spots} spot(s) initialized.', 'success')
    return redirect(url_for('admin_dashboard', user_id=session['user_id']))




@app.route('/admin_dashboard/edit_parking_lot/<int:lot_id>')
@admin_required
def edit_parking_lot(lot_id):
    parking_lot = Parking_Lot.query.get(lot_id)
    if not parking_lot:
        flash('Parking lot not found', 'danger')
        return redirect(url_for('admin_dashboard', user_id=session['user_id']))
    
    return render_template('edit_parking_lot.html', parking_lot=parking_lot)


@app.route('/admin_dashboard/edit_parking_lot/<int:lot_id>', methods=['POST'])
@admin_required
def edit_parking_lot_post(lot_id):
    parking_lot = Parking_Lot.query.get(lot_id)
    if not parking_lot:
        flash('Parking lot not found', 'danger')
        return redirect(url_for('admin_dashboard', user_id=session['user_id']))
    
    prime_location_name = request.form.get('prime_location_name')
    address = request.form.get('address')
    pin_code = request.form.get('pin_code')
    price_per_hour = request.form.get('price_per_hour')
    maximum_spots = request.form.get('maximum_spots')
    
    if not prime_location_name or not address or not pin_code or not price_per_hour or not maximum_spots:
        flash('All fields are required', 'danger')
        return redirect(url_for('edit_parking_lot', lot_id=lot_id))
    
    parking_lot.prime_location_name = prime_location_name
    parking_lot.address = address
    parking_lot.pin_code = pin_code
    parking_lot.price_per_hour = float(price_per_hour)
    parking_lot.maximum_spots = int(maximum_spots)
    
    db.session.commit()
    
    flash('Parking lot updated successfully', 'success')
    return redirect(url_for('admin_dashboard', user_id=session['user_id']))






@app.route('/admin_dashboard/delete_parking_lot/<int:lot_id>', methods=['POST'])
@admin_required
def delete_parking_lot(lot_id):
    parking_lot = Parking_Lot.query.get(lot_id)
    if not parking_lot:
        flash('Parking lot not found', 'danger')
        return redirect(url_for('admin_dashboard', user_id=session['user_id']))
    
    # Check if any spot is occupied
    occupied_spots = Parking_Spot.query.filter_by(lot_id=lot_id, status='R').count()
    
    if occupied_spots > 0:
        flash('Cannot delete parking lot. Some spots are still reserved.', 'danger')
        return redirect(url_for('admin_dashboard', user_id=session['user_id']))

    # Delete all spots related to the lot
    Parking_Spot.query.filter_by(lot_id=lot_id).delete()


    db.session.delete(parking_lot)
    db.session.commit()

    flash('Parking lot and all associated available spots deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard', user_id=session['user_id']))




@app.route('/admin_dashboard/view_parking_spots/<int:lot_id>')
@admin_required
def view_parking_spots(lot_id):
    parking_lot = Parking_Lot.query.get(lot_id)
    if not parking_lot:
        flash('Parking lot not found', 'danger')
        return redirect(url_for('admin_dashboard', user_id=session['user_id']))
    
    return render_template('view_parking_spots.html', parking_lot=parking_lot, parking_spots=parking_lot.parking_spots)





@app.route('/admin_dashboard/add_parking_spot/<int:lot_id>', methods=['GET', 'POST'])
@admin_required
def add_parking_spot(lot_id):
    parking_lot = Parking_Lot.query.get(lot_id)
    if not parking_lot:
        flash('Parking lot not found', 'danger')
        return redirect(url_for('admin_dashboard', user_id=session['user_id']))

    if request.method == 'POST':
        num_spots = request.form.get('num_spots')
        try:
            num_spots = int(num_spots)
            if num_spots <= 0:
                flash('Please enter a positive number', 'danger')
                return render_template('add_parking_spot.html', parking_lot=parking_lot)

            current_spot_count = Parking_Spot.query.filter_by(lot_id=lot_id).count()
            if current_spot_count + num_spots > parking_lot.maximum_spots:
                flash(f'Cannot add {num_spots} spot(s). Lot can only have {parking_lot.maximum_spots - current_spot_count} more.', 'danger')
                return render_template('add_parking_spot.html', parking_lot=parking_lot)

            for _ in range(num_spots):
                new_spot = Parking_Spot(lot_id=lot_id, status='A')  
                db.session.add(new_spot)

            db.session.commit()
            flash(f'{num_spots} parking spot(s) added successfully.', 'success')
            return redirect(url_for('view_parking_spots', lot_id=lot_id))

        except ValueError:
            flash('Please enter a valid number', 'danger')

    return render_template('add_parking_spot.html', parking_lot=parking_lot)



@app.route('/admin_dashboard/parking_spot/<int:spot_id>')
@admin_required
def parking_spot(spot_id):
    spot = Parking_Spot.query.get(spot_id)
    if not spot:
        flash("Parking spot not found", "danger")
        return redirect(url_for('admin_dashboard', user_id=session['user_id']))

    return render_template('parking_spot.html', spot=spot)



@app.route('/admin_dashboard/delete_parking_spot/<int:spot_id>', methods=['POST'])
@admin_required
def delete_parking_spot(spot_id):
    spot = Parking_Spot.query.get(spot_id)
    if not spot:
        flash('Parking spot not found', 'danger')
        return redirect(url_for('admin_dashboard', user_id=session['user_id']))
    
    lot_id = spot.lot_id
    db.session.delete(spot)
    db.session.commit()
    flash(f"Spot #{spot_id} deleted successfully", "success")
    return redirect(url_for('view_parking_spots', lot_id=lot_id))





@app.route('/admin_dashboard/users')
@admin_required
def users_list():
    users = User.query.all()

    user_data = []
    for user in users:
        # Fetch all distinct vehicle numbers used by this user
        reservations = Reservation.query.filter_by(user_id=user.id).all()
        vehicle_numbers = list({r.vehicle_number for r in reservations})  # Use set to remove duplicates
        
        if vehicle_numbers:
            vehicle_display = ", ".join(vehicle_numbers)
        else:
            vehicle_display = "NA"

        user_data.append({
            'name': user.name,
            'username': user.username,
            'is_admin': user.is_admin,
            'vehicle_numbers': vehicle_display
        })

    return render_template('users_list.html', users=user_data)




@app.route('/admin_dashboard/reservation-history')
@admin_required
def admin_reservation_history():
    all_reservations = Reservation.query.options(
        joinedload(Reservation.parking_spot).joinedload(Parking_Spot.parking_lot),
        joinedload(Reservation.user)
    ).order_by(
        case((Reservation.end_time == None, 0), else_=1),
        Reservation.start_time.desc()
    ).all()

    ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.now(ist)

    for res in all_reservations:
        if res.start_time.tzinfo is None:
            res.start_time = ist.localize(res.start_time)
        if res.end_time and res.end_time.tzinfo is None:
            res.end_time = ist.localize(res.end_time)

    return render_template(
        'admin_reservation_history.html',
        all_reservations=all_reservations,
        now_ist=now_ist
    )
    
    
    
    





##----------------------user dashboard----------------------##



@app.route('/user-dashboard/<int:user_id>')
@auth_required
def user_dashboard(user_id):
    user = User.query.get_or_404(session['user_id'])

    recent_reservations = Reservation.query.options(
        joinedload(Reservation.parking_spot).joinedload(Parking_Spot.parking_lot)
    ).filter_by(user_id=user.id).order_by(
        case((Reservation.end_time == None, 0), else_=1),
        Reservation.start_time.desc()
    ).limit(3).all()

    query = request.args.get("query")

    if query:
        matching_lots = Parking_Lot.query.filter(
            or_(
                Parking_Lot.prime_location_name.ilike(f"%{query}%"),
                Parking_Lot.address.ilike(f"%{query}%"),
                Parking_Lot.pin_code.ilike(f"%{query}%")
            )
        ).all()

        if not matching_lots:
            flash(f"No parking lots found matching: '{query}'", "warning")

        matching_ids = [lot.id for lot in matching_lots]
        remaining_lots = Parking_Lot.query.filter(
            ~Parking_Lot.id.in_(matching_ids)
        ).all()

        parking_lots = matching_lots + remaining_lots
    else:
        parking_lots = Parking_Lot.query.all()

    for lot in parking_lots:
        lot.available_spots_count = Parking_Spot.query.filter_by(lot_id=lot.id, status='A').count()

    return render_template(
        'user_dashboard.html',
        user=user,
        user_id=user.id,
        name=user.name,
        username=user.username,
        recent_reservations=recent_reservations,
        parking_lots=parking_lots,
        scroll_to_search=True if query else False
    )





@app.route('/user_dashboard/book/<int:lot_id>', methods=['GET', 'POST'])
@auth_required
def book_parking_spot(lot_id):
    lot = Parking_Lot.query.get_or_404(lot_id)
    user = User.query.get(session['user_id'])

    # Get the first available spot in both GET and POST
    spot = Parking_Spot.query.filter_by(lot_id=lot_id, status='A').first()

    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number')
        spot_id = request.form.get('spot_id')

        if not vehicle_number:
            flash("Please enter your vehicle number.", "danger")
            return render_template('book_parking_spot.html', lot=lot, user=user, spot=spot)

        if not spot:
            flash("No available spots in this parking lot.", "danger")
            return redirect(url_for('user_dashboard', user_id=user.id))

        if spot.status != 'A':
            flash("Selected spot is no longer available.", "danger")
            return redirect(url_for('user_dashboard', user_id=user.id))

        
        spot.status = 'R'
        db.session.commit()

        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        reservation = Reservation(
            user_id=user.id,
            spot_id=spot.id,
            date=now.date(),
            start_time=now,
            end_time=None,  
            vehicle_number=vehicle_number,
            hours_parked=0,
            parking_cost_per_hour=lot.price_per_hour,
            total_parking_cost=0.0
)


        db.session.add(reservation)
        db.session.commit()

        flash(f"Spot #{spot.id} booked successfully!", "success")
        return redirect(url_for('user_dashboard', user_id=user.id))

    return render_template('book_parking_spot.html', lot=lot, user=user, spot=spot)




@app.route('/user_dashboard/release/<int:reservation_id>', methods=['GET', 'POST'])
@auth_required
def release_parking_spot(reservation_id):
    user_id = session.get('user_id')
    reservation = Reservation.query.get_or_404(reservation_id)

    if reservation.user_id != user_id:
        flash("You do not have permission to release this reservation.", "danger")
        return redirect(url_for('user_dashboard', user_id=user_id))

    spot = Parking_Spot.query.get(reservation.spot_id)
    if not spot:
        flash("Associated parking spot not found.", "danger")
        return redirect(url_for('user_dashboard', user_id=user_id))

    lot = spot.parking_lot

    if reservation.end_time:
        flash("This parking reservation is already marked as completed.", "warning")
        return redirect(url_for('user_dashboard', user_id=user_id))

    ist = pytz.timezone("Asia/Kolkata")
    current_time = datetime.now(ist)

    
    if reservation.start_time.tzinfo is None or reservation.start_time.tzinfo.utcoffset(reservation.start_time) is None:
        start_time_aware = ist.localize(reservation.start_time)
    else:
        start_time_aware = reservation.start_time

    duration = current_time - start_time_aware
    hours = round(duration.total_seconds() / 3600, 2)
    hours = max(hours, 1)
    duration_minutes = int(duration.total_seconds() // 60)
    duration_str = f"{duration_minutes // 60} hr {duration_minutes % 60} min"


    if request.method == 'POST':
        reservation.end_time = current_time
        reservation.hours_parked = hours
        reservation.total_parking_cost = hours * reservation.parking_cost_per_hour

        spot.status = 'A'

        db.session.commit()

        flash(f"Spot #{spot.id} released successfully. Total cost: ₹{reservation.total_parking_cost:.2f}", "success")
        return redirect(url_for('user_dashboard', user_id=user_id))

    return render_template(
        'release_parking_spot.html',
        reservation=reservation,
        lot=lot,
        spot=spot,
        simulated_end_time=current_time,
        total_cost=hours * reservation.parking_cost_per_hour,
        duration_str=duration_str
    )
    
    

@app.route('/user_dashboard/reservation-history/<int:user_id>')
@auth_required
def reservation_history(user_id):
    user = User.query.get_or_404(session['user_id'])

    all_reservations = Reservation.query.options(
        joinedload(Reservation.parking_spot).joinedload(Parking_Spot.parking_lot)
    ).filter_by(user_id=user.id).order_by(
        case((Reservation.end_time == None, 0), else_=1),
        Reservation.start_time.desc()
    ).all()

    ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.now(ist)

    
    for res in all_reservations:
        if res.start_time.tzinfo is None:
            res.start_time = ist.localize(res.start_time)
        if res.end_time and res.end_time.tzinfo is None:
            res.end_time = ist.localize(res.end_time)

    return render_template(
        'reservation_history.html',
        user=user,
        all_reservations=all_reservations,
        now_ist=now_ist
    )
    








