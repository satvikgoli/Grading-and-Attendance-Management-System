from flask import Flask
from models import db, User, Student, Teacher, Subject, StudentSubject, Attendance, Grade, GradeCategory
from datetime import datetime
import os

# Get absolute path for database file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'GAMS_database.db')

# Create Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

def setup_database():
    with app.app_context():
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # Create all tables
        db.create_all()
        print("Created all database tables successfully!")
        
        try:
            # Create admin user
            admin = User(username='admin', email='admin@gams.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Created admin user")
            
            # Create subjects
            subjects_data = [
                "Analysis of Algorithm",
                "Advance Database Systems",
                "Advanced Operating Systems",
                "Pattern Recognition",
                "AI & ML",
                "Neural Networks",
                "Theory of Automata",
                "Computer Organization and Architecture"
            ]
            
            subjects = []
            for subject_name in subjects_data:
                subject = Subject(name=subject_name)
                db.session.add(subject)
                subjects.append(subject)
            db.session.commit()
            print("Created subjects")
            
            # Create teachers with their subjects
            teachers_data = [
                {"name": "Dr. Smith", "subject_index": 0},
                {"name": "Prof. Johnson", "subject_index": 1},
                {"name": "Dr. Williams", "subject_index": 2},
                {"name": "Prof. Brown", "subject_index": 3},
                {"name": "Dr. Davis", "subject_index": 4},
                {"name": "Prof. Miller", "subject_index": 5},
                {"name": "Dr. Wilson", "subject_index": 6},
                {"name": "Prof. Moore", "subject_index": 7}
            ]
            
            for i, teacher_data in enumerate(teachers_data):
                teacher_user = User(
                    username=f'teacher{i+1}',
                    email=f'teacher{i+1}@gams.com',
                    role='teacher'
                )
                teacher_user.set_password('teacher123')
                db.session.add(teacher_user)
                db.session.commit()
                
                first_name, last_name = teacher_data["name"].split()
                teacher = Teacher(
                    user_id=teacher_user.id,
                    first_name=first_name,
                    last_name=last_name,
                    subject_id=subjects[teacher_data["subject_index"]].id,
                    is_approved=True
                )
                db.session.add(teacher)
                db.session.commit()
                print(f"Created teacher: {teacher_data['name']}")
            
            # Create students with their subjects
            students_data = [
                {
                    "name": ("John", "Doe"),
                    "email": "john.doe@gams.com",
                    "student_id": "2024001",
                    "gender": "M",
                    "dob": "2000-01-15",
                    "phone": "1234567890",
                    "subject_indices": [0, 1, 2]
                },
                {
                    "name": ("Jane", "Smith"),
                    "email": "jane.smith@gams.com",
                    "student_id": "2024002",
                    "gender": "F",
                    "dob": "2000-03-20",
                    "phone": "2345678901",
                    "subject_indices": [2, 3, 4]
                },
                {
                    "name": ("Michael", "Johnson"),
                    "email": "michael.j@gams.com",
                    "student_id": "2024003",
                    "gender": "M",
                    "dob": "2000-05-10",
                    "phone": "3456789012",
                    "subject_indices": [4, 5, 6]
                }
            ]
            
            for i, student_data in enumerate(students_data):
                # Create user account
                student_user = User(
                    username=f'student{i+1}',
                    email=student_data["email"],
                    role='student'
                )
                student_user.set_password('student123')
                db.session.add(student_user)
                db.session.commit()
                
                # Create student profile
                student = Student(
                    user_id=student_user.id,
                    student_id=student_data["student_id"],
                    first_name=student_data["name"][0],
                    last_name=student_data["name"][1],
                    gender=student_data["gender"],
                    date_of_birth=datetime.strptime(student_data["dob"], '%Y-%m-%d'),
                    email=student_data["email"],
                    phone_number=student_data["phone"],
                    is_approved=True
                )
                db.session.add(student)
                db.session.commit()
                
                # Assign subjects to student
                for subject_index in student_data["subject_indices"]:
                    student_subject = StudentSubject(
                        student_id=student.id,
                        subject_id=subjects[subject_index].id
                    )
                    db.session.add(student_subject)
                db.session.commit()
                print(f"Created student: {student_data['name'][0]} {student_data['name'][1]}")
            
            # Create grade categories for each subject
            categories = ["Assignments", "Mid-term", "Final Exam", "Projects"]
            for subject in subjects:
                teacher = Teacher.query.filter_by(subject_id=subject.id).first()
                if teacher:
                    for category_name in categories:
                        category = GradeCategory(
                            name=category_name,
                            teacher_id=teacher.id,
                            subject_id=subject.id
                        )
                        db.session.add(category)
            db.session.commit()
            print("Created grade categories")
            
            print("\nDatabase setup completed successfully!")
            print("\nLogin credentials:")
            print("Admin - username: admin, password: admin123")
            print("Teachers - username: teacher1-8, password: teacher123")
            print("Students - username: student1-3, password: student123")
            
        except Exception as e:
            print(f"Error setting up database: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    setup_database() 