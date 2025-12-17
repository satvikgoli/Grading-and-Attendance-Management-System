import sqlite3
import time
import os

def table_exists(cursor, table_name):
    """Check if a table exists in the database"""
    cursor.execute(f"""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='{table_name}'
    """)
    return cursor.fetchone() is not None

def delete_student_teacher_data():
    """Delete all student and teacher data from the database"""
    db_path = 'instance/school.db'
    max_retries = 3
    retry_delay = 2  # seconds
    
    # Tables to delete from, in order of foreign key dependencies
    tables = [
        'attendance',
        'grade',
        'class_student',
        'student_subject',
        'grade_category',
        'student',
        'teacher',
        'user'  # Special case - we'll only delete students and teachers
    ]
    
    for attempt in range(max_retries):
        try:
            # Connect directly to the SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Enable foreign key support
            cursor.execute('PRAGMA foreign_keys = ON')
            
            # Start transaction
            cursor.execute('BEGIN TRANSACTION')
            
            try:
                # Delete from each table if it exists
                for table in tables:
                    if table_exists(cursor, table):
                        if table == 'user':
                            # Special case for user table - only delete students and teachers
                            cursor.execute("DELETE FROM user WHERE role IN ('student', 'teacher')")
                            print(f"Deleted student and teacher users from {table}")
                        else:
                            cursor.execute(f'DELETE FROM {table}')
                            print(f"Deleted all records from {table}")
                
                # Commit the transaction
                conn.commit()
                print("\nSuccessfully deleted all student and teacher data")
                
            except Exception as e:
                # Rollback in case of error
                conn.rollback()
                raise e
            
            finally:
                # Close the connection
                cursor.close()
                conn.close()
                
            return
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                print(f"Database is locked, retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                continue
            print(f"Error: {str(e)}")
            raise
        except Exception as e:
            print(f"Error: {str(e)}")
            raise

if __name__ == '__main__':
    try:
        delete_student_teacher_data()
    except Exception as e:
        print(f"Failed to delete data: {str(e)}")
        exit(1) 