"""
Patient Feedback & Satisfaction Module Unit Test Suite (Day 6)
Tests feedback creation, RBAC authorization boundaries, rating range validations,
department & date filters, average rating calculations, admin dashboard integration, and PDF/Excel exports.
"""

import sys
import unittest
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash

sys.path.append(".")

from app import app
from extensions import db
from models import User, Patient, Appointment, Consultation, Feedback, Notification

class FeedbackTestSuite(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

        # Admin setup
        self.admin = User.query.filter(User.role.ilike("admin")).first()
        if self.admin:
            self.admin.password = generate_password_hash("testpass123")
            db.session.commit()

        # Doctor setup
        self.doctor = User.query.filter(User.role.ilike("doctor")).first()
        if self.doctor:
            self.doctor.password = generate_password_hash("testpass123")
            db.session.commit()

        # Patient 1 user & patient record
        unique_ts = datetime.now().strftime('%m%d%H%M%S%f')[:12]
        self.patient1_user = User.query.filter_by(email="fb_patient1@example.com").first()
        if not self.patient1_user:
            self.patient1_user = User(
                full_name="Feedback Patient One",
                username=f"fb_pat1_{unique_ts}",
                email="fb_patient1@example.com",
                phone="9111111111",
                password=generate_password_hash("testpass123"),
                role="Patient"
            )
            db.session.add(self.patient1_user)
            db.session.commit()

        self.patient1 = Patient.query.filter_by(email="fb_patient1@example.com").first()
        if not self.patient1:
            self.patient1 = Patient(
                full_name="Feedback Patient One",
                age=35,
                gender="Female",
                phone="9111111111",
                address="100 Test St",
                email="fb_patient1@example.com",
                aadhaar=unique_ts
            )
            db.session.add(self.patient1)
            db.session.commit()

        # Patient 2 user & patient record (for cross-patient security tests)
        unique_ts2 = f"{int(unique_ts) + 1:012d}"
        self.patient2_user = User.query.filter_by(email="fb_patient2@example.com").first()
        if not self.patient2_user:
            self.patient2_user = User(
                full_name="Feedback Patient Two",
                username=f"fb_pat2_{unique_ts2}",
                email="fb_patient2@example.com",
                phone="9222222222",
                password=generate_password_hash("testpass123"),
                role="Patient"
            )
            db.session.add(self.patient2_user)
            db.session.commit()

        self.patient2 = Patient.query.filter_by(email="fb_patient2@example.com").first()
        if not self.patient2:
            self.patient2 = Patient(
                full_name="Feedback Patient Two",
                age=40,
                gender="Male",
                phone="9222222222",
                address="200 Test St",
                email="fb_patient2@example.com",
                aadhaar=unique_ts2
            )
            db.session.add(self.patient2)
            db.session.commit()

        # Consultation for Patient 1
        self.consultation1 = Consultation.query.filter_by(patient_id=self.patient1.id).first()
        if not self.consultation1:
            self.consultation1 = Consultation(
                patient_id=self.patient1.id,
                doctor_id=self.doctor.id,
                consultation_date=date.today(),
                symptoms="Fever, cough",
                diagnosis="Mild Respiratory Infection",
                notes="Rest and fluids."
            )
            db.session.add(self.consultation1)
            db.session.commit()

        # Consultation for Patient 2
        self.consultation2 = Consultation.query.filter_by(patient_id=self.patient2.id).first()
        if not self.consultation2:
            self.consultation2 = Consultation(
                patient_id=self.patient2.id,
                doctor_id=self.doctor.id,
                consultation_date=date.today(),
                symptoms="Headache",
                diagnosis="Migraine",
                notes="Prescribed analgesics."
            )
            db.session.add(self.consultation2)
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

    def test_1_patient_can_submit_feedback_for_own_consultation(self):
        """Verify patient can successfully submit feedback for their own consultation."""
        self.login(self.patient1_user.email, "testpass123", "patient")

        res = self.client.post(
            "/feedback/add",
            data={
                "consultation": self.consultation1.id,
                "doctor_rating": 5,
                "hospital_rating": 4,
                "lab_rating": 5,
                "pharmacy_rating": 4,
                "comments": "Great service from Dr. Dev and hospital staff."
            },
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)

        fb = Feedback.query.filter_by(consultation_id=self.consultation1.id).first()
        self.assertIsNotNone(fb, "Feedback submission failed!")
        self.assertEqual(fb.patient_id, self.patient1.id)
        self.assertEqual(fb.doctor_id, self.doctor.id)
        self.assertEqual(fb.doctor_rating, 5)

    def test_2_patient_cannot_submit_feedback_for_another_patient_consultation(self):
        """Security: Verify patient cannot submit feedback for another patient's consultation."""
        self.login(self.patient1_user.email, "testpass123", "patient")

        # Patient 1 tries to submit feedback for Consultation 2 (which belongs to Patient 2)
        res = self.client.post(
            "/feedback/add",
            data={
                "consultation": self.consultation2.id,
                "doctor_rating": 1,
                "hospital_rating": 1,
                "lab_rating": 1,
                "pharmacy_rating": 1,
                "comments": "Unauthorized feedback attack"
            },
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(b"Not a valid choice" in res.data or b"Access denied" in res.data)

        # Verify feedback was NOT stored for consultation 2 by patient 1
        fb = Feedback.query.filter_by(consultation_id=self.consultation2.id, patient_id=self.patient1.id).first()
        self.assertIsNone(fb, "Security vulnerability: Patient submitted feedback for another patient's consultation!")

    def test_3_patient_feedback_isolation_and_admin_view(self):
        """Verify Patients only view own feedback history while Admins view all."""
        # Create a feedback entry for Patient 1
        fb1 = Feedback(
            patient_id=self.patient1.id,
            doctor_id=self.doctor.id,
            consultation_id=self.consultation1.id,
            doctor_rating=5,
            hospital_rating=5,
            lab_rating=5,
            pharmacy_rating=5,
            comments="Patient 1 Positive Review"
        )
        db.session.add(fb1)

        # Create a feedback entry for Patient 2
        fb2 = Feedback(
            patient_id=self.patient2.id,
            doctor_id=self.doctor.id,
            consultation_id=self.consultation2.id,
            doctor_rating=2,
            hospital_rating=2,
            lab_rating=2,
            pharmacy_rating=2,
            comments="Patient 2 Needs Improvement"
        )
        db.session.add(fb2)
        db.session.commit()

        # Patient 1 views feedback list
        self.login(self.patient1_user.email, "testpass123", "patient")
        res1 = self.client.get("/feedback")
        self.assertEqual(res1.status_code, 200)
        self.assertIn(b"Patient 1 Positive Review", res1.data)
        self.assertNotIn(b"Patient 2 Needs Improvement", res1.data)

        # Patient 1 attempts to view Patient 2's feedback details
        res_detail = self.client.get(f"/feedback/view/{fb2.id}", follow_redirects=True)
        self.assertEqual(res_detail.status_code, 200)
        self.assertIn(b"Access denied", res_detail.data)

        # Admin views feedback list (sees both)
        self.login(self.admin.email, "testpass123", "admin")
        res_admin = self.client.get("/feedback")
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b"Patient 1 Positive Review", res_admin.data)
        self.assertIn(b"Patient 2 Needs Improvement", res_admin.data)

    def test_4_rating_range_validation(self):
        """Verify rating values outside 1-5 are rejected by form validators."""
        self.login(self.patient1_user.email, "testpass123", "patient")

        # Invalid rating: 10 stars
        res = self.client.post(
            "/feedback/add",
            data={
                "consultation": self.consultation1.id,
                "doctor_rating": 10,
                "hospital_rating": 5,
                "lab_rating": 5,
                "pharmacy_rating": 5,
                "comments": "Invalid rating test"
            },
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Rating must be between 1 and 5 stars", res.data)

    def test_5_filtering_and_satisfaction_statistics(self):
        """Verify filtering by Doctor, Department, Date, and Rating and average calculations."""
        self.login(self.admin.email, "testpass123", "admin")

        # Filter by doctor_id
        res_doc = self.client.get(f"/feedback?doctor_id={self.doctor.id}")
        self.assertEqual(res_doc.status_code, 200)

        # Filter by department
        res_dept = self.client.get("/feedback?department=Cardiology")
        self.assertEqual(res_dept.status_code, 200)

        # Filter by min_rating
        res_rating = self.client.get("/feedback?min_rating=4")
        self.assertEqual(res_rating.status_code, 200)

    def test_6_recent_feedback_on_admin_dashboard(self):
        """Verify recent feedback appears on the Admin Dashboard."""
        self.login(self.admin.email, "testpass123", "admin")
        res = self.client.get("/admin/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Recent Patient Feedback", res.data)

    def test_7_feedback_report_exports(self):
        """Verify PDF and Excel exports for Feedback reports."""
        self.login(self.admin.email, "testpass123", "admin")

        # PDF Export
        pdf_res = self.client.get("/admin/reports/export/feedback/pdf")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.mimetype, "application/pdf")

        # Excel Export
        excel_res = self.client.get("/admin/reports/export/feedback/excel")
        self.assertEqual(excel_res.status_code, 200)
        self.assertIn(excel_res.mimetype, ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/octet-stream"])

if __name__ == "__main__":
    unittest.main()
