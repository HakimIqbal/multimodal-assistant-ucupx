import subprocess
import os
from datetime import datetime

def backup_database():
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sql')
    db_url = os.getenv('SUPABASE_URL')
    db_key = os.getenv('SUPABASE_KEY')
    if not db_url or not db_key:
        print('[Backup] Missing SUPABASE_URL or SUPABASE_KEY')
        return False
    host = db_url.replace('https://', '').replace('.supabase.co', '.supabase.co')
    cmd = [
        'pg_dump',
        '-h', host,
        '-U', 'postgres',
        '-d', 'postgres',
        '-f', backup_file
    ]
    env = os.environ.copy()
    env['PGPASSWORD'] = db_key
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0:
            print(f'[Backup] Database backup saved to {backup_file}')
            return True
        else:
            print(f'[Backup] Backup failed: {result.stderr}')
            return False
    except Exception as e:
        print(f'[Backup] Exception: {e}')
        return False

if __name__ == "__main__":
    backup_database() 