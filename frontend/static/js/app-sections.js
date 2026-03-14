/**
 * Huntarr - Section Switching Logic
 * Extracted from app.js to reduce file size.
 * Contains the switchSection() method that handles all section navigation.
 * Loaded after app.js in bundle-app.js — uses Object.assign to extend huntarrUI.
 */

Object.assign(huntarrUI, {

    switchSection: function (section) {
        console.log(`[huntarrUI] *** SWITCH SECTION CALLED *** section: ${section}, current: ${this.currentSection}`);
        // Legacy redirects
        if (section === 'movie-hunt-home') section = 'home';
        if (section === 'tv-hunt-settings') section = 'home';
        if (section === 'movie-hunt-settings') section = 'home';
        if (section === 'tv-hunt-collection') section = 'home';
        if (section === 'movie-hunt-collection') section = 'home';
        if (section === 'movie-hunt-calendar') section = 'home';
        if (section === 'tv-hunt-calendar') section = 'home';
        if (section === 'tv-hunt-settings-sizes') section = 'home';
        if (section === 'requestarr-services') section = 'requestarr-bundles';

        // Feature flag guards
        var requestarrSections = ['requestarr', 'requestarr-discover', 'requestarr-movies', 'requestarr-tv', 'requestarr-smarthunt', 'requestarr-hidden', 'requestarr-personal-blacklist', 'requestarr-options', 'requestarr-filters', 'requestarr-settings', 'requestarr-smarthunt-settings', 'requestarr-users', 'requestarr-bundles', 'requestarr-requests', 'requestarr-global-blacklist'];
        var thirdPartyAppSections = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros', 'prowlarr', 'swaparr'];

        if (this._enableRequestarr === false && requestarrSections.indexOf(section) !== -1) {
            console.log('[huntarrUI] Requests disabled - redirecting to home');
            this.switchSection('home'); return;
        }
        if (this._enableThirdPartyApps === false && thirdPartyAppSections.indexOf(section) !== -1) {
            console.log('[huntarrUI] 3rd Party Apps disabled - redirecting to home');
            this.switchSection('home'); return;
        }

        // Role-based guard: restrict non-owner users to allowed sections only
        if (this._userRole && this._userRole !== 'owner' && this.isAdminOnlySection(section)) {
            console.log('[huntarrUI] Non-owner role restricted - redirecting to discover');
            this.switchSection('requestarr-discover'); return;
        }

        // Check for unsaved changes before allowing navigation
        if (this.isInitialized && this.currentSection && this.currentSection !== section) {
            // Check for unsaved Swaparr changes if leaving Swaparr section
            if (this.currentSection === 'swaparr' && window.SettingsForms && typeof window.SettingsForms.checkUnsavedChanges === 'function') {
                if (!window.SettingsForms.checkUnsavedChanges()) {
                    console.log(`[huntarrUI] Navigation cancelled due to unsaved Swaparr changes`);
                    return; // User chose to stay and save changes
                }
            }

            // Check for unsaved Settings changes if leaving Settings section
            if (this.currentSection === 'settings' && window.SettingsForms && typeof window.SettingsForms.checkUnsavedChanges === 'function') {
                if (!window.SettingsForms.checkUnsavedChanges()) {
                    console.log(`[huntarrUI] Navigation cancelled due to unsaved Settings changes`);
                    return; // User chose to stay and save changes
                }
            }

            // Check for unsaved Notifications changes if leaving Notifications section
            if (this.currentSection === 'notifications' && window.SettingsForms && typeof window.SettingsForms.checkUnsavedChanges === 'function') {
                if (!window.SettingsForms.checkUnsavedChanges()) {
                    console.log(`[huntarrUI] Navigation cancelled due to unsaved Notifications changes`);
                    return; // User chose to stay and save changes
                }
            }

            // Check for unsaved App instance changes if leaving Apps section
            const appSections = ['apps'];
            if (appSections.includes(this.currentSection) && window.SettingsForms && typeof window.SettingsForms.checkUnsavedChanges === 'function') {
                if (!window.SettingsForms.checkUnsavedChanges()) {
                    console.log(`[huntarrUI] Navigation cancelled due to unsaved App changes`);
                    return; // User chose to stay and save changes
                }
            }

            // Check for unsaved Prowlarr changes if leaving Prowlarr section
            if (this.currentSection === 'prowlarr' && window.SettingsForms && typeof window.SettingsForms.checkUnsavedChanges === 'function') {
                if (!window.SettingsForms.checkUnsavedChanges()) {
                    console.log(`[huntarrUI] Navigation cancelled due to unsaved Prowlarr changes`);
                    return; // User chose to stay and save changes
                }
            }

            // Check for unsaved Profile Editor changes if leaving Profile Editor
            if (this.currentSection === 'profile-editor' && section !== 'profile-editor' && window.SettingsForms && typeof window.SettingsForms.isProfileEditorDirty === 'function' && window.SettingsForms.isProfileEditorDirty()) {
                window.SettingsForms.confirmLeaveProfileEditor(function (result) {
                    if (result === 'save') {
                        window.SettingsForms.saveProfileFromEditor(section);
                    } else if (result === 'discard') {
                        window.SettingsForms.cancelProfileEditor(section);
                    }
                });
                return;
            }


            // Check for unsaved Instance Editor changes if leaving Instance Editor
            if (this.currentSection === 'instance-editor' && section !== 'instance-editor' && window.SettingsForms && typeof window.SettingsForms.confirmLeaveInstanceEditor === 'function' && typeof window.SettingsForms.isInstanceEditorDirty === 'function' && window.SettingsForms.isInstanceEditorDirty()) {
                window.SettingsForms.confirmLeaveInstanceEditor((result) => {
                    if (result === 'save') {
                        // true means navigate back after save
                        window.SettingsForms._instanceEditorNextSection = section;
                        window.SettingsForms.saveInstanceFromEditor(true);
                    } else if (result === 'discard') {
                        window.SettingsForms.cancelInstanceEditor(section);
                    }
                });
                return;
            }


            // Don't refresh page when navigating to/from instance editor or between app sections
            const noRefreshSections = ['home', 'instance-editor', 'profile-editor', 'sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros', 'prowlarr', 'swaparr', 'system', 'hunt-manager', 'logs', 'about', 'settings', 'scheduling', 'notifications', 'backup-restore', 'settings-logs', 'user', 'requestarr', 'requestarr-discover', 'requestarr-movies', 'requestarr-tv', 'requestarr-hidden', 'requestarr-personal-blacklist', 'requestarr-options', 'requestarr-filters', 'requestarr-settings', 'requestarr-smarthunt', 'requestarr-smarthunt-settings', 'requestarr-users', 'requestarr-bundles', 'requestarr-requests', 'requestarr-global-blacklist'];
            const skipRefresh = noRefreshSections.includes(section) || noRefreshSections.includes(this.currentSection);

            if (!skipRefresh) {
                console.log(`[huntarrUI] User switching from ${this.currentSection} to ${section}, refreshing page...`);
                // Store the target section in localStorage so we can navigate to it after refresh
                localStorage.setItem('huntarr-target-section', section);
                location.reload();
                return;
            } else {
                console.log(`[huntarrUI] Switching from ${this.currentSection} to ${section} without page refresh (app/editor navigation)`);
            }
        }

        // Stop stats polling when leaving home section
        if (window.HuntarrStats) window.HuntarrStats.stopPolling();

        // Cleanup on section switch
        if (this.currentSection === 'home' && window.CycleCountdown && typeof window.CycleCountdown.cleanup === 'function') {
            window.CycleCountdown.cleanup();
        }

        // Update active section
        this.elements.sections.forEach(s => {
            s.classList.remove('active');
            s.style.display = 'none';
        });

        // Additionally, make sure scheduling section is completely hidden
        if (section !== 'scheduling' && this.elements.schedulingSection) {
            this.elements.schedulingSection.style.display = 'none';
        }

        // Update navigation
        this.elements.navItems.forEach(item => {
            item.classList.remove('active');
        });

        // Show selected section
        let newTitle = 'Home'; // Default title
        if (section === 'home' && this.elements.homeSection) {
            this.elements.homeSection.classList.add('active');
            this.elements.homeSection.style.display = 'block';
            if (this.elements.homeNav) this.elements.homeNav.classList.add('active');
            newTitle = 'Home';
            this.currentSection = 'home';

            // Show main sidebar when returning to home
            this.showMainSidebar();

            // Disconnect logs if switching away from logs
            this.disconnectAllEventSources();

            // Check app connections when returning to home page to update status
            // This will call updateEmptyStateVisibility() after all checks complete
            this.checkAppConnections();
            // Load Swaparr status
            this.loadSwaparrStatus();
            // Refresh stats when returning to home section
            this.loadMediaStats();
            // Initialize view toggle and start live polling
            if (window.HuntarrStats) {
                window.HuntarrStats.initViewToggle();
                window.HuntarrStats.startPolling();
            }
            // Re-initialize cycle countdown when returning to home (cleanup stops it when leaving)
            if (window.CycleCountdown && typeof window.CycleCountdown.initialize === 'function') {
                window.CycleCountdown.initialize();
            }
            // Refresh home page content (re-check all settings, visibility, Smart Hunt)
            if (window.HomeRequestarr) {
                window.HomeRequestarr.refresh();
            }
            // Show welcome message on first visit (not during setup wizard)
            this._maybeShowWelcome();
        } else if (section === 'about') {
            // About removed — redirect to home
            this.switchSection('home'); return;
        } else if ((section === 'system' || section === 'hunt-manager' || section === 'logs') && document.getElementById('systemSection')) {
            // System section with sidebar sub-navigation (Hunt Manager, Logs)
            var systemSection = document.getElementById('systemSection');
            systemSection.classList.add('active');
            systemSection.style.display = 'block';

            // Determine which tab to show
            var activeTab = section === 'system' ? 'hunt-manager' : section;
            if (window.HuntarrNavigation) window.HuntarrNavigation.switchSystemTab(activeTab);

            // Set title based on active tab
            var tabTitles = { 'hunt-manager': 'Hunt Manager', 'logs': 'Logs' };
            newTitle = tabTitles[activeTab] || 'System';
            this.currentSection = section === 'system' ? 'hunt-manager' : section;

            // Expand System group in unified sidebar
            if (typeof expandSidebarGroup === 'function') expandSidebarGroup('sidebar-group-system');
            if (typeof setActiveNavItem === 'function') setActiveNavItem();

            // Initialize the active tab's module
            if (activeTab === 'hunt-manager') {
                if (typeof huntManagerModule !== 'undefined') huntManagerModule.refresh();
            } else if (activeTab === 'logs') {
                if (window.LogsModule && typeof window.LogsModule.setAppFilterContext === 'function') {
                    window.LogsModule.setAppFilterContext('system');
                }
                if (window.LogsModule && typeof window.LogsModule.updateDebugLevelVisibility === 'function') {
                    window.LogsModule.updateDebugLevelVisibility();
                }
                if (window.LogsModule) {
                    try {
                        if (window.LogsModule.initialized) { window.LogsModule.connectToLogs(); }
                        else { window.LogsModule.init(); }
                    } catch (error) { console.error('[huntarrUI] Error during LogsModule calls:', error); }
                }
            }
            // ── Tor Hunt sections ─────────────────────────────────────────
        } else if (section === 'requestarr' && document.getElementById('requestarr-section')) {
            document.getElementById('requestarr-section').classList.add('active');
            document.getElementById('requestarr-section').style.display = 'block';
            if (document.getElementById('requestarrNav')) document.getElementById('requestarrNav').classList.add('active');
            newTitle = 'Discover';
            this.currentSection = 'requestarr';

            // Switch to Requestarr sidebar
            this.showRequestarrSidebar();

            // Show discover view by default
            this.runWhenRequestarrReady('discover', () => {
                if (window.RequestarrDiscover && typeof window.RequestarrDiscover.switchView === 'function') {
                    window.RequestarrDiscover.switchView('discover');
                }
            });
        } else if (section === 'requestarr-discover' && document.getElementById('requestarr-section')) {
            document.getElementById('requestarr-section').classList.add('active');
            document.getElementById('requestarr-section').style.display = 'block';
            if (document.getElementById('requestarrDiscoverNav')) document.getElementById('requestarrDiscoverNav').classList.add('active');
            newTitle = 'Discover';
            this.currentSection = 'requestarr-discover';

            // Switch to Requestarr sidebar
            this.showRequestarrSidebar();

            // Show discover view
            this.runWhenRequestarrReady('discover', () => {
                if (window.RequestarrDiscover && typeof window.RequestarrDiscover.switchView === 'function') {
                    window.RequestarrDiscover.switchView('discover');
                }
            });
        } else if (section === 'requestarr-movies' && document.getElementById('requestarr-section')) {
            document.getElementById('requestarr-section').classList.add('active');
            document.getElementById('requestarr-section').style.display = 'block';
            if (document.getElementById('requestarrMoviesNav')) document.getElementById('requestarrMoviesNav').classList.add('active');
            this.showRequestarrSidebar();

            newTitle = 'Movies';
            this.currentSection = 'requestarr-movies';

            // Force movies view layout immediately
            const viewIds = [
                'requestarr-discover-view',
                'requestarr-movies-view',
                'requestarr-tv-view',
                'requestarr-hidden-view',
                'requestarr-smarthunt-view',
                'requestarr-options-view',
                'requestarr-users-view',
                'requestarr-bundles-view',
                'requestarr-requests-view',
                'requestarr-global-blacklist-view'
            ];
            viewIds.forEach((viewId) => {
                const view = document.getElementById(viewId);
                if (!view) return;
                view.classList.remove('active');
                view.style.display = 'none';
            });
            const moviesView = document.getElementById('requestarr-movies-view');
            if (moviesView) {
                moviesView.classList.add('active');
                moviesView.style.display = 'block';
            }

            // Show movies view
            this.runWhenRequestarrReady('movies', () => {
                if (window.RequestarrDiscover && typeof window.RequestarrDiscover.switchView === 'function') {
                    window.RequestarrDiscover.switchView('movies');
                }
            });
        } else if (section === 'requestarr-tv' && document.getElementById('requestarr-section')) {
            document.getElementById('requestarr-section').classList.add('active');
            document.getElementById('requestarr-section').style.display = 'block';
            if (document.getElementById('requestarrTVNav')) document.getElementById('requestarrTVNav').classList.add('active');
            newTitle = 'TV Shows';
            this.currentSection = 'requestarr-tv';

            // Switch to Requestarr sidebar
            this.showRequestarrSidebar();

            // Show TV view
            this.runWhenRequestarrReady('tv', () => {
                if (window.RequestarrDiscover && typeof window.RequestarrDiscover.switchView === 'function') {
                    window.RequestarrDiscover.switchView('tv');
                }
            });
        } else if ((section === 'requestarr-hidden' || section === 'requestarr-personal-blacklist') && document.getElementById('requestarr-section')) {
            document.getElementById('requestarr-section').classList.add('active');
            document.getElementById('requestarr-section').style.display = 'block';
            if (document.getElementById('requestarrPersonalBlacklistNav')) document.getElementById('requestarrPersonalBlacklistNav').classList.add('active');
            newTitle = 'Personal Blacklist';
            this.currentSection = 'requestarr-personal-blacklist';

            // Switch to Requestarr sidebar
            this.showRequestarrSidebar();

            // Show hidden view
            this.runWhenRequestarrReady('hidden', () => {
                if (window.RequestarrDiscover && typeof window.RequestarrDiscover.switchView === 'function') {
                    window.RequestarrDiscover.switchView('hidden');
                }
            });
        } else if (section === 'requestarr-smarthunt' && document.getElementById('requestarr-section')) {
            document.getElementById('requestarr-section').classList.add('active');
            document.getElementById('requestarr-section').style.display = 'block';
            if (document.getElementById('requestarrSmartHuntNav')) document.getElementById('requestarrSmartHuntNav').classList.add('active');
            newTitle = 'Smart Hunt';
            this.currentSection = 'requestarr-smarthunt';

            // Switch to Requestarr sidebar
            this.showRequestarrSidebar();

            // Show Smart Hunt view
            this.runWhenRequestarrReady('smarthunt', () => {
                if (window.RequestarrDiscover && typeof window.RequestarrDiscover.switchView === 'function') {
                    window.RequestarrDiscover.switchView('smarthunt');
                }
            });
        } else if ((section === 'requestarr-options' || section === 'requestarr-filters' || section === 'requestarr-settings' || section === 'requestarr-smarthunt-settings') && document.getElementById('requestarr-section')) {
            document.getElementById('requestarr-section').classList.add('active');
            document.getElementById('requestarr-section').style.display = 'block';
            if (document.getElementById('requestarrOptionsNav')) document.getElementById('requestarrOptionsNav').classList.add('active');
            newTitle = 'Options';
            this.currentSection = 'requestarr-options';

            // Switch to Requestarr sidebar
            this.showRequestarrSidebar();

            // Show consolidated options view
            this.runWhenRequestarrReady('options', () => {
                if (window.RequestarrDiscover && typeof window.RequestarrDiscover.switchView === 'function') {
                    window.RequestarrDiscover.switchView('options');
                }
            });
        } else if (section === 'requestarr-users' && document.getElementById('requestarr-section')) {
            document.getElementById('requestarr-section').classList.add('active');
            document.getElementById('requestarr-section').style.display = 'block';
            if (document.getElementById('requestarrUsersNav')) document.getElementById('requestarrUsersNav').classList.add('active');
            newTitle = 'Users';
            this.currentSection = 'requestarr-users';

            // Switch to Requestarr sidebar
            this.showRequestarrSidebar();

            // Show users view
            this.runWhenRequestarrReady('users', () => {
                if (window.RequestarrDiscover && typeof window.RequestarrDiscover.switchView === 'function') {
                    window.RequestarrDiscover.switchView('users');
                }
            });
        } else if (section === 'requestarr-bundles' && document.getElementById('requestarr-section')) {
            document.getElementById('requestarr-section').classList.add('active');
            document.getElementById('requestarr-section').style.display = 'block';
            if (document.getElementById('requestarrBundlesNav')) document.getElementById('requestarrBundlesNav').classList.add('active');
            newTitle = 'Bundles';
            this.currentSection = 'requestarr-bundles';

            // Switch to Requestarr sidebar
            this.showRequestarrSidebar();

            // Show bundles view
            this.runWhenRequestarrReady('bundles', () => {
                if (window.RequestarrDiscover && typeof window.RequestarrDiscover.switchView === 'function') {
                    window.RequestarrDiscover.switchView('bundles');
                }
            });
        } else if (section === 'requestarr-requests' && document.getElementById('requestarr-section')) {
            document.getElementById('requestarr-section').classList.add('active');
            document.getElementById('requestarr-section').style.display = 'block';
            if (document.getElementById('requestarrRequestsNav')) document.getElementById('requestarrRequestsNav').classList.add('active');
            newTitle = 'Requests';
            this.currentSection = 'requestarr-requests';

            // Switch to Requestarr sidebar
            this.showRequestarrSidebar();

            // Show requests view
            this.runWhenRequestarrReady('requests', () => {
                if (window.RequestarrDiscover && typeof window.RequestarrDiscover.switchView === 'function') {
                    window.RequestarrDiscover.switchView('requests');
                }
            });
        } else if (section === 'requestarr-global-blacklist' && document.getElementById('requestarr-section')) {
            document.getElementById('requestarr-section').classList.add('active');
            document.getElementById('requestarr-section').style.display = 'block';
            if (document.getElementById('requestarrGlobalBlacklistNav')) document.getElementById('requestarrGlobalBlacklistNav').classList.add('active');
            newTitle = 'Global Blacklist';
            this.currentSection = 'requestarr-global-blacklist';

            // Switch to Requestarr sidebar
            this.showRequestarrSidebar();

            // Show global blacklist view
            this.runWhenRequestarrReady('global-blacklist', () => {
                if (window.RequestarrDiscover && typeof window.RequestarrDiscover.switchView === 'function') {
                    window.RequestarrDiscover.switchView('global-blacklist');
                }
            });
        } else if (section === 'apps') {
            console.log('[huntarrUI] Apps section requested - redirecting to Sonarr by default');
            // Instead of showing apps dashboard, redirect to Sonarr
            this.switchSection('sonarr');
            window.location.hash = '#sonarr';
            return;
        } else if (section === 'sonarr' && document.getElementById('sonarrSection')) {
            document.getElementById('sonarrSection').classList.add('active');
            document.getElementById('sonarrSection').style.display = 'block';
            if (document.getElementById('appsSonarrNav')) document.getElementById('appsSonarrNav').classList.add('active');
            newTitle = 'Sonarr';
            this.currentSection = 'sonarr';

            // Switch to Apps sidebar
            this.showAppsSidebar();

            // Initialize app module for sonarr
            if (typeof appsModule !== 'undefined') {
                appsModule.init('sonarr');
            }
        } else if (section === 'radarr' && document.getElementById('radarrSection')) {
            document.getElementById('radarrSection').classList.add('active');
            document.getElementById('radarrSection').style.display = 'block';
            if (document.getElementById('appsRadarrNav')) document.getElementById('appsRadarrNav').classList.add('active');
            newTitle = 'Radarr';
            this.currentSection = 'radarr';

            // Switch to Apps sidebar
            this.showAppsSidebar();

            // Initialize app module for radarr
            if (typeof appsModule !== 'undefined') {
                appsModule.init('radarr');
            }
        } else if (section === 'lidarr' && document.getElementById('lidarrSection')) {
            document.getElementById('lidarrSection').classList.add('active');
            document.getElementById('lidarrSection').style.display = 'block';
            if (document.getElementById('appsLidarrNav')) document.getElementById('appsLidarrNav').classList.add('active');
            newTitle = 'Lidarr';
            this.currentSection = 'lidarr';

            // Switch to Apps sidebar
            this.showAppsSidebar();

            // Initialize app module for lidarr
            if (typeof appsModule !== 'undefined') {
                appsModule.init('lidarr');
            }
        } else if (section === 'readarr' && document.getElementById('readarrSection')) {
            document.getElementById('readarrSection').classList.add('active');
            document.getElementById('readarrSection').style.display = 'block';
            if (document.getElementById('appsReadarrNav')) document.getElementById('appsReadarrNav').classList.add('active');
            newTitle = 'Readarr';
            this.currentSection = 'readarr';

            // Switch to Apps sidebar
            this.showAppsSidebar();

            // Initialize app module for readarr
            if (typeof appsModule !== 'undefined') {
                appsModule.init('readarr');
            }
        } else if (section === 'whisparr' && document.getElementById('whisparrSection')) {
            document.getElementById('whisparrSection').classList.add('active');
            document.getElementById('whisparrSection').style.display = 'block';
            if (document.getElementById('appsWhisparrNav')) document.getElementById('appsWhisparrNav').classList.add('active');
            newTitle = 'Whisparr V2';
            this.currentSection = 'whisparr';

            // Switch to Apps sidebar
            this.showAppsSidebar();

            // Initialize app module for whisparr
            if (typeof appsModule !== 'undefined') {
                appsModule.init('whisparr');
            }
        } else if (section === 'eros' && document.getElementById('erosSection')) {
            document.getElementById('erosSection').classList.add('active');
            document.getElementById('erosSection').style.display = 'block';
            if (document.getElementById('appsErosNav')) document.getElementById('appsErosNav').classList.add('active');
            newTitle = 'Whisparr V3';
            this.currentSection = 'eros';

            // Switch to Apps sidebar
            this.showAppsSidebar();

            // Initialize app module for eros
            if (typeof appsModule !== 'undefined') {
                appsModule.init('eros');
            }
        } else if (section === 'swaparr' && document.getElementById('swaparrSection')) {
            document.getElementById('swaparrSection').classList.add('active');
            document.getElementById('swaparrSection').style.display = 'block';
            if (document.getElementById('appsSwaparrNav')) document.getElementById('appsSwaparrNav').classList.add('active');
            newTitle = 'Swaparr';
            this.currentSection = 'swaparr';

            // Show Apps sidebar (Swaparr lives under Apps)
            this.showAppsSidebar();

            // Initialize Swaparr section
            this.initializeSwaparr();
        } else if (section === 'settings' && document.getElementById('settingsSection')) {
            document.getElementById('settingsSection').classList.add('active');
            document.getElementById('settingsSection').style.display = 'block';
            newTitle = 'Settings';
            this.currentSection = 'settings';
            this.showSettingsSidebar();
            this.initializeSettings();
        } else if (section === 'settings-logs' && document.getElementById('settingsLogsSection')) {
            document.getElementById('settingsLogsSection').classList.add('active');
            document.getElementById('settingsLogsSection').style.display = 'block';
            newTitle = 'Log Settings';
            this.currentSection = 'settings-logs';
            this.showSettingsSidebar();
            this.initializeLogsSettings();
        } else if (section === 'scheduling' && document.getElementById('schedulingSection')) {
            document.getElementById('schedulingSection').classList.add('active');
            document.getElementById('schedulingSection').style.display = 'block';
            newTitle = 'Scheduling';
            this.currentSection = 'scheduling';
            this.showSettingsSidebar();
            if (typeof window.refreshSchedulingInstances === 'function') {
                window.refreshSchedulingInstances();
            }
        } else if (section === 'notifications' && document.getElementById('notificationsSection')) {
            document.getElementById('notificationsSection').classList.add('active');
            document.getElementById('notificationsSection').style.display = 'block';
            newTitle = 'Notifications';
            this.currentSection = 'notifications';
            this.showSettingsSidebar();
            this.initializeNotifications();
        } else if (section === 'backup-restore' && document.getElementById('backupRestoreSection')) {
            document.getElementById('backupRestoreSection').classList.add('active');
            document.getElementById('backupRestoreSection').style.display = 'block';
            newTitle = 'Backup / Restore';
            this.currentSection = 'backup-restore';
            this.showSettingsSidebar();
            this.initializeBackupRestore();
        } else if (section === 'prowlarr' && document.getElementById('prowlarrSection')) {
            document.getElementById('prowlarrSection').classList.add('active');
            document.getElementById('prowlarrSection').style.display = 'block';
            if (document.getElementById('appsProwlarrNav')) document.getElementById('appsProwlarrNav').classList.add('active');
            newTitle = 'Prowlarr';
            this.currentSection = 'prowlarr';

            // Switch to Apps sidebar for prowlarr
            this.showAppsSidebar();

            // Initialize prowlarr settings if not already done
            this.initializeProwlarr();
        } else if (section === 'user' && document.getElementById('userSection')) {
            document.getElementById('userSection').classList.add('active');
            document.getElementById('userSection').style.display = 'block';
            newTitle = 'User';
            this.currentSection = 'user';
            this.showSettingsSidebar();
            this.initializeUser();
        } else if (section === 'instance-editor' && document.getElementById('instanceEditorSection')) {
            document.getElementById('instanceEditorSection').classList.add('active');
            document.getElementById('instanceEditorSection').style.display = 'block';
            this.currentSection = 'instance-editor';
            if (window.SettingsForms && window.SettingsForms._currentEditing && window.SettingsForms._currentEditing.appType === 'indexer') {
                var inst = window.SettingsForms._currentEditing.originalInstance || {};
                var preset = (inst.preset || 'manual').toString().toLowerCase().trim();
                newTitle = (window.SettingsForms.getIndexerPresetLabel && window.SettingsForms.getIndexerPresetLabel(preset)) ? (window.SettingsForms.getIndexerPresetLabel(preset) + ' Indexer Editor') : 'Indexer Editor';
                this.showMainSidebar();
            } else if (window.SettingsForms && window.SettingsForms._currentEditing && window.SettingsForms._currentEditing.appType === 'client') {
                var ct = (window.SettingsForms._currentEditing.originalInstance && window.SettingsForms._currentEditing.originalInstance.type) ? String(window.SettingsForms._currentEditing.originalInstance.type).toLowerCase() : 'manual';
                newTitle = (ct === 'qbittorrent' ? 'qBittorrent' : ct) + ' Connection Settings';
                this.showMainSidebar();
            } else {
                var appName = 'Instance Editor';
                if (window.SettingsForms && window.SettingsForms._currentEditing && window.SettingsForms._currentEditing.appType) {
                    var appType = window.SettingsForms._currentEditing.appType;
                    appName = appType.charAt(0).toUpperCase() + appType.slice(1);
                }
                newTitle = appName;
                this.showAppsSidebar();
            }
        } else {
            // Default to home if section is unknown or element missing
            if (this.elements.homeSection) {
                this.elements.homeSection.classList.add('active');
                this.elements.homeSection.style.display = 'block';
            }
            if (this.elements.homeNav) this.elements.homeNav.classList.add('active');
            newTitle = 'Home';
            this.currentSection = 'home';

            // Show main sidebar
            this.showMainSidebar();
        }

        // Disconnect logs when switching away from logs section
        if (this.currentSection !== 'logs' && window.LogsModule) {
            window.LogsModule.disconnectAllEventSources();
        }

        // Update the page title
        const pageTitleElement = document.getElementById('currentPageTitle');
        if (pageTitleElement) {
            pageTitleElement.textContent = newTitle;
            // Also update mobile page title
            if (typeof window.updateMobilePageTitle === 'function') {
                window.updateMobilePageTitle(newTitle);
            }
        } else {
            console.warn("[huntarrUI] currentPageTitle element not found during section switch.");
        }
    },

});
