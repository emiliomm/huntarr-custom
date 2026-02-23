"""
Requestarr User Management Routes
Handles CRUD for local users, role management, and Plex user import.
Owner-only endpoints (role == 'owner').
"""

from flask import Blueprint, request, jsonify
import logging
import secrets
import string
from src.primary.utils.database import get_database
from src.primary.auth import hash_password, verify_password, get_username_from_session, SESSION_COOKIE_NAME

logger = logging.getLogger(__name__)

requestarr_users_bp = Blueprint('requestarr_users', __name__, url_prefix='/api/requestarr/users')


# ── Helpers ──────────────────────────────────────────────────

def _get_current_user():
    """Get the current authenticated user's requestarr profile (with role).
    Falls back to treating the main Huntarr user as 'owner' if they exist
    in the main users table but haven't been synced to requestarr_users yet.
    """
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    username = get_username_from_session(session_token)
    if not username:
        # Check bypass modes
        try:
            from src.primary.settings_manager import load_settings
            settings = load_settings("general")
            if settings.get("local_access_bypass") or settings.get("proxy_auth_bypass"):
                db = get_database()
                main_user = db.get_first_user()
                if main_user:
                    username = main_user.get('username')
        except Exception:
            pass
    if not username:
        return None
    db = get_database()
    # First try requestarr_users table (has role info)
    req_user = db.get_requestarr_user_by_username(username)
    if req_user:
        return req_user
    # Fallback: main Huntarr user — treat as owner (they are the server admin)
    main_user = db.get_user_by_username(username)
    if main_user:
        main_user['role'] = 'owner'
        return main_user
    return None


def _require_owner():
    """Returns (user_dict, error_response). If error_response is not None, return it."""
    user = _get_current_user()
    if not user:
        return None, (jsonify({'error': 'Not authenticated'}), 401)
    role = user.get('role', 'user')
    if role != 'owner':
        return None, (jsonify({'error': 'Insufficient permissions'}), 403)
    return user, None


def _resolve_category(cat_value):
    """Resolve a category value to its compound appType:instanceName form.
    If the value is 'bundle:X', look up the bundle's primary instance.
    Otherwise return the value as-is (already in appType:instanceName format).
    """
    if not cat_value:
        return ''
    if cat_value.startswith('bundle:'):
        try:
            bundle_id = int(cat_value.split(':', 1)[1])
            db = get_database()
            bundles = db.get_bundles()
            for b in bundles:
                if b['id'] == bundle_id:
                    return f"{b['primary_app_type']}:{b['primary_instance_name']}"
        except Exception:
            pass
        return ''  # Bundle not found — defunct
    return cat_value


def _sanitize_user(user_dict):
    """Strip sensitive fields before sending to frontend."""
    if not user_dict:
        return None
    safe = {
        'id': user_dict.get('id'),
        'username': user_dict.get('username'),
        'email': user_dict.get('email', ''),
        'role': user_dict.get('role', 'user'),
        'permissions': user_dict.get('permissions', '{}'),
        'created_at': user_dict.get('created_at'),
        'plex_user_data': user_dict.get('plex_user_data'),
        'avatar_url': user_dict.get('avatar_url') or None,
        'request_count': user_dict.get('request_count', 0),
        'tv_category': user_dict.get('tv_category', ''),
        'movie_category': user_dict.get('movie_category', ''),
    }
    # Resolve categories to compound appType:instanceName for frontend use
    safe['resolved_movie_category'] = _resolve_category(safe['movie_category'])
    safe['resolved_tv_category'] = _resolve_category(safe['tv_category'])
    # Extract avatar from plex data if not already set in avatar_url column
    if not safe['avatar_url'] and isinstance(safe['plex_user_data'], dict):
        safe['avatar_url'] = safe['plex_user_data'].get('thumb')
    # Parse permissions JSON
    if isinstance(safe['permissions'], str):
        import json
        try:
            safe['permissions'] = json.loads(safe['permissions'])
        except Exception:
            safe['permissions'] = {}
    return safe


# ── Default permissions per role ─────────────────────────────

DEFAULT_PERMISSIONS = {
    'owner': {
        'request_movies': True,
        'request_tv': True,
        'auto_approve': True,
        'auto_approve_movies': True,
        'auto_approve_tv': True,
        'manage_requests': True,
        'manage_users': True,
        'view_requests': True,
        'hide_media_global': True,
    },
    'user': {
        'request_movies': True,
        'request_tv': True,
        'auto_approve': False,
        'auto_approve_movies': False,
        'auto_approve_tv': False,
        'manage_requests': False,
        'manage_users': False,
        'view_requests': False,
        'hide_media_global': False,
    },
}


