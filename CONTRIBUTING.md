# Contributing

Thanks for your interest in improving **Spoti Overlay**! Please keep contributions focused and consistent with the project's existing style.

## Setup

```bash
git clone https://github.com/ProAi-0121/spoti-overlay.git
cd spoti-overlay
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create your `.env` from `.env.example` and fill in your Spotify credentials:

```bash
copy .env.example .env
```

## Development

- The entry point is `spoti.py`.
- Keep changes minimal and preserve the existing architecture (this is a small, focused utility, not a large framework app).
- Never commit `.env` or any tokens/cache files — they are already ignored via `.gitignore`.
- Avoid scope creep: prefer targeted fixes over large refactors.

## Testing

Currently there is no automated test suite. Before submitting a change, make sure the app still starts without errors:

```bash
python spoti.py
```

## Branches & pull requests

1. Create a branch for your work:
   ```bash
   git checkout -b my-feature
   ```
2. Make your changes and commit them with clear, descriptive messages.
3. Push the branch and open a pull request against `main`.
4. In the PR description, explain what the change does and why it is needed.