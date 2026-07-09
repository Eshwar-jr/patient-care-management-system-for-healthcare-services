import os
import sys
from datetime import datetime
import pandas as pd
from app import app
from extensions import db
from models import Patient

def calculate_age(dob_str):
    """Calculates age based on date of birth in format DD-MM-YYYY or YYYY-MM-DD."""
    if pd.isna(dob_str) or not str(dob_str).strip():
        return None
    
    dob_str_clean = str(dob_str).strip()
    
    # Try parsing format DD-MM-YYYY (e.g. 04-06-1955)
    for date_format in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            dob = datetime.strptime(dob_str_clean, date_format)
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        except ValueError:
            continue
            
    return None

def import_patients(csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at '{csv_path}'")
        sys.exit(1)
        
    print(f"Reading CSV file from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Validate required columns
    required_cols = ['first_name', 'last_name']
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Required column '{col}' is missing from the CSV file.")
            sys.exit(1)
            
    imported_count = 0
    skipped_count = 0
    
    print("Connecting to the database and importing records...")
    
    with app.app_context():
        for index, row in df.iterrows():
            row_num = index + 2  # 1-based index + header row
            
            first_name = str(row.get('first_name', '')).strip() if not pd.isna(row.get('first_name')) else ''
            last_name = str(row.get('last_name', '')).strip() if not pd.isna(row.get('last_name')) else ''
            
            # Check if name columns are empty
            if not first_name and not last_name:
                print(f"Row {row_num}: Skipped (first_name and last_name are empty)")
                skipped_count += 1
                continue
                
            full_name = f"{first_name} {last_name}".strip()
            
            # Format and handle phone
            phone_val = row.get('contact_number')
            if pd.isna(phone_val):
                phone = None
            else:
                phone = str(phone_val).strip()
                # Clean scientific notation or float conversion side-effects (e.g., "123456.0")
                if phone.endswith('.0'):
                    phone = phone[:-2]
            
            # Handle address
            addr_val = row.get('address')
            address = str(addr_val).strip() if not pd.isna(addr_val) else None
            
            # Handle gender
            gender_val = row.get('gender')
            gender = str(gender_val).strip() if not pd.isna(gender_val) else None
            
            # Calculate age from DOB
            dob_val = row.get('date_of_birth')
            age = calculate_age(dob_val)
            
            # Truncate strings to prevent MySQL VARCHAR limits overflow
            if full_name:
                full_name = full_name[:100]
            if phone:
                phone = phone[:15]
            if address:
                address = address[:200]
            if gender:
                gender = gender[:20]
                
            # Check if patient already exists in DB with same name and phone
            existing_patient = Patient.query.filter_by(full_name=full_name, phone=phone).first()
            if existing_patient:
                print(f"Row {row_num}: Skipped duplicate patient '{full_name}' with phone '{phone}'")
                skipped_count += 1
                continue
                
            # Create and add the Patient object
            new_patient = Patient(
                full_name=full_name,
                age=age,
                gender=gender,
                phone=phone,
                address=address,
                blood_group=None,
                disease=None
            )
            
            try:
                db.session.add(new_patient)
                db.session.commit()
                imported_count += 1
                print(f"Row {row_num}: Imported '{full_name}' (Age: {age if age is not None else 'N/A'})")
            except Exception as e:
                db.session.rollback()
                print(f"Row {row_num}: Error importing patient '{full_name}': {str(e)}")
                skipped_count += 1
                
    print("\nImport Summary:")
    print(f"Successfully imported: {imported_count} records")
    print(f"Skipped / Duplicate: {skipped_count} records")

if __name__ == "__main__":
    default_csv = r"C:\Users\eshwa\Downloads\patients.csv\patientsss.csv"
    csv_file = sys.argv[1] if len(sys.argv) > 1 else default_csv
    import_patients(csv_file)