# ── Routes ───────────────────────────────────────────────────

@requestarr_users_bp.route('/has-non-owner', methods=['GET'])
def has_non_owner_users():
    """Check if non-owner requestarr users exist. Owner only."""
    _, err = _require_owner()
    if err:
        return err
    try:
        db = get_database()
        users = db.get_all_requestarr_users()
        has_non_owner = any(u.get('role') != 'owner' for u in users)
        return jsonify({'has_non_owner': has_non_owner})
    except Exception as e:
        logger.error(f"Error checking non-owner users: {e}")
        return jsonify({'error': 'Failed to check users'}), 500

@requestarr_users_bp.route('', methods=['GET'])
def list_users():
    """List all users (owner only)."""
    _, err = _require_owner()
    if err:
        return err
    try:
        db = get_database()
        users = db.get_all_requestarr_users()
        return jsonify({'users': [_sanitize_user(u) for u in users]})
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({'error': 'Failed to list users'}), 500


@requestarr_users_bp.route('', methods=['POST'])
def create_user():
    """Create a local user (owner only)."""
    current_user, err = _require_owner()
    if err:
        return err
    try:
        data = request.json or {}
        username = (data.get('username') or '').strip()
        email = (data.get('email') or '').strip()
        password = data.get('password', '')
        role = data.get('role', 'user')

        if not username or len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        if not password or len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        if role not in ('user',):
            return jsonify({'error': 'Invalid role. Must be user'}), 400

        # Generate default permissions for the role
        import json
        permissions = json.dumps(DEFAULT_PERMISSIONS.get(role, DEFAULT_PERMISSIONS['user']))

        db = get_database()
        # Check if username already exists in requestarr_users
        existing = db.get_requestarr_user_by_username(username)
        if existing:
            return jsonify({'error': 'Username already exists'}), 409
        # Also check main users table to avoid conflicts
        existing_main = db.get_user_by_username(username)
        if existing_main:
            return jsonify({'error': 'Username already exists'}), 409

        success = db.create_requestarr_user(username, password, email, role, permissions)
        if success:
            logger.info(f"User '{username}' created by '{current_user.get('username')}' with role '{role}'")
            new_user = db.get_requestarr_user_by_username(username)
            # Apply default categories (or explicit ones from request)
            if new_user:
                cat_updates = {}
                if 'movie_category' in data:
                    cat_updates['movie_category'] = data['movie_category']
                else:
                    default_movie = db.get_general_setting('default_movie_category', '')
                    if default_movie:
                        cat_updates['movie_category'] = default_movie
                if 'tv_category' in data:
                    cat_updates['tv_category'] = data['tv_category']
                else:
                    default_tv = db.get_general_setting('default_tv_category', '')
                    if default_tv:
                        cat_updates['tv_category'] = default_tv
                if cat_updates:
                    db.update_requestarr_user(new_user['id'], cat_updates)
                    new_user = db.get_requestarr_user_by_username(username)
            return jsonify({'success': True, 'user': _sanitize_user(new_user)}), 201
        return jsonify({'error': 'Failed to create user'}), 500
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': 'Failed to create user'}), 500


@requestarr_users_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update a user (owner only)."""
    current_user, err = _require_owner()
    if err:
        return err
    try:
        data = request.json or {}
        db = get_database()
        target = db.get_requestarr_user_by_id(user_id)
        if not target:
            return jsonify({'error': 'User not found'}), 404

        # Can't change the owner's role
        if target.get('role') == 'owner' and data.get('role') and data['role'] != 'owner':
            return jsonify({'error': 'Cannot change the owner role'}), 403

        updates = {}
        if 'username' in data and data['username'].strip():
            updates['username'] = data['username'].strip()
        if 'email' in data:
            updates['email'] = (data['email'] or '').strip()
        if 'role' in data and data['role'] in ('user',):
            if target.get('role') != 'owner':
                updates['role'] = data['role']
        if 'password' in data and data['password']:
            if len(data['password']) < 8:
                return jsonify({'error': 'Password must be at least 8 characters'}), 400
            updates['password'] = hash_password(data['password'])
        if 'permissions' in data and isinstance(data['permissions'], dict):
            import json
            updates['permissions'] = json.dumps(data['permissions'])
        if 'tv_category' in data:
            updates['tv_category'] = data.get('tv_category', '')
        if 'movie_category' in data:
            updates['movie_category'] = data.get('movie_category', '')

        if updates:
            success = db.update_requestarr_user(user_id, updates)
            if not success:
                return jsonify({'error': 'Failed to update user'}), 500

        updated = db.get_requestarr_user_by_id(user_id)
        return jsonify({'success': True, 'user': _sanitize_user(updated)})
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return jsonify({'error': 'Failed to update user'}), 500


@requestarr_users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user (owner only). Cannot delete owner."""
    current_user, err = _require_owner()
    if err:
        return err
    try:
        db = get_database()
        target = db.get_requestarr_user_by_id(user_id)
        if not target:
            return jsonify({'error': 'User not found'}), 404
        if target.get('role') == 'owner':
            return jsonify({'error': 'Cannot delete the owner account'}), 403
        if target.get('id') == current_user.get('id'):
            return jsonify({'error': 'Cannot delete your own account'}), 403

        success = db.delete_requestarr_user(user_id)
        if success:
            logger.info(f"User '{target.get('username')}' deleted by '{current_user.get('username')}'")
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to delete user'}), 500
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({'error': 'Failed to delete user'}), 500


