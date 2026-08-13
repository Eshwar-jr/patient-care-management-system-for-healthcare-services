"""
Performance Test Suite for IPCMS
Benchmarks REST API latency, Dashboard caching performance,
Appointment scheduling throughput, and API query pagination.
"""

import sys
import time
import unittest
from werkzeug.security import generate_password_hash

sys.path.append(".")

from app import app
from extensions import db
from models import User, Patient, Appointment, Consultation, Prescription, LabReport
from datetime import date, time as dtime

class PerformanceTestSuite(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        self.admin = User.query.filter(User.role.ilike("admin")).first()
        if self.admin:
            self.admin.password = generate_password_hash("perfpass123")
            db.session.commit()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def login_as_admin(self):
        self.client.get("/logout")
        return self.client.post(
            "/login/admin",
            data={"email": self.admin.email, "password": "perfpass123"},
            follow_redirects=True
        )

    def test_1_rest_api_latency_benchmarks(self):
        """Measure latency (in milliseconds) for REST API endpoints."""
        self.login_as_admin()

        api_endpoints = [
            "/api/patients",
            "/api/doctors",
            "/api/consultations",
            "/api/prescriptions",
            "/api/lab_reports"
        ]

        print("\n--- REST API Latency Benchmarks ---")
        for endpoint in api_endpoints:
            start_time = time.perf_counter()
            res = self.client.get(endpoint)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            self.assertEqual(res.status_code, 200, f"Endpoint {endpoint} failed!")
            print(f"GET {endpoint:<20}: {latency_ms:.2f} ms")
            self.assertLess(latency_ms, 500.0, f"Endpoint {endpoint} exceeded 500ms latency threshold!")

    def test_2_dashboard_caching_performance(self):
        """Compare response latency of uncached vs cached admin dashboard rendering."""
        self.login_as_admin()

        # Pass 1: Force uncached calculation
        t0 = time.perf_counter()
        res1 = self.client.get("/admin/dashboard?nocache=1")
        t_uncached_ms = (time.perf_counter() - t0) * 1000.0
        self.assertEqual(res1.status_code, 200)

        # Pass 2: Serve from in-memory cache
        t1 = time.perf_counter()
        res2 = self.client.get("/admin/dashboard")
        t_cached_ms = (time.perf_counter() - t1) * 1000.0
        self.assertEqual(res2.status_code, 200)

        print("\n--- Admin Dashboard Performance ---")
        print(f"Uncached Load: {t_uncached_ms:.2f} ms")
        print(f"Cached Load  : {t_cached_ms:.2f} ms")
        self.assertLessEqual(t_cached_ms, t_uncached_ms + 10.0, "Cached load should be faster or comparable to uncached!")

    def test_3_appointment_scheduling_efficiency(self):
        """Measure creation efficiency for appointment scheduling."""
        self.login_as_admin()
        patient = Patient.query.first()
        self.assertIsNotNone(patient)

        start_time = time.perf_counter()
        res = self.client.post(
            "/appointments/add",
            data={
                "patient": patient.id,
                "doctor_name": "Dr. Dev",
                "appointment_date": date.today().strftime("%Y-%m-%d"),
                "appointment_time": "11:00",
                "reason": "Performance Benchmark Test"
            },
            follow_redirects=True
        )
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        self.assertEqual(res.status_code, 200)
        print(f"\nAppointment Scheduling Duration: {duration_ms:.2f} ms")
        self.assertLess(duration_ms, 300.0, "Appointment creation exceeded 300ms!")

    def test_4_api_pagination_performance(self):
        """Test API pagination structure and verify page limits."""
        self.login_as_admin()

        # Query page 1 with per_page=5
        res = self.client.get("/api/patients?page=1&per_page=5")
        self.assertEqual(res.status_code, 200)

        data = res.get_json()
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertIn("page", data)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["per_page"], 5)
        self.assertLessEqual(len(data["items"]), 5)
        print(f"\nPaginated API Payload: {len(data['items'])} items (Total: {data['total']})")

if __name__ == "__main__":
    unittest.main()
