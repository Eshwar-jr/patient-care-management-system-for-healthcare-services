from flask import request, jsonify
from app import app
from extensions import db
from models import Patient, User, Consultation, Prescription, LabReport
from werkzeug.security import generate_password_hash
from datetime import datetime, date
from flask_login import login_required, current_user

# ==================================================
# SERIALIZATION HELPERS
# ==================================================

def serialize_patient(p):
    return {
        "id": p.id,
        "full_name": p.full_name,
        "age": p.age,
        "gender": p.gender,
        "phone": p.phone,
        "address": p.address,
        "blood_group": p.blood_group,
        "disease": p.disease,
        "aadhaar": p.aadhaar,
        "email": p.email
    }

def serialize_doctor(d):
    return {
        "id": d.id,
        "full_name": d.full_name,
        "username": d.username,
        "email": d.email,
        "phone": d.phone,
        "role": d.role,
        "created_at": d.created_at.isoformat() if d.created_at else None
    }

def serialize_consultation(c):
    return {
        "id": c.id,
        "patient_id": c.patient_id,
        "doctor_id": c.doctor_id,
        "consultation_date": c.consultation_date.strftime("%Y-%m-%d") if c.consultation_date else None,
        "symptoms": c.symptoms,
        "diagnosis": c.diagnosis,
        "notes": c.notes,
        "bill_id": c.bill_id
    }

def serialize_prescription(pr):
    return {
        "id": pr.id,
        "patient_id": pr.patient_id,
        "doctor_id": pr.doctor_id,
        "medication_name": pr.medication_name,
        "dosage": pr.dosage,
        "frequency": pr.frequency,
        "duration": pr.duration,
        "instructions": pr.instructions,
        "date_prescribed": pr.date_prescribed.strftime("%Y-%m-%d") if pr.date_prescribed else None
    }

def serialize_lab_report(l):
    return {
        "id": l.id,
        "patient_id": l.patient_id,
        "requested_by_id": l.requested_by_id,
        "performed_by_id": l.performed_by_id,
        "test_name": l.test_name,
        "status": l.status,
        "results": l.results,
        "lab_notes": l.lab_notes,
        "request_date": l.request_date.strftime("%Y-%m-%d") if l.request_date else None,
        "result_date": l.result_date.strftime("%Y-%m-%d") if l.result_date else None,
        "bill_id": l.bill_id
    }

# ==================================================
# 1. PATIENT CRUD API
# ==================================================

@app.route("/api/patients", methods=["GET"])
@login_required
def api_get_patients():
    try:
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if page:
            pagination = Patient.query.paginate(page=page, per_page=per_page, error_out=False)
            return jsonify({
                "items": [serialize_patient(p) for p in pagination.items],
                "total": pagination.total,
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page
            }), 200
        patients = Patient.query.all()
        return jsonify([serialize_patient(p) for p in patients]), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/patients/<int:id>", methods=["GET"])
@login_required
def api_get_patient(id):
    try:
        p = Patient.query.get(id)
        if not p:
            return jsonify({"success": False, "message": "Record not found"}), 404
        return jsonify(serialize_patient(p)), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/patients", methods=["POST"])
