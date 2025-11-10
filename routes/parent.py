from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import User, Child, Upload, Visit, Guidance, db
from datetime import datetime
from sqlalchemy import func
import os
import json

parent_bp = Blueprint('parent', __name__)

# --------------------------
# Access Control
# --------------------------
def parent_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'parent':
            flash('Parent access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# --------------------------
# Dashboard
# --------------------------
@parent_bp.route('/dashboard')
@login_required
@parent_required
def dashboard():
    if current_user.status != 'approved':
        flash('Your account is pending approval. Please wait for admin approval.', 'warning')
        return render_template('parent/pending.html')

    children = Child.query.filter_by(parent_id=current_user.id).all()
    recent_uploads = Upload.query.filter_by(parent_id=current_user.id).order_by(Upload.upload_date.desc()).limit(5).all()

    # ✅ FIXED: Use func.date() to ensure datetime comparison works
    today = datetime.now().date()
    upcoming_visits = Visit.query.filter(
        Visit.parent_id == current_user.id,
        Visit.status == 'scheduled',
        func.date(Visit.visit_date) >= today
    ).order_by(Visit.visit_date.asc()).limit(5).all()

    pending_uploads = Upload.query.filter_by(parent_id=current_user.id, status='pending').count()
    verified_uploads = Upload.query.filter_by(parent_id=current_user.id, status='verified').count()

    # Debug info (safe to remove after testing)
    print("DEBUG Upcoming Visits:", [(v.id, v.parent_id, v.visit_date, v.status) for v in upcoming_visits])

    return render_template(
        'parent/dashboard.html',
        children=children,
        recent_uploads=recent_uploads,
        upcoming_visits=upcoming_visits,
        pending_uploads=pending_uploads,
        verified_uploads=verified_uploads
    )

# --------------------------
# Children
# --------------------------
@parent_bp.route('/children')
@login_required
@parent_required
def view_children():
    if current_user.status != 'approved':
        flash('Your account is pending approval.', 'warning')
        return redirect(url_for('parent.dashboard'))
    
    children = Child.query.filter_by(parent_id=current_user.id).all()
    return render_template('parent/children.html', children=children)

# --------------------------
# Upload Documents
# --------------------------
@parent_bp.route('/uploads', methods=['GET', 'POST'])
@login_required
@parent_required
def manage_uploads():
    if current_user.status != 'approved':
        flash('Your account is pending approval.', 'warning')
        return redirect(url_for('parent.dashboard'))
    
    if request.method == 'POST':
        child_id = request.form.get('child_id')
        upload_type = request.form.get('upload_type')
        file = request.files.get('file')
        
        if not file or not file.filename:
            flash('Please select a file.', 'danger')
            return redirect(url_for('parent.manage_uploads'))
        
        child = Child.query.get(int(child_id))
        if not child or child.parent_id != current_user.id:
            flash('Invalid child.', 'danger')
            return redirect(url_for('parent.manage_uploads'))
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        
        upload = Upload(
            parent_id=current_user.id,
            child_id=child.id,
            upload_type=upload_type,
            file_path=f"documents/{filename}",
            status='pending'
        )
        
        db.session.add(upload)
        db.session.commit()
        
        flash('Document uploaded successfully. Waiting for staff verification.', 'success')
        return redirect(url_for('parent.manage_uploads'))
    
    children = Child.query.filter_by(parent_id=current_user.id).all()
    uploads = Upload.query.filter_by(parent_id=current_user.id).order_by(Upload.upload_date.desc()).all()
    return render_template('parent/uploads.html', children=children, uploads=uploads)

# --------------------------
# Visits
# --------------------------
@parent_bp.route('/visits')
@login_required
@parent_required
def view_visits():
    if current_user.status != 'approved':
        flash('Your account is pending approval.', 'warning')
        return redirect(url_for('parent.dashboard'))
    
    visits = Visit.query.filter_by(parent_id=current_user.id).order_by(Visit.visit_date.desc()).all()
    return render_template('parent/visits.html', visits=visits)

# --------------------------
# Guidance
# --------------------------
@parent_bp.route('/guidance')
@login_required
@parent_required
def view_guidance():
    guidance_list = Guidance.query.order_by(Guidance.created_at.desc()).all()
    return render_template('parent/guidance.html', guidance_list=guidance_list)

# --------------------------
# Profile
# --------------------------
@parent_bp.route('/profile')
@login_required
@parent_required
def profile():
    return render_template('parent/profile.html')

@parent_bp.route('/profile/update', methods=['POST'])
@login_required
@parent_required
def update_profile():
    current_user.name = request.form.get('name', current_user.name)
    current_user.address = request.form.get('address', current_user.address)
    current_user.phone = request.form.get('phone', current_user.phone)
    
    db.session.commit()
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('parent.profile'))
