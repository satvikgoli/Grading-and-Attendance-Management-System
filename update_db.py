from app import app, db
from models import GradeCategory

def update_database():
    with app.app_context():
        # Create the GradeCategory table
        db.create_all()
        print("Database updated successfully!")

if __name__ == "__main__":
    update_database() 