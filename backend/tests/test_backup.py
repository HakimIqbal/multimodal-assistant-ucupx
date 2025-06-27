import pytest
from unittest.mock import patch
from backend.backup import backup_database

def test_backup_database_success(monkeypatch):
    class DummyResult:
        returncode = 0
        stderr = ''
    monkeypatch.setenv('SUPABASE_URL', 'https://dummy.supabase.co')
    monkeypatch.setenv('SUPABASE_KEY', 'dummykey')
    with patch('subprocess.run', return_value=DummyResult()):
        assert backup_database() is True

def test_backup_database_fail(monkeypatch):
    class DummyResult:
        returncode = 1
        stderr = 'error'
    monkeypatch.setenv('SUPABASE_URL', 'https://dummy.supabase.co')
    monkeypatch.setenv('SUPABASE_KEY', 'dummykey')
    with patch('subprocess.run', return_value=DummyResult()):
        assert backup_database() is False 