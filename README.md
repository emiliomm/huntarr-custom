> [!IMPORTANT]
> This is an archive of the repo formerly at plexguide/huntarr.io. It is preserved for posterity after the original author went scorched earth when significant security vulnerabilities were pointed out to them.
>
> **THIS REPO IS NOT UNDER ACTIVE DEVELOPMENT. USE THIS CODE AT YOUR OWN RISK!**
> 
> Discussion: [Reddit: The Huntarr Github page has been taken down](https://www.reddit.com/r/selfhosted/comments/1rcmgnn/) ([Archive link](https://archive.is/rKnQb))
> 
> Git mirror imported from https://git.aronwk.com/mirror/Huntarr

> [!CAUTION]
> Significant security vulnerabilites have been reported with this code.
> 
> See: [Reddit: Huntarr - Your passwords and your entire arr stack's API keys are exposed to anyone on your network, or worse, the internet.](https://www.reddit.com/r/selfhosted/comments/1rckopd/huntarr_your_passwords_and_your_entire_arr_stacks/) ([Archive link](https://archive.is/Tn5pu))


<h1 align="center">Huntarr</h1>

<p align="center">
  <img src="frontend/static/logo/128.png" alt="Huntarr Logo" width="100" height="100">
</p>

<p align="center">
  A media automation platform that goes beyond the *arr ecosystem. Huntarr hunts for missing content and quality upgrades across your existing Sonarr, Radarr, Lidarr, Readarr, and Whisparr instances — while also providing its own built-in Movie Hunt, TV Hunt, Index Master, NZB Hunt, and Requestarr modules that can replace or complement your existing stack.
</p>

<p align="center">
  <a href="https://hub.docker.com/r/huntarr/huntarr"><img src="https://img.shields.io/docker/pulls/huntarr/huntarr?style=flat-square&label=Docker%20Pulls" alt="Docker Pulls"></a>
  <a href="https://github.com/plexguide/Huntarr.io/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-blue?style=flat-square" alt="License"></a>
  <a href="https://discord.com/invite/PGJJjR5Cww"><img src="https://img.shields.io/discord/1370922258247454821?color=7289DA&label=Discord&style=flat-square&logo=discord" alt="Discord"></a>
</p>

<p align="center">
  <a href="https://github.com/plexguide/Huntarr.io/stargazers"><img src="https://img.shields.io/github/stars/plexguide/Huntarr.io?style=social&label=Star%20Huntarr" alt="GitHub Stars"></a>
</p>

<h2 align="center">Stars help others discover Huntarr — if you find it useful, click the ⭐ in the upper-right corner!</h2>

---

## Support — Building My Daughter's Future

My 12-year-old daughter loves singing, dancing, and exploring STEM. She's an A-B honor roll student with big dreams. Any donation you make goes directly toward her college fund, helping her turn those dreams into reality. Thank you sincerely for your support!

[![Donate with PayPal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/donate?hosted_button_id=58AYJ68VVMGSC)

---

> **🚀 HuntarrOS is here.** Rebuilt from the ground up for 2026 — a self-hosted server management platform running as a single Docker container. App store, Cloudflare Tunnels, Traefik, MergerFS drive pooling, backups, and more. One-line install on Ubuntu & Debian.
>
> [![HuntarrOS on GitHub](https://img.shields.io/github/stars/plexguide/PlexGuide.com?style=social&label=HuntarrOS)](https://github.com/plexguide/PlexGuide.com) — https://HuntarrOS.com

---

<p align="center">
  <img src="docs/readme/Main.jpg" alt="Huntarr Dashboard" width="800">
</p>

---

## Table of Contents

- [What Huntarr Does](#what-huntarr-does)
- [Third-Party *arr Support](#third-party-arr-support)
- [Movie Hunt & TV Hunt](#movie-hunt--tv-hunt)
- [Index Master](#index-master)
- [NZB Hunt](#nzb-hunt)
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

Beyond missing-content hunting, Huntarr now includes a full suite of built-in modules that can replace parts of your stack entirely or run alongside what you already have:

| Module | What It Does |
|--------|-------------|
| **Movie Hunt** | A built-in movie management system with its own indexers, download clients, and discovery UI — no Radarr required |
| **TV Hunt** | A built-in TV show management system — track series, seasons, and episodes without needing Sonarr |
| **Index Master** | Manage and search your Usenet and torrent indexers directly inside Huntarr — a full Prowlarr alternative |
| **NZB Hunt** | A complete Usenet download client with multi-server support, speed limiting, direct unpack, and a full queue UI |
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

## Movie Hunt & TV Hunt

Browse, discover, and manage your media collection with a full visual interface. Movie Hunt and TV Hunt are built-in alternatives to Radarr and Sonarr — see what's in your library, what's missing, and what needs upgrading, all in one place.

**Key capabilities:**
- Visual discovery interface — browse trending, popular, and upcoming titles
- Library management — add, track, and monitor your collection
- Quality profiles — define your preferred formats, resolutions, and cutoffs
- Root folder management — configure where media lands on disk
- Direct import — detect files already on disk and import them without re-downloading
- Requestarr integration — users can request content that flows through your approval queue

Use Movie Hunt and TV Hunt standalone, or alongside your existing Radarr/Sonarr instances. They share indexer and download client configuration through Index Master and NZB Hunt.

<p align="center">
  <img src="docs/readme/MediaHunt.jpg" alt="Movie Hunt & TV Hunt" width="800">
</p>

---

## Index Master

Manage your indexers directly inside Huntarr. Add Usenet and torrent indexers, test connections, configure API keys, and search across all of them — no separate Prowlarr instance required. Index Master feeds into both the built-in Movie Hunt / TV Hunt modules and the third-party *arr hunting engine.

**Supports:**
- Newznab-compatible Usenet indexers
- Torznab-compatible torrent indexers
- Per-indexer API key and rate limit management
- Connection testing and health status

---

## NZB Hunt

A full Usenet download client built directly into Huntarr. Connect your NNTP servers and download NZBs without installing SABnzbd, NZBGet, or any other download manager.

**Features:**
- Multi-server NNTP connections with up to 120 simultaneous threads
- Direct unpack — extracts RAR archives while downloading, not after
- PAR2 verification and repair for corrupted downloads
- Encrypted RAR detection with configurable action (abort by default on new installs)
- Speed limiting with per-server bandwidth tracking
- Full queue management — pause, resume, prioritize, remove
- Categories — automatic folder organization by movie/TV instance
- Duplicate detection — smart and identical download prevention
- Download history with per-server bandwidth statistics

<p align="center">
  <img src="docs/readme/NZBHunt.jpg" alt="NZB Hunt" width="800">
</p>

---

## Requestarr

A complete media request platform built into Huntarr. Users can discover and request movies and TV shows, requests flow through an owner-controlled approval queue, and approved content is automatically added to the appropriate library.

**Key features:**
- **User accounts** — invite users with per-user permissions and category assignments
- **Approval queue** — owners review and approve or deny requests before anything is added
- **Auto-approve** — grant trusted users instant approval so requests go straight through
- **Bundles** — group multiple instances together so a single request sends to all of them simultaneously; member failures are non-fatal and the system moves on automatically
- **Requestarr works with everything** — Movie Hunt, TV Hunt, Sonarr, Radarr, or any combination
- **Plex integration** — optional Plex SSO lets users log in with their Plex accounts

<p align="center">
  <img src="docs/readme/Requests.jpg" alt="Requestarr" width="800">
</p>

---

## Add to Library

Add new movies and TV shows in seconds. Search by title, pick your instance and quality profile, choose a root folder, and send it straight to your library — whether that's through Movie Hunt, TV Hunt, Sonarr, Radarr, or a bundle that hits all of them at once.

Huntarr even detects if files are already sitting on disk and lets you import them directly without re-downloading.

<p align="center">
  <img src="docs/readme/AddToLibrary.jpg" alt="Add to Library" width="800">
</p>

---

## How It Works

1. **Connect** — Point Huntarr at your Sonarr, Radarr, Lidarr, Readarr, or Whisparr instances (or configure the built-in Movie Hunt / TV Hunt modules)
2. **Hunt Missing** — Scans your entire library for content that's monitored but not downloaded, then searches your indexers in small, safe batches
3. **Hunt Upgrades** — Identifies items that exist but fall below your quality cutoff, then triggers upgrade searches automatically
4. **Smart Rate Management** — Configurable per-instance hourly search caps, automatic pause when download queues are full, and restart delay management to avoid indexer bans
5. **Notifications** — Sends alerts via Discord, Telegram, Pushover, Email, and more when Huntarr grabs something or completes a cycle
6. **Repeat** — Waits for your configured interval, then starts the next cycle. Completely hands-off, continuous library improvement

---

## Installation

### Docker (Recommended)

```bash
docker run -d \
  --name huntarr \
  --restart unless-stopped \
  -p 9705:9705 \
  -v /path/to/config:/config \
  -v /path/to/media:/media       # Optional — for Movie Hunt / TV Hunt library access \
  -v /path/to/downloads:/downloads # Optional — for NZB Hunt download output \
  -e TZ=America/New_York \
  huntarr/huntarr:latest
```

### Docker Compose

```yaml
services:
  huntarr:
    image: huntarr/huntarr:latest
    container_name: huntarr
    restart: unless-stopped
    ports:
      - "9705:9705"
    volumes:
      - /path/to/config:/config
      - /path/to/media:/media           # Optional — for Movie Hunt / TV Hunt library access
      - /path/to/downloads:/downloads   # Optional — for NZB Hunt download output
    environment:
      - TZ=America/New_York
      - PUID=1000    # Optional — run as specific user ID (default: 0 = root)
      - PGID=1000    # Optional — run as specific group ID (default: 0 = root)
```

### Volume & Environment Reference

| Path / Variable | Required | Purpose |
|----------------|----------|---------|
| `/config` | **Yes** | Persistent config, database, logs, and settings |
| `/media` | No | Media library root — required for Movie Hunt / TV Hunt root folders |
| `/downloads` | No | Download directory — required for NZB Hunt (temp and complete folders live here) |
| `TZ` | No | Timezone for scheduling and logs (e.g. `America/New_York`, default: `UTC`) |
| `PUID` | No | User ID to run as. Unraid: `99`, Linux: `1000`, default: `0` (root) |
| `PGID` | No | Group ID to run as. Unraid: `100`, Linux: `1000`, default: `0` (root) |

### More Installation Methods

- [Unraid Installation](https://plexguide.github.io/Huntarr.io/getting-started/installation.html#unraid-installation)
- [Windows Installation](https://plexguide.github.io/Huntarr.io/getting-started/installation.html#windows-installation)
- [macOS Installation](https://plexguide.github.io/Huntarr.io/getting-started/installation.html#macos-installation)
- [Linux Installation](https://plexguide.github.io/Huntarr.io/getting-started/installation.html#linux-installation)

Once running, open your browser to `http://<your-server-ip>:9705`.

For full documentation, visit the [Huntarr Docs](https://plexguide.github.io/Huntarr.io/).

---

## The Classic

For those who remember where it all started — a bash script that simply asked Sonarr and Radarr to go looking.

<p align="center">
  <img src="docs/readme/OldSchool.png" alt="The Original" width="800">
</p>

---

## Other Projects

- [HuntarrOS](https://github.com/plexguide/PlexGuide.com) — Self-hosted server management platform with Docker app store, reverse proxies, and MergerFS — https://HuntarrOS.com
- [Seekandwatch](https://github.com/softerfish/seekandwatch) — A streamlined media discovery and watchlist tool for finding and tracking content across your media stack
- [Unraid Intel ARC Deployment](https://github.com/plexguide/Unraid_Intel-ARC_Deployment) — Convert videos to AV1 format using Intel ARC GPUs on Unraid

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

## Contributors

<a href="https://github.com/plexguide/Huntarr.io/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=plexguide/Huntarr.io" alt="Contributors" />
</a>

## Change Log

Visit the [Releases](https://github.com/plexguide/Huntarr.io/releases/) page.

## License

Licensed under the [GNU General Public License v3.0](https://github.com/plexguide/Huntarr.io/blob/main/LICENSE).
