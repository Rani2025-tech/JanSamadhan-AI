import os
import sys
import json
import re
import secrets
from dotenv import load_dotenv

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

from backend.db.database import init_db, ensure_admin, get_user_by_email, create_staff_user

def seed():
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        print("ERROR: ADMIN_PASSWORD environment variable is not set. Refusing to run staff seed.", file=sys.stderr)
        sys.exit(1)

    print("Initializing database tables and ensuring admin exists...")
    init_db()
    ensure_admin()
    print("Admin verified.")

    dept_path = os.path.join(os.path.dirname(__file__), "..", "data", "departments.json")
    if not os.path.exists(dept_path):
        print(f"ERROR: Departments file not found at {dept_path}", file=sys.stderr)
        sys.exit(1)

    with open(dept_path, "r", encoding="utf-8") as f:
        depts_data = json.load(f)

    departments = []
    for item in depts_data:
        dept_name = item.get("department")
        if dept_name and dept_name not in departments:
            departments.append(dept_name)

    demo_pwd_env = os.getenv("DEMO_OFFICIAL_PASSWORD")
    generated_random = False
    if not demo_pwd_env:
        demo_pwd_env = secrets.token_urlsafe(12)
        generated_random = True
        print(f"NOTICE: DEMO_OFFICIAL_PASSWORD not set in environment. Generated one-time password for demo accounts: {demo_pwd_env}")

    print(f"\nSeeding official accounts for {len(departments)} departments...")
    created_count = 0
    existing_count = 0

    for dept in departments:
        # Create a clean slug for email
        slug = re.sub(r'[^a-zA-Z0-9]+', '_', dept.lower()).strip('_')
        email = f"official_{slug}@jansamadhan.local"
        name = f"{dept} Official"

        existing = get_user_by_email(email)
        if existing:
            existing_count += 1
            print(f" - [EXISTS] {email} ({dept})")
        else:
            create_staff_user(
                name=name,
                email=email,
                password=demo_pwd_env,
                department=dept
            )
            created_count += 1
            print(f" - [CREATED] {email} ({dept})")

    print(f"\nDone! Created: {created_count}, Already existed: {existing_count}")
    if generated_random:
        print(f"Remember to save the demo password: {demo_pwd_env}")

if __name__ == "__main__":
    seed()

