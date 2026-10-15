# AGENTS.md

Notes for AI agents (and humans) working in this repo. Read alongside
**`CLAUDE.md`** — that file is the fork's project memory (auto-loaded each
session) and already records architecture, past decisions, and operational
gotchas; do **not** re-litigate anything decided there.

## Stack

- **Backend:** Django 6.1, DRF 3.18, `oauth2_provider` (OIDC), Redis (cache + RQ),
  per-app "parameters registry" (`modoboa/parameters/tools.py`). Python
  3.12–3.14 (`pyproject.toml`; CI and production on 3.14). Versioning via `setuptools_scm`
  (`modoboa/version.py`); local builds report something like `2.9.1+sintraN`.
- **Frontend:** Vue 3 + Vuetify 4, Vite 8 (Rolldown), Module Federation
  (`@module-federation/vite`), `vue3-gettext`, Pinia, vue-router, axios, OIDC
  via `oidc-client-ts`. **Yarn classic (v1)** only — the repo ships
  `frontend/yarn.lock`; do **not** use npm or commit `package-lock.json`.
  Release CI uses `yarn install --frozen-lockfile`, so any new dep must update
  the lockfile in the same commit.
- **App layout:** Django app packages live under `modoboa/` (`core`, `admin`,
  `lib`, `webmail`, `limits`, `policyd`, `dmarc`, `dnstools`, …). The
  frontend SPA lives in `frontend/` and builds to `modoboa/frontend_dist/`
  (consumed by the Python package; `load_initial_data` symlinks it into the
  served `frontend/` dir).

## Commands — backend

```bash
# install (editable) with dev + test extras
pip install -e .[dev,test,ldap]

# run the FULL unit-test suite (sqlite, no services needed)
cd test_project && DB=sqlite python manage.py test modoboa

# run a single app / file / class / method
cd test_project && DB=sqlite python manage.py test modoboa.core
cd test_project && DB=sqlite python manage.py test modoboa.core.tests_views CoreViewTests.test_foo

# a quick runserver against sqlite (migrate first)
cd test_project && DB=sqlite DEBUG=1 python manage.py migrate --no-input && python manage.py runserver
```

- The test project is `test_project/test_project/` (settings inherit from
  `modoboa/test_settings.py`). `DJANGO_SETTINGS_MODULE=test_project.settings`
  is the default for `test_project/manage.py`.
- **`tests.py` at the repo root is NOT the unit-test runner** — it is a
  `DeployTest` that shells out to `modoboa-admin.py deploy` and requires a
  live Postgres (`DB=postgres`; MySQL is no longer supported by this fork).
  CI runs it plus `manage.py test modoboa` against Postgres; locally prefer
  the sqlite path above for unit tests.
- Tox (`tox.ini`) re-runs the same flow under each Python; to exercise a
  specific env: `tox -e py312` (note `changedir = test_project`).
- Lint: `ruff check` (config in `pyproject.toml`; **migrations are excluded**
  — never hand-edit migration files, generate with `manage.py makemigrations`).
  Format: `black`. All wired into `.pre-commit-config.yaml`.

## Commands — frontend

```bash
cd frontend
yarn install          # yarn v1; Node 22+ (Vite 8 needs it)
yarn dev              # real backend at http://127.0.0.1:8000
yarn dev:mock         # MSW-mocked API, OIDC bypassed, boots logged-in (HTTP)
yarn build            # -> ../modoboa/frontend_dist/
yarn test             # vitest, run once   |  yarn test:watch  for watch
yarn lint             # eslint --fix          |  yarn lint-no-fix  to check only
yarn format          # prettier --write
```

- `dev:mock` runs over **plain HTTP on purpose**: a self-signed HTTPS cert
  breaks the MSW service-worker registration. Everything mock-related is
  gated on `VITE_MOCK_API` (dynamic import) → **MSW is DCE'd from production
  builds; never import `src/mocks/*` unconditionally**.
- OIDC-by-pass glue for mock mode lives in `src/stores/auth.store.js`
  (`validateAccess`/`login`/`$reset`); they also check the global
  `globalThis.__MODOBOA_MOCK_API__` set in `main.js`, because `import.meta.env`
  isn't reliably injected into Module-Federation-exposed modules.
- Runtime config: `src/main.js` fetches **`config.json`** before mount; the
  value is held in `src/config.js` (`setGlobalConfig` / `useGlobalConfig`) —
  not in `main.js`, to avoid a `store ↔ main` cycle.
- See `frontend/README.md` and `frontend/DEV_SEM_BACKEND.md` for the full
  mock/MSW and Storybook workflows.

### i18n (frontend)

```
yarn gettext:extract   # source strings -> src/locale/<lang>/app.po
# (edit .po msgstr)
yarn gettext:compile   # -> src/locale/translations.json (committed, ALL langs)
```

- Which languages ship is set by `locales.config.js`; override at build time
  with `MODOBOA_LOCALES=en,pt_BR,fr yarn build`. `en` is always included.
  Note: `pt_BR` = Brazilian Portuguese; `br` = **Breton**, not Brazil.

## CI (`.github/workflows/`)

- **`modoboa.yml`** (Python) has `paths-ignore: frontend/**` (and `*.po`,
  `doc-ng/**`) — frontend-only PRs do **not** run the Python matrix. CI matrix
  runs against `postgres` only on Python 3.12, with redis,
  openldap, and a redis-sentinel compose job for `modoboa.policyd`.
- **`frontend.yml`** runs `yarn install` → `yarn test` → `yarn build` on Node 24
  for `paths: frontend/**`.
- **`release.yml`**: on `release: published` or `v*` tag → builds frontend,
  compiles `.mo`, runs `python -m build`, attaches the **wheel** to the GitHub
  Release. The tag must point at the fix commit (build uses the tag ref). PyPI
  publish is gated to `github.repository == 'modoboa/modoboa'` — **forks can't
  publish**, so don't try to wire publish secrets into a fork.

## Migrations

Django migrations under each `modoboa/<app>/migrations/`. Ruff is configured
to exclude them. When changing models, `python manage.py makemigrations
<app>` from `test_project/`. `load_initial_data` is a custom management
command: besides creating fixtures it **recreates the `frontend/` symlinks
into `frontend_dist/`** — that's why `index.html` must stay a symlink, never a
real file (otherwise stale HTML pointing at old assets gets served).

## Conventions specific to this fork

- **Branch / PR / release:** PRs created as **draft**, merged after CI green;
  commit/PR titles and bodies in **English**; include the *what* and *why*
  (and for bug/perf fixes, concrete repro/test steps). Use `Co-Authored-By:
  Claude ...` and `Claude-Session: ...` trailers on commits. Do not include
  internal model identifiers in commits/PRs/code.
- **Versioning:** `setuptools_scm`; local versions look like `2.9.1+sintraN`.
- **Server ops commands** (for `mail.sintraffms.com`) must be handed to the
  operator as a **single line chained with `&&`**, never as multi-step blocks.
- **Never version** network captures (`*.har`) — they contain tokens/cookies.
- **`*.mo` files are gitignored** (regenerated from `*.po`); don't commit them.
- Before proposing anything Bruno asks for, **present drawbacks / trade-offs /
  risks first** (cost, maintenance, security, UX) and only proceed after the
  OK. Be honest when a gain is cosmetic/marginal — recommend not doing it.
- Decisions already taken and not to be re-litigated (cache for LocalConfig,
  MDI-SVG icons, self-hosted Roboto, content-hashed MF bootstrap, Dovecot
  `auth_cache`, `WEBMAIL_IMAP_POOL`, etc.) are listed in `CLAUDE.md` — defer
  to it.