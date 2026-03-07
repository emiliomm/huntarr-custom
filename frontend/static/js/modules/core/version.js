/**
 * Version & Info Module
 * Handles version checking, GitHub stars, and user info display
 */

window.HuntarrVersion = {
    loadCurrentVersion: function () {
        HuntarrUtils.fetchWithTimeout('./version.txt')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load version.txt');
                }
                return response.text();
            })
            .then(version => {
                // Store in localStorage for sidebar footer display
                try {
                    const versionInfo = localStorage.getItem('huntarr-version-info') || '{}';
                    const parsedInfo = JSON.parse(versionInfo);
                    parsedInfo.currentVersion = version.trim();
                    localStorage.setItem('huntarr-version-info', JSON.stringify(parsedInfo));
                } catch (e) {
                    console.error('Error saving current version to localStorage:', e);
                }
            })
            .catch(error => {
                console.error('Error loading current version:', error);
            });
    },

    // Removed loadLatestVersion, loadBetaVersion, and loadGitHubStarCount

    loadUsername: function () {
        HuntarrUtils.fetchWithTimeout('./api/user/info')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch user info');
                }
                return response.json();
            })
            .then(data => {
                const usernameElement = document.getElementById('username');
                if (usernameElement && data.username) {
                    usernameElement.textContent = data.username;
                    // Store username in localStorage for reference
                    localStorage.setItem('huntarr-username', data.username);
                }

                // Check local access bypass status after loading username
                if (window.HuntarrAuth) {
                    window.HuntarrAuth.checkLocalAccessBypassStatus();
                }
            })
            .catch(error => {
                console.error('Error loading username:', error);

                // Still check local access bypass status even if username loading failed
                if (window.HuntarrAuth) {
                    window.HuntarrAuth.checkLocalAccessBypassStatus();
                }
            });
    }
};
