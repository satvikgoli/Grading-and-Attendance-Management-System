from flask import Flask
from models import db, User, Student, Teacher, Subject, StudentSubject
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/GAMS_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def create_sample_data():
    with app.app_context():
        # Create tables
        db.create_all()
        print("Created database tables")
        
        try:
            # Create admin
            admin = User(username='admin', email='admin@school.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Created admin user")
            
            # Create subjects
            subjects_list = [
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
            for subject_name in subjects_list:
                subject = Subject(name=subject_name)
                db.session.add(subject)
                subjects.append(subject)
            db.session.commit()
            print("Created subjects")
            
            # Create teachers
            for i, subject in enumerate(subjects, 1):
                teacher_user = User(
                    username=f'teacher{i}',
                    email=f'teacher{i}@school.com',
                    role='teacher'
                )
                teacher_user.set_password('teacher123')
                db.session.add(teacher_user)
                db.session.commit()
                
                teacher = Teacher(
                    user_id=teacher_user.id,
                    first_name=f'Teacher',
                    last_name=str(i),
                    subject_id=subject.id,
                    is_approved=True
                )
                db.session.add(teacher)
                db.session.commit()
                print(f"Created teacher {i}")
            
            # Create students
            students_data = [
                {
                    'username': 'student1',
                    'email': 'student1@school.com',
                    'student_id': 'S001',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'gender': 'M',
                    'dob': '2000-01-01',
                    'phone': '1234567890',
                    'subjects': subjects[:3]
                },
                {
                    'username': 'student2',
                    'email': 'student2@school.com',
                    'student_id': 'S002',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'gender': 'F',
                    'dob': '2000-02-15',
                    'phone': '2345678901',
                    'subjects': subjects[2:5]
                },
                {
                    'username': 'student3',
                    'email': 'student3@school.com',
                    'student_id': 'S003',
                    'first_name': 'Mike',
                    'last_name': 'Wilson',
                    'gender': 'M',
                    'dob': '2000-03-20',
                    'phone': '3456789012',
                    'subjects': subjects[4:7]
                }
            ]
            
            for data in students_data:
                student_user = User(
                    username=data['username'],
                    email=data['email'],
                    role='student'
                )
                student_user.set_password('student123')
                db.session.add(student_user)
                db.session.commit()
                
                student = Student(
                    user_id=student_user.id,
                    student_id=data['student_id'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    gender=data['gender'],
                    date_of_birth=datetime.strptime(data['dob'], '%Y-%m-%d'),
                    email=data['email'],
                    phone_number=data['phone'],
                    is_approved=True
                )
                db.session.add(student)
                db.session.commit()
                
                for subject in data['subjects']:
                    student_subject = StudentSubject(
                        student_id=student.id,
                        subject_id=subject.id
                    )
                    db.session.add(student_subject)
                db.session.commit()
                print(f"Created student: {data['first_name']} {data['last_name']}")
            
            print("\nSample data created successfully!")
            print("\nLogin credentials:")
            print("Admin - username: admin, password: admin123")
            print("Teachers - username: teacher1-8, password: teacher123")
            print("Students - username: student1-3, password: student123")
            
        except Exception as e:
            print(f"Error creating sample data: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_sample_data() 