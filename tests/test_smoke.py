"""
Production Deployment Smoke Test Suite (Day 7)
Verifies application initialization, database health, route protections,
API authentication requirements, RBAC access, and reporting availability.
"""

import sys
import unittest
from werkzeug.security import generate_password_hash

sys.path.append(".")

from app import app
from extensions import db
from models import User

class SmokeTestSuite(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

        # Admin user
        self.admin = User.query.filter(User.role.ilike("admin")).first()
        if self.admin:
            self.admin.password = generate_password_hash("testpass123")
            db.session.commit()

        # Patient user
        self.patient_user = User.query.filter(User.role.ilike("patient")).first()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def login(self, email, password, role):
        self.client.get("/logout")
        return self.client.post(
            f"/login/{role}",
            data={"email": email, "password": password},
            follow_redirects=True
        )

    def test_1_health_check_endpoint(self):
        """Verify /health returns HTTP 200 with status healthy and database connected."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("database"), "connected")

    def test_2_database_connectivity(self):
        """Verify direct SQLAlchemy database query execution works."""
        result = db.session.execute(db.select(1)).scalar()
        self.assertEqual(result, 1)

    def test_3_login_page_loads(self):
        """Verify login portal page loads with HTTP 200."""
        res = self.client.get("/login/admin")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Login", res.data)

    def test_4_admin_dashboard_protected(self):
        """Verify unauthenticated request to /admin/dashboard is blocked (redirects to login/role)."""
        self.client.get("/logout")
        res = self.client.get("/admin/dashboard")
        self.assertIn(res.status_code, [302, 401])

    def test_5_api_endpoint_requires_authentication(self):
        """Verify unauthenticated request to REST API /api/patients is blocked."""
        self.client.get("/logout")
        res = self.client.get("/api/patients")
        self.assertIn(res.status_code, [302, 401])

    def test_6_reports_dashboard_accessible_to_admin(self):
        """Verify reports dashboard is accessible to authorized Admin user."""
        if self.admin:
            self.login(self.admin.email, "testpass123", "admin")
            res = self.client.get("/admin/reports")
            self.assertEqual(res.status_code, 200)

    def test_7_feedback_page_accessible_by_role(self):
        """Verify /feedback page is accessible according to RBAC."""
        if self.admin:
            self.login(self.admin.email, "testpass123", "admin")
            res = self.client.get("/feedback")
            self.assertEqual(res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
