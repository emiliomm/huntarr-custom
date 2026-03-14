"""Auto-extracted database mixin — see db_mixins/__init__.py"""
import json
import sqlite3
import time
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ExtrasMixin:
    """Notifications, indexer hunt, hunt history, setup progress."""

    def _parse_notification_row(self, d: dict) -> dict:
        """Parse a notification connection row from the database."""
        for key in ('settings', 'triggers'):
            if isinstance(d.get(key), str):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    d[key] = {}
        d['enabled'] = bool(d.get('enabled', 1))
        d['include_app_name'] = bool(d.get('include_app_name', 1))
        d['include_instance_name'] = bool(d.get('include_instance_name', 1))
        d.setdefault('app_scope', 'all')
        d.setdefault('instance_scope', 'all')
        d.setdefault('category', 'instance')
        return d

    def get_notification_connections(self) -> List[Dict[str, Any]]:
        """Return all notification connections."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM notification_connections ORDER BY app_scope, id'
            ).fetchall()
            return [self._parse_notification_row(dict(row)) for row in rows]

    def get_notification_connection(self, conn_id: int) -> Optional[Dict[str, Any]]:
        """Return a single notification connection by ID."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM notification_connections WHERE id = ?', (conn_id,)
            ).fetchone()
            if not row:
                return None
            return self._parse_notification_row(dict(row))

    def save_notification_connection(self, data: Dict[str, Any]) -> int:
        """Create or update a notification connection. Returns the connection ID."""
        conn_id = data.get('id')
        name = data.get('name', 'Unnamed')
        provider = data.get('provider', '')
        enabled = 1 if data.get('enabled', True) else 0
        settings_json = json.dumps(data.get('settings', {}))
        triggers_json = json.dumps(data.get('triggers', {}))
        include_app = 1 if data.get('include_app_name', True) else 0
        include_inst = 1 if data.get('include_instance_name', True) else 0
        app_scope = data.get('app_scope', 'all')
        instance_scope = data.get('instance_scope', 'all')
        category = data.get('category', 'instance')

        with self.get_connection() as conn:
            if conn_id:
                conn.execute('''
                    UPDATE notification_connections
                    SET name = ?, provider = ?, enabled = ?, settings = ?,
                        triggers = ?, include_app_name = ?, include_instance_name = ?,
                        app_scope = ?, instance_scope = ?, category = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (name, provider, enabled, settings_json, triggers_json,
                      include_app, include_inst, app_scope, instance_scope, category, conn_id))
                conn.commit()
                return conn_id
            else:
                cursor = conn.execute('''
                    INSERT INTO notification_connections
                    (name, provider, enabled, settings, triggers, include_app_name,
                     include_instance_name, app_scope, instance_scope, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, provider, enabled, settings_json, triggers_json,
                      include_app, include_inst, app_scope, instance_scope, category))
                conn.commit()
                return cursor.lastrowid

    def delete_notification_connection(self, conn_id: int) -> bool:
        """Delete a notification connection by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'DELETE FROM notification_connections WHERE id = ?', (conn_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    # ── User Notification Connections ──────────────────────────────────────

    def _parse_user_notification_row(self, d: dict) -> dict:
        """Parse a user notification connection row."""
        for key in ('settings', 'triggers'):
            if isinstance(d.get(key), str):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    d[key] = {}
        d['enabled'] = bool(d.get('enabled', 1))
        return d

    def get_user_notification_connections(self, username: str) -> List[Dict[str, Any]]:
        """Return all notification connections for a user."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM user_notification_connections WHERE username = ? ORDER BY id',
                (username,)
            ).fetchall()
            return [self._parse_user_notification_row(dict(row)) for row in rows]

    def get_user_notification_connection(self, conn_id: int) -> Optional[Dict[str, Any]]:
        """Return a single user notification connection by ID."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM user_notification_connections WHERE id = ?', (conn_id,)
            ).fetchone()
            if not row:
                return None
            return self._parse_user_notification_row(dict(row))

    def save_user_notification_connection(self, username: str, data: Dict[str, Any]) -> int:
        """Create or update a user notification connection. Returns the connection ID."""
        conn_id = data.get('id')
        name = data.get('name', 'Unnamed')
        provider = data.get('provider', '')
        enabled = 1 if data.get('enabled', True) else 0
        settings_json = json.dumps(data.get('settings', {}))
        triggers_json = json.dumps(data.get('triggers', {}))

        with self.get_connection() as conn:
            if conn_id:
                conn.execute('''
                    UPDATE user_notification_connections
                    SET name = ?, provider = ?, enabled = ?, settings = ?,
                        triggers = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND username = ?
                ''', (name, provider, enabled, settings_json, triggers_json, conn_id, username))
                conn.commit()
                return conn_id
            else:
                cursor = conn.execute('''
                    INSERT INTO user_notification_connections
                    (username, name, provider, enabled, settings, triggers)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (username, name, provider, enabled, settings_json, triggers_json))
                conn.commit()
                return cursor.lastrowid

    def delete_user_notification_connection(self, username: str, conn_id: int) -> bool:
        """Delete a user notification connection by ID (scoped to username)."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'DELETE FROM user_notification_connections WHERE id = ? AND username = ?',
                (conn_id, username)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_all_user_notification_connections(self) -> List[Dict[str, Any]]:
        """Return all user notification connections (for dispatch across all users)."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM user_notification_connections WHERE enabled = 1 ORDER BY username, id'
            ).fetchall()
            return [self._parse_user_notification_row(dict(row)) for row in rows]

