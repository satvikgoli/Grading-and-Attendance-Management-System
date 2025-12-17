from flask import Flask
from models import db, Student, Teacher
from sqlalchemy import text
import os

def run_migrations():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_new.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        try:
            # Add is_approved column to Student table if it doesn't exist
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE student ADD COLUMN is_approved BOOLEAN DEFAULT FALSE'))
                conn.execute(text('ALTER TABLE teacher ADD COLUMN is_approved BOOLEAN DEFAULT FALSE'))
                conn.commit()
            print("Successfully added is_approved columns to Student and Teacher tables")
            
            # Update existing records to be approved
            Student.query.update({Student.is_approved: True})
            Teacher.query.update({Teacher.is_approved: True})
            db.session.commit()
            print("Successfully updated existing records to be approved")
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    run_migrations() 