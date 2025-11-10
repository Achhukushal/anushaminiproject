from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import User, Staff, Child, Upload, Visit, db
from datetime import datetime
import os
import json
import uuid  # for unique filenames

# ------------------------------
# Blueprint Setup
# ------------------------------
staff_bp = Blueprint('staff', __name__)

# ------------------------------
# Access Control Decorator
# ------------------------------
def staff_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'staff':
            flash('Staff access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------------------
# Dashboard
# ------------------------------
@staff_bp.route('/dashboard')
@login_required
@staff_required
def dashboard():
    staff = Staff.query.filter_by(email=current_user.email).first()
    if not staff:
        flash('Staff record not found.', 'danger')
        return redirect(url_for('auth.logout'))
    
    assigned_parents = User.query.filter_by(staff_id=staff.id, role='parent', status='approved').all()
    pending_uploads = Upload.query.join(User).filter(
        User.staff_id == staff.id,
        Upload.status == 'pending'
    ).all()
    
    upcoming_visits = Visit.query.filter_by(
        staff_id=staff.id,
        status='scheduled'
    ).filter(Visit.visit_date >= datetime.now().date()).all()
    
    recent_visits = Visit.query.filter_by(staff_id=staff.id).order_by(Visit.visit_date.desc()).limit(5).all()
    
    return render_template(
        'staff/dashboard.html',
        staff=staff,
        assigned_parents=assigned_parents,
        pending_uploads=pending_uploads,
        upcoming_visits=upcoming_visits,
        recent_visits=recent_visits
    )

# ------------------------------
# View Assigned Parents
# ------------------------------
@staff_bp.route('/parents')
@login_required
@staff_required
def view_parents():
    staff = Staff.query.filter_by(email=current_user.email).first()
    if not staff:
        flash('Staff record not found.', 'danger')
        return redirect(url_for('auth.logout'))
    
    assigned_parents = User.query.filter_by(staff_id=staff.id, role='parent', status='approved').all()
    return render_template('staff/parents.html', parents=assigned_parents, staff=staff)

# ------------------------------
# View Individual Parent Details
# ------------------------------
@staff_bp.route('/parents/<int:parent_id>')
@login_required
@staff_required
def view_parent_detail(parent_id):
    staff = Staff.query.filter_by(email=current_user.email).first()
    parent = User.query.get_or_404(parent_id)
    
    if parent.staff_id != staff.id:
        flash('You are not assigned to this parent.', 'danger')
        return redirect(url_for('staff.view_parents'))
    
    children = Child.query.filter_by(parent_id=parent.id).all()
    uploads = Upload.query.filter_by(parent_id=parent.id).order_by(Upload.upload_date.desc()).all()
    visits = Visit.query.filter_by(parent_id=parent.id).order_by(Visit.visit_date.desc()).all()
    
    return render_template(
        'staff/parent_detail.html',
        parent=parent,
        children=children,
        uploads=uploads,
        visits=visits
    )

# ------------------------------
# View Uploads
# ------------------------------
@staff_bp.route('/uploads')
@login_required
@staff_required
def view_uploads():
    staff = Staff.query.filter_by(email=current_user.email).first()
    status = request.args.get('status', 'pending')
    
    query = Upload.query.join(User).filter(User.staff_id == staff.id)
    if status != 'all':
        query = query.filter(Upload.status == status)
    
    uploads = query.order_by(Upload.upload_date.desc()).all()
    return render_template('staff/uploads.html', uploads=uploads, status=status)

# ------------------------------
# Verify Uploads
# ------------------------------
@staff_bp.route('/uploads/<int:upload_id>/verify', methods=['POST'])
@login_required
@staff_required
def verify_upload(upload_id):
    staff = Staff.query.filter_by(email=current_user.email).first()
    upload = Upload.query.get_or_404(upload_id)
    
    if upload.parent.staff_id != staff.id:
        flash('You are not authorized to verify this upload.', 'danger')
        return redirect(url_for('staff.view_uploads'))
    
    action = request.form.get('action')
    feedback = request.form.get('feedback', '')
    
    if action == 'approve':
        upload.status = 'verified'
        upload.verified_by = staff.id
        upload.verified_at = datetime.utcnow()
        upload.feedback = feedback
        flash('Document verified successfully.', 'success')
    elif action == 'reject':
        upload.status = 'rejected'
        upload.verified_by = staff.id
        upload.verified_at = datetime.utcnow()
        upload.feedback = feedback
        flash('Document rejected.', 'info')
    
    db.session.commit()
    return redirect(url_for('staff.view_uploads'))

# ------------------------------
# View Visits
# ------------------------------
@staff_bp.route('/visits')
@login_required
@staff_required
def view_visits():
    staff = Staff.query.filter_by(email=current_user.email).first()
    if not staff:
        flash('Staff record not found.', 'danger')
        return redirect(url_for('auth.logout'))
    
    status = request.args.get('status', 'all')
    
    query = Visit.query.filter_by(staff_id=staff.id)
    if status != 'all':
        query = query.filter(Visit.status == status)
    
    visits = query.order_by(Visit.visit_date.desc()).all()
    assigned_parents = User.query.filter_by(staff_id=staff.id, role='parent', status='approved').all()
    return render_template('staff/visits.html', visits=visits, status=status, assigned_parents=assigned_parents)

# ------------------------------
# Add a New Visit
# ------------------------------
@staff_bp.route('/visits/add', methods=['POST'])
@login_required
@staff_required
def add_visit():
    staff = Staff.query.filter_by(email=current_user.email).first()
    parent_id = request.form.get('parent_id')
    visit_date = request.form.get('visit_date')
    remarks = request.form.get('remarks')
    
    parent = User.query.get(int(parent_id))
    if not parent or parent.staff_id != staff.id:
        flash('Invalid parent or not assigned to you.', 'danger')
        return redirect(url_for('staff.view_visits'))
    
    visit = Visit(
    parent_id=parent.id,  # must be numeric user ID
    staff_id=staff.id,
    visit_date=datetime.strptime(visit_date, '%Y-%m-%d').date(),
    remarks=remarks,
    status='scheduled'
)
    
    db.session.add(visit)
    db.session.commit()
    
    flash('Visit scheduled successfully.', 'success')
    return redirect(url_for('staff.view_visits'))

# ------------------------------
# Complete a Visit (File Upload Fix)
# ------------------------------
@staff_bp.route('/visits/<int:visit_id>/complete', methods=['POST'])
@login_required
@staff_required
def complete_visit(visit_id):
    staff = Staff.query.filter_by(email=current_user.email).first()
    visit = Visit.query.get_or_404(visit_id)
    
    if visit.staff_id != staff.id:
        flash('You are not authorized to complete this visit.', 'danger')
        return redirect(url_for('staff.view_visits'))
    
    visit.status = 'completed'
    visit.remarks = request.form.get('remarks', visit.remarks)
    
    photos = []
    if 'photos' in request.files:
        files = request.files.getlist('photos')
        for file in files:
            if file and file.filename:
                # ✅ Safe unique filename
                filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'visits', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                photos.append(f"visits/{filename}")
    
    if photos:
        visit.photos = json.dumps(photos)
    
    db.session.commit()
    flash('Visit marked as completed.', 'success')
    return redirect(url_for('staff.view_visits'))
