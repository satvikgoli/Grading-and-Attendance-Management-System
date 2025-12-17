from app import app, db
from models import User, Student, Teacher, Subject, Grade, GradeCategory, Attendance, Class, ClassStudent, StudentSubject
import os
from flask import Flask
from sqlalchemy import text
import time
import sqlite3

def reset_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("Dropped all tables")
        
        # Create all tables
        db.create_all()
        print("Created all tables")
        
        # Create default admin user
        admin = User(username='admin', email='admin@school.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create default subjects
        subjects = [
            "Analysis of Algorithm",
            "Advance Database Systems",
            "Advanced Operating Systems",
            "Pattern Recognition",
            "AI & ML",
            "Neural Networks",
            "Theory of Automata",
            "Computer Organization and Architecture"
        ]
        
        for subject_name in subjects:
            subject = Subject(name=subject_name)
            db.session.add(subject)
        
        try:
            db.session.commit()
            print("Created default data")
        except Exception as e:
            print(f"Error creating default data: {e}")
            db.session.rollback()

def delete_student_teacher_data(app):
    """Delete all student and teacher data while preserving the database structure"""
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                # Close any existing connections
                db.session.close()
                db.engine.dispose()
                
                # Delete in correct order to handle foreign key constraints
                # First delete all related records
                db.session.execute(text('DELETE FROM attendance'))
                db.session.execute(text('DELETE FROM grade'))
                db.session.execute(text('DELETE FROM class_student'))
                db.session.execute(text('DELETE FROM student_subject'))
                db.session.execute(text('DELETE FROM grade_category'))
                
                # Delete students and teachers
                db.session.execute(text('DELETE FROM student'))
                db.session.execute(text('DELETE FROM teacher'))
                
                # Delete associated user accounts (except admin)
                db.session.execute(text("DELETE FROM user WHERE role IN ('student', 'teacher')"))
                
                db.session.commit()
                print("Successfully deleted all student and teacher data")
                return
                
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                print(f"Database is locked, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            raise
        except Exception as e:
            print(f"Error deleting data: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    reset_database()
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/school.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Delete student and teacher data only
    delete_student_teacher_data(app) 