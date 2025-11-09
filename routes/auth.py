from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, Staff, db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'staff':
            return redirect(url_for('staff.dashboard'))
        elif current_user.role == 'parent':
            return redirect(url_for('parent.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        staff_id = request.form.get('staff_id')
        parent_id = request.form.get('parent_id')
        role = request.form.get('role')
        
        user = None
        
        if role == 'admin':
            user = User.query.filter_by(email=email, role='admin').first()
        elif role == 'staff':
            if staff_id:
                staff = Staff.query.filter_by(staff_id=staff_id).first()
                if staff and check_password_hash(staff.password, password):
                    user = User.query.filter_by(email=staff.email, role='staff').first()
                    if not user:
                        # Create user entry for staff if doesn't exist
                        user = User(
                            email=staff.email,
                            password=staff.password,
                            name=staff.name,
                            role='staff',
                            status='approved'
                        )
                        db.session.add(user)
                        db.session.commit()
                    if user:
                        login_user(user)
                        return redirect(url_for('staff.dashboard'))
                else:
                    flash('Invalid Staff ID or password. Please try again.', 'danger')
        elif role == 'parent':
            if parent_id:
                user = User.query.filter_by(parent_id=parent_id, role='parent').first()
        
        if user:
            if role == 'staff':
                # Staff login is handled above
                pass
            elif check_password_hash(user.password, password):
                if user.status == 'approved' or user.role == 'admin':
                    login_user(user)
                    if user.role == 'admin':
                        return redirect(url_for('admin.dashboard'))
                    elif user.role == 'parent':
                        return redirect(url_for('parent.dashboard'))
                else:
                    flash('Your account is pending approval. Please wait for admin approval.', 'warning')
            else:
                flash('Invalid credentials. Please try again.', 'danger')
        elif role != 'staff':
            flash('Invalid credentials. Please try again.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('parent.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        address = request.form.get('address')
        phone = request.form.get('phone')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')
        
        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email,
            password=hashed_password,
            name=name,
            address=address,
            phone=phone,
            role='parent',
            status='pending'
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please wait for admin approval. You will receive your unique Parent ID after approval.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

