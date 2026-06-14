# Agent Instructions

This is a **dual monorepo** — pnpm/Turborepo for Vue/Nuxt apps + Cargo workspace for the Rust Harness CLI.

## Commands

- `pnpm dev` — start dev servers (Vue app at :3000, Nuxt docs at :3001)
- `pnpm build` — turbo build across all apps/packages
- `pnpm lint` — turbo lint
- `pnpm format` — `prettier --write "**/*.{ts,tsx,md}"` (no prettier config file; uses defaults)
- `cargo test` — run ~31 Rust unit tests in `crates/harness-cli`
- use `pnpm`, never `npm`

## Monorepo

- `apps/web` — Vue 3 + Vite (trivial scaffolding — just renders `<Page />` from `ui`)
- `apps/docs` — Nuxt 3 (trivial scaffolding — same pattern)
- `packages/ui` — shared UI components (3 Turborepo-branded demo components: `Card`, `Gradient`, `Page`)
- `packages/tsconfig` — shared TS configs
- `packages/eslint-config-custom` — shared ESLint configs
- `crates/harness-cli` — Rust CLI (the primary product, 6107 lines, SQLite-backed, clap CLI, ~15 subcommands)

No JS/TS tests exist — Rust tests via `cargo test` only.

## Rust CLI release

Push tag `v*` or `harness-cli-v*` → CI builds releases for 5 platforms. Merged PRs touching `crates/harness-cli/`, `scripts/schema/`, or Cargo metadata auto-bump patch version, tag, and release. `scripts/build-harness-cli-release.sh` builds locally to `dist/`.

## Phase plans

PHASE4 (mechanical verification) is implemented. PHASE5 (evolution infrastructure) is current. See `PHASE2.md`–`PHASE5.md`.

## Skills

11 agent skills in `.agents/skills/`. Use `skill` tool: `nuxt`, `vue`, `vue-best-practices`, `turborepo`, `frontend-design`, `deploy-to-vercel`, `vercel-cli-with-tokens`, `vercel-optimize`, `web-design-guidelines`, `writing-guidelines`, `find-skills`.

<!-- HARNESS:BEGIN -->
## Harness

This repo uses Harness. Before work, read:

- `README.md`
- `docs/HARNESS.md`
- `docs/FEATURE_INTAKE.md`
- `docs/ARCHITECTURE.md`
- `docs/CONTEXT_RULES.md`
- `docs/TOOL_REGISTRY.md`
- `scripts/bin/harness-cli query matrix` on macOS/Linux, or `.\scripts\bin\harness-cli.exe query matrix` on Windows

Use the Rust Harness CLI at `scripts/bin/harness-cli` on macOS/Linux or
`scripts/bin/harness-cli.exe` on Windows as the main operational tool. Before a
step that could use an external tool, run `scripts/bin/harness-cli query tools
--capability <name> --status present` to see what is equipped; an absent
capability is a clean skip.
<!-- HARNESS:END -->
