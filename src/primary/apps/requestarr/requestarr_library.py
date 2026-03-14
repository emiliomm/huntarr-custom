"""
Requestarr Library Mixin
Library status checks, batch status, availability, and enabled instances.
Extracted from requestarr/__init__.py to reduce file size.
"""

import requests
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class LibraryMixin:
    """Library status checks, batch status, availability, and enabled instances."""

    def get_series_status_from_sonarr(self, tmdb_id: int, instance_name: str) -> Dict[str, Any]:
        """Get series status from Sonarr - missing episodes, available, etc."""
        try:
            already_requested_in_db = self.db.is_already_requested(tmdb_id, 'tv', 'sonarr', instance_name)
            
            # Get Sonarr instance config
            app_config = self.db.get_app_config('sonarr')
            if not app_config or not app_config.get('instances'):
                return {'exists': False, 'previously_requested': already_requested_in_db}
            
            target_instance = None
            for instance in app_config['instances']:
                if instance.get('name') == instance_name:
                    target_instance = instance
                    break
            
            if not target_instance:
                return {'exists': False, 'previously_requested': already_requested_in_db}
            
            # Get series from Sonarr
            sonarr_url = target_instance.get('api_url', '') or target_instance.get('url', '')
            sonarr_api_key = target_instance.get('api_key', '')
            
            if not sonarr_url or not sonarr_api_key:
                return {'exists': False, 'previously_requested': already_requested_in_db}
            
            sonarr_url = sonarr_url.rstrip('/')
            
            # Search for series by TMDB ID
            headers = {'X-Api-Key': sonarr_api_key}
            response = requests.get(
                f"{sonarr_url}/api/v3/series",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get series from Sonarr: {response.status_code}")
                return {'exists': False, 'previously_requested': already_requested_in_db}
            
            series_list = response.json()
            
            logger.info(f"Searching for TMDB ID {tmdb_id} in {len(series_list)} series")
            
            # Find series with matching TMDB ID
            for series in series_list:
                series_tmdb = series.get('tmdbId')
                
                # Only check tmdbId field (tvdbId is TVDB, not TMDB)
                if series_tmdb == tmdb_id:
                    # Series exists in Sonarr
                    statistics = series.get('statistics', {})
                    total_episodes = statistics.get('episodeCount', 0)
                    available_episodes = statistics.get('episodeFileCount', 0)
                    missing_episodes = total_episodes - available_episodes
                    series_id = series.get('id')

                    def _extract_quality_from_episode_file(ef: dict) -> Optional[str]:
                        """Extract quality/resolution from Sonarr episodeFile. Tries multiple JSON paths."""
                        if not ef:
                            return None
                        # Try quality.quality.name, qualityQuality.name, quality.name (Sonarr/Radarr structure)
                        for qkey in ('quality', 'Quality', 'qualityQuality'):
                            q = ef.get(qkey) or {}
                            if not isinstance(q, dict):
                                continue
                            inner = q.get('quality') or q.get('Quality') or {}
                            if isinstance(inner, dict):
                                name = (inner.get('name') or inner.get('Name') or '').strip()
                                if name:
                                    return name
                            name = (q.get('name') or q.get('Name') or '').strip()
                            if name:
                                return name
                        # Fallback: parse from filename (relativePath, path)
                        import os
                        fpath = ef.get('relativePath') or ef.get('path') or ef.get('RelativePath') or ef.get('Path') or ''
                        if fpath:
                            from src.primary.routes.media_hunt.helpers import _extract_quality_from_filename
                            fname = os.path.basename(str(fpath))
                            parsed = _extract_quality_from_filename(fname)
                            if parsed and parsed != '-':
                                return parsed
                        return None

                    # Fetch episode-level details (status, quality) for per-episode display
                    seasons_with_episodes = []
                    try:
                        ep_resp = requests.get(
                            f"{sonarr_url}/api/v3/episode",
                            params={"seriesId": series_id},
                            headers=headers,
                            timeout=15
                        )
                        if ep_resp.status_code == 200:
                            all_episodes = ep_resp.json()
                            # Fetch episode files for quality via GET /api/v3/episodefile?seriesId=X
                            episode_id_to_quality = {}
                            try:
                                ef_resp = requests.get(
                                    f"{sonarr_url}/api/v3/episodefile",
                                    params={"seriesId": series_id},
                                    headers=headers,
                                    timeout=15
                                )
                                if ef_resp.status_code == 200:
                                    episode_files = ef_resp.json()
                                    files_list = episode_files if isinstance(episode_files, list) else ([episode_files] if episode_files else [])
                                    for ef_item in files_list:
                                        q = _extract_quality_from_episode_file(ef_item)
                                        if q:
                                            eids = ef_item.get('episodeIds')
                                            if not eids and ef_item.get('episodeId') is not None:
                                                eids = [ef_item.get('episodeId')]
                                            for eid in (eids or []):
                                                if eid is not None:
                                                    episode_id_to_quality[eid] = q
                            except Exception as ef_err:
                                logger.debug(f"Sonarr episodefile fetch for series {series_id}: {ef_err}")
                            by_season = {}
                            per_episode_fetch_count = 0
                            max_per_episode_fetches = 100  # cap to avoid hammering API on huge series
                            for ep in all_episodes:
                                sn = ep.get('seasonNumber')
                                if sn is None:
                                    continue
                                if sn not in by_season:
                                    by_season[sn] = []
                                ef = ep.get('episodeFile') or {}
                                qname = _extract_quality_from_episode_file(ef)
                                if not qname and ep.get('hasFile') and ep.get('id'):
                                    qname = episode_id_to_quality.get(ep['id'])
                                # Fallback: episode has episodeFile.id but no quality - fetch file directly
                                if not qname and ep.get('hasFile') and ef and per_episode_fetch_count < max_per_episode_fetches:
                                    ef_id = ef.get('id') or ef.get('Id')
                                    if ef_id is not None:
                                        try:
                                            per_episode_fetch_count += 1
                                            efr = requests.get(
                                                f"{sonarr_url}/api/v3/episodefile/{ef_id}",
                                                headers=headers,
                                                timeout=5
                                            )
                                            if efr.status_code == 200:
                                                qname = _extract_quality_from_episode_file(efr.json())
                                        except Exception:
                                            pass
                                by_season[sn].append({
                                    'season_number': sn,
                                    'seasonNumber': sn,
                                    'episode_number': ep.get('episodeNumber'),
                                    'episodeNumber': ep.get('episodeNumber'),
                                    'title': ep.get('title') or ep.get('name') or '',
                                    'name': ep.get('title') or ep.get('name') or '',
                                    'air_date': ep.get('airDate') or '',
                                    'airDate': ep.get('airDate') or '',
                                    'status': 'available' if ep.get('hasFile') else 'missing',
                                    'episodeFile': ef if ep.get('hasFile') else None,
                                    'quality': qname if qname else None,
                                })
                            for sn in sorted(by_season.keys()):
                                eps_sorted = sorted(by_season[sn], key=lambda e: (e.get('episode_number') or 0), reverse=True)
                                seasons_with_episodes.append({
                                    'season_number': sn,
                                    'seasonNumber': sn,
                                    'episodes': eps_sorted,
                                })
                    except Exception as ep_err:
                        logger.warning(f"Sonarr episode fetch for series {series_id} failed (no per-episode status): {ep_err}")
                        seasons_with_episodes = []  # Avoid series.get('seasons') - lacks episode-level status/quality

                    # Determine "previously_requested" status intelligently:
                    # - Only mark as "previously requested" if series was requested but has NO episodes yet
                    # - If there are missing episodes, DON'T mark as previously requested (could be new episodes)
                    # - This allows users to request new episodes that air after their initial request
                    
                    previously_requested = False
                    
                    if already_requested_in_db:
                        # Series was requested through Requestarr
                        if total_episodes > 0 and available_episodes == 0:
                            # No episodes downloaded yet - still waiting on initial request
                            previously_requested = True
                        elif missing_episodes > 0:
                            # Has missing episodes - could be new episodes that aired
                            # Don't mark as previously requested so user can request them
                            previously_requested = False
                        else:
                            # All episodes downloaded or no episodes to download
                            previously_requested = False
                    elif total_episodes > 0 and available_episodes == 0:
                        # Not in Requestarr DB but in Sonarr with no episodes = requested elsewhere
                        previously_requested = True
                    
                    logger.debug(f"Found series in Sonarr: {series.get('title')} - {available_episodes}/{total_episodes} episodes, missing: {missing_episodes}, previously_requested: {previously_requested}")
                    
                    path_val = (series.get('path') or series.get('Path') or series.get('rootFolderPath') or series.get('RootFolderPath') or '').strip()
                    return {
                        'exists': True,
                        'monitored': series.get('monitored', False),
                        'path': path_val,
                        'root_folder_path': path_val,
                        'total_episodes': total_episodes,
                        'available_episodes': available_episodes,
                        'missing_episodes': missing_episodes,
                        'previously_requested': previously_requested,
                        'seasons': seasons_with_episodes,
                    }
            
            logger.info(f"Series with TMDB ID {tmdb_id} not found in Sonarr")
            return {
                'exists': False,
                'previously_requested': already_requested_in_db,
            }
            
        except Exception as e:
            logger.error(f"Error getting series status from Sonarr: {e}")
            return {
                'exists': False,
                'previously_requested': False,
            }

    def trigger_sonarr_season_search(self, tmdb_id: int, instance_name: str, season_number: int) -> Dict[str, Any]:
        """Trigger Sonarr SeasonSearch command for a series/season. Series must exist in Sonarr."""
        try:
            app_config = self.db.get_app_config('sonarr')
            if not app_config or not app_config.get('instances'):
                return {'success': False, 'message': 'No Sonarr instance configured'}
            target = next((i for i in app_config['instances'] if (i.get('name') or '').strip() == instance_name), None)
            if not target:
                return {'success': False, 'message': f'Sonarr instance "{instance_name}" not found'}
            url = (target.get('api_url') or target.get('url') or '').rstrip('/')
            api_key = (target.get('api_key') or '').strip()
            if not url or not api_key:
                return {'success': False, 'message': 'Invalid Sonarr instance configuration'}
            headers = {'X-Api-Key': api_key}
            resp = requests.get(f"{url}/api/v3/series", headers=headers, timeout=10)
            if resp.status_code != 200:
                return {'success': False, 'message': 'Failed to reach Sonarr'}
            for s in resp.json():
                if s.get('tmdbId') == tmdb_id:
                    series_id = s.get('id')
                    if series_id is None:
                        break
                    from src.primary.apps.sonarr.api import search_season
                    cmd_id = search_season(url, api_key, 15, series_id, season_number)
                    if cmd_id:
                        return {'success': True, 'message': 'Season search started'}
                    return {'success': False, 'message': 'Failed to trigger season search'}
            return {'success': False, 'message': 'Series not in Sonarr. Add it first.'}
        except Exception as e:
            logger.error(f"Sonarr season search error: {e}")
            return {'success': False, 'message': str(e) or 'Request failed'}

    def trigger_sonarr_episode_search(self, tmdb_id: int, instance_name: str, season_number: int, episode_number: int) -> Dict[str, Any]:
        """Trigger Sonarr EpisodeSearch command for a specific episode. Series must exist in Sonarr."""
        try:
            app_config = self.db.get_app_config('sonarr')
            if not app_config or not app_config.get('instances'):
                return {'success': False, 'message': 'No Sonarr instance configured'}
            target = next((i for i in app_config['instances'] if (i.get('name') or '').strip() == instance_name), None)
            if not target:
                return {'success': False, 'message': f'Sonarr instance "{instance_name}" not found'}
            url = (target.get('api_url') or target.get('url') or '').rstrip('/')
            api_key = (target.get('api_key') or '').strip()
            if not url or not api_key:
                return {'success': False, 'message': 'Invalid Sonarr instance configuration'}
            headers = {'X-Api-Key': api_key}
            resp = requests.get(f"{url}/api/v3/series", headers=headers, timeout=10)
            if resp.status_code != 200:
                return {'success': False, 'message': 'Failed to reach Sonarr'}
            series_id = None
            for s in resp.json():
                if s.get('tmdbId') == tmdb_id:
                    series_id = s.get('id')
                    break
            if series_id is None:
                return {'success': False, 'message': 'Series not in Sonarr. Add it first.'}
            ep_resp = requests.get(f"{url}/api/v3/episode", params={"seriesId": series_id}, headers=headers, timeout=15)
            if ep_resp.status_code != 200:
                return {'success': False, 'message': 'Failed to fetch episodes'}
            for ep in ep_resp.json():
                if ep.get('seasonNumber') == season_number and ep.get('episodeNumber') == episode_number:
                    ep_id = ep.get('id')
                    if ep_id is not None:
                        from src.primary.apps.sonarr.api import search_episode
                        cmd_id = search_episode(url, api_key, 15, [ep_id])
                        if cmd_id:
                            return {'success': True, 'message': 'Episode search started'}
                        return {'success': False, 'message': 'Failed to trigger episode search'}
                    break
            return {'success': False, 'message': 'Episode not found in Sonarr'}
        except Exception as e:
            logger.error(f"Sonarr episode search error: {e}")
            return {'success': False, 'message': str(e) or 'Request failed'}


    def check_seasons_in_sonarr(self, tmdb_id: int, instance_name: str) -> List[int]:
        """Check which seasons of a TV show are already in Sonarr"""
        status = self.get_series_status_from_sonarr(tmdb_id, instance_name)
        if status.get('exists'):
            seasons = status.get('seasons', [])
            return [s.get('seasonNumber') for s in seasons if s.get('seasonNumber') is not None]
        return []
    
    def get_movie_status_from_radarr(self, tmdb_id: int, instance_name: str) -> Dict[str, Any]:
        """Get movie status from Radarr - in library, previously requested, etc."""
        try:
            already_requested_in_db = self.db.is_already_requested(tmdb_id, 'movie', 'radarr', instance_name)
            
            # Get Radarr instance config
            app_config = self.db.get_app_config('radarr')
            if not app_config or not app_config.get('instances'):
                return {'in_library': False, 'previously_requested': already_requested_in_db}
            
            target_instance = None
            for instance in app_config['instances']:
                if instance.get('name') == instance_name:
                    target_instance = instance
                    break
            
            if not target_instance:
                return {'in_library': False, 'previously_requested': already_requested_in_db}
            
            # Get movie from Radarr
            radarr_url = target_instance.get('api_url', '') or target_instance.get('url', '')
            radarr_api_key = target_instance.get('api_key', '')
            
            if not radarr_url or not radarr_api_key:
                return {'in_library': False, 'previously_requested': already_requested_in_db}
            
            radarr_url = radarr_url.rstrip('/')
            
            # Search for movie by TMDB ID
            headers = {'X-Api-Key': radarr_api_key}
            response = requests.get(
                f"{radarr_url}/api/v3/movie",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get movies from Radarr: {response.status_code}")
                return {'in_library': False, 'previously_requested': already_requested_in_db}
            
            movies_list = response.json()
            
            logger.info(f"Searching for TMDB ID {tmdb_id} in {len(movies_list)} movies")
            
            for movie in movies_list:
                movie_tmdb = movie.get('tmdbId')
                if movie_tmdb == tmdb_id:
                    has_file = movie.get('hasFile', False)
                    logger.debug(f"Found movie in Radarr: {movie.get('title')} - Has file: {has_file}")
                    
                    # Check if previously requested
                    # Priority: Requestarr DB > Radarr status
                    previously_requested = already_requested_in_db or (not has_file)
                    
                    return {
                        'in_library': has_file,
                        'previously_requested': previously_requested,
                        'monitored': movie.get('monitored', False),
                    }
            
            logger.info(f"Movie with TMDB ID {tmdb_id} not found in Radarr")
            return {
                'in_library': False,
                'previously_requested': already_requested_in_db,
            }
            
        except Exception as e:
            logger.error(f"Error getting movie status from Radarr: {e}")
            return {
                'in_library': False,
                'previously_requested': False,
            }

    def get_radarr_movie_detail_status(self, tmdb_id: int, instance_name: str) -> Dict[str, Any]:
        """Get movie detail for Requestarr info bar: path, status, quality_profile, file_size."""
        try:
            app_config = self.db.get_app_config('radarr')
            if not app_config or not app_config.get('instances'):
                return {'success': True, 'found': False}

            target_instance = None
            for instance in app_config['instances']:
                if instance.get('name') == instance_name:
                    target_instance = instance
                    break

            if not target_instance:
                return {'success': True, 'found': False}

            radarr_url = (target_instance.get('api_url') or target_instance.get('url') or '').rstrip('/')
            radarr_api_key = (target_instance.get('api_key') or '').strip()
            if not radarr_url or not radarr_api_key:
                return {'success': True, 'found': False}

            headers = {'X-Api-Key': radarr_api_key}
            response = requests.get(f"{radarr_url}/api/v3/movie", headers=headers, timeout=10)
            if response.status_code != 200:
                logger.error("Radarr movie list failed: %s", response.status_code)
                return {'success': False, 'found': False}

            movies_list = response.json()
            for movie in movies_list:
                if movie.get('tmdbId') != tmdb_id:
                    continue
                has_file = movie.get('hasFile', False)
                movie_file = movie.get('movieFile') or {}
                path = (movie_file.get('path') or movie_file.get('relativePath') or '').strip() or '-'
                file_size = movie_file.get('size') or 0
                quality_profile = '-'
                quality_profile_obj = movie.get('qualityProfile')
                if isinstance(quality_profile_obj, dict) and quality_profile_obj.get('name'):
                    quality_profile = quality_profile_obj['name']
                elif has_file:
                    q = (movie_file.get('quality') or {}).get('quality')
                    if isinstance(q, dict) and q.get('name'):
                        quality_profile = q['name']

                if has_file:
                    status = 'downloaded'
                else:
                    status = 'missing'  # in Radarr but no file -> requested

                return {
                    'success': True,
                    'found': True,
                    'path': path,
                    'status': status,
                    'quality_profile': quality_profile,
                    'file_size': file_size,
                }

            return {'success': True, 'found': False}
        except Exception as e:
            logger.error("Error getting Radarr movie detail: %s", e)
            return {'success': False, 'found': False}

    
    def check_library_status_batch(self, items: List[Dict[str, Any]], app_type: str = None, instance_name: str = None) -> List[Dict[str, Any]]:
        """
        Check library status for a batch of media items.
        Adds status flags to each item:
        - 'in_library': Complete (all episodes for TV, has file for movies)
        - 'partial': TV shows with some but not all episodes
        - 'pending': Item has a pending request from the current user
        
        Args:
            items: List of media items to check
            app_type: Optional app type to check (radarr/sonarr). If None, checks all instances.
            instance_name: Optional instance name to check. If None, checks all instances.
        """
        try:
            # Get pending + approved request tmdb_ids for badge enrichment
            pending_tmdb_ids = set()
            approved_tmdb_ids = set()
            try:
                from flask import request as flask_request
                from src.primary.auth import get_username_from_session, SESSION_COOKIE_NAME
                from src.primary.utils.database import get_database as _get_db
                session_token = flask_request.cookies.get(SESSION_COOKIE_NAME)
                username = get_username_from_session(session_token)
                if username:
                    _db = _get_db()
                    # Owner is in `users` table, non-owner users are in `requestarr_users`
                    user = _db.get_user_by_username(username) or _db.get_requestarr_user_by_username(username)
                    if user:
                        pending_tmdb_ids = _db.get_pending_request_tmdb_ids(user_id=user.get('id'))
                    # Approved requests (any user) — movies approved but possibly not yet in collection
                    approved_tmdb_ids = _db.get_approved_request_tmdb_ids()
            except Exception:
                pass  # Not in a request context or auth unavailable — skip pending check

            # Get enabled instances
            instances = self.get_enabled_instances()
            
            if not instances['radarr'] and not instances['sonarr']:
                # No instances configured, mark all as not in library
                for item in items:
                    item['in_library'] = False
                    item['partial'] = False
                    item['pending'] = False
                return items
            
            # Filter instances based on app_type and instance_name if provided
            radarr_instances = instances['radarr']
            sonarr_instances = instances['sonarr']
            
            if app_type and instance_name:
                if app_type == 'radarr':
                    radarr_instances = [inst for inst in radarr_instances if inst['name'] == instance_name]
                    sonarr_instances = []
                elif app_type == 'sonarr':
                    sonarr_instances = [inst for inst in sonarr_instances if inst['name'] == instance_name]
                    radarr_instances = []
            else:
                logger.debug(f"No instance filtering - checking all instances (Radarr: {len(radarr_instances)}, Sonarr: {len(sonarr_instances)})")
            
            # Get all movies from filtered Radarr instances
            radarr_tmdb_ids = set()
            radarr_monitored_tmdb_ids = set()  # In Radarr but no file yet
            for instance in radarr_instances:
                try:
                    headers = {'X-Api-Key': instance['api_key']}
                    response = requests.get(
                        f"{instance['url'].rstrip('/')}/api/v3/movie",
                        headers=headers,
                        timeout=10
                    )
                    if response.status_code == 200:
                        movies = response.json()
                        for movie in movies:
                            if movie.get('hasFile', False):  # Only count movies with files
                                radarr_tmdb_ids.add(movie.get('tmdbId'))
                            else:
                                # In Radarr but no file yet — treat as partial (monitored)
                                radarr_monitored_tmdb_ids.add(movie.get('tmdbId'))
                        logger.debug(f"Found {len(radarr_tmdb_ids)} movies with files + {len(radarr_monitored_tmdb_ids)} monitored in Radarr instance {instance['name']}")
                except Exception as e:
                    logger.error(f"Error checking Radarr instance {instance['name']}: {e}")
            
            # Get all series from filtered Sonarr instances
            sonarr_tmdb_ids = set()
            sonarr_partial_tmdb_ids = set()
            for instance in sonarr_instances:
                try:
                    headers = {'X-Api-Key': instance['api_key']}
                    response = requests.get(
                        f"{instance['url'].rstrip('/')}/api/v3/series",
                        headers=headers,
                        timeout=10
                    )
                    if response.status_code == 200:
                        series_list = response.json()
                        for series in series_list:
                            statistics = series.get('statistics', {})
                            total_episodes = statistics.get('episodeCount', 0)
                            available_episodes = statistics.get('episodeFileCount', 0)
                            
                            tmdb_id = series.get('tmdbId')
                            if not tmdb_id:
                                continue
                            # Mark as in_library if all episodes are available
                            if total_episodes > 0 and available_episodes == total_episodes:
                                sonarr_tmdb_ids.add(tmdb_id)
                            # Mark as partial if series exists in Sonarr (monitored)
                            # — even with 0 episodes downloaded, it's "in the library"
                            else:
                                sonarr_partial_tmdb_ids.add(tmdb_id)
                        logger.debug(f"Found {len(sonarr_tmdb_ids)} complete series and {len(sonarr_partial_tmdb_ids)} partial series in Sonarr instance {instance['name']}")
                except Exception as e:
                    logger.error(f"Error checking Sonarr instance {instance['name']}: {e}")
            
            # Mark each item with status
            for item in items:
                tmdb_id = item.get('tmdb_id')
                # Normalize to int for consistent set lookups
                try:
                    tmdb_id = int(tmdb_id)
                except (TypeError, ValueError):
                    pass
                media_type = item.get('media_type')
                
                # Set library status
                if media_type == 'movie':
                    # Check Radarr
                    item['in_library'] = tmdb_id in radarr_tmdb_ids
                    # Movies in collection but without files yet → partial (shows bookmark, not download icon)
                    item['partial'] = (not item['in_library']) and (tmdb_id in radarr_monitored_tmdb_ids)
                    # Fallback: approved in DB but not yet in any collection → still partial
                    if not item['in_library'] and not item['partial'] and tmdb_id in approved_tmdb_ids:
                        item['partial'] = True
                    item['importable'] = False
                elif media_type == 'tv':
                    item['in_library'] = tmdb_id in sonarr_tmdb_ids
                    item['partial'] = tmdb_id in sonarr_partial_tmdb_ids
                    # Fallback: approved in DB but not yet in any collection → still partial
                    if not item['in_library'] and not item['partial'] and tmdb_id in approved_tmdb_ids:
                        item['partial'] = True
                    item['importable'] = False
                else:
                    item['in_library'] = False
                    item['partial'] = False
                    item['importable'] = False

                # Pending request badge: only show if NOT already in library or partial
                item['pending'] = (tmdb_id in pending_tmdb_ids) and not item['in_library'] and not item['partial']
            
            return items
            
        except Exception as e:
            logger.error(f"Error checking library status batch: {e}")
            # On error, mark all as not in library
            for item in items:
                item['in_library'] = False
                item['partial'] = False
                item['pending'] = False
            return items
    
    def filter_available_media(self, items: List[Dict[str, Any]], media_type: str) -> List[Dict[str, Any]]:
        """
        Filter out media items that are already available in library.
        Returns only items where in_library AND partial are both False.
        
        "Hide items in library" means hide anything the user already has
        in their arr apps — whether fully downloaded (in_library) or just
        monitored/partially downloaded (partial).
        
        Args:
            items: List of media items with 'in_library' and 'partial' status
            media_type: 'movie' or 'tv'
            
        Returns:
            Filtered list excluding items already in library or partially in library
        """
        try:
            filtered_items = [
                item for item in items
                if not item.get('in_library', False) and not item.get('partial', False)
            ]
            logger.info(f"Filtered {media_type} results: {len(items)} total -> {len(filtered_items)} not in library (removed {len(items) - len(filtered_items)} in_library/partial)")
            return filtered_items
        except Exception as e:
            logger.error(f"Error filtering available media: {e}")
            return items  # Return all items on error
    
    def filter_hidden_media(self, items: List[Dict[str, Any]], app_type: str = None, instance_name: str = None) -> List[Dict[str, Any]]:
        """
        Filter out media items that have been permanently hidden (cross-instance).
        Personal blacklist now applies across ALL instances for the user.
        
        Args:
            items: List of media items with 'tmdb_id' and 'media_type'
            app_type: Kept for backward compat, no longer used for filtering
            instance_name: Kept for backward compat, no longer used for filtering
            
        Returns:
            Filtered list excluding hidden media
        """
        try:
            filtered_items = []
            for item in items:
                tmdb_id = item.get('tmdb_id')
                media_type = item.get('media_type')
                
                if not self.db.is_media_hidden(tmdb_id, media_type):
                    filtered_items.append(item)
            
            if len(filtered_items) < len(items):
                logger.info(f"Filtered hidden media: {len(items)} total -> {len(filtered_items)} after removing hidden")
            
            return filtered_items
        except Exception as e:
            logger.error(f"Error filtering hidden media: {e}")
            return items  # Return all items on error
    

    def _get_availability_status(self, tmdb_id: int, media_type: str, instance: Dict[str, str], app_type: str) -> Dict[str, Any]:
        """Get availability status for media item"""
        if not instance:
            return {
                'status': 'error',
                'message': 'Instance not found',
                'in_app': False,
                'already_requested': False
            }
        
        # Check if already requested first (this doesn't require API connection)
        try:
            already_requested = self.db.is_already_requested(tmdb_id, media_type, app_type, instance.get('name'))
            if already_requested:
                return {
                    'status': 'requested',
                    'message': 'Previously requested',
                    'in_app': False,
                    'already_requested': True
                }
        except Exception as e:
            logger.error(f"Error checking request history: {e}")
        
        # Check if instance is properly configured
        url = instance.get('api_url', '') or instance.get('url', '')
        if not url or not instance.get('api_key'):
            return {
                'status': 'available_to_request',
                'message': 'Ready to request (instance needs configuration)',
                'in_app': False,
                'already_requested': False
            }
        
        try:
            # Check if exists in app
            exists_result = self._check_media_exists(tmdb_id, media_type, instance, app_type)
            
            if exists_result['exists']:
                # Handle Sonarr series with episode completion logic
                if app_type == 'sonarr' and 'episode_file_count' in exists_result:
                    episode_file_count = exists_result['episode_file_count']
                    episode_count = exists_result['episode_count']
                    
                    if episode_count == 0:
                        # Series exists but no episodes expected yet
                        return {
                            'status': 'available',
                            'message': f'Series in library (no episodes available yet)',
                            'in_app': True,
                            'already_requested': False,
                            'episode_stats': f'{episode_file_count}/{episode_count}'
                        }
                    elif episode_file_count >= episode_count:
                        # All episodes downloaded
                        return {
                            'status': 'available',
                            'message': f'Complete series in library ({episode_file_count}/{episode_count})',
                            'in_app': True,
                            'already_requested': False,
                            'episode_stats': f'{episode_file_count}/{episode_count}'
                        }
                    else:
                        # Missing episodes - allow requesting missing ones
                        missing_count = episode_count - episode_file_count
                        return {
                            'status': 'available_to_request_missing',
                            'message': f'Request missing episodes ({episode_file_count}/{episode_count}, {missing_count} missing)',
                            'in_app': True,
                            'already_requested': False,
                            'episode_stats': f'{episode_file_count}/{episode_count}',
                            'missing_episodes': missing_count,
                            'series_id': exists_result.get('series_id')
                        }
                else:
                    # Radarr or other apps - simple exists check
                    return {
                        'status': 'available',
                        'message': 'Already in library',
                        'in_app': True,
                        'already_requested': False
                    }
            else:
                return {
                    'status': 'available_to_request',
                    'message': 'Available to request',
                    'in_app': False,
                    'already_requested': False
                }
                
        except Exception as e:
            logger.error(f"Error checking availability in {app_type}: {e}")
            # If we can't check the app, still allow requesting
            return {
                'status': 'available_to_request',
                'message': 'Available to request (could not verify library)',
                'in_app': False,
                'already_requested': False
            }
    
    def get_enabled_instances(self) -> Dict[str, List[Dict[str, str]]]:
        """Get enabled and properly configured Sonarr and Radarr instances"""
        instances = {'sonarr': [], 'radarr': []}
        seen_names = {'sonarr': set(), 'radarr': set()}
        
        try:
            # Get Sonarr instances
            sonarr_config = self.db.get_app_config('sonarr')
            if sonarr_config and sonarr_config.get('instances'):
                for instance in sonarr_config['instances']:
                    # Database stores URL as 'api_url', map it to 'url' for consistency
                    url = instance.get('api_url', '') or instance.get('url', '')
                    api_key = instance.get('api_key', '')
                    name = instance.get('name', 'Default')
                    
                    # Only include instances that are enabled AND have proper configuration
                    # AND not already added (deduplicate by name case-insensitively)
                    name_lower = name.strip().lower()
                    if (instance.get('enabled', False) and 
                        url.strip() and 
                        api_key.strip() and
                        name_lower not in seen_names['sonarr']):
                        instances['sonarr'].append({
                            'name': name.strip(),
                            'url': url.strip(),
                            'api_key': api_key.strip()
                        })
                        seen_names['sonarr'].add(name_lower)
            
            # Get Radarr instances
            radarr_config = self.db.get_app_config('radarr')
            if radarr_config and radarr_config.get('instances'):
                for instance in radarr_config['instances']:
                    # Database stores URL as 'api_url', map it to 'url' for consistency
                    url = instance.get('api_url', '') or instance.get('url', '')
                    api_key = instance.get('api_key', '')
                    name = instance.get('name', 'Default')
                    
                    # Only include instances that are enabled AND have proper configuration
                    # AND not already added (deduplicate by name case-insensitively)
                    name_lower = name.strip().lower()
                    if (instance.get('enabled', False) and 
                        url.strip() and 
                        api_key.strip() and
                        name_lower not in seen_names['radarr']):
                        instances['radarr'].append({
                            'name': name.strip(),
                            'url': url.strip(),
                            'api_key': api_key.strip()
                        })
                        seen_names['radarr'].add(name_lower)
            
            return instances
            
        except Exception as e:
            logger.error(f"Error getting enabled instances: {e}")
            return {'sonarr': [], 'radarr': []}
