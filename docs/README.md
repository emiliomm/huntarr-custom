# Huntarr Documentation

This is the documentation site for [Huntarr](https://github.com/emiliomm/huntarr-custom), served via GitHub Pages at [emiliomm.github.io/huntarr-custom](https://emiliomm.github.io/huntarr-custom/).

## Site Structure

```
docs/
├── index.html                    # Welcome / landing page
├── css/main.css                  # Shared stylesheet for all pages
├── js/main.js                    # Shared JavaScript (sidebar, back-to-top, mobile nav)
├── images/                       # Logo and app icons
│   ├── huntarr-logo.png
│   └── admin9705.png
├── getting-started/
│   ├── installation.html         # Docker, Unraid, Windows, macOS, Linux, source install
│   ├── setup-wizard.html         # First-launch setup wizard walkthrough
│   └── first-steps.html          # Post-install guide — connect apps, schedule, notify
├── apps/
│   └── index.html                # 3rd Party Apps (Sonarr, Radarr, Lidarr, Readarr, Whisparr)
├── requestarr/
│   └── index.html                # Requestarr — user requests, approval queue, bundles
├── settings/
│   ├── index.html                # Main settings overview
│   ├── scheduling.html           # Hunt intervals, caps, and cycle settings
│   ├── notifications.html        # Discord, Telegram, Pushover, Email, Apprise
│   ├── backup-restore.html       # Automatic and manual backups
│   ├── log-settings.html         # Log level, retention, and export
│   └── user-account.html         # Password, 2FA, Plex SSO
├── system/
│   ├── hunt-manager.html         # Manual hunt triggers, per-instance controls
│   ├── logs.html                 # Log viewer and filtering
│   └── api.html                  # REST API reference
└── help/
    ├── faq.html                  # Frequently asked questions and troubleshooting
```

## Development

This is a plain HTML static site — no build step required. Open any HTML file directly in a browser or serve locally:

```bash
cd docs
python3 -m http.server 8000
```

Then visit http://localhost:8000.

## Adding or Editing Pages

Every page shares the same sidebar navigation. The sidebar is duplicated in each HTML file (no server-side includes in a static site). When adding a new page or renaming an existing one:

1. Add the new `<a href="...">` entry to the sidebar in **every** HTML file.
2. Mark the current page's link with `class="active"` in the sidebar for that page.
3. Use relative paths (`../` prefix for pages one level deep, e.g. `getting-started/`).

## Important Links Preserved

The following URLs must not change — they are referenced in external documentation, Discord, and the README.md:

| Purpose | URL |
|---------|-----|
| Installation | `https://emiliomm.github.io/huntarr-custom/getting-started/installation.html` |
| Unraid install | `https://emiliomm.github.io/huntarr-custom/getting-started/installation.html#unraid-installation` |
| Windows install | `https://emiliomm.github.io/huntarr-custom/getting-started/installation.html#windows-installation` |
| macOS install | `https://emiliomm.github.io/huntarr-custom/getting-started/installation.html#macos-installation` |
| Linux install | `https://emiliomm.github.io/huntarr-custom/getting-started/installation.html#linux-installation` |

## GitHub Pages

The site deploys automatically from the `docs/` folder on the main branch. The `.nojekyll` file ensures GitHub Pages serves files as-is without Jekyll processing.
