import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def run_backup():
    db_url = os.getenv("DATABASE_URL", "mysql+pymysql://root:Eshwarnjr10*@localhost/hospital_management_system")
    
    # Parse SQLAlchemy URL format: mysql+pymysql://user:pass@host:port/dbname
    if "://" in db_url:
        scheme, rest = db_url.split("://", 1)
        auth_host_db = rest.split("/")
        dbname = auth_host_db[1] if len(auth_host_db) > 1 else "hospital_management_system"
        user_pass_host = auth_host_db[0]
        
        user_pass, host_port = user_pass_host.split("@") if "@" in user_pass_host else ("root:", "localhost")
        user = user_pass.split(":")[0] if ":" in user_pass else user_pass
        password = user_pass.split(":")[1] if ":" in user_pass else ""
        host = host_port.split(":")[0] if ":" in host_port else host_port
    else:
        user, password, host, dbname = "root", "", "localhost", "hospital_management_system"

    backup_dir = os.path.join(os.path.dirname(__file__), "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"ipcms_backup_{timestamp}.sql")

    env = os.environ.copy()
    if password:
        env["MYSQL_PWD"] = password

    # Search for mysqldump executable
    mysqldump_bin = "mysqldump"
    common_win_paths = [
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
        r"C:\Program Files\MySQL\MySQL Server 8.1\bin\mysqldump.exe",
        r"C:\Program Files\MySQL\MySQL Server 8.2\bin\mysqldump.exe",
        r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe",
        r"C:\Program Files\MySQL\MySQL Workbench 8.0 CE\mysqldump.exe",
        r"C:\xampp\mysql\bin\mysqldump.exe"
    ]
    for p in common_win_paths:
        if os.path.exists(p):
            mysqldump_bin = p
            break

    cmd = [mysqldump_bin, "-h", host, "-u", user, dbname]
    print(f"[*] Creating MySQL Database Backup for '{dbname}' using '{mysqldump_bin}'...")
    
    try:
        with open(backup_file, "w", encoding="utf-8") as f:
            res = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)
        if res.returncode == 0:
            print(f"[SUCCESS] Backup successfully created at: {backup_file}")
            return True, backup_file
        else:
            print(f"[ERROR] mysqldump failed: {res.stderr}")
            return False, res.stderr
    except FileNotFoundError:
        print("[ERROR] mysqldump utility not found in system PATH or common installation directories.")
        print("        To fix: Add MySQL bin directory (e.g. C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin) to system PATH.")
        return False, "mysqldump executable not found"

if __name__ == "__main__":
    run_backup()