@login_required
def api_create_patient():
    try:
        data = request.get_json()
        if not data or "full_name" not in data or not data["full_name"].strip():
            return jsonify({"success": False, "message": "Validation failed: full_name is required"}), 400

        # Unique checks
        if "aadhaar" in data and data["aadhaar"]:
            existing = Patient.query.filter_by(aadhaar=data["aadhaar"]).first()
            if existing:
                return jsonify({"success": False, "message": "Validation failed: Aadhaar number already exists"}), 400

        p = Patient(
            full_name=data["full_name"].strip(),
            age=data.get("age"),
            gender=data.get("gender"),
            phone=data.get("phone"),
            address=data.get("address"),
            blood_group=data.get("blood_group"),
            disease=data.get("disease"),
            aadhaar=data.get("aadhaar"),
            email=data.get("email")
        )
        db.session.add(p)
        db.session.commit()
        return jsonify(serialize_patient(p)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/patients/<int:id>", methods=["PUT"])
@login_required
def api_update_patient(id):
    try:
        p = Patient.query.get(id)
        if not p:
            return jsonify({"success": False, "message": "Record not found"}), 404

        data = request.get_json()
        if not data or "full_name" not in data or not data["full_name"].strip():
            return jsonify({"success": False, "message": "Validation failed: full_name is required"}), 400

        # Unique checks for Aadhaar
        if "aadhaar" in data and data["aadhaar"]:
            existing = Patient.query.filter(Patient.aadhaar == data["aadhaar"], Patient.id != id).first()
            if existing:
                return jsonify({"success": False, "message": "Validation failed: Aadhaar number already exists"}), 400

        p.full_name = data["full_name"].strip()
        p.age = data.get("age")
        p.gender = data.get("gender")
        p.phone = data.get("phone")
        p.address = data.get("address")
        p.blood_group = data.get("blood_group")
        p.disease = data.get("disease")
        p.aadhaar = data.get("aadhaar")
        p.email = data.get("email")
        db.session.commit()
        return jsonify(serialize_patient(p)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/patients/<int:id>", methods=["DELETE"])
@login_required
def api_delete_patient(id):
    try:
        p = Patient.query.get(id)
        if not p:
            return jsonify({"success": False, "message": "Record not found"}), 404
        db.session.delete(p)
        db.session.commit()
        return jsonify({"success": True, "message": "Patient deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

# ==================================================
# 2. DOCTOR CRUD API
# ==================================================

@app.route("/api/doctors", methods=["GET"])
@login_required
def api_get_doctors():
    try:
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if page:
            pagination = User.query.filter_by(role="Doctor").paginate(page=page, per_page=per_page, error_out=False)
            return jsonify({
                "items": [serialize_doctor(d) for d in pagination.items],
                "total": pagination.total,
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page
            }), 200
        doctors = User.query.filter_by(role="Doctor").all()
        return jsonify([serialize_doctor(d) for d in doctors]), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/doctors/<int:id>", methods=["GET"])
@login_required
def api_get_doctor(id):
    try:
        d = User.query.filter_by(id=id, role="Doctor").first()
        if not d:
            return jsonify({"success": False, "message": "Record not found"}), 404
        return jsonify(serialize_doctor(d)), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/doctors", methods=["POST"])
@login_required
def api_create_doctor():
    try:
        data = request.get_json()
        required_fields = ["full_name", "username", "email", "phone", "password"]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"success": False, "message": f"Validation failed: {field} is required"}), 400

        # Unique checks
        if User.query.filter_by(username=data["username"].strip()).first():
            return jsonify({"success": False, "message": "Validation failed: Username already exists"}), 400
        if User.query.filter_by(email=data["email"].strip()).first():
            return jsonify({"success": False, "message": "Validation failed: Email already exists"}), 400

        d = User(
            full_name=data["full_name"].strip(),
            username=data["username"].strip(),
            email=data["email"].strip(),
            phone=data["phone"].strip(),
            password=generate_password_hash(data["password"]),
            role="Doctor"
        )
        db.session.add(d)
        db.session.commit()
        return jsonify(serialize_doctor(d)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/doctors/<int:id>", methods=["PUT"])
@login_required
def api_update_doctor(id):
    try:
        d = User.query.filter_by(id=id, role="Doctor").first()
        if not d:
            return jsonify({"success": False, "message": "Record not found"}), 404

        data = request.get_json()
        required_fields = ["full_name", "username", "email", "phone"]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"success": False, "message": f"Validation failed: {field} is required"}), 400

        # Unique checks
        if User.query.filter(User.username == data["username"].strip(), User.id != id).first():
            return jsonify({"success": False, "message": "Validation failed: Username already exists"}), 400
        if User.query.filter(User.email == data["email"].strip(), User.id != id).first():
            return jsonify({"success": False, "message": "Validation failed: Email already exists"}), 400

        d.full_name = data["full_name"].strip()
        d.username = data["username"].strip()
        d.email = data["email"].strip()
        d.phone = data["phone"].strip()
        if "password" in data and data["password"].strip():
            d.password = generate_password_hash(data["password"])
        db.session.commit()
        return jsonify(serialize_doctor(d)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/doctors/<int:id>", methods=["DELETE"])
@login_required
def api_delete_doctor(id):
    try:
        d = User.query.filter_by(id=id, role="Doctor").first()
        if not d:
            return jsonify({"success": False, "message": "Record not found"}), 404
        db.session.delete(d)
        db.session.commit()
        return jsonify({"success": True, "message": "Doctor deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

# ==================================================
# 3. CONSULTATION CRUD API
# ==================================================

@app.route("/api/consultations", methods=["GET"])
@login_required
def api_get_consultations():
    try:
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if page:
            pagination = Consultation.query.paginate(page=page, per_page=per_page, error_out=False)
            return jsonify({
                "items": [serialize_consultation(c) for c in pagination.items],
                "total": pagination.total,
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page
            }), 200
        consultations = Consultation.query.all()
        return jsonify([serialize_consultation(c) for c in consultations]), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/consultations/<int:id>", methods=["GET"])
@login_required
def api_get_consultation(id):
    try:
        c = Consultation.query.get(id)
        if not c:
            return jsonify({"success": False, "message": "Record not found"}), 404
        return jsonify(serialize_consultation(c)), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/consultations", methods=["POST"])
@login_required
def api_create_consultation():
    try:
        data = request.get_json()
        required_fields = ["patient_id", "doctor_id", "symptoms", "diagnosis"]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"success": False, "message": f"Validation failed: {field} is required"}), 400

        # Verify Patient and Doctor exist
        if not Patient.query.get(data["patient_id"]):
            return jsonify({"success": False, "message": "Validation failed: Patient does not exist"}), 400
        if not User.query.filter_by(id=data["doctor_id"], role="Doctor").first():
            return jsonify({"success": False, "message": "Validation failed: Doctor does not exist"}), 400

        # Parse date
        c_date = date.today()
        if "consultation_date" in data and data["consultation_date"]:
            try:
                c_date = datetime.strptime(data["consultation_date"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"success": False, "message": "Validation failed: consultation_date must be in YYYY-MM-DD format"}), 400

        c = Consultation(
            patient_id=int(data["patient_id"]),
            doctor_id=int(data["doctor_id"]),
            consultation_date=c_date,
            symptoms=data["symptoms"].strip(),
            diagnosis=data["diagnosis"].strip(),
            notes=data.get("notes"),
            bill_id=data.get("bill_id")
        )
        db.session.add(c)
        db.session.commit()
        return jsonify(serialize_consultation(c)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/consultations/<int:id>", methods=["PUT"])
@login_required
def api_update_consultation(id):
    try:
        c = Consultation.query.get(id)
        if not c:
            return jsonify({"success": False, "message": "Record not found"}), 404

        data = request.get_json()
        required_fields = ["patient_id", "doctor_id", "symptoms", "diagnosis"]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"success": False, "message": f"Validation failed: {field} is required"}), 400

        # Verify Patient and Doctor exist
        if not Patient.query.get(data["patient_id"]):
            return jsonify({"success": False, "message": "Validation failed: Patient does not exist"}), 400
        if not User.query.filter_by(id=data["doctor_id"], role="Doctor").first():
            return jsonify({"success": False, "message": "Validation failed: Doctor does not exist"}), 400

        # Parse date
        c_date = date.today()
        if "consultation_date" in data and data["consultation_date"]:
            try:
                c_date = datetime.strptime(data["consultation_date"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"success": False, "message": "Validation failed: consultation_date must be in YYYY-MM-DD format"}), 400

        c.patient_id = int(data["patient_id"])
        c.doctor_id = int(data["doctor_id"])
        c.consultation_date = c_date
        c.symptoms = data["symptoms"].strip()
        c.diagnosis = data["diagnosis"].strip()
        c.notes = data.get("notes")
        c.bill_id = data.get("bill_id")
        db.session.commit()
        return jsonify(serialize_consultation(c)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/consultations/<int:id>", methods=["DELETE"])
@login_required
def api_delete_consultation(id):
    try:
        c = Consultation.query.get(id)
        if not c:
            return jsonify({"success": False, "message": "Record not found"}), 404
        db.session.delete(c)
        db.session.commit()
        return jsonify({"success": True, "message": "Consultation deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

# ==================================================
# 4. PRESCRIPTION CRUD API
# ==================================================

@app.route("/api/prescriptions", methods=["GET"])
@login_required
def api_get_prescriptions():
    try:
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if page:
            pagination = Prescription.query.paginate(page=page, per_page=per_page, error_out=False)
            return jsonify({
                "items": [serialize_prescription(pr) for pr in pagination.items],
                "total": pagination.total,
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page
            }), 200
        prescriptions = Prescription.query.all()
        return jsonify([serialize_prescription(pr) for pr in prescriptions]), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/prescriptions/<int:id>", methods=["GET"])
@login_required
def api_get_prescription(id):
    try:
        pr = Prescription.query.get(id)
        if not pr:
            return jsonify({"success": False, "message": "Record not found"}), 404
        return jsonify(serialize_prescription(pr)), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/prescriptions", methods=["POST"])
@login_required
def api_create_prescription():
    try:
        data = request.get_json()
        required_fields = ["patient_id", "doctor_id", "medication_name", "dosage", "frequency", "duration"]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"success": False, "message": f"Validation failed: {field} is required"}), 400

        # Verify Patient and Doctor exist
        if not Patient.query.get(data["patient_id"]):
            return jsonify({"success": False, "message": "Validation failed: Patient does not exist"}), 400
        if not User.query.filter_by(id=data["doctor_id"], role="Doctor").first():
            return jsonify({"success": False, "message": "Validation failed: Doctor does not exist"}), 400

        # Parse date
        p_date = date.today()
        if "date_prescribed" in data and data["date_prescribed"]:
            try:
                p_date = datetime.strptime(data["date_prescribed"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"success": False, "message": "Validation failed: date_prescribed must be in YYYY-MM-DD format"}), 400

        pr = Prescription(
            patient_id=int(data["patient_id"]),
            doctor_id=int(data["doctor_id"]),
            medication_name=data["medication_name"].strip(),
            dosage=data["dosage"].strip(),
            frequency=data["frequency"].strip(),
            duration=data["duration"].strip(),
            instructions=data.get("instructions"),
            date_prescribed=p_date
        )
        db.session.add(pr)
        db.session.commit()
        return jsonify(serialize_prescription(pr)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/prescriptions/<int:id>", methods=["PUT"])
@login_required
def api_update_prescription(id):
    try:
        pr = Prescription.query.get(id)
        if not pr:
            return jsonify({"success": False, "message": "Record not found"}), 404

        data = request.get_json()
        required_fields = ["patient_id", "doctor_id", "medication_name", "dosage", "frequency", "duration"]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"success": False, "message": f"Validation failed: {field} is required"}), 400

        # Verify Patient and Doctor exist
        if not Patient.query.get(data["patient_id"]):
            return jsonify({"success": False, "message": "Validation failed: Patient does not exist"}), 400
        if not User.query.filter_by(id=data["doctor_id"], role="Doctor").first():
            return jsonify({"success": False, "message": "Validation failed: Doctor does not exist"}), 400

        # Parse date
        p_date = date.today()
        if "date_prescribed" in data and data["date_prescribed"]:
            try:
                p_date = datetime.strptime(data["date_prescribed"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"success": False, "message": "Validation failed: date_prescribed must be in YYYY-MM-DD format"}), 400

        pr.patient_id = int(data["patient_id"])
        pr.doctor_id = int(data["doctor_id"])
        pr.medication_name = data["medication_name"].strip()
        pr.dosage = data["dosage"].strip()
        pr.frequency = data["frequency"].strip()
        pr.duration = data["duration"].strip()
        pr.instructions = data.get("instructions")
        pr.date_prescribed = p_date
        db.session.commit()
        return jsonify(serialize_prescription(pr)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/prescriptions/<int:id>", methods=["DELETE"])
@login_required
def api_delete_prescription(id):
    try:
        pr = Prescription.query.get(id)
        if not pr:
            return jsonify({"success": False, "message": "Record not found"}), 404
        db.session.delete(pr)
        db.session.commit()
        return jsonify({"success": True, "message": "Prescription deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

# ==================================================
# 5. LABORATORY CRUD API
# ==================================================

@app.route("/api/lab_reports", methods=["GET"])
@login_required
def api_get_lab_reports():
    try:
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if page:
            pagination = LabReport.query.paginate(page=page, per_page=per_page, error_out=False)
            return jsonify({
                "items": [serialize_lab_report(l) for l in pagination.items],
                "total": pagination.total,
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page
            }), 200
        reports = LabReport.query.all()
        return jsonify([serialize_lab_report(l) for l in reports]), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/lab_reports/<int:id>", methods=["GET"])
@login_required
def api_get_lab_report(id):
    try:
        l = LabReport.query.get(id)
        if not l:
            return jsonify({"success": False, "message": "Record not found"}), 404
        return jsonify(serialize_lab_report(l)), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/lab_reports", methods=["POST"])
@login_required
def api_create_lab_report():
    try:
        data = request.get_json()
        required_fields = ["patient_id", "requested_by_id", "test_name"]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"success": False, "message": f"Validation failed: {field} is required"}), 400

        # Verify Patient and Users exist
        if not Patient.query.get(data["patient_id"]):
            return jsonify({"success": False, "message": "Validation failed: Patient does not exist"}), 400
        if not User.query.get(data["requested_by_id"]):
            return jsonify({"success": False, "message": "Validation failed: Requesting User does not exist"}), 400
        if "performed_by_id" in data and data["performed_by_id"]:
            if not User.query.get(data["performed_by_id"]):
                return jsonify({"success": False, "message": "Validation failed: Performing User does not exist"}), 400

        # Dates
        req_date = date.today()
        if "request_date" in data and data["request_date"]:
            try:
                req_date = datetime.strptime(data["request_date"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"success": False, "message": "Validation failed: request_date must be in YYYY-MM-DD format"}), 400

        res_date = None
        if "result_date" in data and data["result_date"]:
            try:
                res_date = datetime.strptime(data["result_date"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"success": False, "message": "Validation failed: result_date must be in YYYY-MM-DD format"}), 400

        l = LabReport(
            patient_id=int(data["patient_id"]),
            requested_by_id=int(data["requested_by_id"]),
            performed_by_id=int(data["performed_by_id"]) if data.get("performed_by_id") else None,
            test_name=data["test_name"].strip(),
            status=data.get("status", "Pending").strip(),
            results=data.get("results"),
            lab_notes=data.get("lab_notes"),
            request_date=req_date,
            result_date=res_date,
            bill_id=data.get("bill_id")
        )
        db.session.add(l)
        db.session.commit()
        return jsonify(serialize_lab_report(l)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/lab_reports/<int:id>", methods=["PUT"])
@login_required
def api_update_lab_report(id):
    try:
        l = LabReport.query.get(id)
        if not l:
            return jsonify({"success": False, "message": "Record not found"}), 404

        data = request.get_json()
        required_fields = ["patient_id", "requested_by_id", "test_name"]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"success": False, "message": f"Validation failed: {field} is required"}), 400

        # Verify Patient and Users exist
        if not Patient.query.get(data["patient_id"]):
            return jsonify({"success": False, "message": "Validation failed: Patient does not exist"}), 400
        if not User.query.get(data["requested_by_id"]):
            return jsonify({"success": False, "message": "Validation failed: Requesting User does not exist"}), 400
        if "performed_by_id" in data and data["performed_by_id"]:
            if not User.query.get(data["performed_by_id"]):
                return jsonify({"success": False, "message": "Validation failed: Performing User does not exist"}), 400

        # Dates
        req_date = date.today()
        if "request_date" in data and data["request_date"]:
            try:
                req_date = datetime.strptime(data["request_date"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"success": False, "message": "Validation failed: request_date must be in YYYY-MM-DD format"}), 400

        res_date = None
        if "result_date" in data and data["result_date"]:
            try:
                res_date = datetime.strptime(data["result_date"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"success": False, "message": "Validation failed: result_date must be in YYYY-MM-DD format"}), 400

        l.patient_id = int(data["patient_id"])
        l.requested_by_id = int(data["requested_by_id"])
        l.performed_by_id = int(data["performed_by_id"]) if data.get("performed_by_id") else None
        l.test_name = data["test_name"].strip()
        l.status = data.get("status", "Pending").strip()
        l.results = data.get("results")
        l.lab_notes = data.get("lab_notes")
        l.request_date = req_date
        l.result_date = res_date
        l.bill_id = data.get("bill_id")
        db.session.commit()
        return jsonify(serialize_lab_report(l)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route("/api/lab_reports/<int:id>", methods=["DELETE"])
@login_required
def api_delete_lab_report(id):
    try:
        l = LabReport.query.get(id)
        if not l:
            return jsonify({"success": False, "message": "Record not found"}), 404
        db.session.delete(l)
        db.session.commit()
        return jsonify({"success": True, "message": "Lab report deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
