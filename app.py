from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime
from models import db, User, Student, Teacher, Attendance, Grade, Class, ClassStudent, Subject, StudentSubject, GradeCategory, init_db
import os
from sqlalchemy import select

# Get absolute path for database file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'GAMS_database.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize database
with app.app_context():
    db.create_all()
    # Only initialize if no users exist
    if not User.query.first():
        init_db(app)  # This will handle subject creation and other initialization

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Please enter both username and password', 'error')
                return redirect(url_for('login'))
            
            user = User.query.filter_by(username=username).first()
            
            if not user:
                flash('Invalid username or password', 'error')
                return redirect(url_for('login'))
            
            if not user.check_password(password):
                flash('Invalid username or password', 'error')
                return redirect(url_for('login'))
            
            # Check if user is admin
            if user.role == 'admin':
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
            
            # For teachers, check approval status
            if user.role == 'teacher':
                teacher = Teacher.query.filter_by(user_id=user.id).first()
                if not teacher or not teacher.is_approved:
                    flash('Your account is pending admin approval. Please wait for approval.', 'warning')
                    return redirect(url_for('login'))
            
            # For students, check approval status
            if user.role == 'student':
                student = Student.query.filter_by(user_id=user.id).first()
                if not student or not student.is_approved:
                    flash('Your account is pending admin approval. Please wait for approval.', 'warning')
                    return redirect(url_for('login'))
            
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash('An error occurred during login. Please try again.', 'error')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return render_template('admin_dashboard.html')
    elif current_user.role == 'teacher':
        return render_template('teacher_dashboard.html', active_page='dashboard')
    else:
        student = Student.query.filter_by(user_id=current_user.id).first()
        return render_template('student_dashboard.html', student=student, user=current_user)

@app.route('/attendance')
@login_required
def attendance():
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student record not found.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get attendance records for each subject
    attendance_by_subject = {}
    
    for subject in student.subjects:
        records = Attendance.query.filter_by(
            student_id=student.id,
            subject_id=subject.id
        ).all()
        
        # Calculate attendance percentage for this subject
        total_classes = len(records)
        present_count = 0
        attendance_percentage = 0
        
        if total_classes > 0:
            present_count = sum(1 for record in records if record.status == 'present')
            attendance_percentage = (present_count / total_classes) * 100
        
        attendance_by_subject[subject.name] = {
            'records': records,
            'percentage': attendance_percentage,
            'total_classes': total_classes,
            'present_count': present_count
        }
    
    return render_template(
        'student_attendance.html',
        student=student,
        user=current_user,
        attendance_by_subject=attendance_by_subject
    )

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            student_id = request.form.get('student_id')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            gender = request.form.get('gender')
            date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d')
            email = request.form.get('email')
            phone_number = request.form.get('phone_number')
            subject_ids = request.form.getlist('subjects')  # Get multiple subjects

            app.logger.info(f"Received registration data: username={username}, email={email}, student_id={student_id}")

            # Validate number of subjects
            if not subject_ids:
                flash('Please select at least one subject', 'error')
                return redirect(url_for('student_register'))
            if len(subject_ids) > 3:
                flash('You can select up to 3 subjects only', 'error')
                return redirect(url_for('student_register'))

            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
                return redirect(url_for('student_register'))

            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'error')
                return redirect(url_for('student_register'))

            # Create user
            user = User(username=username, email=email, role='student')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            app.logger.info(f"Created user with ID: {user.id}")

            # Create student
            student = Student(
                user_id=user.id,
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=date_of_birth,
                email=email,
                phone_number=phone_number
            )
            db.session.add(student)
            db.session.commit()
            app.logger.info(f"Created student with ID: {student.id}")

            # Add selected subjects
            subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all()
            student.subjects.extend(subjects)
            db.session.commit()
            app.logger.info(f"Added {len(subjects)} subjects to student")

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error during student registration: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('student_register'))

    # Get available subjects
    subjects = Subject.query.all()
    return render_template('student_register.html', subjects=subjects)

@app.route('/get_subjects')
def get_subjects():
    # Get all subjects from the Subject model
    subjects = Subject.query.all()
    return jsonify([subject.name for subject in subjects])

