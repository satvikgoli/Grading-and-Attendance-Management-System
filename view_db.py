from app import app, db
from models import User, Student, Teacher, Subject, StudentSubject, Grade, GradeCategory, Attendance

def print_table_contents(table_name, records):
    print(f"\n=== {table_name} ===")
    if not records:
        print("No records found")
        return
    
    # Print column headers
    if records:
        columns = records[0].__table__.columns.keys()
        print(" | ".join(columns))
        print("-" * 80)
    
    # Print records
    for record in records:
        values = [str(getattr(record, col)) for col in columns]
        print(" | ".join(values))

def view_database():
    with app.app_context():
        # Users
        users = User.query.all()
        print_table_contents("Users", users)
        
        # Students
        students = Student.query.all()
        print_table_contents("Students", students)
        
        # Teachers
        teachers = Teacher.query.all()
        print_table_contents("Teachers", teachers)
        
        # Subjects
        subjects = Subject.query.all()
        print_table_contents("Subjects", subjects)
        
        # Student-Subject Associations
        student_subjects = StudentSubject.query.all()
        print_table_contents("Student-Subject Associations", student_subjects)
        
        # Grade Categories
        grade_categories = GradeCategory.query.all()
        print_table_contents("Grade Categories", grade_categories)
        
        # Grades
        grades = Grade.query.all()
        print_table_contents("Grades", grades)
        
        # Attendance
        attendance = Attendance.query.all()
        print_table_contents("Attendance", attendance)

if __name__ == '__main__':
    view_database() 