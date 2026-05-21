from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from config import Config
from models import db, User, Subscription, Student, Teacher, Attendance, Grade, Fee, CalendarEvent
from datetime import datetime, date, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
import os
import uuid

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

def migrate_subscription_schema():
    """Ensure legacy subscription columns are migrated to the current schema."""
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            if 'subscriptions' not in inspector.get_table_names():
                return

            columns = [column['name'] for column in inspector.get_columns('subscriptions')]
            with db.engine.begin() as conn:
                if 'plan' in columns and 'subscription_type' not in columns:
                    conn.execute(text('ALTER TABLE subscriptions RENAME COLUMN plan TO subscription_type'))
                if 'end_date' in columns and 'expiry_date' not in columns:
                    conn.execute(text('ALTER TABLE subscriptions RENAME COLUMN end_date TO expiry_date'))
                if 'updated_at' not in columns:
                    conn.execute(text('ALTER TABLE subscriptions ADD COLUMN updated_at DATETIME'))

                # SQLite cannot alter a column nullable state directly, so recreate table if needed
                columns = [column['name'] for column in inspector.get_columns('subscriptions')]
                if 'subscription_type' in columns:
                    info = conn.execute(text("PRAGMA table_info(subscriptions);"))
                    notnull_info = {row[1]: row[3] for row in info}
                    if notnull_info.get('subscription_type') == 1:
                        conn.execute(text('CREATE TABLE subscriptions_new (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL UNIQUE, subscription_type VARCHAR(50), status VARCHAR(20) DEFAULT \'Inactive\', start_date DATE, expiry_date DATE, created_at DATETIME, updated_at DATETIME)'))
                        conn.execute(text('INSERT INTO subscriptions_new (id, user_id, subscription_type, status, start_date, expiry_date, created_at, updated_at) SELECT id, user_id, subscription_type, status, start_date, expiry_date, created_at, updated_at FROM subscriptions'))
                        conn.execute(text('DROP TABLE subscriptions'))
                        conn.execute(text('ALTER TABLE subscriptions_new RENAME TO subscriptions'))
    except Exception:
        pass

migrate_subscription_schema()

def migrate_teachers_schema():
    """Remove UNIQUE constraint from teachers.email to allow duplicates."""
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            if 'teachers' not in inspector.get_table_names():
                return
            
            with db.engine.begin() as conn:
                # Check if email column has UNIQUE constraint
                try:
                    info_result = conn.execute(text("PRAGMA table_info(teachers);"))
                    rows = info_result.fetchall()
                    # If we have teachers, check the schema
                    conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name='teachers' AND name LIKE '%email%';"))
                    
                    # Recreate table without unique constraint on email
                    conn.execute(text('''
                        CREATE TABLE teachers_new (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            employee_id VARCHAR(50) NOT NULL UNIQUE,
                            first_name VARCHAR(100) NOT NULL,
                            last_name VARCHAR(100) NOT NULL,
                            email VARCHAR(120),
                            phone VARCHAR(20) NOT NULL,
                            qualification VARCHAR(200),
                            specialization VARCHAR(100),
                            date_of_birth DATE,
                            gender VARCHAR(10),
                            joining_date DATE,
                            department VARCHAR(100),
                            address TEXT,
                            salary FLOAT,
                            status VARCHAR(20) DEFAULT 'Active',
                            created_at DATETIME,
                            FOREIGN KEY(user_id) REFERENCES users(id)
                        )
                    '''))
                    conn.execute(text('''
                        INSERT INTO teachers_new 
                        SELECT id, user_id, employee_id, first_name, last_name, email, phone, 
                               qualification, specialization, date_of_birth, gender, joining_date,
                               department, address, salary, status, created_at
                        FROM teachers
                    '''))
                    conn.execute(text('DROP TABLE teachers'))
                    conn.execute(text('ALTER TABLE teachers_new RENAME TO teachers'))
                except Exception:
                    pass
    except Exception:
        pass

migrate_teachers_schema()

# School name persistence helpers
SCHOOL_NAME_FILE = os.path.join(os.path.dirname(__file__), 'school_name.txt')

def load_school_name():
    if os.path.exists(SCHOOL_NAME_FILE):
        try:
            with open(SCHOOL_NAME_FILE, 'r', encoding='utf-8') as file:
                name = file.read().strip()
                if name:
                    return name
        except Exception:
            pass
    return app.config.get('SCHOOL_NAME', 'Your School Name')


def save_school_name(name):
    try:
        with open(SCHOOL_NAME_FILE, 'w', encoding='utf-8') as file:
            file.write(name.strip())
    except Exception:
        pass

