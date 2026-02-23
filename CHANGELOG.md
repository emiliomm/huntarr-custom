# Huntarr v9.4.1 — Changelog

This release is a massive overhaul of Huntarr — the architecture has been simplified by removing SABnzbd/NZBGet in favor of the built-in NZB Hunt, the entire UI has been modernized with a premium glassmorphism design, and powerful new automation features like Disk Space Pause and Search Order Toggle give you smarter control over your media hunting. Security has been hardened, the menu system has been rebuilt from scratch, and the Requestarr experience is now on par with standalone apps like Overseerr.

- 🔀 **Search Order Toggle** — Choose how missing items are searched: Random, Newest First, or Oldest First. Sorted by release/air date so you control what gets grabbed first.
- 💾 **Disk Space Pause** — Huntarr now reads disk space from your *arr apps before each cycle and automatically pauses hunting when any root folder drops below your configured threshold. Set to 0 to disable.
- 🎛️ **Per-User Smart Filters** — Completely rebuilt filter system with auto-save, keyword blacklists, content rating dropdowns, and per-user preferences that persist across sessions and devices.
- 🏗️ **Simplified Architecture** — Removed SABnzbd, NZBGet, and the download clients page entirely. NZB Hunt and Index Master handle everything natively with zero external dependencies.
- 🎨 **Premium UI Modernization** — Full glassmorphism redesign across Requestarr, Smart Hunt, menus, and settings. Rigid multi-grid layout system, infinite scroll, animated cards, and frosted glass styling throughout.
- 📦 **Request Bundles** — Group multiple instances (e.g., 1080p + 4K Radarr) into a single bundle. One request hits all bundled instances simultaneously with fault-tolerant cascading.
- 🔒 **Security Hardening** — Non-owner users are now fully isolated to only their allowed actions. Users can self-manage passwords, 2FA, and Plex account linking from their own profile.
- 🔗 **IMDB & TMDB Links** — Advanced request pages now include direct links to IMDB and TMDB so users can research titles before requesting. TV shows now display full metadata (network, seasons, episode count).
- 📡 **New Notification Providers** — Added Gotify, Ntfy, and LunaSea alongside existing Discord, Telegram, Pushover, Email, and Apprise support.
- 🌐 **Proxy Support & External URLs** — Route outbound traffic through HTTP/SOCKS4/SOCKS5 proxies, and configure separate internal vs. external URLs for your *arr apps.
