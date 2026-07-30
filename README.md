# Language Teacher

Chinese-teaching CLI app (`product/`) plus a dev-automation pipeline (`devtools/`) that implements
user stories and opens PRs.

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Docker (for Ollama)
- [gh CLI](https://cli.github.com/), authenticated
- Anthropic API key (for `devtools/`)

## 1. Start Ollama

```
docker compose up -d
docker exec language_teacher ollama pull qwen2.5:7b
```

The pulled model persists across restarts via a named volume.

## 2. Run the product CLI

```
cd product
uv sync
uv run product
```

## 3. Run devtools

```
cd devtools
cp .env.example .env   # fill in ANTHROPIC_API_KEY
uv sync
uv run implement US-01   # write code for a story
uv run ship US-01         # test, commit, push, open PR
```

## Tests & linting

Run inside either `product/` or `devtools/`:

```
uv run pytest
uv run ruff check .
```

## Backlog

See [USER_STORIES.md](./USER_STORIES.md).