MASTER_ACTIVATION_PASSWORD = 'THEFREEGUY409605$'
SUBSCRIPTION_DURATIONS = {
    'Monthly': 30,
    'Yearly': 365
}


def get_user_subscription(user_id):
    if not user_id:
        return None
    return Subscription.query.filter_by(user_id=user_id).first()


def create_inactive_subscription(user_id):
    subscription = Subscription(
        user_id=user_id,
        subscription_type=None,
        start_date=None,
        expiry_date=None,
        status='Inactive'
    )
    db.session.add(subscription)
    db.session.commit()
    return subscription


def ensure_user_subscription(user_id):
    subscription = get_user_subscription(user_id)
    if not subscription:
        return create_inactive_subscription(user_id)
    return subscription


def update_subscription_status(subscription):
    if not subscription:
        return None

    if subscription.expiry_date and date.today() > subscription.expiry_date:
        if subscription.status != 'Expired':
            subscription.status = 'Expired'
            db.session.commit()

    return subscription


def get_subscription_info(user_id):
    if not user_id:
        return {
            'active': False,
            'subscription_type': None,
            'expiry_date': None,
            'remaining_days': 0,
            'expired': False,
            'status': 'Inactive'
        }

    subscription = ensure_user_subscription(user_id)
    subscription = update_subscription_status(subscription)
    expiry_date = subscription.expiry_date
    remaining_days = 0
    expired = False
    active = False

    if expiry_date:
        remaining_days = max((expiry_date - date.today()).days, 0)
        expired = date.today() > expiry_date

    active = subscription.status == 'Active' and not expired
    if subscription.status == 'Expired':
        expired = True

    return {
        'active': active,
        'subscription_type': subscription.subscription_type,
        'expiry_date': expiry_date,
        'remaining_days': remaining_days,
        'expired': expired,
        'status': subscription.status
    }


# Context processor to pass globals to templates
@app.context_processor
def inject_globals():
    subscription_info = get_subscription_info(getattr(g, 'current_user', None).id) if getattr(g, 'current_user', None) else {
        'active': False,
        'subscription_type': None,
        'expiry_date': None,
        'remaining_days': 0,
        'expired': False,
        'status': 'Inactive'
    }

    return {
        'current_date': date.today(),
        'current_year': datetime.now().year,
        'school_name': load_school_name(),
        'current_user': getattr(g, 'current_user', None),
        'subscription_info': subscription_info,
        'license_info': subscription_info
    }

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.before_request
def load_current_user():
    g.current_user = None
    user_id = session.get('user_id')
    if user_id:
        g.current_user = User.query.get(user_id)

@app.before_request
def require_login():
    allowed_endpoints = {
        'login',
        'logout',
        'register',
        'activate',
        'static',
        'page_not_found',
        'internal_error'
    }
    if request.endpoint not in allowed_endpoints and not session.get('user_id'):
        return redirect(url_for('login'))

