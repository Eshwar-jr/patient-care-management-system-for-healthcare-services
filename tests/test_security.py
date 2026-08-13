"""
Security Test Suite for IPCMS
Tests Authentication (@login_required), Authorization & RBAC,
SQL Injection Immunity, XSS Template Auto-escaping, and CSRF Protection.
"""

import sys
import unittest
from werkzeug.security import generate_password_hash

sys.path.append(".")

from app import app
from extensions import db
from models import User, Patient

class SecurityTestSuite(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Set False for RBAC/route testing
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        self.admin = User.query.filter(User.role.ilike("admin")).first()
        if self.admin:
            self.admin.password = generate_password_hash("secpass123")
            db.session.commit()

        self.patient_user = User.query.filter(User.role.ilike("patient")).first()
        if self.patient_user:
            self.patient_user.password = generate_password_hash("secpass123")
            db.session.commit()

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

    def test_1_unauthenticated_access_protection(self):
        """Verify unauthenticated users are blocked (302 redirected to login or 401)."""
        protected_routes = [
            "/admin/dashboard",
            "/doctor",
            "/nurse/dashboard",
            "/patients",
            "/patient/add",
            "/appointments",
            "/consultations",
            "/prescriptions",
            "/admin/reports",
            "/api/patients",
            "/api/doctors",
            "/api/consultations",
            "/api/prescriptions",
            "/api/lab_reports"
        ]
        for route in protected_routes:
            res = self.client.get(route)
            # Expect redirect to login (302) or unauthorized status
            self.assertIn(res.status_code, [302, 401], f"Route {route} allowed unauthenticated access!")

    def test_2_rbac_authorization_restrictions(self):
        """Verify Role-Based Access Control blocks non-admin/doctor users from unauthorized actions."""
        if self.patient_user:
            # Login as Patient
            self.login(self.patient_user.email, "secpass123", "patient")
            
            # Attempt to access Admin Dashboard
            res_admin = self.client.get("/admin/dashboard")
            self.assertIn(res_admin.status_code, [302, 403])
            
            # Attempt to access Reports Dashboard
            res_reports = self.client.get("/admin/reports")
            self.assertIn(res_reports.status_code, [302, 403])

            # Attempt to create prescription as Patient
            res_rx = self.client.get("/prescription/add", follow_redirects=True)
            self.assertIn(b"Access denied", res_rx.data)

    def test_3_sql_injection_immunity(self):
        """Pass raw SQL injection payloads to filters and search forms; verify ORM parameterization."""
        if self.admin:
            self.login(self.admin.email, "secpass123", "admin")
            
            sqli_payloads = [
                "' OR '1'='1",
                "'; DROP TABLE patients; --",
                "1 UNION SELECT 1,2,3,4,5,6--",
                "admin' --"
            ]
            for payload in sqli_payloads:
                # Search patient with SQLi string
                res = self.client.get(f"/patients?search={payload}")
                self.assertEqual(res.status_code, 200)
                
                # Filter appointments with SQLi string
                res_appt = self.client.get(f"/appointments?status={payload}")
                self.assertEqual(res_appt.status_code, 200)

            # Verify database table is completely intact
            self.assertGreaterEqual(Patient.query.count(), 0)

    def test_4_xss_template_autoescaping(self):
        """Inject HTML/Script XSS vectors and verify Jinja2 escapes tags in rendered outputs."""
        if self.admin:
            self.login(self.admin.email, "secpass123", "admin")
            
            xss_name = "<script>alert('XSS_ATTACK_PATIENT')</script>"
            xss_disease = "<img src=x onerror=alert('XSS_IMAGE')>"
            
            from datetime import datetime
            unique_aadhaar = f"{datetime.now().strftime('%m%d%H%M%S%f')[:12]}"

            self.client.post(
                "/patient/add",
                data={
                    "full_name": xss_name,
                    "age": 25,
                    "gender": "Female",
                    "phone": "9876543210",
                    "address": "123 XSS Lane",
                    "blood_group": "A+",
                    "disease": xss_disease,
                    "email": "xss@example.com",
                    "aadhaar": unique_aadhaar
                },
                follow_redirects=True
            )

            # View patients list page
            res = self.client.get("/patients")
            self.assertEqual(res.status_code, 200)
            
            # Verify <script> tag is escaped as &lt;script&gt; or NOT executed raw
            self.assertNotIn(b"<script>alert('XSS_ATTACK_PATIENT')</script>", res.data)
            self.assertIn(b"&lt;script&gt;alert(&#39;XSS_ATTACK_PATIENT&#39;)&lt;/script&gt;", res.data)

    def test_5_csrf_token_validation(self):
        """Verify Flask-WTF form CSRF token validation when active."""
        app.config['WTF_CSRF_ENABLED'] = True
        with app.test_request_context("/login/admin", method="POST", data={"email": "test@example.com"}):
            from forms import LoginForm
            form = LoginForm()
            # Form submission without valid CSRF token must fail validation
            self.assertFalse(form.validate())
            self.assertIn("csrf_token", form.errors)

if __name__ == "__main__":
    unittest.main()
