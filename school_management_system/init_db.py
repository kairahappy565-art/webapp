#!/usr/bin/env python
"""
Database Initialization Script
Populates the database with sample data for testing
"""

from datetime import datetime, date, timedelta
from app import app, db
from models import User, Student, Teacher, Attendance, Grade, Fee, CalendarEvent

def init_sample_data():
    """Initialize database with sample data"""
    
    with app.app_context():
        # Clear existing data
        print("Clearing existing data...")
        db.drop_all()
        
        # Create tables
        print("Creating tables...")
        db.create_all()

        # Ensure a default owner user exists
        default_username = 'admin'
        default_password = 'admin123'
        admin_user = User.query.filter_by(username=default_username).first()
        if not admin_user:
            admin_user = User(username=default_username)
            admin_user.set_password(default_password)
            db.session.add(admin_user)
            db.session.commit()
            print(f"Created default user: {default_username}")
        owner_id = admin_user.id
        
        # Sample Students
        print("Adding sample students...")
        students = [
            Student(
                user_id=owner_id,
                roll_number="10001",
                first_name="Aarav",
                last_name="Sharma",
                email="aarav.sharma@school.com",
                phone="9876543210",
                date_of_birth=date(2008, 5, 15),
                gender="Male",
                class_level="10-A",
                address="123 Main Street, City",
                guardian_name="Rajesh Sharma",
                guardian_phone="9876543200",
                status="Active"
            ),
            Student(
                user_id=owner_id,
                roll_number="10002",
                first_name="Priya",
                last_name="Patel",
                email="priya.patel@school.com",
                phone="9876543211",
                date_of_birth=date(2008, 8, 20),
                gender="Female",
                class_level="10-A",
                address="456 Oak Avenue, City",
                guardian_name="Anjali Patel",
                guardian_phone="9876543201",
                status="Active"
            ),
            Student(
                user_id=owner_id,
                roll_number="10003",
                first_name="Rohan",
                last_name="Kumar",
                email="rohan.kumar@school.com",
                phone="9876543212",
                date_of_birth=date(2008, 12, 10),
                gender="Male",
                class_level="10-B",
                address="789 Pine Road, City",
                guardian_name="Vikram Kumar",
                guardian_phone="9876543202",
                status="Active"
            ),
            Student(
                user_id=owner_id,
                roll_number="10004",
                first_name="Neha",
                last_name="Singh",
                email="neha.singh@school.com",
                phone="9876543213",
                date_of_birth=date(2009, 3, 25),
                gender="Female",
                class_level="10-B",
                address="321 Elm Street, City",
                guardian_name="Arjun Singh",
                guardian_phone="9876543203",
                status="Active"
            ),
            Student(
                user_id=owner_id,
                roll_number="10005",
                first_name="Arjun",
                last_name="Gupta",
                email="arjun.gupta@school.com",
                phone="9876543214",
                date_of_birth=date(2009, 7, 8),
                gender="Male",
                class_level="10-A",
                address="654 Maple Lane, City",
                guardian_name="Suresh Gupta",
                guardian_phone="9876543204",
                status="Active"
            ),
        ]
        
        for student in students:
            db.session.add(student)
        
        db.session.commit()
        print(f"Added {len(students)} students")
        
        # Sample Teachers
        print("Adding sample teachers...")
        teachers = [
            Teacher(
                user_id=owner_id,
                employee_id="T001",
                first_name="Rajesh",
                last_name="Verma",
                email="rajesh.verma@school.com",
                phone="9876543300",
                qualification="B.Sc, B.Ed",
                specialization="Mathematics",
                gender="Male",
                department="Science",
                joining_date=date(2015, 6, 1),
                salary=50000,
                status="Active"
            ),
            Teacher(
                user_id=owner_id,
                employee_id="T002",
                first_name="Deepika",
                last_name="Reddy",
                email="deepika.reddy@school.com",
                phone="9876543301",
                qualification="B.A, B.Ed",
                specialization="English",
                gender="Female",
                department="Languages",
                joining_date=date(2018, 7, 15),
                salary=45000,
                status="Active"
            ),
            Teacher(
                user_id=owner_id,
                employee_id="T003",
                first_name="Amar",
                last_name="Singh",
                email="amar.singh@school.com",
                phone="9876543302",
                qualification="B.Sc, B.Ed",
                specialization="Physics",
                gender="Male",
                department="Science",
                joining_date=date(2016, 9, 1),
                salary=52000,
                status="Active"
            ),
            Teacher(
                user_id=owner_id,
                employee_id="T004",
                first_name="Meera",
                last_name="Nair",
                email="meera.nair@school.com",
                phone="9876543303",
                qualification="B.Sc, B.Ed",
                specialization="Chemistry",
                gender="Female",
                department="Science",
                joining_date=date(2017, 8, 15),
                salary=48000,
                status="Active"
            ),
        ]
        
        for teacher in teachers:
            db.session.add(teacher)
        
        db.session.commit()
        print(f"Added {len(teachers)} teachers")
        
        # Sample Attendance Records
        print("Adding sample attendance records...")
        today = date.today()
        attendance_records = []
        
        for student in students[:3]:
            for i in range(10):
                attendance_date = today - timedelta(days=i)
                status = "Present" if i % 3 != 0 else "Absent"
                attendance = Attendance(
                    user_id=owner_id,
                    student_id=student.id,
                    date=attendance_date,
                    status=status,
                    recorded_by="Admin"
                )
                attendance_records.append(attendance)
        
        for record in attendance_records:
            db.session.add(record)
        
        db.session.commit()
        print(f"Added {len(attendance_records)} attendance records")
        
        # Sample Grades
        print("Adding sample grades...")
        subjects = ["Mathematics", "English", "Science", "Social Studies"]
        exam_types = ["Unit Test 1", "Unit Test 2", "Mid Term", "Final"]
        
        grades = []
        for student in students[:3]:
            for subject in subjects:
                grade = Grade(
                    user_id=owner_id,
                    student_id=student.id,
                    teacher_id=teachers[0].id if subject == "Mathematics" else teachers[1].id,
                    subject=subject,
                    exam_name="Mid Term",
                    marks=75 + (student.id % 25),
                    total_marks=100,
                    recorded_date=today - timedelta(days=15)
                )
                grade.calculate_grade()
                grades.append(grade)
        
        for grade in grades:
            db.session.add(grade)
        
        db.session.commit()
        print(f"Added {len(grades)} grades")
        
        # Sample Fees
        print("Adding sample fees...")
        fee_types = ["Tuition Fee", "Transportation Fee", "Library Fee", "Sports Fee"]
        fees = []
        
        for student in students:
            for fee_type in fee_types:
                fee = Fee(
                    user_id=owner_id,
                    student_id=student.id,
                    fee_type=fee_type,
                    amount=5000 if fee_type == "Tuition Fee" else 2000,
                    due_date=today + timedelta(days=30),
                    amount_paid=5000 if fee_type == "Tuition Fee" else 0,
                    status="Paid" if fee_type == "Tuition Fee" else "Pending",
                    payment_method="Online" if fee_type == "Tuition Fee" else None,
                    payment_date=today - timedelta(days=5) if fee_type == "Tuition Fee" else None
                )
                fees.append(fee)
        
        for fee in fees:
            db.session.add(fee)
        
        db.session.commit()
        print(f"Added {len(fees)} fee records")
        
        # Sample Calendar Events
        print("Adding sample calendar events...")
        calendar_events = [
            CalendarEvent(
                user_id=owner_id,
                title="School Independence Day Celebration",
                description="Annual Independence Day celebration with cultural programs",
                event_date=today + timedelta(days=10),
                event_type="Event",
                is_reminder=True,
                reminder_days=7
            ),
            CalendarEvent(
                user_id=owner_id,
                title="Mid-Term Examinations",
                description="First mid-term examinations for all classes",
                event_date=today + timedelta(days=20),
                event_type="Exam",
                is_reminder=True,
                reminder_days=14
            ),
            CalendarEvent(
                user_id=owner_id,
                title="Parent-Teacher Meeting",
                description="Quarterly parent-teacher meeting to discuss student progress",
                event_date=today + timedelta(days=15),
                event_type="Meeting",
                is_reminder=True,
                reminder_days=3
            ),
            CalendarEvent(
                user_id=owner_id,
                title="School Sports Day",
                description="Annual sports competition and games",
                event_date=today + timedelta(days=30),
                event_type="Sports",
                is_reminder=True,
                reminder_days=7
            ),
            CalendarEvent(
                user_id=owner_id,
                title="Christmas Holiday",
                description="School closed for Christmas celebrations",
                event_date=today + timedelta(days=45),
                event_type="Holiday",
                is_reminder=True,
                reminder_days=1
            )
        ]
        
        for event in calendar_events:
            db.session.add(event)
        
        db.session.commit()
        print(f"Added {len(calendar_events)} calendar events")
        
        print("\n✅ Database initialization completed successfully!")
        print("\nSample Data Summary:")
        print(f"  - Students: {len(students)}")
        print(f"  - Teachers: {len(teachers)}")
        print(f"  - Attendance Records: {len(attendance_records)}")
        print(f"  - Grades: {len(grades)}")
        print(f"  - Fee Records: {len(fees)}")
        print(f"  - Calendar Events: {len(calendar_events)}")
        print("\nYou can now access the application at http://localhost:5000")

if __name__ == "__main__":
    try:
        init_sample_data()
    except Exception as e:
        print(f"\n❌ Error initializing database: {str(e)}")
        import traceback
        traceback.print_exc()
