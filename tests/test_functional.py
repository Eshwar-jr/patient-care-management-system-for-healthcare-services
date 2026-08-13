"""
Functional Test Suite for IPCMS
Tests Patient Registration, Staff/Patient Login, Appointment Scheduling,
Consultation Recording, Prescription Issuance, and Reports & File Exports.
"""

import sys
import unittest
from datetime import date, time, timedelta

sys.path.append(".")

from app import app
from extensions import db
from models import User, Patient, Appointment, Consultation, Prescription, Bill, LabReport
from werkzeug.security import generate_password_hash

class FunctionalTestSuite(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        # Ensure test admin and doctor exist with known credentials
        self.admin = User.query.filter(User.role.ilike("admin")).first()
        if self.admin:
            self.admin.password = generate_password_hash("testpass123")
            db.session.commit()

        self.doctor = User.query.filter(User.role.ilike("doctor")).first()
        if self.doctor:
            self.doctor.password = generate_password_hash("testpass123")
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

    def test_1_user_login(self):
        """Test authentication and dashboard redirects for admin and doctor roles."""
        if self.admin:
            res = self.login(self.admin.email, "testpass123", "admin")
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Unread Alerts", res.data)
            self.assertIn(b"Disease Distribution", res.data)
            self.assertIn(b"Laboratory Test Statistics", res.data)

        if self.doctor:
            res = self.login(self.doctor.email, "testpass123", "doctor")
            self.assertEqual(res.status_code, 200)

    def test_2_patient_registration(self):
        """Test patient creation via backend patient/add route."""
        self.login(self.admin.email, "testpass123", "admin")

        from datetime import datetime
        unique_aadhaar = f"{datetime.now().strftime('%m%d%H%M%S%f')[:12]}"
        res = self.client.post(
            "/patient/add",
            data={
                "full_name": "Test Functional Patient",
                "age": 30,
                "gender": "Male",
                "phone": "9876543210",
                "address": "123 Test Street",
                "blood_group": "O+",
                "disease": "Hypertension",
                "email": "func_patient@example.com",
                "aadhaar": unique_aadhaar
            },
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)

        # Verify patient exists in DB
        patient = Patient.query.filter_by(aadhaar=unique_aadhaar).first()
        self.assertIsNotNone(patient)
        self.assertEqual(patient.full_name, "Test Functional Patient")

    def test_3_appointment_scheduling(self):
        """Test booking an appointment for a patient."""
        self.login(self.admin.email, "testpass123", "admin")

        patient = Patient.query.first()
        self.assertIsNotNone(patient)

        res = self.client.post(
            "/appointments/add",
            data={
                "patient": patient.id,
                "doctor_name": self.doctor.full_name if self.doctor else "Dr. Dev",
                "appointment_date": (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "appointment_time": "10:30",
                "reason": "Routine Checkup"
            },
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)

        appt = Appointment.query.filter_by(patient_id=patient.id, reason="Routine Checkup").first()
        self.assertIsNotNone(appt)

    def test_4_consultation_recording_and_auto_completion(self):
        """Test recording a consultation and verifying appointment auto-completion."""
        self.login(self.doctor.email, "testpass123", "doctor")

        patient = Patient.query.first()
        appt = Appointment(
            patient_id=patient.id,
            doctor_name=self.doctor.full_name if self.doctor else "Dr. Dev",
            appointment_date=date.today(),
            appointment_time=time(14, 0),
            reason="Fever & Cough",
            status="Scheduled"
        )
        db.session.add(appt)
        db.session.commit()

        res = self.client.post(
            f"/consultation/add?patient_id={patient.id}&appointment_id={appt.id}",
            data={
                "patient": patient.id,
                "consultation_date": date.today().strftime("%Y-%m-%d"),
                "symptoms": "High fever, chills, sore throat",
                "diagnosis": "Viral Influenza",
                "notes": "Prescribed rest and fluids",
                "fee": 500.00
            },
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)

        # Verify consultation created
        consultation = Consultation.query.filter_by(patient_id=patient.id, diagnosis="Viral Influenza").first()
        self.assertIsNotNone(consultation)

        # Verify appointment updated to Completed
        updated_appt = Appointment.query.get(appt.id)
        self.assertEqual(updated_appt.status, "Completed")

    def test_5_prescription_creation(self):
        """Test writing a prescription for a patient."""
        self.login(self.doctor.email, "testpass123", "doctor")

        patient = Patient.query.first()
        res = self.client.post(
            "/prescription/add",
            data={
                "patient": patient.id,
                "medication_name": "Paracetamol 500mg",
                "dosage": "1 tablet",
                "frequency": "Thrice daily",
                "duration": "5 days",
                "date_prescribed": date.today().strftime("%Y-%m-%d"),
                "instructions": "Take after meals"
            },
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)

        rx = Prescription.query.filter_by(patient_id=patient.id, medication_name="Paracetamol 500mg").first()
        self.assertIsNotNone(rx)

    def test_6_reports_and_exports(self):
        """Test administrative reporting dashboard rendering and PDF/CSV/Excel exports."""
        self.login(self.admin.email, "testpass123", "admin")

        # View reporting dashboard
        res = self.client.get("/admin/reports")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Administrative Reporting", res.data)

        # Test PDF Export
        pdf_res = self.client.get("/admin/reports/export/patients/pdf")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.mimetype, "application/pdf")

        # Test CSV Export
        csv_res = self.client.get("/admin/reports/export/patients/csv")
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.mimetype, "text/csv")

        # Test Excel Export
        excel_res = self.client.get("/admin/reports/export/patients/excel")
        self.assertEqual(excel_res.status_code, 200)
        self.assertEqual(excel_res.mimetype, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    unittest.main()