@requestarr_users_bp.route('/me', methods=['GET'])
def get_current_user_info():
    """Get the current user's info (any authenticated user)."""
    user = _get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    # Also check if they have a requestarr user record
    db = get_database()
    req_user = db.get_requestarr_user_by_username(user.get('username'))
    if req_user:
        return jsonify({'user': _sanitize_user(req_user)})
    # Return basic info from the main users table (owner fallback)
    import json as _json
    avatar_url = None
    plex_data = user.get('plex_user_data')
    if isinstance(plex_data, str):
        try:
            plex_data = _json.loads(plex_data)
        except Exception:
            plex_data = None
    if isinstance(plex_data, dict):
        avatar_url = plex_data.get('thumb')
    return jsonify({'user': {
        'id': user.get('id'),
        'username': user.get('username'),
        'role': user.get('role', 'owner'),
        'permissions': DEFAULT_PERMISSIONS.get('owner', {}),
        'created_at': user.get('created_at'),
        'avatar_url': avatar_url,
    }})


@requestarr_users_bp.route('/permissions-template', methods=['GET'])
def get_permissions_template():
    """Get the default permissions for each role."""
    return jsonify(DEFAULT_PERMISSIONS)


@requestarr_users_bp.route('/generate-password', methods=['GET'])
def generate_password():
    """Generate a random secure password."""
    chars = string.ascii_letters + string.digits + '!@#$%'
    pwd = ''.join(secrets.choice(chars) for _ in range(16))
    return jsonify({'password': pwd})


# ── Plex Import ──────────────────────────────────────────────

def _fetch_plex_users(plex_token):
    """Fetch all Plex users with server/library access using the XML users API.
    Returns a list of dicts with id, username, email, thumb.
    Falls back to the v2 friends endpoint if the XML endpoint fails.
    """
    import requests as req
    import xml.etree.ElementTree as ET

    users = {}

    # Primary: XML endpoint returns all users who have access to your server
    try:
        resp = req.get(
            'https://plex.tv/api/users',
            headers={'X-Plex-Token': plex_token, 'Accept': 'application/xml'},
            timeout=15,
        )
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for user_el in root.findall('User'):
                uid = int(user_el.get('id', 0))
                if uid == 0:
                    continue
                users[uid] = {
                    'id': uid,
                    'username': user_el.get('username') or user_el.get('title', ''),
                    'email': user_el.get('email', ''),
                    'thumb': user_el.get('thumb', ''),
                }
    except Exception as e:
        logger.warning(f"Plex XML users endpoint failed, falling back to v2/friends: {e}")

    # Fallback / supplement: v2 friends endpoint (JSON, may have extra data)
    try:
        resp = req.get(
            'https://plex.tv/api/v2/friends',
            headers={'X-Plex-Token': plex_token, 'Accept': 'application/json'},
            timeout=15,
        )
        if resp.status_code == 200:
            for f in resp.json():
                uid = f.get('id')
                if not uid:
                    continue
                if uid not in users:
                    users[uid] = {
                        'id': uid,
                        'username': f.get('username') or f.get('title', ''),
                        'email': f.get('email', ''),
                        'thumb': f.get('thumb', ''),
                    }
                else:
                    # Supplement missing fields from friends data
                    if not users[uid]['thumb'] and f.get('thumb'):
                        users[uid]['thumb'] = f['thumb']
                    if not users[uid]['email'] and f.get('email'):
                        users[uid]['email'] = f['email']
    except Exception as e:
        logger.warning(f"Plex v2/friends endpoint failed: {e}")

    if not users:
        raise RuntimeError("Could not fetch Plex users from any endpoint")

    return sorted(users.values(), key=lambda u: (u.get('username') or '').lower())


