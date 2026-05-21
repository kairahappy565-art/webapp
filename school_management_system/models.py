from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Subscription(db.Model):
    """Subscription model for per-user licensing"""
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    subscription_type = db.Column(db.String(50))  # Monthly, Yearly
    start_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Inactive')  # Inactive, Active, Expired
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user = db.relationship('User', backref=db.backref('subscription', uselist=False))

    def is_active(self):
        if self.status != 'Active' or not self.expiry_date:
            return False
        return date.today() <= self.expiry_date

    def update_status(self):
        if self.expiry_date and date.today() > self.expiry_date:
            self.status = 'Expired'


class Student(db.Model):
    """Student model"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    class_level = db.Column(db.String(50), nullable=False)
    admission_date = db.Column(db.Date, default=datetime.now)
    address = db.Column(db.Text)
    guardian_name = db.Column(db.String(100))
    guardian_phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('students', lazy=True))
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    grades = db.relationship('Grade', backref='student', lazy=True, cascade='all, delete-orphan')
    fees = db.relationship('Fee', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_display_email(self):
        if not self.email or self.email.startswith('no-email-'):
            return 'NO EMAIL'
        return self.email

    def has_real_email(self):
        return bool(self.email and not self.email.startswith('no-email-'))
    
    def get_attendance_percentage(self):
        """Calculate attendance percentage"""
        total = Attendance.query.filter_by(student_id=self.id, user_id=self.user_id).count()
        if total == 0:
            return 0
        present = Attendance.query.filter_by(student_id=self.id, user_id=self.user_id, status='Present').count()
        return (present / total) * 100 if total > 0 else 0
    
    def get_gpa(self):
        """Calculate GPA from grades"""
        grades = Grade.query.filter_by(student_id=self.id, user_id=self.user_id).all()
        if not grades:
            return 0.0
        total = sum(g.marks for g in grades)
        return round(total / len(grades), 2)


class Teacher(db.Model):
    """Teacher model"""
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    qualification = db.Column(db.String(200))
    specialization = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    joining_date = db.Column(db.Date, default=datetime.now)
    department = db.Column(db.String(100))
    address = db.Column(db.Text)
    salary = db.Column(db.Float)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('teachers', lazy=True))
    classes_taught = db.relationship('Grade', backref='teacher', lazy=True)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Attendance(db.Model):
    """Attendance model"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Present, Absent, Leave
    remarks = db.Column(db.Text)
    recorded_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref=db.backref('attendance_records', lazy=True))
    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='unique_student_date'),)


class Grade(db.Model):
    """Grade/Marks model"""
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    exam_name = db.Column(db.String(100))
    marks = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Float, default=100)
    percentage = db.Column(db.Float)
    grade = db.Column(db.String(5))  # A, B, C, D, F
    recorded_date = db.Column(db.Date, default=datetime.now)
    remarks = db.Column(db.Text)

    user = db.relationship('User', backref=db.backref('grades', lazy=True))
    
    def calculate_grade(self):
        """Calculate Zambian grading system result from percentage"""
        if self.total_marks > 0:
            percentage = (self.marks / self.total_marks) * 100
            self.percentage = round(percentage, 2)
            
            if percentage >= 75:
                self.grade = 'Distinction'
            elif percentage >= 65:
                self.grade = 'Merit'
            elif percentage >= 50:
                self.grade = 'Credit'
            elif percentage >= 40:
                self.grade = 'Pass'
            else:
                self.grade = 'Fail'


class Fee(db.Model):
    """School fees model"""
    __tablename__ = 'fees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    fee_type = db.Column(db.String(100), nullable=False)  # Tuition, Transportation, etc.
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    payment_date = db.Column(db.Date)
    amount_paid = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='Pending')  # Pending, Paid, Overdue
    payment_method = db.Column(db.String(50))  # Cash, Check, Online
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', backref=db.backref('fees', lazy=True))


class CalendarEvent(db.Model):
    """School calendar events model"""
    __tablename__ = 'calendar_events'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    event_type = db.Column(db.String(50), default='Event')  # Event, Holiday, Exam, Meeting
    is_reminder = db.Column(db.Boolean, default=True)
    reminder_days = db.Column(db.Integer, default=7)  # Days before event to show reminder
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user = db.relationship('User', backref=db.backref('calendar_events', lazy=True))
    
    def days_until(self):
        """Calculate days until event"""
        from datetime import date
        return (self.event_date - date.today()).days
    
    def should_remind(self):
        """Check if reminder should be shown"""
        if not self.is_reminder:
            return False
        days_until = self.days_until()
        return days_until >= 0 and days_until <= self.reminder_days
