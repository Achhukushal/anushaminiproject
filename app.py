from flask import Flask, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# -------------------------------
# Flask App Setup
# -------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///adoption_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# -------------------------------
# Ensure Upload Folders Exist
# -------------------------------
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'guidance'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'visits'), exist_ok=True)

# -------------------------------
# Database & Login Setup
# -------------------------------
from models import db, User, Staff, Child, Upload, Visit, Guidance

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------------
# Register Blueprints
# -------------------------------
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.staff import staff_bp
from routes.parent import parent_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(staff_bp, url_prefix='/staff')
app.register_blueprint(parent_bp, url_prefix='/parent')

# -------------------------------
# Route to Serve Uploaded Files
# -------------------------------
@app.route('/uploads/<path:filename>')
def uploaded_files(filename):
    """
    Allows serving user-uploaded files from /uploads directory.
    Example: /uploads/documents/test.pdf
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------------------
# Default Route
# -------------------------------
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

# -------------------------------
# Create Database & Default Admin
# -------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Create default admin if not exists
        admin = User.query.filter_by(email='admin@adoption.com', role='admin').first()
        if not admin:
            from werkzeug.security import generate_password_hash
            admin = User(
                email='admin@adoption.com',
                password=generate_password_hash('admin123'),
                name='System Admin',
                role='admin',
                status='approved'
            )
            db.session.add(admin)
            db.session.commit()

    # Run Flask app
    app.run(debug=True)
