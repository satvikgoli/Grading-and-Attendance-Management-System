import os
import time
import signal
import psutil
import sys

def find_and_kill_db_processes():
    """Find and kill processes that might be using the database file"""
    db_file = os.path.abspath('instance/school_new.db')
    killed = False
    
    for proc in psutil.process_iter(['pid', 'name', 'open_files']):
        try:
            # Check if this process has the database file open
            if proc.info['open_files']:
                for file in proc.info['open_files']:
                    if file.path == db_file:
                        print(f"Found process using database: {proc.info['name']} (PID: {proc.info['pid']})")
                        os.kill(proc.info['pid'], signal.SIGTERM)
                        killed = True
                        print(f"Terminated process: {proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if killed:
        # Give processes time to clean up
        time.sleep(2)
        print("Cleaned up database processes")
    else:
        print("No processes found using the database")

if __name__ == "__main__":
    find_and_kill_db_processes() 