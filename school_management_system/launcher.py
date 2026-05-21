import threading
import webview
import sys
import os

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    os.chdir(base_dir)

from app import app, db

def run_flask():
    with app.app_context():
        db.create_all()
    app.run(port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    
    import time
    time.sleep(2)
    
    webview.create_window(
        'School Management System',
        'http://localhost:5000',
        width=1200,
        height=750,
        resizable=True
    )
    webview.start()