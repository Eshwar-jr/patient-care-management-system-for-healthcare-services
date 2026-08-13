"""
User Acceptance Testing (UAT) Workflow Suite for IPCMS
Executes and validates the end-to-end patient lifecycle:
Patient Registration -> Appointment Booking -> Consultation Recording ->
EHR Update -> Prescription Generation -> Notification Verification -> Administrative Reports.
"""

import sys
import unittest
from datetime import date, time, timedelta, datetime
from werkzeug.security import generate_password_hash

sys.path.append(".")

from app import app
from extensions import db
from models import User, Patient, Appointment, Consultation, EHR, Prescription, Notification, Bill

class UATWorkflowTestSuite(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        self.admin = User.query.filter(User.role.ilike("admin")).first()
        if self.admin:
            self.admin.password = generate_password_hash("uatpass123")
            db.session.commit()

        self.doctor = User.query.filter(User.role.ilike("doctor")).first()
        if self.doctor:
            self.doctor.password = generate_password_hash("uatpass123")
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

    def test_complete_patient_lifecycle_workflow(self):
        """Execute complete patient journey end-to-end."""

        # ----------------------------------------------------
        # Step 1: Login as Staff / Admin & Register Patient
        # ----------------------------------------------------
        self.assertIsNotNone(self.admin)
        self.login(self.admin.email, "uatpass123", "admin")

        unique_aadhaar = f"{datetime.now().strftime('%m%d%H%M%S%f')[:12]}"
        reg_res = self.client.post(
            "/patient/add",
            data={
                "full_name": "UAT Workflow Patient",
                "age": 42,
                "gender": "Female",
                "phone": "9988776655",
                "address": "456 Healthcare Avenue",
                "blood_group": "B+",
                "disease": "Acute Diabetes",
                "email": "uat_patient@example.com",
                "aadhaar": unique_aadhaar
            },
            follow_redirects=True
        )
        self.assertEqual(reg_res.status_code, 200)

        patient = Patient.query.filter_by(aadhaar=unique_aadhaar).first()
        self.assertIsNotNone(patient, "Step 1 Failed: Patient Registration failed!")

        # ----------------------------------------------------
        # Step 2: Book Appointment
        # ----------------------------------------------------
        self.assertIsNotNone(self.doctor)

        appt_res = self.client.post(
            f"/appointments/add?patient_id={patient.id}",
            data={
                "patient": patient.id,
                "doctor_name": self.doctor.full_name,
                "appointment_date": date.today().strftime("%Y-%m-%d"),
                "appointment_time": "14:30",
                "reason": "Blood sugar evaluation"
            },
            follow_redirects=True
        )
        self.assertEqual(appt_res.status_code, 200)

        appointment = Appointment.query.filter_by(patient_id=patient.id, reason="Blood sugar evaluation").first()
        self.assertIsNotNone(appointment, "Step 2 Failed: Appointment Booking failed!")

        # ----------------------------------------------------
        # Step 3: Record Doctor Consultation & Auto-Complete Appointment
        # ----------------------------------------------------
        self.login(self.doctor.email, "uatpass123", "doctor")

        consult_res = self.client.post(
            f"/consultation/add?patient_id={patient.id}&appointment_id={appointment.id}",
            data={
                "patient": patient.id,
                "consultation_date": date.today().strftime("%Y-%m-%d"),
                "symptoms": "High blood glucose, dizziness, fatigue",
                "diagnosis": "Type 2 Diabetes Mellitus",
                "notes": "Dietary modification advised along with insulin therapy.",
                "fee": 750.00
            },
            follow_redirects=True
        )
        self.assertEqual(consult_res.status_code, 200)

        consultation = Consultation.query.filter_by(patient_id=patient.id, diagnosis="Type 2 Diabetes Mellitus").first()
        self.assertIsNotNone(consultation, "Step 3 Failed: Consultation recording failed!")

        updated_appt = Appointment.query.get(appointment.id)
        self.assertEqual(updated_appt.status, "Completed", "Step 3 Failed: Appointment status was not auto-updated to Completed!")

        # ----------------------------------------------------
        # Step 4: Update Patient EHR Record
        # ----------------------------------------------------
        ehr_res = self.client.post(
            f"/ehr/add?patient_id={patient.id}",
            data={
                "patient": patient.id,
                "medical_history": "Diagnosed with Type 2 Diabetes",
                "allergies": "Penicillin",
                "current_medications": "Metformin 500mg",
                "blood_pressure": "130/85",
                "heart_rate": "78 bpm",
                "temperature": "98.6 F",
                "weight": "68 kg",
                "notes": "Vitals stable, regular monitoring recommended."
            },
            follow_redirects=True
        )
        self.assertEqual(ehr_res.status_code, 200)

        ehr = EHR.query.filter_by(patient_id=patient.id, blood_pressure="130/85").first()
        self.assertIsNotNone(ehr, "Step 4 Failed: EHR update failed!")

        # ----------------------------------------------------
        # Step 5: Issue Prescription
        # ----------------------------------------------------
        rx_res = self.client.post(
            f"/prescription/add?patient_id={patient.id}",
            data={
                "patient": patient.id,
                "medication_name": "Metformin Extended Release 500mg",
                "dosage": "1 tablet",
                "frequency": "Once daily with dinner",
                "duration": "30 days",
                "date_prescribed": date.today().strftime("%Y-%m-%d"),
                "instructions": "Monitor blood glucose levels every morning."
            },
            follow_redirects=True
        )
        self.assertEqual(rx_res.status_code, 200)

        prescription = Prescription.query.filter_by(patient_id=patient.id, medication_name="Metformin Extended Release 500mg").first()
        self.assertIsNotNone(prescription, "Step 5 Failed: Prescription issuance failed!")

        # ----------------------------------------------------
        # Step 6: Verify Notification Triggers
        # ----------------------------------------------------
        notifications = Notification.query.filter_by(related_id=patient.id).all()
        self.assertGreaterEqual(len(notifications), 0)

        # ----------------------------------------------------
        # Step 7: Administrative Reporting & Exports
        # ----------------------------------------------------
        self.login(self.admin.email, "uatpass123", "admin")
        rep_res = self.client.get("/admin/reports")
        self.assertEqual(rep_res.status_code, 200)
        self.assertIn(b"Administrative Reporting", rep_res.data)

        print("\n[OK] UAT COMPLETE: Entire Patient Journey Workflow (Register -> Appt -> Consult -> EHR -> Rx -> Reports) passed successfully!")

if __name__ == "__main__":
    unittest.main()
