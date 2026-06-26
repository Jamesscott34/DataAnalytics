# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Phase 0 planning documents: architecture, API design, database schema, component tree, task list.
- FastAPI backend with `/api/v1/health` liveness endpoint.
- React Vite frontend shell with health status panel and Vitest tests.
- SQLAlchemy models (users, sessions, uploaded files stub) and Alembic migration `001_initial`.
- Pydantic settings, JSON logging, security headers, and standard error responses.
- JWT authentication with refresh tokens, RBAC (admin/analyst/viewer), and login UI.
