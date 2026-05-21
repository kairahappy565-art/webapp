# School Management System

A professional, modern School Management System built with Python Flask, featuring a dark blue responsive design with comprehensive management tools for students, teachers, attendance, grades, and school fees.

## Features

### 📊 Dashboard
- Real-time statistics and analytics
- Quick access to key metrics
- Recent activities overview
- System health monitoring

### 👨‍🎓 Student Management
- Complete student profiles with personal information
- Roll number tracking
- Class/division management
- Guardian information
- Contact management
- Status tracking (Active, Inactive, Graduated)

### 👨‍🏫 Teacher Management
- Teacher profiles and credentials
- Employee ID tracking
- Department and specialization management
- Salary management
- Professional qualifications
- Status tracking

### 📋 Attendance Management
- Daily attendance tracking
- Mark attendance by class or individual
- Attendance statistics
- Present/Absent/Leave status
- Bulk attendance operations

### 📊 Grade Management
- Record student grades and marks
- Subject-wise grading
- Exam-based records
- Automatic GPA calculation
- Letter grade assignment (A, B, C, D, F)
- Percentage calculation

### 💰 School Fees Management
- Fee type management
- Payment tracking
- Due date management
- Payment method recording
- Balance calculation
- Overdue notification
- Financial statistics

## Technologies Used

- **Backend**: Python Flask 2.3.2
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Custom CSS with dark blue professional theme
- **Responsive Design**: Mobile-first approach

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Setup Instructions

1. **Navigate to the project directory:**
   ```bash
   cd school_management_system
   ```

2. **Create a virtual environment:**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database:**
   ```bash
   python -c "from app import app; from models import db; app.app_context().push(); db.create_all(); print('Database initialized successfully!')"
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Access the application:**
   - Open your browser and navigate to `http://localhost:5000`
   - The application will be running on port 5000

## Project Structure

```
school_management_system/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── models.py                   # Database models
├── requirements.txt            # Python dependencies
├── templates/                  # HTML templates
│   ├── base.html              # Base template with sidebar
│   ├── dashboard.html         # Dashboard page
│   ├── students.html          # Student list
│   ├── student_form.html      # Add/Edit student
│   ├── student_detail.html    # Student profile
│   ├── teachers.html          # Teacher list
│   ├── teacher_form.html      # Add/Edit teacher
│   ├── teacher_detail.html    # Teacher profile
│   ├── attendance.html        # Attendance tracking
│   ├── grades.html            # Grades list
│   ├── grade_form.html        # Add/Edit grade
│   ├── fees.html              # Fees management
│   ├── fee_form.html          # Add/Edit fee
│   ├── 404.html               # 404 error page
│   └── 500.html               # 500 error page
└── static/
    ├── css/
    │   └── style.css          # Main stylesheet
    └── js/
        └── script.js          # JavaScript functionality
```

## Database Models

### Student
- Roll Number, Name, Email, Phone
- Date of Birth, Gender, Class/Division
- Admission Date, Address
- Guardian Information
- Status tracking
- Relationships: Attendance, Grades, Fees

### Teacher
- Employee ID, Name, Email, Phone
- Qualifications, Specialization
- Department, Joining Date
- Salary, Status
- Relationships: Grades

### Attendance
- Student Reference
- Date and Status (Present/Absent/Leave)
- Remarks
- Recorded by information

### Grade
- Student and Teacher References
- Subject, Exam Name
- Marks and Total Marks
- Automatic Grade Calculation (A-F)
- Percentage Calculation

### Fee
- Student Reference
- Fee Type
- Amount, Due Date
- Payment Tracking (Amount Paid, Date, Method)
- Status (Pending/Paid/Overdue)

## Key Features

### Modern UI/UX
- Dark blue professional theme
- Responsive design (mobile, tablet, desktop)
- Smooth animations and transitions
- Clean card-based layouts
- Intuitive navigation

### Responsive Design
- Mobile-first approach
- Tablets and desktop optimized
- Flexible sidebar navigation
- Responsive tables and forms
- Touch-friendly interface

### Data Management
- Pagination for large datasets
- Search and filter functionality
- Sorting capabilities
- Bulk operations support
- Data validation

### Security Features
- Form validation
- CSRF protection ready
- Secure session management
- Database transaction handling
- Error handling

## Usage Guide

### Adding a Student
1. Navigate to Students → Add Student
2. Fill in all required fields
3. Click "Add Student" to save
4. View student profile from the list

### Recording Attendance
1. Go to Attendance Management
2. Select date and class (optional)
3. Mark attendance status for each student
4. Changes are saved automatically

### Managing Grades
1. Go to Grades → Add Grade
2. Select student and teacher
3. Enter subject, marks, and exam name
4. Grade is calculated automatically
5. Save the record

### Tracking Fees
1. Go to School Fees → Add Fee
2. Select student and fee type
3. Enter amount and due date
4. Track payment status
5. Update payment information

## Performance Optimization

- Efficient database queries with pagination
- CSS and JavaScript minification ready
- Lazy loading of images
- Optimized database indexes
- Caching-friendly structure

## Browser Support

- Chrome/Chromium (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers

## File Sizes

- Main CSS: ~45KB
- Main JavaScript: ~12KB
- Templates: Lightweight and efficient

## Customization

### Theme Customization
Edit `static/css/style.css` to modify:
- Color scheme (update CSS variables in `:root`)
- Font styles
- Spacing and sizing
- Animations and transitions

### Sidebar Navigation
Edit `templates/base.html` to:
- Add new menu items
- Modify navigation structure
- Change icons

### Database Models
Edit `models.py` to:
- Add new fields to existing models
- Create new models
- Modify relationships

## Future Enhancements

- [ ] User authentication and login system
- [ ] Role-based access control (Admin, Teacher, Student)
- [ ] Report generation (PDF/Excel)
- [ ] Email notifications
- [ ] SMS alerts
- [ ] Parent portal access
- [ ] Student portal
- [ ] Timetable management
- [ ] Exam scheduling
- [ ] Result analysis
- [ ] API endpoints
- [ ] Advanced analytics and charts

## Troubleshooting

### Port Already in Use
If port 5000 is already in use:
```bash
python app.py --port 5001
```

### Database Issues
Reset the database:
```bash
rm school_management.db
python -c "from app import app; from models import db; app.app_context().push(); db.create_all()"
```

### Missing Dependencies
Reinstall requirements:
```bash
pip install --upgrade -r requirements.txt
```

## License

This project is provided as-is for educational and professional use.

## Support & Contribution

For issues, suggestions, or contributions, please feel free to reach out or create a pull request.

## Version

**Version**: 1.0.0
**Last Updated**: 2024

---

**Happy Managing! 🎓**
