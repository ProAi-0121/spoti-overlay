# Security Policy

## Reporting a vulnerability

If you discover a security issue in this project, please report it privately instead of opening a public issue.

**How to report:**

- **GitHub:** Use the repository's [private security advisory](https://github.com/ProAi-0121/spoti-overlay/security/advisories/new) feature (recommended if available).
- **Maintainer placeholder:** Provide a private channel to the maintainer once contacted.

> If a maintainer contact email is not listed here yet, use the private security advisory above, or open a normal issue if a direct contact channel is unavailable.

## Scope

Please do **not** disclose confirmed or suspected vulnerabilities publicly until they have been reviewed and, where relevant, fixed.

## Security notes for users

- **`.env` contains sensitive Spotify credentials.** It is git-ignored; never commit or share it.
- The `.cache-{username}` file created by Spotipy stores your OAuth token. Treat it as a secret and do not commit it.
- If you ever believe a credential was exposed (e.g., committed or shared), **revoke/rotate it** immediately in your [Spotify dashboard](https://developer.spotify.com/dashboard) and in any affected token stores.