@app.route('/teacher/register', methods=['GET', 'POST'])
def teacher_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        subject_name = request.form.get('subject')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('teacher_register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('teacher_register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('teacher_register'))

        # Get subject first
        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            flash('Invalid subject selected', 'error')
            return redirect(url_for('teacher_register'))

        # Create user
        user = User(username=username, email=email, role='teacher')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Create teacher with subject reference
        teacher = Teacher(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            subject_id=subject.id
        )
        db.session.add(teacher)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    # Get available subjects for the form
    subjects = Subject.query.all()
    return render_template('teacher_register.html', subjects=subjects)

@app.route('/teacher/attendance', methods=['GET', 'POST'])
@login_required
def teacher_attendance():
    if not current_user.is_teacher:
        flash('Access denied. Teachers only.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Get teacher record and subject
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if not teacher:
            flash('Teacher record not found.', 'error')
            return redirect(url_for('dashboard'))
        
        # Get the subject name
        subject = Subject.query.get(teacher.subject_id)
        if not subject:
            flash('Subject not found.', 'error')
            return redirect(url_for('dashboard'))
        
        # Get students who have selected this teacher's subject
        students = Student.query.join(StudentSubject).join(Subject).filter(
            Subject.id == teacher.subject_id
        ).all()
        
        if request.method == 'POST':
            try:
                date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
                
                if not date:
                    flash('Please select a date.', 'error')
                    return redirect(url_for('teacher_attendance'))
                
                # Begin a new transaction
                db.session.begin_nested()
                
                # Process attendance for each student
                for student in students:
                    status = request.form.get(f'status_{student.id}')
                    notes = request.form.get(f'notes_{student.id}')
                    
                    # Check if attendance record already exists
                    attendance = Attendance.query.filter_by(
                        student_id=student.id,
                        teacher_id=teacher.id,
                        subject_id=teacher.subject_id,
                        date=date
                    ).first()
                    
                    if attendance:
                        # Update existing record
                        attendance.status = status
                        attendance.notes = notes
                    else:
                        # Create new record
                        attendance = Attendance(
                            student_id=student.id,
                            teacher_id=teacher.id,
                            subject_id=teacher.subject_id,
                            date=date,
                            status=status,
                            notes=notes
                        )
                        db.session.add(attendance)
                
                # Commit the transaction
                db.session.commit()
                flash('Attendance saved successfully.', 'success')
                return redirect(url_for('teacher_attendance'))
            
            except Exception as e:
                db.session.rollback()
                flash('Error saving attendance. Please try again.', 'error')
                app.logger.error(f'Error saving attendance: {str(e)}')
                return redirect(url_for('teacher_attendance'))
        
        return render_template(
            'teacher_attendance.html',
            current_date=datetime.now(),
            students=students,
            teacher=teacher,
            subject=subject
        )
    
    except Exception as e:
        app.logger.error(f'Error in teacher attendance: {str(e)}')
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/teacher/grade_categories', methods=['GET', 'POST'])
@login_required
def teacher_grade_categories():
    print("Accessing grade categories route")  # Debug print
    
    if not current_user.is_teacher:
        flash('Access denied. Teachers only.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Get teacher record
        teacher = db.session.query(Teacher).filter_by(user_id=current_user.id).first()
        if not teacher:
            flash('Teacher record not found.', 'error')
            return redirect(url_for('dashboard'))
        
        # Get subject
        subject = db.session.get(Subject, teacher.subject_id)
        if not subject:
            flash('Subject not found.', 'error')
            return redirect(url_for('dashboard'))
        
        # Handle POST request for creating new category
        if request.method == 'POST':
            category_name = request.form.get('category_name')
            if not category_name:
                flash('Category name is required', 'error')
                return redirect(url_for('teacher_grade_categories'))
            
            try:
                # Create new category
                new_category = GradeCategory(
                    name=category_name,
                    teacher_id=teacher.id,
                    subject_id=teacher.subject_id
                )
                db.session.add(new_category)
                db.session.commit()
                flash('Grade category created successfully!', 'success')
            except Exception as e:
                print(f"Error creating category: {str(e)}")  # Debug print
                db.session.rollback()
                flash('An error occurred while creating the category', 'error')
            
            return redirect(url_for('teacher_grade_categories'))
        
        # Get categories for GET request
        categories = db.session.query(GradeCategory).filter_by(
            teacher_id=teacher.id,
            subject_id=teacher.subject_id
        ).order_by(GradeCategory.created_date.desc()).all()
        
        return render_template('teacher_grade_categories.html',
                             teacher=teacher,
                             subject=subject,
                             categories=categories)
    
    except Exception as e:
        print(f"Error in grade categories: {str(e)}")  # Debug print
        flash('An error occurred while loading grade categories', 'error')
        return redirect(url_for('dashboard'))

@app.route('/teacher/grades/<int:category_id>', methods=['GET', 'POST'])
@login_required
def teacher_grades(category_id):
    if not current_user.is_teacher:
        flash('Access denied. Teachers only.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        teacher = db.session.query(Teacher).filter_by(user_id=current_user.id).first()
        if not teacher:
            flash('Teacher record not found.', 'error')
            return redirect(url_for('dashboard'))
        
        category = db.session.get(GradeCategory, category_id)
        if not category or category.teacher_id != teacher.id:
            flash('Grade category not found.', 'error')
            return redirect(url_for('teacher_grade_categories'))
        
        subject = db.session.get(Subject, teacher.subject_id)
        if not subject:
            flash('Subject not found.', 'error')
            return redirect(url_for('dashboard'))
        
        # Handle POST request for grade submission
        if request.method == 'POST':
            student_id = request.form.get('student_id')
            grade_value = request.form.get('grade')
            
            if not student_id or not grade_value:
                flash('Missing required fields.', 'error')
                return redirect(url_for('teacher_grades', category_id=category_id))
            
            try:
                grade_value = float(grade_value)
                if not (0 <= grade_value <= 100):
                    raise ValueError("Grade must be between 0 and 100")
                
                # Check if grade exists
                grade = Grade.query.filter_by(
                    student_id=student_id,
                    category_id=category_id
                ).first()
                
                if grade:
                    # Update existing grade
                    grade.grade = grade_value
                    grade.date = datetime.utcnow()
                else:
                    # Create new grade
                    grade = Grade(
                        student_id=student_id,
                        teacher_id=teacher.id,
                        subject_id=subject.id,
                        category_id=category_id,
                        grade=grade_value
                    )
                    db.session.add(grade)
                
                db.session.commit()
                flash('Grade saved successfully!', 'success')
                
            except ValueError as e:
                flash(str(e), 'error')
            except Exception as e:
                db.session.rollback()
                flash('Error saving grade. Please try again.', 'error')
                print(f"Error saving grade: {str(e)}")
        
        # Get students enrolled in this subject using the StudentSubject association
        students = Student.query.join(StudentSubject).filter(
            StudentSubject.subject_id == teacher.subject_id
        ).all()
        
        if not students:
            flash('No students are currently enrolled in this subject.', 'info')
        
        # Get grades
        student_grades = {}
        grade_dates = {}
        for student in students:
            grade = Grade.query.filter_by(
                student_id=student.id,
                category_id=category_id
            ).first()
            if grade:
                student_grades[student.id] = grade.grade
                grade_dates[student.id] = grade.date
            else:
                student_grades[student.id] = None
                grade_dates[student.id] = None
        
        return render_template('teacher_grades.html',
                             teacher=teacher,
                             subject=subject,
                             category=category,
                             students=students,
                             student_grades=student_grades,
                             grade_dates=grade_dates)
                             
    except Exception as e:
        print(f"Error in teacher grades: {str(e)}")  # Debug print
        flash('An error occurred while loading the grades page', 'error')
        return redirect(url_for('teacher_grade_categories'))

def get_letter_grade(percentage):
    if percentage is None:
        return None
    if percentage >= 90:
        return 'A'
    elif percentage >= 80:
        return 'B'
    elif percentage >= 70:
        return 'C'
    elif percentage >= 60:
        return 'D'
    else:
        return 'F'

# Add the function to Jinja2 environment
app.jinja_env.globals.update(get_letter_grade=get_letter_grade)

@app.route('/student/grades')
@login_required
def student_grades():
    if not current_user.is_student:
        flash('Access denied. Students only.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            flash('Student record not found.', 'error')
            return redirect(url_for('dashboard'))
        
        # Get grades for all subjects
        grades_by_subject = {}
        total_grades = 0
        graded_subjects = 0
        
        for subject in student.subjects:
            # Get all grade categories for this subject
            categories = GradeCategory.query.filter_by(subject_id=subject.id).all()
            subject_grades = []
            
            for category in categories:
                grade = Grade.query.filter_by(
                    student_id=student.id,
                    subject_id=subject.id,
                    category_id=category.id
                ).first()
                
                if grade:
                    subject_grades.append({
                        'category': category.name,
                        'grade': grade.grade,
                        'date': grade.date
                    })
            
            # Calculate subject average
            if subject_grades:
                subject_average = sum(g['grade'] for g in subject_grades) / len(subject_grades)
                total_grades += subject_average
                graded_subjects += 1
            else:
                subject_average = None
            
            teacher = Teacher.query.filter_by(subject_id=subject.id).first()
            teacher_name = f"{teacher.first_name} {teacher.last_name}" if teacher else "Not Assigned"
            
            grades_by_subject[subject.name] = {
                'grades': subject_grades,
                'average': subject_average,
                'letter_grade': get_letter_grade(subject_average),
                'teacher': teacher_name
            }
        
        # Calculate overall average and letter grade
        overall_average = total_grades / graded_subjects if graded_subjects > 0 else 0
        overall_letter_grade = get_letter_grade(overall_average) if graded_subjects > 0 else None
        
        return render_template('student_grades.html',
                             student=student,
                             grades_by_subject=grades_by_subject,
                             overall_average=overall_average,
                             overall_letter_grade=overall_letter_grade)
    
    except Exception as e:
        print(f"Error loading student grades: {str(e)}")  # Debug print
        flash('An error occurred while loading grades.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/admin/pending_approvals')
@login_required
def pending_approvals():
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get pending teachers and students
    pending_teachers = Teacher.query.filter_by(is_approved=False).all()
    pending_students = Student.query.filter_by(is_approved=False).all()
    
    return render_template('admin_pending_approvals.html',
                         pending_teachers=pending_teachers,
                         pending_students=pending_students)

@app.route('/admin/approve_teacher/<int:teacher_id>', methods=['POST'])
@login_required
def approve_teacher(teacher_id):
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    teacher = Teacher.query.get_or_404(teacher_id)
    teacher.is_approved = True
    db.session.commit()
    flash(f'Teacher {teacher.first_name} {teacher.last_name} has been approved.', 'success')
    return redirect(url_for('pending_approvals'))

@app.route('/admin/approve_student/<int:student_id>', methods=['POST'])
@login_required
def approve_student(student_id):
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    student = Student.query.get_or_404(student_id)
    student.is_approved = True
    db.session.commit()
    flash(f'Student {student.first_name} {student.last_name} has been approved.', 'success')
    return redirect(url_for('pending_approvals'))

@app.route('/admin/decline_student/<int:student_id>', methods=['POST'])
@login_required
def decline_student(student_id):
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    
    # Delete the student and associated user
    db.session.delete(student)
    if user:
        db.session.delete(user)
    db.session.commit()
    
    flash(f'Student {student.first_name} {student.last_name} has been declined and removed.', 'warning')
    return redirect(url_for('pending_approvals'))

@app.route('/admin/decline_teacher/<int:teacher_id>', methods=['POST'])
@login_required
def decline_teacher(teacher_id):
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    teacher = Teacher.query.get_or_404(teacher_id)
    user = User.query.get(teacher.user_id)
    
    # Delete the teacher and associated user
    db.session.delete(teacher)
    if user:
        db.session.delete(user)
    db.session.commit()
    
    flash(f'Teacher {teacher.first_name} {teacher.last_name} has been declined and removed.', 'warning')
    return redirect(url_for('pending_approvals'))

if __name__ == '__main__':
    app.run(debug=True)