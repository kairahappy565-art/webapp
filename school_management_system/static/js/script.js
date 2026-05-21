// School Management System - JavaScript

// ==================== SIDEBAR NAVIGATION ====================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar state
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.btn-toggle-sidebar');
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
    
    // Close sidebar when clicking on mobile
    if (window.innerWidth <= 768) {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                // Don't close if it's a submenu toggle
                if (!this.parentElement.querySelector('.submenu')) {
                    sidebar.classList.remove('show');
                }
            });
        });
    }
    
    // Submenu toggle
    const submenuToggles = document.querySelectorAll('.nav-link[data-toggle]');
    submenuToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const submenu = this.nextElementSibling;
            if (submenu && submenu.classList.contains('submenu')) {
                submenu.classList.toggle('show');
                this.parentElement.classList.toggle('active');
            }
        });
    });
    
    // Set active nav item
    const currentLocation = location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.href.includes(currentLocation)) {
            link.classList.add('active');
            // Also activate parent submenu
            const parent = link.closest('.nav-item');
            if (parent && parent.previousElementSibling) {
                const toggle = parent.previousElementSibling.querySelector('.nav-link[data-toggle]');
                if (toggle) {
                    toggle.classList.add('active');
                    toggle.nextElementSibling?.classList.add('show');
                }
            }
        }
    });
    
    // Initialize tooltips and other components
    initializeDataTables();
    initializeAttendanceForm();
    initializeDeleteButtons();
});

// ==================== DATA TABLES ====================

function initializeDataTables() {
    // Add sorting functionality to tables
    const tables = document.querySelectorAll('.table-sortable');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th[data-sortable]');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(table, index);
            });
        });
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Determine sort direction
    const header = table.querySelectorAll('th')[columnIndex];
    let isAscending = !header.classList.contains('sort-asc');
    
    // Remove previous sort indicators
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add sort indicator to current header
    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as numbers
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        
        // Sort as strings
        return isAscending 
            ? aValue.localeCompare(bValue) 
            : bValue.localeCompare(aValue);
    });
    
    // Rebuild table
    rows.forEach(row => tbody.appendChild(row));
}

// ==================== ATTENDANCE FORM ====================

function initializeAttendanceForm() {
    const attendanceInputs = document.querySelectorAll('.attendance-checkbox, .attendance-status');
    attendanceInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.dataset.studentId && this.dataset.date) {
                const studentId = this.dataset.studentId;
                const date = this.dataset.date;
                const status = this.value;
                setAttendanceStatus(studentId, date, status);
            }
        });
    });
}

function saveAttendance(checkbox) {
    const studentId = checkbox.dataset.studentId;
    const date = checkbox.dataset.date;
    const status = checkbox.checked ? 'Present' : 'Absent';
    
    fetch('/attendance/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            student_id: studentId,
            date: date,
            status: status
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Attendance saved successfully', 'success');
        } else {
            showNotification('Error saving attendance: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error saving attendance', 'error');
    });
}

function setAttendanceStatus(studentId, date, status) {
    fetch('/attendance/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            student_id: studentId,
            date: date,
            status: status
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Attendance updated successfully', 'success');
        } else {
            showNotification('Error updating attendance', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating attendance', 'error');
    });
}

// ==================== DELETE BUTTONS ====================

function initializeDeleteButtons() {
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const itemName = this.dataset.item || 'item';
            if (confirm(`Are you sure you want to delete this ${itemName}? This action cannot be undone.`)) {
                this.closest('form').submit();
            } else {
                e.preventDefault();
            }
        });
    });
}

// ==================== NOTIFICATIONS ====================

function showNotification(message, type = 'info', duration = 3000) {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.textContent = message;
    
    if (container) {
        container.appendChild(notification);
    } else {
        document.body.appendChild(notification);
    }
    
    // Auto remove after duration
    if (duration > 0) {
        setTimeout(() => {
            notification.remove();
        }, duration);
    }
}

function updateFeeBalance() {
    const amountInput = document.getElementById('amount');
    const paidInput = document.getElementById('amount_paid');
    const balanceInput = document.getElementById('remaining_balance');

    if (!amountInput || !paidInput || !balanceInput) {
        return;
    }

    const amount = parseFloat(amountInput.value) || 0;
    const paid = parseFloat(paidInput.value) || 0;
    const balance = Math.max(amount - paid, 0);

    balanceInput.value = `ZMW ${balance.toFixed(2)}`;
}

function printFeeReceipt() {
    const schoolName = document.getElementById('school_name')?.value || 'School';
    const studentSelect = document.getElementById('student_id');
    const studentName = studentSelect ? studentSelect.options[studentSelect.selectedIndex]?.text || '' : '';
    const feeType = document.getElementById('fee_type')?.value || '';
    const amount = parseFloat(document.getElementById('amount')?.value) || 0;
    const amountPaid = parseFloat(document.getElementById('amount_paid')?.value) || 0;
    const dueDate = document.getElementById('due_date')?.value || '';
    const paymentDate = document.getElementById('payment_date')?.value || 'Not set';
    const paymentMethod = document.getElementById('payment_method')?.value || 'Not set';
    const status = document.getElementById('status')?.value || (amountPaid >= amount ? 'Paid' : 'Pending');
    const remarks = document.getElementById('remarks')?.value || 'None';
    const balance = Math.max(amount - amountPaid, 0);

    const receiptHtml = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Fee Receipt</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 30px; }
        .receipt-header { text-align: center; margin-bottom: 30px; }
        .receipt-header h1 { margin: 0; font-size: 28px; }
        .receipt-header p { margin: 5px 0 0; color: #555; }
        .receipt-section { border: 1px solid #ccc; padding: 20px; border-radius: 8px; }
        .receipt-row { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .receipt-row strong { width: 180px; }
        .receipt-footer { margin-top: 30px; text-align: center; color: #666; }
    </style>
</head>
<body>
    <div class="receipt-header">
        <h1>${schoolName}</h1>
        <p>Fee Receipt</p>
    </div>
    <div class="receipt-section">
        <div class="receipt-row"><strong>Student</strong><span>${studentName}</span></div>
        <div class="receipt-row"><strong>Fee Type</strong><span>${feeType}</span></div>
        <div class="receipt-row"><strong>Amount</strong><span>ZMW ${amount.toFixed(2)}</span></div>
        <div class="receipt-row"><strong>Amount Paid</strong><span>ZMW ${amountPaid.toFixed(2)}</span></div>
        <div class="receipt-row"><strong>Remaining Balance</strong><span>ZMW ${balance.toFixed(2)}</span></div>
        <div class="receipt-row"><strong>Due Date</strong><span>${dueDate}</span></div>
        <div class="receipt-row"><strong>Payment Date</strong><span>${paymentDate}</span></div>
        <div class="receipt-row"><strong>Payment Method</strong><span>${paymentMethod}</span></div>
        <div class="receipt-row"><strong>Status</strong><span>${status}</span></div>
        <div class="receipt-row"><strong>Remarks</strong><span>${remarks}</span></div>
    </div>
    <div class="receipt-footer">
        <p>Generated on ${new Date().toLocaleString()}</p>
    </div>
    <script>
        window.onload = function() { window.print(); };
    </script>
</body>
</html>`;

    const receiptWindow = window.open('', '_blank');
    if (!receiptWindow) {
        alert('Please enable popups to print receipts.');
        return;
    }

    receiptWindow.document.write(receiptHtml);
    receiptWindow.document.close();
}