@app.before_request
def require_subscription():
    allowed_endpoints = {
        'login',
        'logout',
        'register',
        'activate',
        'static',
        'page_not_found',
        'internal_error'
    }

    if request.endpoint in allowed_endpoints:
        return

    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    subscription = ensure_user_subscription(user_id)
    update_subscription_status(subscription)

    if subscription.status == 'Expired':
        session.clear()
        flash('Your subscription has expired. Please renew it to continue.', 'error')
        return redirect(url_for('login'))

    if subscription.status != 'Active' and request.endpoint != 'activate':
        flash('Your subscription is inactive. Please activate a plan to continue.', 'info')
        return redirect(url_for('activate'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password.', 'error')
            return render_template('login.html', username=username)

        subscription = ensure_user_subscription(user.id)
        update_subscription_status(subscription)

        session.clear()
        session['user_id'] = user.id
        session.permanent = True

        if subscription.status == 'Expired':
            flash('Your subscription has expired. Please renew your plan to continue.', 'error')
            return redirect(url_for('activate'))

        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/activate', methods=['GET', 'POST'])
def activate():
    """System activation page with subscription plan selection."""
    if not session.get('user_id'):
        flash('Please log in before activating a subscription.', 'info')
        return redirect(url_for('login'))

    subscription = ensure_user_subscription(session['user_id'])
    subscription_info = get_subscription_info(session['user_id'])

    if request.method == 'POST':
        activation_password = request.form.get('activation_password', '').strip()
        subscription_plan = request.form.get('subscription_plan', 'Monthly')

        if activation_password != MASTER_ACTIVATION_PASSWORD:
            flash('Invalid activation password. Please try again.', 'error')
        elif subscription_plan not in SUBSCRIPTION_DURATIONS:
            flash('Please select a valid subscription plan.', 'error')
        else:
            expiry_date = date.today() + timedelta(days=SUBSCRIPTION_DURATIONS[subscription_plan])
            subscription.subscription_type = subscription_plan
            subscription.start_date = date.today()
            subscription.expiry_date = expiry_date
            subscription.status = 'Active'
            db.session.commit()
            flash(f'Activation successful! Your {subscription_plan} subscription is active until {expiry_date.strftime("%d %B %Y")}.', 'success')
            return redirect(url_for('dashboard'))

    if subscription_info['active'] and subscription_info['expiry_date'] and not subscription_info['expired']:
        return redirect(url_for('dashboard'))

    return render_template('activate.html', license_info=subscription_info)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not password or not confirm_password:
            flash('All fields are required for account creation.', 'error')
            return render_template('register.html', username=username)

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('register.html', username=username)

        if User.query.filter_by(username=username).first():
            flash('This username is already taken. Please choose another.', 'error')
            return render_template('register.html', username=username)

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        create_inactive_subscription(new_user.id)

        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    response = redirect(url_for('login'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# ==================== DASHBOARD ROUTES ====================

@app.route('/')
def dashboard():
    """Main dashboard view"""
    subscription_info = get_subscription_info(session['user_id'])

    # Get statistics
    total_students = Student.query.filter_by(user_id=session['user_id']).count()
    total_teachers = Teacher.query.filter_by(user_id=session['user_id']).count()
    active_students = Student.query.filter_by(user_id=session['user_id'], status='Active').count()
    active_teachers = Teacher.query.filter_by(user_id=session['user_id'], status='Active').count()
    
    # Get recent activities
    recent_students = Student.query.filter_by(user_id=session['user_id']).order_by(Student.created_at.desc()).limit(5).all()
    recent_teachers = Teacher.query.filter_by(user_id=session['user_id']).order_by(Teacher.created_at.desc()).limit(5).all()
    
    # Get attendance summary for today
    today = date.today()
    today_attendance = Attendance.query.filter_by(date=today, user_id=session['user_id']).all()
    present_count = len([a for a in today_attendance if a.status == 'Present'])
    absent_count = len([a for a in today_attendance if a.status == 'Absent'])
    
    # Get pending fees
    pending_fees = Fee.query.filter_by(status='Pending', user_id=session['user_id']).count()
    pending_amount = sum(f.amount - f.amount_paid for f in Fee.query.filter_by(status='Pending', user_id=session['user_id']).all())
    
    # Get upcoming calendar events/reminders
    upcoming_events = CalendarEvent.query.filter(
        CalendarEvent.user_id == session['user_id'],
        CalendarEvent.event_date >= today
    ).order_by(CalendarEvent.event_date).limit(5).all()
    
    # Get events that should show reminders
    reminders = [event for event in upcoming_events if event.should_remind()]
    
    return render_template('dashboard.html',
                         total_students=total_students,
                         total_teachers=total_teachers,
                         active_students=active_students,
                         active_teachers=active_teachers,
                         recent_students=recent_students,
                         recent_teachers=recent_teachers,
                         present_count=present_count,
                         absent_count=absent_count,
                         pending_fees=pending_fees,
                         pending_amount=pending_amount,
                         upcoming_events=upcoming_events,
                         reminders=reminders,
                         subscription_type=subscription_info['subscription_type'],
                         expiry_date=subscription_info['expiry_date'],
                         remaining_days=subscription_info['remaining_days'])

# ==================== STUDENT MANAGEMENT ROUTES ====================

@app.route('/students')
def students_list():
    """Student list view"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    class_filter = request.args.get('class', '')
    
    query = Student.query.filter_by(user_id=session['user_id'])
    
    if search:
        query = query.filter(
            (Student.first_name.ilike(f'%{search}%')) |
            (Student.last_name.ilike(f'%{search}%')) |
            (Student.roll_number.ilike(f'%{search}%')) |
            (Student.email.ilike(f'%{search}%'))
        )
    
    if class_filter:
        query = query.filter_by(class_level=class_filter)
    
    students = query.paginate(page=page, per_page=10)
    
    # Get unique classes for filter
    classes = db.session.query(Student.class_level).filter(Student.user_id == session['user_id']).distinct().all()
    classes = [c[0] for c in classes if c[0]]
    
    return render_template('students.html',
                         students=students,
                         classes=classes,
                         search=search,
                         class_filter=class_filter)

@app.route('/student/add', methods=['GET', 'POST'])
def add_student():
    """Add new student"""
    form_data = {
        'roll_number': '',
        'first_name': '',
        'last_name': '',
        'email': '',
        'phone': '',
        'date_of_birth': '',
        'gender': '',
        'class_level': '',
        'address': '',
        'guardian_name': '',
        'guardian_phone': ''
    }

    if request.method == 'POST':
        for key in form_data:
            form_data[key] = request.form.get(key, '').strip()

        missing_fields = [
            field for field in ['roll_number', 'first_name', 'last_name', 'class_level']
            if not form_data[field]
        ]

        if not form_data['email'] and not form_data['phone']:
            flash('Please provide either a Gmail address or a phone number.', 'error')
            return render_template('student_form.html', title='Add Student', form_data=form_data)

        if missing_fields:
            flash('Please fill in all required fields before adding a student.', 'error')
            return render_template('student_form.html', title='Add Student', form_data=form_data)

        duplicate_roll = Student.query.filter_by(user_id=session['user_id'], roll_number=form_data['roll_number']).first()
        if duplicate_roll:
            flash('A student with that roll number already exists in your account.', 'error')
            return render_template('student_form.html', title='Add Student', form_data=form_data)

        email_value = form_data['email']
        if email_value:
            duplicate_email = Student.query.filter_by(user_id=session['user_id'], email=email_value).first()
            if duplicate_email:
                flash('A student with that email address already exists in your account.', 'error')
                return render_template('student_form.html', title='Add Student', form_data=form_data)
        else:
            email_value = f'no-email-{session["user_id"]}-{uuid.uuid4().hex}@example.com'

        try:
            student = Student(
                user_id=session['user_id'],
                roll_number=form_data['roll_number'],
                first_name=form_data['first_name'],
                last_name=form_data['last_name'],
                email=email_value,
                phone=form_data['phone'],
                date_of_birth=datetime.strptime(form_data['date_of_birth'], '%Y-%m-%d').date() if form_data['date_of_birth'] else None,
                gender=form_data['gender'],
                class_level=form_data['class_level'],
                address=form_data['address'],
                guardian_name=form_data['guardian_name'],
                guardian_phone=form_data['guardian_phone']
            )
            db.session.add(student)
            db.session.commit()
            flash(f'Student {student.get_full_name()} added successfully!', 'success')
            return redirect(url_for('students_list'))
        except IntegrityError:
            db.session.rollback()
            flash('Unable to add student. A student with the same roll number or email may already exist.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {str(e)}', 'error')

    return render_template('student_form.html', title='Add Student', form_data=form_data)

@app.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
def edit_student(student_id):
    """Edit student"""
    student = Student.query.filter_by(id=student_id, user_id=session['user_id']).first_or_404()
    
    if request.method == 'POST':
        try:
            student.first_name = request.form.get('first_name')
            student.last_name = request.form.get('last_name')
            student.email = request.form.get('email')
            student.phone = request.form.get('phone')
            student.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None
            student.gender = request.form.get('gender')
            student.class_level = request.form.get('class_level')
            student.address = request.form.get('address')
            student.guardian_name = request.form.get('guardian_name')
            student.guardian_phone = request.form.get('guardian_phone')
            student.status = request.form.get('status')
            
            db.session.commit()
            flash(f'Student {student.get_full_name()} updated successfully!', 'success')
            return redirect(url_for('students_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student: {str(e)}', 'error')
    
    return render_template('student_form.html', title='Edit Student', student=student, form_data={})

@app.route('/student/<int:student_id>/view')
def view_student(student_id):
    """View student details"""
    student = Student.query.filter_by(id=student_id, user_id=session['user_id']).first_or_404()
    
    # Get student stats
    attendance_records = Attendance.query.filter_by(student_id=student_id, user_id=session['user_id']).all()
    grades = Grade.query.filter_by(student_id=student_id, user_id=session['user_id']).all()
    fees = Fee.query.filter_by(student_id=student_id, user_id=session['user_id']).all()
    
    return render_template('student_detail.html',
                         student=student,
                         attendance_records=attendance_records,
                         grades=grades,
                         fees=fees)

@app.route('/student/<int:student_id>/delete', methods=['POST'])
def delete_student(student_id):
    """Delete student"""
    student = Student.query.filter_by(id=student_id, user_id=session['user_id']).first_or_404()
    try:
        db.session.delete(student)
        db.session.commit()
        flash(f'Student {student.get_full_name()} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
    
    return redirect(url_for('students_list'))

# ==================== TEACHER MANAGEMENT ROUTES ====================

@app.route('/teachers')
def teachers_list():
    """Teacher list view"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    dept_filter = request.args.get('department', '')
    
    query = Teacher.query.filter_by(user_id=session['user_id'])
    
    if search:
        query = query.filter(
            (Teacher.first_name.ilike(f'%{search}%')) |
            (Teacher.last_name.ilike(f'%{search}%')) |
            (Teacher.employee_id.ilike(f'%{search}%')) |
            (Teacher.email.ilike(f'%{search}%'))
        )
    
    if dept_filter:
        query = query.filter_by(department=dept_filter)
    
    teachers = query.paginate(page=page, per_page=10)
    
    # Get unique departments
    departments = db.session.query(Teacher.department).filter(Teacher.user_id == session['user_id']).distinct().all()
    departments = [d[0] for d in departments if d[0]]
    
    return render_template('teachers.html',
                         teachers=teachers,
                         departments=departments,
                         search=search,
                         dept_filter=dept_filter)

@app.route('/teacher/add', methods=['GET', 'POST'])
def add_teacher():
    """Add new teacher"""
    if request.method == 'POST':
        try:
            teacher = Teacher(
                user_id=session['user_id'],
                employee_id=request.form.get('employee_id'),
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                qualification=request.form.get('qualification'),
                specialization=request.form.get('specialization'),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None,
                gender=request.form.get('gender'),
                department=request.form.get('department'),
                address=request.form.get('address'),
                salary=float(request.form.get('salary')) if request.form.get('salary') else None
            )
            db.session.add(teacher)
            db.session.commit()
            flash(f'Teacher {teacher.get_full_name()} added successfully!', 'success')
            return redirect(url_for('teachers_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding teacher: {str(e)}', 'error')
    
    return render_template('teacher_form.html', title='Add Teacher')

@app.route('/teacher/<int:teacher_id>/edit', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    """Edit teacher"""
    teacher = Teacher.query.filter_by(id=teacher_id, user_id=session['user_id']).first_or_404()
    
    if request.method == 'POST':
        try:
            teacher.first_name = request.form.get('first_name')
            teacher.last_name = request.form.get('last_name')
            teacher.email = request.form.get('email')
            teacher.phone = request.form.get('phone')
            teacher.qualification = request.form.get('qualification')
            teacher.specialization = request.form.get('specialization')
            teacher.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None
            teacher.gender = request.form.get('gender')
            teacher.department = request.form.get('department')
            teacher.address = request.form.get('address')
            teacher.salary = float(request.form.get('salary')) if request.form.get('salary') else None
            teacher.status = request.form.get('status')
            
            db.session.commit()
            flash(f'Teacher {teacher.get_full_name()} updated successfully!', 'success')
            return redirect(url_for('teachers_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating teacher: {str(e)}', 'error')
    
    return render_template('teacher_form.html', title='Edit Teacher', teacher=teacher)

@app.route('/teacher/<int:teacher_id>/view')
def view_teacher(teacher_id):
    """View teacher details"""
    teacher = Teacher.query.filter_by(id=teacher_id, user_id=session['user_id']).first_or_404()
    grades = Grade.query.filter_by(teacher_id=teacher_id, user_id=session['user_id']).all()
    
    return render_template('teacher_detail.html', teacher=teacher, grades=grades)

@app.route('/teacher/<int:teacher_id>/delete', methods=['POST'])
def delete_teacher(teacher_id):
    """Delete teacher"""
    teacher = Teacher.query.filter_by(id=teacher_id, user_id=session['user_id']).first_or_404()
    try:
        db.session.delete(teacher)
        db.session.commit()
        flash(f'Teacher {teacher.get_full_name()} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting teacher: {str(e)}', 'error')
    
    return redirect(url_for('teachers_list'))

# ==================== ATTENDANCE ROUTES ====================

@app.route('/attendance')
def attendance_list():
    """Attendance view"""
    date_filter = request.args.get('date', str(date.today()))
    class_filter = request.args.get('class', '')
    
    try:
        selected_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
    except:
        selected_date = date.today()
    
    attendance_records = Attendance.query.filter_by(date=selected_date, user_id=session['user_id'])
    
    # Get students for the selected class
    if class_filter:
        students = Student.query.filter_by(class_level=class_filter, user_id=session['user_id']).all()
    else:
        students = Student.query.filter_by(user_id=session['user_id']).all()
    
    # Create attendance map
    attendance_map = {a.student_id: a for a in attendance_records.all()}
    
    # Get unique classes
    classes = db.session.query(Student.class_level).filter(Student.user_id == session['user_id']).distinct().all()
    classes = [c[0] for c in classes if c[0]]
    
    return render_template('attendance.html',
                         students=students,
                         attendance_map=attendance_map,
                         selected_date=selected_date,
                         classes=classes,
                         class_filter=class_filter)

@app.route('/attendance/save', methods=['POST'])
def save_attendance():
    """Save attendance record"""
    try:
        data = request.get_json(force=True) or {}
        student_id = data.get('student_id')
        att_date_str = data.get('date')
        status = data.get('status')

        if not student_id or not att_date_str or not status:
            raise ValueError('Missing attendance data.')

        student_id = int(student_id)
        att_date = datetime.strptime(att_date_str, '%Y-%m-%d').date()

        if status not in ('Present', 'Absent', 'Leave'):
            raise ValueError('Invalid attendance status.')

        if not Student.query.filter_by(id=student_id, user_id=session['user_id']).first():
            raise ValueError('Student not found.')

        # Check if attendance record exists
        existing = Attendance.query.filter_by(student_id=student_id, date=att_date, user_id=session['user_id']).first()

        if existing:
            existing.status = status
        else:
            attendance = Attendance(
                user_id=session['user_id'],
                student_id=student_id,
                date=att_date,
                status=status,
                recorded_by='Admin'
            )
            db.session.add(attendance)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Attendance saved successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

# ==================== GRADES ROUTES ====================

@app.route('/grades')
def grades_list():
    """Grades view"""
    page = request.args.get('page', 1, type=int)
    student_filter = request.args.get('student', type=int)
    subject_filter = request.args.get('subject', '')
    
    query = Grade.query.filter_by(user_id=session['user_id'])
    
    if student_filter is not None:
        query = query.filter(Grade.student_id == student_filter)
    
    if subject_filter:
        query = query.filter_by(subject=subject_filter)
    
    grades = query.paginate(page=page, per_page=20)
    
    # Get unique subjects
    subjects = db.session.query(Grade.subject).filter(Grade.user_id == session['user_id']).distinct().all()
    subjects = [s[0] for s in subjects if s[0]]
    
    # Get students for filter
    students = Student.query.filter_by(user_id=session['user_id']).all()
    
    return render_template('grades.html',
                         grades=grades,
                         subjects=subjects,
                         students=students,
                         student_filter=student_filter,
                         subject_filter=subject_filter)

@app.route('/grade/add', methods=['GET', 'POST'])
def add_grade():
    """Add grade"""
    if request.method == 'POST':
        try:
            student_id = int(request.form.get('student_id'))
            teacher_id = int(request.form.get('teacher_id'))
            if not Student.query.filter_by(id=student_id, user_id=session['user_id']).first():
                raise ValueError('Student not found.')
            if not Teacher.query.filter_by(id=teacher_id, user_id=session['user_id']).first():
                raise ValueError('Teacher not found.')
            grade = Grade(
                user_id=session['user_id'],
                student_id=student_id,
                teacher_id=teacher_id,
                subject=request.form.get('subject'),
                exam_name=request.form.get('exam_name'),
                marks=float(request.form.get('marks')),
                total_marks=float(request.form.get('total_marks', 100)),
                remarks=request.form.get('remarks')
            )
            grade.calculate_grade()
            db.session.add(grade)
            db.session.commit()
            flash('Grade added successfully!', 'success')
            return redirect(url_for('grade_summary', grade_id=grade.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding grade: {str(e)}', 'error')
    
    students = Student.query.filter_by(user_id=session['user_id']).all()
    teachers = Teacher.query.filter_by(user_id=session['user_id']).all()
    return render_template('grade_form.html', title='Add Grade', students=students, teachers=teachers)

@app.route('/grade/<int:grade_id>/edit', methods=['GET', 'POST'])
def edit_grade(grade_id):
    """Edit grade"""
    grade = Grade.query.filter_by(id=grade_id, user_id=session['user_id']).first_or_404()
    
    if request.method == 'POST':
        try:
            grade.marks = float(request.form.get('marks'))
            grade.total_marks = float(request.form.get('total_marks', 100))
            grade.subject = request.form.get('subject')
            grade.exam_name = request.form.get('exam_name')
            grade.remarks = request.form.get('remarks')
            grade.calculate_grade()
            db.session.commit()
            flash('Grade updated successfully!', 'success')
            return redirect(url_for('grade_summary', grade_id=grade.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating grade: {str(e)}', 'error')
    
    students = Student.query.filter_by(user_id=session['user_id']).all()
    teachers = Teacher.query.filter_by(user_id=session['user_id']).all()
    return render_template('grade_form.html', title='Edit Grade', grade=grade, students=students, teachers=teachers)

@app.route('/grade/<int:grade_id>/summary')
def grade_summary(grade_id):
    grade = Grade.query.filter_by(id=grade_id, user_id=session['user_id']).first_or_404()
    return render_template('grade_summary.html', grade=grade)

@app.route('/grade/<int:grade_id>/delete', methods=['POST'])
def delete_grade(grade_id):
    """Delete grade"""
    grade = Grade.query.filter_by(id=grade_id, user_id=session['user_id']).first_or_404()
    try:
        db.session.delete(grade)
        db.session.commit()
        flash('Grade deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting grade: {str(e)}', 'error')
    
    return redirect(url_for('grades_list'))

@app.route('/student/<int:student_id>/report-card', methods=['GET', 'POST'])
def student_report_card(student_id):
    """Generate student report card with all subjects and grades"""
    student = Student.query.filter_by(id=student_id, user_id=session['user_id']).first_or_404()
    school_name = load_school_name()

    if request.method == 'POST':
        new_school_name = request.form.get('school_name', '').strip()
        if new_school_name:
            save_school_name(new_school_name)
            flash('School name updated successfully!', 'success')
            return redirect(url_for('student_report_card', student_id=student_id))
        else:
            flash('School name cannot be empty.', 'error')
            return redirect(url_for('student_report_card', student_id=student_id))

    # Get all grades for the student, grouped by subject
    grades = Grade.query.filter_by(student_id=student_id, user_id=session['user_id']).all()
    
    # Calculate summary statistics
    total_marks = sum(g.marks for g in grades) if grades else 0
    total_possible = sum(g.total_marks for g in grades) if grades else 0
    overall_percentage = (total_marks / total_possible * 100) if total_possible > 0 else 0
    overall_gpa = student.get_gpa()
    
    return render_template('report_card.html',
                         student=student,
                         grades=grades,
                         total_marks=total_marks,
                         total_possible=total_possible,
                         overall_percentage=overall_percentage,
                         overall_gpa=overall_gpa,
                         school_name=school_name)

# ==================== FEES ROUTES ====================

@app.route('/fees')
def fees_list():
    """Fees view"""
    page = request.args.get('page', 1, type=int)
    student_filter = request.args.get('student', type=int)
    status_filter = request.args.get('status', '')
    
    query = Fee.query.filter_by(user_id=session['user_id'])
    
    if student_filter is not None:
        query = query.filter(Fee.student_id == student_filter)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    fees = query.paginate(page=page, per_page=20)
    
    # Get students for filter
    students = Student.query.filter_by(user_id=session['user_id']).all()
    
    # Calculate statistics
    total_fees = db.session.query(db.func.sum(Fee.amount)).filter(Fee.user_id == session['user_id']).scalar() or 0
    total_paid = db.session.query(db.func.sum(Fee.amount_paid)).filter(Fee.user_id == session['user_id']).scalar() or 0
    total_pending = total_fees - total_paid
    
    return render_template('fees.html',
                         fees=fees,
                         students=students,
                         student_filter=student_filter,
                         status_filter=status_filter,
                         total_fees=total_fees,
                         total_paid=total_paid,
                         total_pending=total_pending)

@app.route('/fee/add', methods=['GET', 'POST'])
def add_fee():
    """Add fee"""
    if request.method == 'POST':
        try:
            due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
            amount_paid = float(request.form.get('amount_paid', 0) or 0)
            payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date() if request.form.get('payment_date') else None
            student_id = int(request.form.get('student_id'))
            if not Student.query.filter_by(id=student_id, user_id=session['user_id']).first():
                raise ValueError('Student not found.')
            fee = Fee(
                user_id=session['user_id'],
                student_id=student_id,
                fee_type=request.form.get('fee_type'),
                amount=float(request.form.get('amount')),
                due_date=due_date,
                amount_paid=amount_paid,
                payment_date=payment_date,
                payment_method=request.form.get('payment_method'),
                status='Paid' if amount_paid >= float(request.form.get('amount')) else 'Pending'
            )
            db.session.add(fee)
            db.session.commit()
            flash('Fee added successfully!', 'success')
            return redirect(url_for('fees_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding fee: {str(e)}', 'error')
    
    students = Student.query.filter_by(user_id=session['user_id']).all()
    return render_template('fee_form.html', title='Add Fee', students=students)

@app.route('/fee/<int:fee_id>/edit', methods=['GET', 'POST'])
def edit_fee(fee_id):
    """Edit fee"""
    fee = Fee.query.filter_by(id=fee_id, user_id=session['user_id']).first_or_404()
    
    if request.method == 'POST':
        try:
            fee.fee_type = request.form.get('fee_type')
            fee.amount = float(request.form.get('amount'))
            fee.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
            fee.amount_paid = float(request.form.get('amount_paid', 0))
            fee.payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date() if request.form.get('payment_date') else None
            fee.status = request.form.get('status')
            fee.remarks = request.form.get('remarks')
            
            db.session.commit()
            flash('Fee updated successfully!', 'success')
            return redirect(url_for('fees_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating fee: {str(e)}', 'error')
    
    students = Student.query.filter_by(user_id=session['user_id']).all()
    return render_template('fee_form.html', title='Edit Fee', fee=fee, students=students)

@app.route('/fee/<int:fee_id>/delete', methods=['POST'])
def delete_fee(fee_id):
    """Delete fee"""
    fee = Fee.query.filter_by(id=fee_id, user_id=session['user_id']).first_or_404()
    try:
        db.session.delete(fee)
        db.session.commit()
        flash('Fee deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting fee: {str(e)}', 'error')
    
    return redirect(url_for('fees_list'))

# ==================== CALENDAR ROUTES ====================

@app.route('/calendar')
def calendar_list():
    """Calendar events view"""
    page = request.args.get('page', 1, type=int)
    type_filter = request.args.get('type', '')
    
    query = CalendarEvent.query.filter_by(user_id=session['user_id']).order_by(CalendarEvent.event_date)
    
    if type_filter:
        query = query.filter_by(event_type=type_filter)
    
    events = query.paginate(page=page, per_page=20)
    
    # Get unique event types
    event_types = db.session.query(CalendarEvent.event_type).filter(CalendarEvent.user_id == session['user_id']).distinct().all()
    event_types = [t[0] for t in event_types if t[0]]
    
    # Get statistics
    today = date.today()
    upcoming_count = CalendarEvent.query.filter(CalendarEvent.user_id == session['user_id'], CalendarEvent.event_date >= today).count()
    past_count = CalendarEvent.query.filter(CalendarEvent.user_id == session['user_id'], CalendarEvent.event_date < today).count()
    reminder_count = len([e for e in CalendarEvent.query.filter(CalendarEvent.user_id == session['user_id'], CalendarEvent.event_date >= today).all() if e.should_remind()])
    
    return render_template('calendar.html',
                         events=events,
                         event_types=event_types,
                         type_filter=type_filter,
                         upcoming_count=upcoming_count,
                         past_count=past_count,
                         reminder_count=reminder_count)

@app.route('/calendar/add', methods=['GET', 'POST'])
def add_calendar_event():
    """Add calendar event"""
    if request.method == 'POST':
        try:
            event_date = datetime.strptime(request.form.get('event_date'), '%Y-%m-%d').date()
            event = CalendarEvent(
                user_id=session['user_id'],
                title=request.form.get('title'),
                description=request.form.get('description'),
                event_date=event_date,
                event_type=request.form.get('event_type'),
                is_reminder=request.form.get('is_reminder') == 'on',
                reminder_days=int(request.form.get('reminder_days', 7))
            )
            db.session.add(event)
            db.session.commit()
            flash('Calendar event added successfully!', 'success')
            return redirect(url_for('calendar_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding event: {str(e)}', 'error')
    
    return render_template('calendar_form.html', title='Add Calendar Event')

@app.route('/calendar/<int:event_id>/edit', methods=['GET', 'POST'])
def edit_calendar_event(event_id):
    """Edit calendar event"""
    event = CalendarEvent.query.filter_by(id=event_id, user_id=session['user_id']).first_or_404()
    
    if request.method == 'POST':
        try:
            event.title = request.form.get('title')
            event.description = request.form.get('description')
            event.event_date = datetime.strptime(request.form.get('event_date'), '%Y-%m-%d').date()
            event.event_type = request.form.get('event_type')
            event.is_reminder = request.form.get('is_reminder') == 'on'
            event.reminder_days = int(request.form.get('reminder_days', 7))
            
            db.session.commit()
            flash('Calendar event updated successfully!', 'success')
            return redirect(url_for('calendar_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating event: {str(e)}', 'error')
    
    return render_template('calendar_form.html', title='Edit Calendar Event', event=event)

@app.route('/calendar/<int:event_id>/delete', methods=['POST'])
def delete_calendar_event(event_id):
    """Delete calendar event"""
    event = CalendarEvent.query.filter_by(id=event_id, user_id=session['user_id']).first_or_404()
    try:
        db.session.delete(event)
        db.session.commit()
        flash('Calendar event deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting event: {str(e)}', 'error')
    
    return redirect(url_for('calendar_list'))

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            default_admin = User(username=Config.DEFAULT_ADMIN_USERNAME)
            default_admin.set_password(Config.DEFAULT_ADMIN_PASSWORD)
            db.session.add(default_admin)
            db.session.commit()
            print(f"Created default admin user: {Config.DEFAULT_ADMIN_USERNAME}")
    app.run(debug=True, host='0.0.0.0', port=5000)
