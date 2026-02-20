import time
import os
import sys
import tempfile

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)

# Mocking TOGETHER_API_KEY because create_app validates it
os.environ["TOGETHER_API_KEY"] = "mock-key"
os.environ["FLASK_ENV"] = "testing"

from app import create_app
from models import db, User, UserSkill, Document
from services.document_service import save_extracted_skills_for_upload

def run_benchmark(num_existing=100, num_new=100):
    # Use a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()

        user = User(email="test@example.com", full_name="Test User")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        user_id = user.id

        # Create a dummy document
        doc = Document(user_id=user_id, doc_type="lebenslauf", file_path="fake.pdf", original_filename="fake.pdf")
        db.session.add(doc)
        db.session.commit()
        doc_id = doc.id

        # Add existing skills
        print(f"Adding {num_existing} existing skills...")
        for i in range(num_existing):
            skill = UserSkill(
                user_id=user_id,
                skill_name=f"Skill {i}",
                skill_category="technical",
                experience_years=1.0
            )
            db.session.add(skill)
        db.session.commit()

        # Prepare skills to save
        extracted_skills = []
        # Some existing (to trigger updates), some new
        for i in range(num_existing // 2, num_existing // 2 + num_new):
            extracted_skills.append({
                "skill_name": f"Skill {i}",
                "skill_category": "technical",
                "experience_years": 2.0
            })

        print(f"Benchmarking save_extracted_skills_for_upload with {len(extracted_skills)} skills...")
        start_time = time.time()
        added_count = save_extracted_skills_for_upload(user_id, extracted_skills, doc_id)
        end_time = time.time()

        duration = end_time - start_time
        print(f"Time taken: {duration:.4f} seconds")
        print(f"Skills added: {added_count}")

        # Cleanup
        db.session.remove()
        db.drop_all()

    os.unlink(db_path)
    return duration

if __name__ == "__main__":
    # Warm up
    run_benchmark(num_existing=10, num_new=10)
    # Actual benchmark
    duration = run_benchmark(num_existing=500, num_new=500)
    print(f"RESULT: {duration}")
