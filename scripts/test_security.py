import sys
import os
import unittest
from pathlib import Path

# Add project root and src to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / 'src'))

from src.primary.web_server import app
from src.primary.utils.database import get_database

class SecurityRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['APPLICATION_ROOT'] = '/'
        cls.client = app.test_client()
        
        db = get_database()
        
        # Clear setup progress first to be safe
        db.clear_setup_progress()
        
        # Add a dummy user so user_exists() is True
        try:
            with db.get_connection() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
                    ("testuser", "testpass")
                )
                
                # Create a valid session token for tests
                conn.execute(
                    "INSERT INTO sessions (username, token, ip_address) VALUES (?, ?, ?)",
                    ("testuser", "dummy_token_123", "127.0.0.1")
                )
                conn.commit()
        except Exception as e:
            print(f"Error adding dummy user: {e}")
            
        # Invalidate auth cache so the middleware picks up the new user
        from src.primary.auth import invalidate_auth_cache
        invalidate_auth_cache()

    def test_settings_general_unauth(self):
        """GET /api/settings/general without session expects 401"""
        resp = self.client.get('/api/settings/general')
        if resp.status_code == 302 and 'login' in resp.headers.get('Location', ''):
            # Auth middleware redirects to login for UI routes, or returns 401 for API
            pass
        else:
            self.assertEqual(resp.status_code, 401)

    def test_settings_general_post_unauth(self):
        """POST /api/settings/general without session expects 401"""
        resp = self.client.post('/api/settings/general', json={"theme": "dark"})
        self.assertEqual(resp.status_code, 401)

    def test_2fa_setup_unauth(self):
        """POST /api/user/2fa/setup without session expects 401"""
        resp = self.client.post('/api/user/2fa/setup')
        self.assertEqual(resp.status_code, 401)

    def test_plex_unlink_unauth(self):
        """POST /api/auth/plex/unlink without session expects 401"""
        resp = self.client.post('/api/auth/plex/unlink')
        self.assertEqual(resp.status_code, 401)

    def test_path_traversal_backup_delete(self):
        """Directly verify BackupManager rejects path traversal sequences"""
        from src.routes.backup_routes import BackupManager
        bm = BackupManager()
        
        with self.assertRaises(ValueError) as context:
            bm._validate_backup_id("../../../etc")
            
        self.assertTrue("Invalid backup ID" in str(context.exception) or "Path traversal detected" in str(context.exception))

    def test_redact_secrets(self):
        """Verify redact_settings masks api_key values"""
        from src.primary.settings_manager import redact_settings
        
        dummy_settings = {
            "radarr": {
                "instances": [
                    {"name": "Server1", "api_key": "secret12345", "url": "http://x"}
                ]
            },
            "general": {
                "dev_key": "some_key_here",
                "theme": "dark"
            }
        }
        
        redacted = redact_settings(dummy_settings)
        
        self.assertEqual(redacted["radarr"]["instances"][0]["api_key"], "***")
        self.assertEqual(redacted["radarr"]["instances"][0]["url"], "http://x")
        self.assertEqual(redacted["general"]["dev_key"], "***")
        self.assertEqual(redacted["general"]["theme"], "dark")

if __name__ == '__main__':
    unittest.main()
