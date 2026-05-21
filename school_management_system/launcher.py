import threading
import webbrowser
import time
import sys
import os

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    os.chdir(base_dir)

try:
    from app import app, db

    def run_flask():
        with app.app_context():
            db.create_all()
        app.run(port=5000, debug=False, use_reloader=False)

    if __name__ == '__main__':
        t = threading.Thread(target=run_flask, daemon=True)
        t.start()
        time.sleep(5)
        webbrowser.open('http://localhost:5000')
        t.join()

except Exception as e:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", str(e))