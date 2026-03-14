/**
 * Huntarr - Card Hover Effects
 * Adds subtle hover animations to app cards
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects to app cards
    const appCards = document.querySelectorAll('.app-stats-card');
    
    appCards.forEach(card => {
        // Add transition properties
        card.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease, filter 0.3s ease';
        
        // Mouse enter event - elevate and highlight card
        card.addEventListener('mouseenter', function() {
            card.style.transform = 'translateY(-5px) scale(1.02)';
            card.style.boxShadow = '0 8px 24px var(--ui-shadow)';
            card.style.filter = 'brightness(1.1)';
            
            // Get app type from classes
            const appType = getAppType(card);
            if (appType) {
                // Add app-specific glow effect
                const glowColors = {
                    'sonarr': '0 0 15px var(--card-hover-effects-color-1)',
                    'radarr': '0 0 15px var(--card-hover-effects-color-2)',
                    'lidarr': '0 0 15px var(--card-hover-effects-color-3)',
                    'readarr': '0 0 15px var(--card-hover-effects-color-4)',
                    'whisparr': '0 0 15px var(--card-hover-effects-color-5)',
                    'eros': '0 0 15px var(--card-hover-effects-color-6)'
                };
                
                if (glowColors[appType]) {
                    card.style.boxShadow += ', ' + glowColors[appType];
                }
            }
        });
        
        // Mouse leave event - return to normal
        card.addEventListener('mouseleave', function() {
            card.style.transform = 'translateY(0) scale(1)';
            card.style.boxShadow = '';
            card.style.filter = 'brightness(1)';
        });
    });
    
    // Helper function to get app type from card classes
    function getAppType(card) {
        const classList = card.classList;
        const appTypes = ['sonarr', 'radarr', 'lidarr', 'readarr', 'whisparr', 'eros', 'swaparr'];
        
        for (const type of appTypes) {
            if (classList.contains(type)) {
                return type;
            }
        }
        
        return null;
    }
});