@requestarr_users_bp.route('/plex/friends', methods=['GET'])
def get_plex_friends():
    """Get Plex users with server access for import (owner only).
    Filters out users that are already imported.
    """
    _, err = _require_owner()
    if err:
        return err
    try:
        db = get_database()
        owner = db.get_first_user()
        if not owner or not owner.get('plex_token'):
            return jsonify({'error': 'No Plex account linked. Link your Plex account in User settings first.'}), 400

        plex_users = _fetch_plex_users(owner['plex_token'])

        # Get existing usernames to mark already-imported users
        existing_users = db.get_all_requestarr_users()
        existing_names = {u.get('username', '').lower() for u in existing_users}

        result = []
        for u in plex_users:
            result.append({
                'id': u['id'],
                'username': u['username'],
                'email': u['email'],
                'thumb': u['thumb'],
                'already_imported': u['username'].lower() in existing_names,
            })
        return jsonify({'friends': result})
    except Exception as e:
        logger.error(f"Error fetching Plex users: {e}")
        return jsonify({'error': 'Failed to fetch Plex users'}), 500


@requestarr_users_bp.route('/plex/import', methods=['POST'])
def import_plex_users():
    """Import selected Plex users as local users (owner only)."""
    current_user, err = _require_owner()
    if err:
        return err
    try:
        data = request.json or {}
        friend_ids = data.get('friend_ids', [])
        if not friend_ids:
            return jsonify({'error': 'No users selected'}), 400

        db = get_database()
        owner = db.get_first_user()
        if not owner or not owner.get('plex_token'):
            return jsonify({'error': 'No Plex account linked'}), 400

        import json
        plex_users = _fetch_plex_users(owner['plex_token'])
        users_map = {u['id']: u for u in plex_users}

        imported = []
        skipped = []
        for fid in friend_ids:
            plex_user = users_map.get(fid)
            if not plex_user:
                skipped.append({'id': fid, 'reason': 'Not found in Plex users'})
                continue

            username = plex_user['username'] or f'plex_{fid}'
            email = plex_user['email']

            existing = db.get_requestarr_user_by_username(username)
            if existing:
                skipped.append({'id': fid, 'username': username, 'reason': 'Already exists'})
                continue

            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))
            permissions = json.dumps(DEFAULT_PERMISSIONS['user'])
            plex_data = json.dumps({
                'plex_id': plex_user['id'],
                'username': username,
                'email': email,
                'thumb': plex_user['thumb'],
            })

            success = db.create_requestarr_user(
                username=username,
                password=temp_password,
                email=email,
                role='user',
                permissions=permissions,
                plex_user_data=plex_data
            )
            if success:
                # Store avatar URL and apply default categories
                new_user = db.get_requestarr_user_by_username(username)
                if new_user:
                    plex_updates = {}
                    if plex_user['thumb']:
                        plex_updates['avatar_url'] = plex_user['thumb']
                    default_movie = db.get_general_setting('default_movie_category', '')
                    if default_movie:
                        plex_updates['movie_category'] = default_movie
                    default_tv = db.get_general_setting('default_tv_category', '')
                    if default_tv:
                        plex_updates['tv_category'] = default_tv
                    if plex_updates:
                        db.update_requestarr_user(new_user['id'], plex_updates)
                imported.append(username)
            else:
                skipped.append({'id': fid, 'username': username, 'reason': 'Creation failed'})

        logger.info(f"Plex import by '{current_user.get('username')}': {len(imported)} imported, {len(skipped)} skipped")
        return jsonify({'success': True, 'imported': imported, 'skipped': skipped})
    except Exception as e:
        logger.error(f"Error importing Plex users: {e}")
        return jsonify({'error': 'Failed to import Plex users'}), 500

# ── Default Categories ───────────────────────────────────────

@requestarr_users_bp.route('/default-categories', methods=['GET'])
def get_default_categories():
    """Get default movie/tv categories for new users."""
    _, err = _require_owner()
    if err:
        return err
    try:
        db = get_database()
        return jsonify({
            'default_movie_category': db.get_general_setting('default_movie_category', ''),
            'default_tv_category': db.get_general_setting('default_tv_category', ''),
        })
    except Exception as e:
        logger.error(f"Error getting default categories: {e}")
        return jsonify({'error': 'Failed to get default categories'}), 500


@requestarr_users_bp.route('/default-categories', methods=['PUT'])
def set_default_categories():
    """Set default movie/tv categories for new users."""
    _, err = _require_owner()
    if err:
        return err
    try:
        data = request.json or {}
        db = get_database()
        if 'default_movie_category' in data:
            db.set_general_setting('default_movie_category', data['default_movie_category'])
        if 'default_tv_category' in data:
            db.set_general_setting('default_tv_category', data['default_tv_category'])
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error setting default categories: {e}")
        return jsonify({'error': 'Failed to set default categories'}), 500
