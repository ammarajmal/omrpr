cat /home/ammar/.kimi/plans/adam-warlock-beta-ray-bill-miss-martian.md
# Plan: Database-Backed Research Publishing Platform for WorldView Seekers

## Context & Goal
WorldView Seekers (WVS) needs a sovereign, source-cited research publishing system that lets the group:
1. Store structured research notes in a database (not just flat Markdown files).
2. Build/publish a public-facing website from those notes.
3. Operate on infrastructure the group controls, with professional engineering discipline.

This directly serves the **Islamic Research Publishing Platform** and **Islamic Research Archive** goals in `WorldView___Domain-2-Roadmap.md` (Track 3.4) and aligns with WVS core values: Basirah (rigor), Itqan (excellence), data sovereignty, and generational thinking.

## Chosen Approach
**Design document + working MVP prototype.**
- A written architecture/design specification.
- A runnable minimum viable prototype in the repo under a new `wvs-platform/` directory.
- The prototype uses the stack already prescribed by WVS Domain 2: **Python/FastAPI**, **React**, **SQLite/PostgreSQL**, **Docker**, **Git**.

## Proposed Tech Stack
| Layer | Choice | Rationale |
|-------|--------|-----------|
| Backend API | Python 3.12 + FastAPI | Matches WVS Track 3.3; excellent docs; modern async; easy SQLite/Postgres support. |
| Database | SQLite for MVP, PostgreSQL for production | SQLite keeps the MVP zero-config and portable; Postgres is the production target (WVS Track 5). |
| ORM/Migrations | SQLModel + Alembic | SQLModel merges Pydantic + SQLAlchemy; Alembic is the standard migration tool. |
| Frontend | React 18 + Vite | Matches WVS Track 3.2; fast dev server; minimal config. |
| Styling | Tailwind CSS | Utility-first, responsive, no design-system overhead for an MVP. |
| Publishing | Static-site generation path (prepared) + live SSR/API site | MVP ships a live search/read site; a static-export generator is designed and partially wired so notes can later be published as a static site. |
| Containerization | Docker + Docker Compose | Matches WVS Track 5.1; one command to run everything locally. |
| Testing | pytest (backend), Vitest (frontend) | Professional coverage from day one. |
| Lint/Format | ruff (Python), ESLint/Prettier (JS/TS) | Standard, fast, low-friction. |
| Version Control | Git | Already WVS standard; repo lives alongside the WVS markdown vault. |

## MVP Feature Scope
### In Scope
1. **Research Note CRUD**: Create, read, update, delete research notes with fields matching `WorldView___Research-Standards.md`:
   - title, slug, claim, source, source_tier, confidence_level, islamic_relevance, objections, open_questions, content (Markdown), author, status (draft/published), tags, created_at, updated_at.
2. **Tagging & Search**: Notes can be tagged; a search endpoint searches title, claim, content, and tags.
3. **Public Read Site**: A React frontend that lists and displays published notes with clean URLs (`/notes/:slug`).
4. **Admin UI**: A simple React admin to create/edit notes (no auth in MVP to keep scope tight; auth is designed and documented for Phase 2).
5. **Source Tier Display**: Visual badges for Tier 1–6 sources, enforcing WVS epistemology.
6. **Markdown Rendering**: Render note content and research-standard fields as formatted HTML.
7. **Dockerized Local Run**: `docker compose up` starts API, database (SQLite volume or Postgres), and frontend.
8. **Seed Data**: A script loads one or two notes from the existing WVS `WorldView___Notes___Power-and-Finance-Systems.md` so the prototype is immediately meaningful.

### Out of Scope for MVP (documented for Phase 2)
- User authentication / role-based access.
- Zotero integration.
- Full static-site export to a separate publish target.
- Arabic NLP / RAG integration.
- VPS deployment automation (Coolify/ansible).
- Multi-tenant workspaces.

## Deliverables
1. **Architecture Document** (`wvs-platform/docs/ARCHITECTURE.md`): high-level design, data model, API design, deployment options, security considerations.
2. **Engineering Standards** (`wvs-platform/docs/ENGINEERING.md`): project conventions, testing policy, branching, CI/CD blueprint, environment setup.
3. **MVP Codebase** (`wvs-platform/`):
   - `backend/`: FastAPI app, SQLModel models, Pydantic schemas, CRUD endpoints, Alembic migrations, tests.
   - `frontend/`: React app with list view, detail view, admin form, search.
   - `docker-compose.yml`, `Dockerfile`s, `.env.example`.
   - `Makefile` or `scripts/` for common tasks (test, migrate, seed, format).
