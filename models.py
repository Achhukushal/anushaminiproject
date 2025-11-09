from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# This will be initialized in app.py
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'staff', 'parent'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    parent_id = db.Column(db.String(20), unique=True)  # Unique ID assigned by admin
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    children = db.relationship('Child', backref='parent', lazy=True)
    uploads = db.relationship('Upload', backref='parent', lazy=True)
    visits = db.relationship('Visit', backref='parent', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Staff(db.Model):
    __tablename__ = 'staff'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    staff_id = db.Column(db.String(20), unique=True, nullable=False)  # Unique staff ID
    phone = db.Column(db.String(20))
    assigned_parent_count = db.Column(db.Integer, default=0)
    max_parents = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assigned_parents = db.relationship('User', backref='mentor', lazy=True)
    visits = db.relationship('Visit', backref='staff', lazy=True)
    
    def __repr__(self):
        return f'<Staff {self.staff_id}>'

class Child(db.Model):
    __tablename__ = 'children'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date)
    gender = db.Column(db.String(10))
    adoption_date = db.Column(db.Date, default=datetime.utcnow)
    background_info = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploads = db.relationship('Upload', backref='child', lazy=True)
    
    def __repr__(self):
        return f'<Child {self.name}>'

class Upload(db.Model):
    __tablename__ = 'uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    upload_type = db.Column(db.String(50), nullable=False)  # 'health', 'vaccination', 'school'
    file_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'verified', 'rejected'
    feedback = db.Column(db.Text)
    verified_by = db.Column(db.Integer, db.ForeignKey('staff.id'))
    verified_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Upload {self.upload_type}>'

class Visit(db.Model):
    __tablename__ = 'visits'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    scheduled_date = db.Column(db.Date)
    remarks = db.Column(db.Text)
    status = db.Column(db.String(20), default='scheduled')  # 'scheduled', 'completed', 'cancelled'
    photos = db.Column(db.Text)  # JSON string of photo paths
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Visit {self.visit_date}>'

class Guidance(db.Model):
    __tablename__ = 'guidance'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_url = db.Column(db.String(255))
    category = db.Column(db.String(50))  # 'guideline', 'faq', 'policy', 'counseling'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Guidance {self.title}>'

