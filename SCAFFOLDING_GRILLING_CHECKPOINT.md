# Language Teacher — Scaffolding Grilling Checkpoint

Status: **interview in progress, not yet acted on**. Per the grilling process, no code/scaffolding should be
implemented until the user has confirmed full shared understanding — including the open question and
remaining branches below.

## Confirmed decisions

1. **Two separate systems**: a product runtime (Chinese-teaching app) and a devtools system
   (dev-automation pipeline). They are not a unified orchestrated workflow.
2. **Product orchestrator** = a real agentic orchestrator (LangGraph). **Devtools orchestrator** = a plain
   deterministic script (no LLM-driven routing needed there).
3. **Primary language**: Python, for both systems.
4. **Product UI for v1**: CLI-first. No web frontend / FastAPI layer yet.
5. **Product orchestrator framework**: LangGraph — explicit graph/state-machine of agent nodes.
6. `USER_STORIES.md` must be written and agreed **before any implementation** (format decided in #17).
7. **v1 product sub-agents** (only two, routed by the LangGraph orchestrator):
   - Conversation/tutor agent — free-form chat practice + inline grammar correction/explanation.
   - Vocab quiz agent — drills specific words/phrases on request.
   - Pronunciation feedback and progress-tracking are deferred to v2.
8. **LLM runtime**: Ollama + `mistral` (7B, default tag), **CPU-only for now**, GPU passthrough later
   (just a compose change, no code changes needed).
9. **No persistence in v1** — every CLI run is an ephemeral conversation. Persistence (likely SQLite later)
   is deferred to v2.
10. **Python dependency manager**: `uv`, for both projects.
11. **Two independent uv projects** (not one shared project) — `product/` and `devtools/`, each with their
    own `pyproject.toml` and venv.
12. **Repo layout**:
    ```
    language_teacher/
    ├── product/              # LangGraph orchestrator + agents
    │   ├── pyproject.toml
    │   ├── src/...
    │   └── promptfoo/        # eval configs live INSIDE product/
    ├── devtools/              # US-implementer + GitHub-workflow pipeline
    │   ├── pyproject.toml
    │   ├── src/...
    │   └── .env / .env.example   # ANTHROPIC_API_KEY (devtools-only secret)
    ├── docker-compose.yml     # Ollama, CPU-only, named volume for model persistence
    ├── USER_STORIES.md
    ├── .github/workflows/     # CI: pytest + ruff
    └── README.md
    ```
13. **Devtools LLM backend**: Claude Agent SDK (not local Ollama) — code-writing quality matters more here
    than for the tutoring product.
14. **GitHub-workflow agent does NOT create branches.** The user creates/checks out the branch manually
    beforehand (exactly like `project-scaffolding` was created manually this session). The agent's scope is:
    **run tests → commit → push → open PR** (`gh pr create`) against whatever branch is currently checked
    out. Fails closed: if tests/lint fail, stop — no commit, no PR.
15. **Test framework**: pytest, for both `product/` and `devtools/`.
16. **CI**: a GitHub Actions workflow runs pytest (+ ruff, see #21) on push/PR, in addition to the agent
    running tests locally before opening a PR.
17. **`USER_STORIES.md` format**:
    ```markdown
    ## US-01: <short title>

    **As a** <role>
    **I want** <capability>
    **So that** <benefit>

    ### Acceptance Criteria
    - [ ] ...
    - [ ] ...
    ```
18. **Ollama model pulling**: manual, one-time step after first `docker compose up -d`
    (`docker exec ollama ollama pull mistral`), documented in the README. A named volume persists pulled
    models across container restarts. No auto-pull entrypoint script.
19. **promptfoo integration**: a custom Python provider that calls the LangGraph orchestrator in-process
    (no HTTP server needed, matches CLI-first architecture). v1 eval scope:
    - Tutor agent responds in **European Portuguese** (not Brazilian), stays on-topic (Chinese learning),
      correctly identifies/corrects grammar mistakes in sample Chinese sentences.
    - Vocab quiz agent asks about the requested vocab and correctly judges right/wrong answers.
    - Orchestrator routing: a "quiz me" message vs. a "let's chat" message routes to the correct sub-agent.
20. **Secrets/config**: `.env` (gitignored) + `.env.example` (committed), scoped to `devtools/` only, holding
    `ANTHROPIC_API_KEY`. `product/` needs no secrets (Ollama is local/unauthenticated).
    `.gitignore` covers `.env`, `__pycache__/`, `.venv/`, etc.
21. **Linting/formatting**: Ruff, for both projects, wired into the same CI workflow as pytest.
22. **Devtools CLI invocation shape**: two separate commands, not one combined.
    ```
    cd devtools
    uv run implement US-01   # US-implementer agent writes/modifies code in product/ only
    uv run ship US-01        # run pytest + ruff on product/ → if green: commit, push, gh pr create
                              # (title/body derived from story) → if red: stop, report, no commit/no PR
    ```
    Reason: write-step often needs iteration/retry before it's ready to ship; splitting avoids re-running
    the whole pipeline on every retry and lets the user inspect the diff before triggering ship.

## Open question — NOT yet confirmed (resume here)

**Devtools internal agent structure.** How is the US-implementer agent (Claude Agent SDK) defined in code:
system prompt content/scope, which tools it gets access to (file read/write, shell/test-run, or just
file edit with `ship` doing tests separately), and how it decides it's "done" implementing a story
(self-reported completion vs. acceptance-criteria checklist vs. some other signal)?

## Not yet discussed — remaining branches to grill before implementation

- Commit message / PR title-body conventions (does the GitHub-workflow agent derive these from the user
  story automatically, in what format?).
- README content/scope (what setup steps get documented there).
- Whether `product/` and `devtools/` each get their own `.gitignore` or share one at repo root.
- LangGraph specifics: state shape, and how the orchestrator actually decides tutor-vs-quiz routing
  (keyword heuristic vs. a small LLM classifier node).

## Reminder for resuming

This is an in-progress `/grilling` interview (see the `grilling` skill, installed globally via
`mattpocock/skills@grilling`). **Do not scaffold/implement anything from this document until the user
explicitly confirms full shared understanding** — resume by asking the open question above, then continue
through the remaining branches, one at a time, with a recommended answer for each.
