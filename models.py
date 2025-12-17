from flask_login import UserMixin
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import os
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Boolean

# Get the absolute path for the database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'GAMS_database.db')

db = SQLAlchemy()

# User Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)
    
    def set_password(self, password):
        self.password = password
        
    def check_password(self, password):
        return self.password == password

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_teacher(self):
        return self.role == 'teacher'

    @property
    def is_student(self):
        return self.role == 'student'

# Student Model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('student', uselist=False))
    attendance = db.relationship('Attendance', backref='student', lazy=True)
    grades = db.relationship('Grade', backref=db.backref('student', lazy=True))
    subjects = db.relationship('Subject', secondary='student_subject', backref=db.backref('students', lazy='dynamic'))

# Subject Model
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    teachers = db.relationship('Teacher', backref='subject', lazy=True)
    attendance_records = db.relationship('Attendance', backref='subject', lazy=True)

# Student-Subject Association Model
class StudentSubject(db.Model):
    __tablename__ = 'student_subject'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    date_joined = db.Column(db.Date, default=datetime.utcnow)

# Teacher Model
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('teacher', uselist=False))
    attendance_records = db.relationship('Attendance', backref='teacher', lazy=True)
    grades = db.relationship('Grade', backref=db.backref('teacher', lazy=True))
    classes = db.relationship('Class', backref='teacher', lazy=True)
    
    def __repr__(self):
        return f'<Teacher {self.first_name} {self.last_name}>'

# Attendance Model
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=True)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)

# Add this new model for grade categories
class GradeCategory(db.Model):
    __tablename__ = 'grade_category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    grades = db.relationship('Grade', backref='category', lazy=True)
    teacher = db.relationship('Teacher', backref='grade_categories')
    subject = db.relationship('Subject', backref='grade_categories')

# Modify the Grade model to include category
class Grade(db.Model):
    __tablename__ = 'grade'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('grade_category.id'), nullable=False)
    grade = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    subject = db.relationship('Subject', backref='subject_grades')

# Class Model
class Class(db.Model):
    __tablename__ = 'class'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    students = db.relationship('Student', secondary='class_student', backref=db.backref('classes', lazy='dynamic'))
    attendance_records = db.relationship('Attendance', backref='class_record', lazy=True)

# Class-Student Association Model
class ClassStudent(db.Model):
    __tablename__ = 'class_student'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date_joined = db.Column(db.Date, default=datetime.utcnow)

def create_default_subjects(app):
    """Create the default subjects in the system"""
    with app.app_context():
        try:
            # Define the default subjects
            default_subjects = [
                "Analysis of Algorithm",
                "Advance Database Systems",
                "Advanced Operating Systems",
                "Pattern Recognition",
                "AI & ML",
                "Neural Networks",
                "Theory of Automata",
                "Computer Organization and Architecture"
            ]
            
            # Create subjects first
            for subject_name in default_subjects:
                try:
                    # Check if subject exists
                    subject = Subject.query.filter_by(name=subject_name).first()
                    if not subject:
                        subject = Subject(name=subject_name)
                        db.session.add(subject)
                        db.session.commit()
                        print(f"Created subject: {subject_name}")
                except Exception as e:
                    print(f"Error creating subject {subject_name}: {str(e)}")
                    db.session.rollback()
                    continue
            
            # Create a teacher for each subject if it doesn't exist
            subjects = Subject.query.all()
            for i, subject in enumerate(subjects, 1):
                try:
                    # Check if a teacher for this subject already exists
                    existing_teacher = Teacher.query.filter_by(subject_id=subject.id).first()
                    if not existing_teacher:
                        # Create user for teacher
                        username = f"teacher{i}"
                        email = f"teacher{i}@school.com"
                        
                        # Check if user exists
                        if not User.query.filter_by(username=username).first():
                            teacher_user = User(username=username, email=email, role='teacher')
                            teacher_user.set_password('teacher123')
                            db.session.add(teacher_user)
                            db.session.commit()

                            # Create teacher
                            teacher = Teacher(
                                user_id=teacher_user.id,
                                first_name=f"Teacher",
                                last_name=str(i),
                                subject_id=subject.id
                            )
                            db.session.add(teacher)
                            db.session.commit()
                            print(f"Created teacher for {subject.name}")
                except Exception as e:
                    print(f"Error creating teacher for subject {subject.name}: {str(e)}")
                    db.session.rollback()
                    continue
            
            print("Default subjects and teachers created successfully")
            
        except Exception as e:
            print(f"Error in create_default_subjects: {str(e)}")
            db.session.rollback()
            raise

def init_db(app):
    """Initialize the database and create tables"""
    with app.app_context():
        try:
            # Create tables if they don't exist (without dropping existing ones)
            db.create_all()
            
            # Create admin user if it doesn't exist
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', email='admin@school.com', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("Created admin user with username 'admin' and password 'admin123'")
            
            # Create default subjects and teachers
            create_default_subjects(app)
            
            print("Database initialization completed successfully")
            
        except Exception as e:
            print(f"Error during database initialization: {str(e)}")
            db.session.rollback()
            raise

def create_sample_data(app):
    """Create sample data for testing"""
    with app.app_context():
        # Check if sample data already exists
        if User.query.filter_by(username='student1').first():
            print("Sample data already exists, skipping creation.")
            return

        # Get first two subjects
        subjects = Subject.query.limit(2).all()
        if not subjects:
            print("No subjects found. Please run init_db first.")
            return

        # Create sample students
        sample_students = [
            {
                'username': 'student1',
                'email': 'student1@school.com',
                'student_id': 'S001',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'gender': 'F',
                'dob': '2000-01-01'
            },
            {
                'username': 'student2',
                'email': 'student2@school.com',
                'student_id': 'S002',
                'first_name': 'John',
                'last_name': 'Doe',
                'gender': 'M',
                'dob': '2000-02-15'
            },
            {
                'username': 'student3',
                'email': 'student3@school.com',
                'student_id': 'S003',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'gender': 'F',
                'dob': '2000-03-20'
            }
        ]

        for student_data in sample_students:
            try:
                # Create user account
                student_user = User(
                    username=student_data['username'],
                    email=student_data['email'],
                    role='student'
                )
                student_user.set_password('student123')
                db.session.add(student_user)
                db.session.commit()

                # Create student profile
                student = Student(
                    user_id=student_user.id,
                    student_id=student_data['student_id'],
                    first_name=student_data['first_name'],
                    last_name=student_data['last_name'],
                    gender=student_data['gender'],
                    date_of_birth=datetime.strptime(student_data['dob'], '%Y-%m-%d'),
                    email=student_data['email'],
                    phone_number='1234567890'
                )
                db.session.add(student)
                db.session.commit()

                # Enroll student in subjects
                student.subjects.extend(subjects)
                db.session.commit()

                print(f"Created student {student_data['username']} with {len(subjects)} subjects")

            except Exception as e:
                print(f"Error creating student {student_data['username']}: {str(e)}")
                db.session.rollback()
                continue

        print("Sample data creation completed")

if __name__ == '__main__':
    # Create a Flask app instance for database initialization
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///GAMS_database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database with the app
    db.init_app(app)
    
    # Create tables and admin user
    print("Initializing database...")
    init_db(app)
    
    # Create sample data
    print("\nCreating sample data...")
    create_sample_data(app)
    
    print("\nDatabase initialization complete!")
    print("You can now run 'app.py' to start the application.")