"""
Requestarr Requests Mixin
Media request/add operations for Radarr, Sonarr, Movie Hunt, and TV Hunt.
Extracted from requestarr/__init__.py to reduce file size.
"""

import requests
import logging
import json
import time
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class RequestsMixin:
    """Media request/add operations for Radarr and Sonarr."""

    def request_media(self, tmdb_id: int, media_type: str, title: str, year: int,
                     overview: str, poster_path: str, backdrop_path: str,
                     app_type: str, instance_name: str, quality_profile_id: int = None,
                     root_folder_path: str = None, quality_profile_name: str = None,
                     start_search: bool = True, minimum_availability: str = 'released',
                     monitor: str = None, movie_monitor: str = None,
                     skip_tracking: bool = False) -> Dict[str, Any]:
        """Request media through the specified app instance.
        skip_tracking: if True, skip the legacy add_request() call (used by approve flow
        where the requestarr_requests record already exists).
        """
        try:
            
            # Get instance configuration first
            app_config = self.db.get_app_config(app_type)
            if not app_config or not app_config.get('instances'):
                return {
                    'success': False,
                    'message': f'No {app_type.title()} instances configured',
                    'status': 'no_instances'
                }
            
            # Find the specific instance
            target_instance = None
            for instance in app_config['instances']:
                if instance.get('name') == instance_name:
                    target_instance = instance
                    break
            
            if not target_instance:
                return {
                    'success': False,
                    'message': f'{app_type.title()} instance "{instance_name}" not found',
                    'status': 'instance_not_found'
                }
            
            # Check if media exists and get detailed info
            exists_result = self._check_media_exists(tmdb_id, media_type, target_instance, app_type)
            
            if exists_result.get('exists'):
                if app_type == 'sonarr' and 'series_id' in exists_result:
                    # Series exists in Sonarr - check if we should request missing episodes
                    episode_file_count = exists_result.get('episode_file_count', 0)
                    episode_count = exists_result.get('episode_count', 0)
                    
                    if episode_file_count < episode_count and episode_count > 0:
                        # Request missing episodes for existing series
                        missing_result = self._request_missing_episodes(exists_result['series_id'], target_instance)
                        
                        if missing_result['success']:
                            # Save request to database
                            if not skip_tracking:
                                self.db.add_request(
                                    tmdb_id, media_type, title, year, overview, 
                                    poster_path, backdrop_path, app_type, instance_name
                                )
                            
                            missing_count = episode_count - episode_file_count
                            return {
                                'success': True,
                                'message': f'Search initiated for {missing_count} missing episodes of {title}',
                                'status': 'requested'
                            }
                        else:
                            return {
                                'success': False,
                                'message': missing_result['message'],
                                'status': 'request_failed'
                            }
                    else:
                        # Series is complete or no episodes expected
                        return {
                            'success': False,
                            'message': f'{title} is already complete in your library',
                            'status': 'already_complete'
                        }
                elif app_type == 'radarr':
                    # Movie exists in Radarr - check if it has file
                    has_file = exists_result.get('has_file', False)
                    if has_file:
                        # Movie is already downloaded
                        return {
                            'success': False,
                            'message': f'{title} already exists in {app_type.title()} - {instance_name}',
                            'status': 'already_exists'
                        }
                    else:
                        # Movie is monitored but not downloaded yet - trigger search
                        movie_data = exists_result.get('movie_data', {})
                        movie_id = movie_data.get('id')
                        
                        if movie_id:
                            # Trigger movie search
                            try:
                                url = (target_instance.get('api_url', '') or target_instance.get('url', '')).rstrip('/')
                                api_key = target_instance.get('api_key', '')
                                
                                search_response = requests.post(
                                    f"{url}/api/v3/command",
                                    headers={'X-Api-Key': api_key},
                                    json={'name': 'MoviesSearch', 'movieIds': [movie_id]},
                                    timeout=10
                                )
                                search_response.raise_for_status()
                                
                                # Save request to database
                                if not skip_tracking:
                                    self.db.add_request(
                                        tmdb_id, media_type, title, year, overview, 
                                        poster_path, backdrop_path, app_type, instance_name
                                    )
                                
                                return {
                                    'success': True,
                                    'message': f'Search initiated for {title} (already in Radarr, triggering download)',
                                    'status': 'requested'
                                }
                            except Exception as e:
                                logger.error(f"Error triggering movie search: {e}")
                                return {
                                    'success': False,
                                    'message': f'{title} is in Radarr but search failed: {str(e)}',
                                    'status': 'request_failed'
                                }
                        else:
                            return {
                                'success': False,
                                'message': f'{title} already exists in {app_type.title()} - {instance_name}',
                                'status': 'already_exists'
                            }
                else:
                    # Media exists in app - can't add again
                    return {
                        'success': False,
                        'message': f'{title} already exists in {app_type.title()} - {instance_name}',
                        'status': 'already_exists'
                    }
            else:
                # Add new media to the app
                add_result = self._add_media_to_app(tmdb_id, media_type, target_instance, app_type, quality_profile_id, root_folder_path, minimum_availability=minimum_availability)
                
                if add_result['success']:
                    # Save request to database
                    if not skip_tracking:
                        self.db.add_request(
                            tmdb_id, media_type, title, year, overview, 
                            poster_path, backdrop_path, app_type, instance_name
                        )
                    
                    return {
                        'success': True,
                        'message': f'{title} successfully requested to {app_type.title()} - {instance_name}',
                        'status': 'requested'
                    }
                else:
                    return {
                        'success': False,
                        'message': add_result['message'],
                        'status': 'request_failed'
                    }
                
        except Exception as e:
            logger.error(f"Error requesting media: {e}")
            return {
                'success': False,
                'message': f'Error requesting {title}: {str(e)}',
                'status': 'error'
            }
    
    
    def _check_media_exists(self, tmdb_id: int, media_type: str, instance: Dict[str, str], app_type: str) -> Dict[str, Any]:
        """Check if media already exists in the app instance"""
        try:
            # Database stores URL as 'api_url', map it to 'url' for consistency
            url = (instance.get('api_url', '') or instance.get('url', '')).rstrip('/')
            api_key = instance.get('api_key', '')
            
            # If no URL or API key, we can't check
            if not url or not api_key:
                logger.debug(f"Instance {instance.get('name')} not configured with URL/API key")
                return {'exists': False}
            
            if app_type == 'radarr':
                # Search for movie by TMDB ID
                response = requests.get(
                    f"{url}/api/v3/movie",
                    headers={'X-Api-Key': api_key},
                    params={'tmdbId': tmdb_id},
                    timeout=10
                )
                response.raise_for_status()
                movies = response.json()
                
                # Check if movie exists AND has file
                if len(movies) > 0:
                    movie = movies[0]
                    has_file = movie.get('hasFile', False)
                    return {
                        'exists': True,
                        'has_file': has_file,
                        'movie_data': movie
                    }
                
                return {'exists': False}
                
            elif app_type == 'sonarr':
                # Search for series
                response = requests.get(
                    f"{url}/api/v3/series",
                    headers={'X-Api-Key': api_key},
                    timeout=10
                )
                response.raise_for_status()
                series_list = response.json()
                
                # Check if any series has matching TMDB ID
                for series in series_list:
                    if series.get('tmdbId') == tmdb_id:
                        # Get episode statistics from the statistics object
                        series_id = series.get('id')
                        statistics = series.get('statistics', {})
                        episode_file_count = statistics.get('episodeFileCount', 0)
                        episode_count = statistics.get('episodeCount', 0)
                        
                        return {
                            'exists': True,
                            'series_id': series_id,
                            'episode_file_count': episode_file_count,
                            'episode_count': episode_count,
                            'series_data': series
                        }
                
                return {'exists': False}
            
            return {'exists': False}
            
        except requests.exceptions.ConnectionError:
            logger.debug(f"Could not connect to {app_type} instance at {url}")
            return {'exists': False}
        except requests.exceptions.Timeout:
            logger.debug(f"Timeout connecting to {app_type} instance at {url}")
            return {'exists': False}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.debug(f"Authentication failed for {app_type} instance")
            elif e.response.status_code == 404:
                logger.debug(f"API endpoint not found for {app_type} instance")
            else:
                logger.debug(f"HTTP error checking {app_type}: {e}")
            return {'exists': False}
        except Exception as e:
            logger.debug(f"Error checking if media exists in {app_type}: {e}")
            return {'exists': False}
    
    def _request_missing_episodes(self, series_id: int, instance: Dict[str, str]) -> Dict[str, Any]:
        """Request missing episodes for an existing series in Sonarr"""
        try:
            # Database stores URL as 'api_url', map it to 'url' for consistency
            url = (instance.get('api_url', '') or instance.get('url', '')).rstrip('/')
            api_key = instance.get('api_key', '')
            
            if not url or not api_key:
                return {
                    'success': False,
                    'message': 'Instance not configured with URL/API key'
                }
            
            # Trigger a series search for missing episodes
            response = requests.post(
                f"{url}/api/v3/command",
                headers={'X-Api-Key': api_key, 'Content-Type': 'application/json'},
                json={
                    'name': 'SeriesSearch',
                    'seriesId': series_id
                },
                timeout=10
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'message': 'Missing episodes search initiated'
            }
            
        except Exception as e:
            logger.error(f"Error requesting missing episodes: {e}")
            return {
                'success': False,
                'message': f'Error requesting missing episodes: {str(e)}'
            }
    
    def _add_media_to_app(self, tmdb_id: int, media_type: str, instance: Dict[str, str], app_type: str, quality_profile_id: int = None, root_folder_path: str = None, minimum_availability: str = None) -> Dict[str, Any]:
        """Add media to the app instance"""
        try:
            # Database stores URL as 'api_url', map it to 'url' for consistency
            url = (instance.get('api_url', '') or instance.get('url', '')).rstrip('/')
            api_key = instance.get('api_key', '')
            
            if not url or not api_key:
                return {
                    'success': False,
                    'message': 'Instance not configured with URL/API key'
                }
            
            if app_type == 'radarr' and media_type == 'movie':
                return self._add_movie_to_radarr(tmdb_id, url, api_key, quality_profile_id, root_folder_path, minimum_availability=minimum_availability)
            elif app_type == 'sonarr' and media_type == 'tv':
                return self._add_series_to_sonarr(tmdb_id, url, api_key, quality_profile_id, root_folder_path)
            else:
                return {
                    'success': False,
                    'message': f'Invalid combination: {media_type} to {app_type}'
                }
                
        except Exception as e:
            logger.error(f"Error adding media to app: {e}")
            return {
                'success': False,
                'message': f'Error adding media: {str(e)}'
            }
    
    def _add_movie_to_radarr(self, tmdb_id: int, url: str, api_key: str, quality_profile_id: int = None, root_folder_path: str = None, minimum_availability: str = None) -> Dict[str, Any]:
        """Add movie to Radarr"""
        try:
            # First, get movie details from Radarr's lookup
            lookup_response = requests.get(
                f"{url}/api/v3/movie/lookup",
                headers={'X-Api-Key': api_key},
                params={'term': f'tmdb:{tmdb_id}'},
                timeout=10
            )
            lookup_response.raise_for_status()
            lookup_results = lookup_response.json()
            
            if not lookup_results:
                return {
                    'success': False,
                    'message': 'Movie not found in Radarr lookup'
                }
            
            movie_data = lookup_results[0]
            
            # Get root folders with retry logic
            import time
            max_retries = 3
            timeout = 30  # Increased for slow Unraid environments
            
            root_folders = None
            for attempt in range(max_retries):
                try:
                    logger.info(f"Fetching root folders from Radarr (attempt {attempt+1}/{max_retries})")
                    root_folders_response = requests.get(
                        f"{url}/api/v3/rootfolder",
                        headers={'X-Api-Key': api_key},
                        timeout=timeout
                    )
                    root_folders_response.raise_for_status()
                    root_folders = root_folders_response.json()
                    break  # Success
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"Timeout/connection error fetching root folders (attempt {attempt+1}): {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Failed to fetch root folders after {max_retries} attempts: {e}")
                        return {
                            'success': False,
                            'message': 'Timeout connecting to Radarr. Please check your instance and try again.'
                        }
                except requests.exceptions.RequestException as e:
                    logger.error(f"API error fetching root folders: {e}")
                    return {
                        'success': False,
                        'message': f'Error fetching root folders: {str(e)}'
                    }
            
            if not root_folders:
                return {
                    'success': False,
                    'message': 'No root folders configured in Radarr'
                }
            
            # Use per-request root, then default from settings, then first folder (issue #806)
            root_paths = [rf['path'] for rf in root_folders]
            selected_root = root_folders[0]['path']
            if root_folder_path and root_folder_path in root_paths:
                selected_root = root_folder_path
            else:
                default_radarr = (self.get_default_root_folders().get('default_root_folder_radarr') or '').strip()
                if default_radarr and default_radarr in root_paths:
                    selected_root = default_radarr
            
            # Get quality profiles with retry logic
            profiles = None
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Fetching quality profiles from Radarr (attempt {attempt+1}/{max_retries})")
                    profiles_response = requests.get(
                        f"{url}/api/v3/qualityprofile",
                        headers={'X-Api-Key': api_key},
                        timeout=timeout
                    )
                    profiles_response.raise_for_status()
                    profiles = profiles_response.json()
                    break  # Success
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"Timeout/connection error fetching quality profiles (attempt {attempt+1}): {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Failed to fetch quality profiles after {max_retries} attempts: {e}")
                        return {
                            'success': False,
                            'message': 'Timeout fetching quality profiles from Radarr. Please check your instance and try again.'
                        }
                except requests.exceptions.RequestException as e:
                    logger.error(f"API error fetching quality profiles: {e}")
                    return {
                        'success': False,
                        'message': f'Error fetching quality profiles: {str(e)}'
                    }
            
            if not profiles:
                return {
                    'success': False,
                    'message': 'No quality profiles configured in Radarr'
                }
            
            # Use provided quality profile ID or default to first one
            selected_profile_id = quality_profile_id if quality_profile_id else profiles[0]['id']
            
            # Prepare movie data for adding
            add_data = {
                'title': movie_data['title'],
                'tmdbId': movie_data['tmdbId'],
                'year': movie_data['year'],
                'rootFolderPath': selected_root,
                'qualityProfileId': selected_profile_id,
                'monitored': True,
                'addOptions': {
                    'searchForMovie': True
                }
            }
            
            # Pass minimumAvailability to Radarr if provided (Radarr API v3 top-level field)
            # Valid values: 'announced', 'inCinemas', 'released'
            if minimum_availability and minimum_availability in ('announced', 'inCinemas', 'released'):
                add_data['minimumAvailability'] = minimum_availability
            
            # Add additional fields from lookup
            for field in ['imdbId', 'overview', 'images', 'genres', 'runtime']:
                if field in movie_data:
                    add_data[field] = movie_data[field]
            
            # Add the movie
            add_response = requests.post(
                f"{url}/api/v3/movie",
                headers={'X-Api-Key': api_key, 'Content-Type': 'application/json'},
                json=add_data,
                timeout=10
            )
            add_response.raise_for_status()
            
            return {
                'success': True,
                'message': 'Movie successfully added to Radarr'
            }
            
        except Exception as e:
            logger.error(f"Error adding movie to Radarr: {e}")
            return {
                'success': False,
                'message': f'Error adding movie to Radarr: {str(e)}'
            }
    
    def _add_series_to_sonarr(self, tmdb_id: int, url: str, api_key: str, quality_profile_id: int = None, root_folder_path: str = None) -> Dict[str, Any]:
        """Add series to Sonarr"""
        try:
            # First, get series details from Sonarr's lookup
            lookup_response = requests.get(
                f"{url}/api/v3/series/lookup",
                headers={'X-Api-Key': api_key},
                params={'term': f'tmdb:{tmdb_id}'},
                timeout=10
            )
            lookup_response.raise_for_status()
            lookup_results = lookup_response.json()
            
            if not lookup_results:
                return {
                    'success': False,
                    'message': 'Series not found in Sonarr lookup'
                }
            
            series_data = lookup_results[0]
            
            # Get root folders with retry logic
            import time
            max_retries = 3
            timeout = 30  # Increased for slow Unraid environments
            
            root_folders = None
            for attempt in range(max_retries):
                try:
                    logger.info(f"Fetching root folders from Sonarr (attempt {attempt+1}/{max_retries})")
                    root_folders_response = requests.get(
                        f"{url}/api/v3/rootfolder",
                        headers={'X-Api-Key': api_key},
                        timeout=timeout
                    )
                    root_folders_response.raise_for_status()
                    root_folders = root_folders_response.json()
                    break  # Success
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"Timeout/connection error fetching root folders (attempt {attempt+1}): {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Failed to fetch root folders after {max_retries} attempts: {e}")
                        return {
                            'success': False,
                            'message': 'Timeout connecting to Sonarr. Please check your instance and try again.'
                        }
                except requests.exceptions.RequestException as e:
                    logger.error(f"API error fetching root folders: {e}")
                    return {
                        'success': False,
                        'message': f'Error fetching root folders: {str(e)}'
                    }
            
            if not root_folders:
                return {
                    'success': False,
                    'message': 'No root folders configured in Sonarr'
                }
            
            # Use per-request root, then default from settings, then first folder (issue #806)
            root_paths = [rf['path'] for rf in root_folders]
            selected_root = root_folders[0]['path']
            if root_folder_path and root_folder_path in root_paths:
                selected_root = root_folder_path
            else:
                default_sonarr = (self.get_default_root_folders().get('default_root_folder_sonarr') or '').strip()
                if default_sonarr and default_sonarr in root_paths:
                    selected_root = default_sonarr
            
            # Get quality profiles with retry logic
            profiles = None
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Fetching quality profiles from Sonarr (attempt {attempt+1}/{max_retries})")
                    profiles_response = requests.get(
                        f"{url}/api/v3/qualityprofile",
                        headers={'X-Api-Key': api_key},
                        timeout=timeout
                    )
                    profiles_response.raise_for_status()
                    profiles = profiles_response.json()
                    break  # Success
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"Timeout/connection error fetching quality profiles (attempt {attempt+1}): {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Failed to fetch quality profiles after {max_retries} attempts: {e}")
                        return {
                            'success': False,
                            'message': 'Timeout fetching quality profiles from Sonarr. Please check your instance and try again.'
                        }
                except requests.exceptions.RequestException as e:
                    logger.error(f"API error fetching quality profiles: {e}")
                    return {
                        'success': False,
                        'message': f'Error fetching quality profiles: {str(e)}'
                    }
            
            if not profiles:
                return {
                    'success': False,
                    'message': 'No quality profiles configured in Sonarr'
                }
            
            # Use provided quality profile ID or default to first one
            selected_profile_id = quality_profile_id if quality_profile_id else profiles[0]['id']
            
            # Prepare series data for adding
            add_data = {
                'title': series_data['title'],
                'tvdbId': series_data.get('tvdbId'),
                'year': series_data.get('year'),
                'rootFolderPath': selected_root,
                'qualityProfileId': selected_profile_id,
                'monitored': True,
                'addOptions': {
                    'searchForMissingEpisodes': True
                }
            }
            
            # Add additional fields from lookup
            for field in ['imdbId', 'overview', 'images', 'genres', 'network', 'seasons']:
                if field in series_data:
                    add_data[field] = series_data[field]
            
            # Add the series
            add_response = requests.post(
                f"{url}/api/v3/series",
                headers={'X-Api-Key': api_key, 'Content-Type': 'application/json'},
                json=add_data,
                timeout=10
            )
            add_response.raise_for_status()
            
            return {
                'success': True,
                'message': 'Series successfully added to Sonarr'
            }
            
        except Exception as e:
            logger.error(f"Error adding series to Sonarr: {e}")
            return {
                'success': False,
                'message': f'Error adding series to Sonarr: {str(e)}'
            }

    def cascade_bundle_requests(self, tmdb_id: int, media_type: str, title: str,
                                year, overview: str, poster_path: str, backdrop_path: str,
                                app_type: str, instance_name: str,
                                start_search: bool = True, minimum_availability: str = 'released',
                                monitor: str = None, movie_monitor: str = None) -> list:
        """After a primary request succeeds, cascade to all bundle members.
        Returns a list of {instance_name, app_type, success, message} for each member."""
        results = []
        try:
            bundles = self.db.get_bundles_for_instance(app_type, instance_name)
            if not bundles:
                return results

            for bundle in bundles:
                for member in bundle.get('members', []):
                    m_app_type = member['app_type']
                    m_instance = member['instance_name']
                    try:
                        result = self.request_media(
                            tmdb_id=tmdb_id, media_type=media_type,
                            title=title, year=year, overview=overview,
                            poster_path=poster_path, backdrop_path=backdrop_path,
                            app_type=m_app_type, instance_name=m_instance,
                            start_search=start_search,
                            minimum_availability=minimum_availability,
                            monitor=monitor, movie_monitor=movie_monitor,
                            skip_tracking=True
                        )
                        status = result.get('status', '')
                        success = result.get('success', False) or status in ('already_exists', 'already_complete')
                        results.append({
                            'bundle': bundle['name'],
                            'instance_name': m_instance,
                            'app_type': m_app_type,
                            'success': success,
                            'message': result.get('message', ''),
                        })
                        logger.info(f"[Bundle:{bundle['name']}] Cascade to {m_app_type}/{m_instance}: {result.get('message', '')}")
                    except Exception as e:
                        logger.error(f"[Bundle:{bundle['name']}] Cascade error for {m_app_type}/{m_instance}: {e}")
                        results.append({
                            'bundle': bundle['name'],
                            'instance_name': m_instance,
                            'app_type': m_app_type,
                            'success': False,
                            'message': str(e),
                        })
        except Exception as e:
            logger.error(f"[Bundle] Error cascading requests: {e}")
        return results

# Global instance
