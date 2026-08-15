# Patient Care Management System for Healthcare Services

A comprehensive healthcare management web application built with Python Flask, SQLAlchemy, MySQL, and Bootstrap 5.

---

## 🚀 Deployment Guide

### 1. Prerequisites
* **Python**: v3.10+
* **MySQL Database**: v8.0+ running on `localhost` (default database: `hospital_management_system`)
* **OS**: Windows / Linux / macOS

### 2. Environment Variables Configuration
Copy `.env.example` to `.env` in the project root:
```bash
cp .env.example .env
```
Configure `.env` with your environment values:
```env
SECRET_KEY=your-secure-secret-key
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost/hospital_management_system
FLASK_ENV=production
FLASK_DEBUG=0
HOST=127.0.0.1
PORT=5000
```

### 3. MySQL Database Setup
Ensure MySQL is running and create the database schema:
```sql
CREATE DATABASE hospital_management_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Database tables and performance indexes are automatically verified and initialized upon application startup (`db.create_all()`).

### 4. Development Startup
To run in development mode with auto-reload:
```bash
python app.py
```
App will start on `http://127.0.0.1:5000`.

### 5. Production Startup (Waitress WSGI Server)
To run using the production multi-threaded WSGI server (`Waitress`):
```bash
python run_production.py
```
This binds to `http://127.0.0.1:5000` with `DEBUG = False`.

### 6. Health Check Endpoint
Verify server and database status via HTTP GET:
```bash
curl http://127.0.0.1:5000/health
```
Response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 7. Database Backup & Restore
* **Create Backup**:
  * Python script: `python database/backup_database.py`
  * Windows Batch script: `backup_database.bat`
  Backups are saved as timestamped `.sql` files in `database/backups/`.
* **Restore Backup**:
  ```bash
  mysql -h localhost -u root -p hospital_management_system < database/backups/ipcms_backup_TIMESTAMP.sql
  ```

### 8. Testing Commands
Run the complete automated test suite (30 tests across 6 suites):
```bash
python -m unittest discover tests/
```
Or run individual test suites:
```bash
python -m unittest tests/test_smoke.py
python -m unittest tests/test_feedback.py
python -m unittest tests/test_functional.py
python -m unittest tests/test_security.py
python -m unittest tests/test_performance.py
python -m unittest tests/test_uat_workflow.py
```
## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.