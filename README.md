> [!IMPORTANT]
> This is a fork of the repo formerly at plexguide/huntarr.io, ater the original author (Admin9705) disappeared when significant security vulnerabilities were found.
>
> 
> Git mirror imported from https://git.aronwk.com/mirror/Huntarr



<h1 align="center">Huntarr</h1>

<p align="center">
  <img src="frontend/static/logo/128.png" alt="Huntarr Logo" width="100" height="100">
</p>

  A media automation platform that goes beyond the *arr ecosystem. Huntarr hunts for missing content and quality upgrades across your existing Sonarr, Radarr, Lidarr, Readarr, and Whisparr instances.
</p>

---

## Table of Contents

- [What Huntarr Does](#what-huntarr-does)
- [Third-Party *arr Support](#third-party-arr-support)
- [Prowlarr Integration](#prowlarr-integration)
- [Requestarr](#requestarr)
- [Add to Library](#add-to-library)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [The Classic](#the-classic)
- [Other Projects](#other-projects)
- [Huntarr + Cleanuparr](#huntarr--cleanuparr)
- [Contributors](#contributors)
- [Change Log](#change-log)
- [License](#license)

---

## What Huntarr Does

Your *arr apps monitor RSS feeds for new releases — but they don't go back and actively search for content already missing from your library. Over time, gaps build up: missing seasons, albums with holes in them, movies stuck below your quality cutoff. Nobody fixes it automatically.

**Huntarr does.** It systematically scans your entire library, identifies all missing content, and searches for it in small, indexer-safe batches that won't get you rate-limited or banned. It also finds content below your quality cutoff and triggers upgrades automatically — completely hands-off.

Beyond missing-content hunting, Huntarr includes built-in modules that complement your existing stack:

| Module | What It Does |
|--------|-------------|
| **Prowlarr** | Huntarr connects to your external Prowlarr instance for centralized indexer management |
| **Requestarr** | A media request system with user accounts, approval queues, bundles, and per-user permissions |

The core philosophy: **third-party *arr support is always first-class.** You can use Huntarr's built-in modules, your existing *arr apps, or both simultaneously. Nothing is forced — every module is optional and independently configurable.

---

## Third-Party *arr Support

Huntarr connects to your existing *arr stack and works alongside it. Add multiple instances of the same app and Huntarr hunts across all of them simultaneously, with independent schedules and caps per instance.

| Sonarr | Radarr | Lidarr | Readarr | Whisparr v2 | Whisparr v3 |
|:------:|:------:|:------:|:-------:|:-----------:|:-----------:|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

<p align="center">
  <img src="docs/readme/ThirdParty.jpg" alt="Third-Party App Connections" width="800">
</p>

Each app connection supports:
- **Missing content hunting** — finds and searches for anything your *arr hasn't picked up yet
- **Quality upgrades** — finds items below your quality cutoff and hunts better versions
- **Multiple instances** — run separate Sonarr instances for 1080p and 4K, each with its own hunt schedule
- **API rate management** — configurable hourly caps per instance so you never overwhelm your indexers

---

## Prowlarr Integration

Huntarr integrates seamlessly with external **Prowlarr** instances. Prowlarr is the recommended tool for managing your indexers across the *arr ecosystem.

**Key benefits:**
- Centralized management of Usenet and torrent indexers
- Automatic syncing of indexers to all your *arr instances
- Proxy support and advanced filtering
- Connection testing and health monitoring

---

## Requestarr

A complete media request platform built into Huntarr. Users can discover and request movies and TV shows, requests flow through an owner-controlled approval queue, and approved content is automatically added to the appropriate library.

**Key features:**
- **User accounts** — invite users with per-user permissions and category assignments
- **Approval queue** — owners review and approve or deny requests before anything is added
- **Auto-approve** — grant trusted users instant approval so requests go straight through
- **Bundles** — group multiple instances together so a single request sends to all of them simultaneously; member failures are non-fatal and the system moves on automatically
- **Requestarr works with everything** — Sonarr, Radarr, or any combination
- **Plex integration** — optional Plex SSO lets users log in with their Plex accounts

<p align="center">
  <img src="docs/readme/Requests.jpg" alt="Requestarr" width="800">
</p>

---

## Add to Library

Add new movies and TV shows in seconds. Search by title, pick your instance and quality profile, choose a root folder, and send it straight to your library — whether that's through Sonarr, Radarr, or a bundle that hits all of them at once.

<p align="center">
  <img src="docs/readme/AddToLibrary.jpg" alt="Add to Library" width="800">
</p>

---

## How It Works

1. **Connect** — Point Huntarr at your Sonarr, Radarr, Lidarr, Readarr, or Whisparr instances
2. **Hunt Missing** — Scans your entire library for content that's monitored but not downloaded, then searches your indexers in small, safe batches
3. **Hunt Upgrades** — Identifies items that exist but fall below your quality cutoff, then triggers upgrade searches automatically
4. **Smart Rate Management** — Configurable per-instance hourly search caps, automatic pause when download queues are full, and restart delay management to avoid indexer bans
5. **Notifications** — Sends alerts via Discord, Telegram, Pushover, Email, and more when Huntarr grabs something or completes a cycle
6. **Repeat** — Waits for your configured interval, then starts the next cycle. Completely hands-off, continuous library improvement

---

## Installation

Huntarr is built with Python and can be run from source on Windows, Linux, and macOS.

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/emiliomm/huntarr-custom.git
   cd huntarr-custom
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Huntarr:**
   ```bash
   python main.py
   ```

### Volume & Environment Reference

| Variable | Required | Purpose |
|----------|----------|---------|
| `HUNTARR_CONFIG_DIR` | No | Persistent config, database, and settings (default: `%APPDATA%/Huntarr` on Windows, `~/.config/Huntarr` on Linux) |
| `TZ` | No | Timezone for scheduling and logs (e.g. `America/New_York`, default: `UTC`) |
| `HUNTARR_PORT` | No | Port to run the web server on (default: `9705`) |

Once running, open your browser to `http://localhost:9705`.

For full documentation, visit the [Huntarr Docs](https://emiliomm.github.io/huntarr-custom/).

---

## The original

Special thanks to the original author, Admin9705, for creating this project.

<p align="center">
  <img src="docs/readme/OldSchool.png" alt="The Original" width="800">
</p>

---

## Huntarr + Cleanuparr

<p align="center">
  <img src="frontend/static/logo/128.png" alt="Huntarr" width="64" height="64">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://github.com/cleanuparr/cleanuparr/blob/main/Logo/128.png?raw=true" alt="Cleanuparr" width="64" height="64">
</p>

Huntarr fills your library. [Cleanuparr](https://github.com/cleanuparr/cleanuparr) protects it.

While Huntarr is out hunting for missing content and upgrading quality, Cleanuparr watches your download queue like a hawk — removing stalled downloads, blocking malicious files, and cleaning up the clutter that builds up over time. One brings content in, the other makes sure only clean downloads get through.

Together they form a self-sustaining media automation loop: Huntarr searches, Cleanuparr filters, and your library grows with zero manual intervention.

[![Cleanuparr on GitHub](https://img.shields.io/github/stars/cleanuparr/cleanuparr?style=flat-square&label=Cleanuparr&logo=github)](https://github.com/cleanuparr/cleanuparr)

---

## Change Log

Visit the [Releases](https://github.com/emiliomm/huntarr-custom/releases/) page.

## License

Licensed under the [GNU General Public License v3.0](https://github.com/emiliomm/huntarr-custom/blob/main/LICENSE).
