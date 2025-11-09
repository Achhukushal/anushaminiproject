# Child Adoption and Growth Tracking System

A comprehensive web-based system for managing child adoption processes and tracking post-adoption child development.

## Features

### 🔐 Three User Roles

1. **Admin** - System administrator with full control
2. **Staff** - Mentors assigned to parents (max 10 parents per staff)
3. **Parents** - Adoptive parents tracking their children's growth

### 📋 Main Functionalities

#### Admin Dashboard
- Manage staff accounts (add/edit/remove)
- Approve/reject parent registrations
- Assign staff to parents (max 10 per staff)
- Add child records to parents
- Manage adoption guidance materials (FAQs, policies, counseling schedules)
- View system statistics and reports
- Export reports (CSV)

#### Staff Dashboard
- View assigned parents and their children
- Verify documents uploaded by parents (health, vaccination, school reports)
- Schedule and complete quarterly home visits
- Provide feedback on uploaded documents
- Track visit history

#### Parent Dashboard
- View adopted child details
- Upload monthly reports:
  - Health check-up details
  - Vaccination updates
  - School progress reports
- View feedback from staff
- Track visit history
- Access adoption guidance materials
- Manage profile

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python app.py
   ```

3. **Access the Application**
   - Open your browser and navigate to `http://localhost:5000`

## Default Login Credentials

### Admin
- **Email:** admin@adoption.com
- **Password:** admin123
- **Role:** Admin

## Getting Started

### For Admin

1. Login with admin credentials
2. Add staff members:
   - Go to "Staff" section
   - Enter Staff ID, Name, Email, Password, and Max Parents (default: 10)
   - Staff will use their Staff ID to login

3. Approve Parent Registrations:
   - Go to "Parents" section
   - Review pending registrations
   - Assign a staff member to each parent
   - System will generate a unique Parent ID
   - Parents will use this Parent ID to login

4. Add Child Records:
   - Go to "Children" section
   - Select parent and enter child details

5. Add Guidance Materials:
   - Go to "Guidance" section
   - Add adoption guidelines, FAQs, policies, or counseling schedules

### For Staff

1. Login with Staff ID (assigned by admin) and password
2. View assigned parents in "Assigned Parents" section
3. Verify documents in "Uploads" section:
   - View uploaded documents
   - Approve or reject with feedback
4. Schedule visits in "Visits" section:
   - Schedule quarterly home visits
   - Mark visits as completed with remarks and photos

### For Parents

1. **Registration:**
   - Click "Register as Parent"
   - Fill in registration form
   - Wait for admin approval
   - You will receive a unique Parent ID after approval

2. **Login:**
   - Use your Parent ID and password to login

3. **Upload Documents:**
   - Go to "Uploads" section
   - Select child and document type
   - Upload file (PDF/Image)
   - Wait for staff verification

4. **View Feedback:**
   - Check upload status and staff feedback
   - View visit history

## Project Structure

```
mini17/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── requirements.txt        # Python dependencies
├── routes/
│   ├── auth.py           # Authentication routes
│   ├── admin.py          # Admin routes
│   ├── staff.py          # Staff routes
│   └── parent.py         # Parent routes
├── templates/
│   ├── base.html         # Base template
│   ├── auth/             # Authentication templates
│   ├── admin/            # Admin templates
│   ├── staff/            # Staff templates
│   └── parent/           # Parent templates
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── main.js       # JavaScript functions
└── uploads/              # Uploaded files (auto-created)
    ├── documents/        # Parent document uploads
    ├── guidance/         # Guidance materials
    └── visits/           # Visit photos
```

## Database Schema

- **users** - Parent and admin user accounts
- **staff** - Staff member records
- **children** - Adopted children records
- **uploads** - Document uploads by parents
- **visits** - Home visit records
- **guidance** - Adoption guidance materials

## Security Notes

⚠️ **Important:** Before deploying to production:
1. Change the `SECRET_KEY` in `app.py`
2. Use a production-grade database (PostgreSQL/MySQL)
3. Implement proper password hashing (already using Werkzeug)
4. Add HTTPS/SSL
5. Implement rate limiting
6. Add input validation and sanitization

## Technologies Used

- **Backend:** Flask (Python)
- **Database:** SQLite (SQLAlchemy ORM)
- **Frontend:** HTML, CSS, JavaScript, Bootstrap 5
- **Authentication:** Flask-Login

## License

This project is for educational purposes.