4. **Seed Data Loader**: imports a curated excerpt from existing WVS notes.
5. **Working Local Demo**: verified by running `docker compose up` and accessing the site.

## Directory Layout (new)
```
/media/ammar/deen/WorldView/web/
├── WVS/                              # existing markdown vault (untouched)
└── wvs-platform/                     # new platform MVP
    ├── README.md
    ├── docker-compose.yml
    ├── Makefile
    ├── docs/
    │   ├── ARCHITECTURE.md
    │   └── ENGINEERING.md
    ├── backend/
    │   ├── Dockerfile
    │   ├── pyproject.toml
    │   ├── alembic/
    │   ├── app/
    │   │   ├── __init__.py
    │   │   ├── main.py
    │   │   ├── config.py
    │   │   ├── database.py
    │   │   ├── models.py
    │   │   ├── schemas.py
    │   │   ├── crud.py
    │   │   ├── routers/
    │   │   │   ├── notes.py
    │   │   │   └── tags.py
    │   │   └── seed.py
    │   └── tests/
    └── frontend/
        ├── Dockerfile
        ├── package.json
        ├── vite.config.ts
        ├── index.html
        └── src/
            ├── main.tsx
            ├── App.tsx
            ├── api/
            ├── components/
            ├── pages/
            └── types/
```

## Key Design Decisions
1. **Database-first**: Notes are relational records, not files. This enables search, filtering, citations, and future analytics that flat Markdown cannot provide.
2. **Source tier as first-class data**: The `source_tier` field is constrained to WVS tiers 1–6 and rendered with colored badges, making epistemology visible.
3. **Markdown body for long-form content**: Keeps authoring lightweight and compatible with WVS Logseq/Markdown workflow.
4. **SQLite default, Postgres ready**: `DATABASE_URL` is environment-driven; the same code runs locally and on a VPS.
5. **Clean separation**: Backend exposes a REST API; frontend is a thin client. This lets future frontends (mobile, static generator) reuse the API.
6. **No auth in MVP**: Acknowledged as a temporary simplification; Phase 2 adds JWT-based auth and role separation (reader / contributor / editor).

## Professional Engineering Practices Applied
- **Version control**: All code committed to Git; conventional commits encouraged.
- **Dependency management**: `pyproject.toml` + `requirements.lock`; `package-lock.json`.
- **Code quality**: ruff, ESLint, Prettier, type hints throughout.
- **Testing**: pytest for API endpoints; Vitest for frontend components; integration test for note lifecycle.
- **Database migrations**: Alembic manages schema changes.
- **Environment configuration**: 12-Factor App style via `.env` files; secrets never committed.
- **Containerization**: Docker Compose for reproducible local development.
- **Documentation**: Architecture and engineering docs kept in-repo, not separate.
- **Observability stub**: Structured logging configured; metrics endpoint reserved for Phase 2.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Scope creep into full CMS | Strict MVP feature list; Phase 2 items explicitly deferred. |
| Auth omitted too long | Documented as next priority; admin routes clearly marked TODO. |
| Front-end complexity | Keep UI to 3 pages (list, detail, admin form) with Tailwind. |
| WVS members new to Docker | README includes step-by-step setup and troubleshooting. |

## Implementation Phases
1. **Phase 0 — Scaffold & docs** (this task): create repo layout, architecture doc, engineering doc, Docker setup.
2. **Phase 1 — Backend MVP**: models, migrations, CRUD API, seed script, tests.
3. **Phase 2 — Frontend MVP**: list/detail/admin pages, search, Markdown rendering.
4. **Phase 3 — Integration & demo**: Docker Compose end-to-end, seed with WVS notes, final verification.

## Success Criteria
- `docker compose up` starts the stack without errors.
- A user can create, edit, search, and publicly view a research note.
- Existing WVS note content appears seeded in the database.
- All backend tests pass.
- Architecture and engineering docs are clear enough for a WVS member to extend the system.
