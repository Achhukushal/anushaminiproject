from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from models import User, Staff, Child, Upload, Visit, Guidance, db
from datetime import datetime, timedelta
import os
import json
from flask import Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_staff = Staff.query.count()
    total_parents = User.query.filter_by(role='parent', status='approved').count()
    pending_parents = User.query.filter_by(role='parent', status='pending').count()
    total_children = Child.query.count()
    total_uploads = Upload.query.count()
    pending_uploads = Upload.query.filter_by(status='pending').count()
    upcoming_visits = Visit.query.filter(Visit.visit_date >= datetime.now().date()).count()
    
    recent_activities = []
    recent_parents = User.query.filter_by(role='parent').order_by(User.created_at.desc()).limit(5).all()
    recent_uploads = Upload.query.order_by(Upload.upload_date.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_staff=total_staff,
                         total_parents=total_parents,
                         pending_parents=pending_parents,
                         total_children=total_children,
                         total_uploads=total_uploads,
                         pending_uploads=pending_uploads,
                         upcoming_visits=upcoming_visits,
                         recent_parents=recent_parents,
                         recent_uploads=recent_uploads)

@admin_bp.route('/staff', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_staff():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        staff_id = request.form.get('staff_id')
        phone = request.form.get('phone')
        max_parents = int(request.form.get('max_parents', 10))
        
        if Staff.query.filter_by(staff_id=staff_id).first():
            flash('Staff ID already exists.', 'danger')
            return redirect(url_for('admin.manage_staff'))
        
        if Staff.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('admin.manage_staff'))
        
        hashed_password = generate_password_hash(password)
        new_staff = Staff(
            name=name,
            email=email,
            password=hashed_password,
            staff_id=staff_id,
            phone=phone,
            max_parents=max_parents
        )
        
        db.session.add(new_staff)
        db.session.commit()
        
        flash('Staff member added successfully.', 'success')
        return redirect(url_for('admin.manage_staff'))
    
    staff_list = Staff.query.all()
    return render_template('admin/staff.html', staff_list=staff_list)

@admin_bp.route('/staff/<int:staff_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    db.session.delete(staff)
    db.session.commit()
    flash('Staff member deleted successfully.', 'success')
    return redirect(url_for('admin.manage_staff'))

@admin_bp.route('/parents')
@login_required
@admin_required
def manage_parents():
    status = request.args.get('status', 'all')
    if status == 'pending':
        parents = User.query.filter_by(role='parent', status='pending').all()
    elif status == 'approved':
        parents = User.query.filter_by(role='parent', status='approved').all()
    else:
        parents = User.query.filter_by(role='parent').all()
    
    staff_list = Staff.query.all()
    return render_template('admin/parents.html', parents=parents, staff_list=staff_list, status=status)

@admin_bp.route('/parents/<int:parent_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_parent(parent_id):
    parent = User.query.get_or_404(parent_id)
    staff_id = request.form.get('staff_id')
    
    if not staff_id:
        flash('Please assign a staff member.', 'danger')
        return redirect(url_for('admin.manage_parents', status='pending'))
    
    staff = Staff.query.get(int(staff_id))
    if not staff:
        flash('Invalid staff member.', 'danger')
        return redirect(url_for('admin.manage_parents', status='pending'))
    
    if staff.assigned_parent_count >= staff.max_parents:
        flash(f'Staff {staff.staff_id} has reached maximum parent limit ({staff.max_parents}).', 'danger')
        return redirect(url_for('admin.manage_parents', status='pending'))
    
    # Generate unique parent ID
    import random
    import string
    parent_id_str = 'PAR' + ''.join(random.choices(string.digits, k=6))
    while User.query.filter_by(parent_id=parent_id_str).first():
        parent_id_str = 'PAR' + ''.join(random.choices(string.digits, k=6))
    
    parent.status = 'approved'
    parent.parent_id = parent_id_str
    parent.staff_id = staff.id
    staff.assigned_parent_count += 1
    
    db.session.commit()
    
    flash(f'Parent approved and assigned to staff {staff.staff_id}. Parent ID: {parent_id_str}', 'success')
    return redirect(url_for('admin.manage_parents', status='pending'))

@admin_bp.route('/parents/<int:parent_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_parent(parent_id):
    parent = User.query.get_or_404(parent_id)
    parent.status = 'rejected'
    db.session.commit()
    flash('Parent registration rejected.', 'info')
    return redirect(url_for('admin.manage_parents', status='pending'))

@admin_bp.route('/children')
@login_required
@admin_required
def manage_children():
    children = Child.query.all()
    parents = User.query.filter_by(role='parent', status='approved').all()
    return render_template('admin/children.html', children=children, parents=parents)

@admin_bp.route('/children/add', methods=['POST'])
@login_required
@admin_required
def add_child():
    parent_id = request.form.get('parent_id')
    name = request.form.get('name')
    dob = request.form.get('dob')
    gender = request.form.get('gender')
    adoption_date = request.form.get('adoption_date')
    background_info = request.form.get('background_info')
    
    parent = User.query.get(int(parent_id))
    if not parent or parent.role != 'parent':
        flash('Invalid parent.', 'danger')
        return redirect(url_for('admin.manage_children'))
    
    child = Child(
        parent_id=parent.id,
        name=name,
        dob=datetime.strptime(dob, '%Y-%m-%d').date() if dob else None,
        gender=gender,
        adoption_date=datetime.strptime(adoption_date, '%Y-%m-%d').date() if adoption_date else None,
        background_info=background_info
    )
    
    db.session.add(child)
    db.session.commit()
    
    flash('Child record added successfully.', 'success')
    return redirect(url_for('admin.manage_children'))

@admin_bp.route('/guidance', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_guidance():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        file = request.files.get('file')
        
        file_url = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'guidance', filename)
            file.save(file_path)
            file_url = f"guidance/{filename}"
        
        guidance = Guidance(
            title=title,
            description=description,
            category=category,
            file_url=file_url,
            created_by=current_user.id
        )
        
        db.session.add(guidance)
        db.session.commit()
        
        flash('Guidance material added successfully.', 'success')
        return redirect(url_for('admin.manage_guidance'))
    
    guidance_list = Guidance.query.order_by(Guidance.created_at.desc()).all()
    return render_template('admin/guidance.html', guidance_list=guidance_list)

@admin_bp.route('/guidance/<int:guidance_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_guidance(guidance_id):
    guidance = Guidance.query.get_or_404(guidance_id)
    if guidance.file_url:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], guidance.file_url)
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.delete(guidance)
    db.session.commit()
    flash('Guidance material deleted successfully.', 'success')
    return redirect(url_for('admin.manage_guidance'))

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    return render_template('admin/reports.html')

@admin_bp.route('/reports/export')
@login_required
@admin_required
def export_reports():
    # Simple CSV export example
    import csv
    from io import StringIO, BytesIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Report Type', 'Count'])
    writer.writerow(['Total Staff', Staff.query.count()])
    writer.writerow(['Total Parents', User.query.filter_by(role='parent', status='approved').count()])
    writer.writerow(['Total Children', Child.query.count()])
    writer.writerow(['Total Uploads', Upload.query.count()])
    writer.writerow(['Pending Uploads', Upload.query.filter_by(status='pending').count()])
    
    output.seek(0)
    mem = BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name='adoption_report.csv'
    )

