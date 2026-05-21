# Quick Start Guide - School Management System

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database with Sample Data
```bash
python init_db.py
```

This will:
- Create the database
- Set up all tables
- Populate with sample data (5 students, 4 teachers, grades, attendance, fees)

### Step 3: Run the Application
```bash
python app.py
```

### Step 4: Access the Application
Open your browser and go to: `http://localhost:5000`

---

## 📊 What's Included

✅ **Complete Student Management System**
- Add/Edit/Delete students
- View detailed student profiles
- Track attendance
- Monitor grades
- Manage fees

✅ **Teacher Management**
- Add/Edit/Delete teachers
- View teacher profiles
- Track grades recorded

✅ **Attendance Tracking**
- Mark attendance by class or date
- Auto-save attendance changes
- Attendance statistics

✅ **Grade Management**
- Record grades and marks
- Automatic grade calculation (A, B, C, D, F)
- Percentage calculation

✅ **Fees Management**
- Track school fees
- Payment management
- Overdue alerts
- Financial statistics

✅ **Professional UI**
- Dark blue theme
- Responsive design
- Mobile-friendly
- Smooth animations

---

## 🔍 Sample Data

After running `init_db.py`, you'll have:

**Students:**
- Aarav Sharma (10-A)
- Priya Patel (10-A)
- Rohan Kumar (10-B)
- Neha Singh (10-B)
- Arjun Gupta (10-A)

**Teachers:**
- Rajesh Verma (Mathematics)
- Deepika Reddy (English)
- Amar Singh (Physics)
- Meera Nair (Chemistry)

---

## 🎯 Key Features to Try

1. **Dashboard**
   - See statistics and recent activities
   - Quick action buttons

2. **Students Management**
   - View all students
   - Click on a student to see details
   - Add new students
   - Edit student information

3. **Attendance**
   - Select a date
   - Mark attendance for all students
   - Changes save automatically

4. **Grades**
   - Add grades for students
   - View all grades
   - Filter by student or subject

5. **Fees**
   - View all fees
   - Track payment status
   - See financial statistics

---

## 🛠️ Customization

### Change Port
Edit `app.py` last line:
```python
app.run(debug=True, host='0.0.0.0', port=8000)  # Change 5000 to 8000
```

### Modify Theme Colors
Edit `static/css/style.css`:
```css
:root {
    --primary-color: #0d47a1;      /* Change this color */
    --secondary-color: #1565c0;
    /* ... more colors ... */
}
```

### Add More Classes
Simply enter them when adding students (e.g., "11-A", "12-B")

---

## 📱 Mobile Access

The system is fully responsive. Access it from:
- Desktop browsers
- Tablets
- Mobile phones
- Just use the URL: `http://localhost:5000`

---

## 🔐 Notes

- No authentication is configured (add it as needed)
- Data is stored in `school_management.db` file
- All changes are saved immediately to the database
- Backup your database file before major changes

---

## 📞 Support

If you encounter any issues:

1. **Port already in use?**
   ```bash
   python app.py  # Try a different port or stop the conflicting process
   ```

2. **Database issues?**
   ```bash
   rm school_management.db
   python init_db.py
   ```

3. **Missing dependencies?**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

---

## 📚 Next Steps

- Customize the school name and logo
- Add more users/teachers
- Configure fees as per your school
- Set up email notifications
- Add user authentication
- Create reports and analytics

---

Enjoy managing your school! 🎓
