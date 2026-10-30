.PHONY: up down logs migrate ingest seed test lint
up:       ; docker compose up --build -d
down:     ; docker compose down
logs:     ; docker compose logs -f --tail=100
migrate:  ; docker compose run --rm backend alembic upgrade head
# make ingest [SRC=dvf]  (SRC absent = toutes les sources activées)
ingest: migrate
	docker compose run --rm backend python -m app.cli ingest $(SRC)
seed: migrate
	docker compose run --rm backend python -m app.cli seed-demo
test:     ; docker compose run --rm --no-deps backend pytest -q && cd frontend && npm test --silent
lint:     ; docker compose run --rm --no-deps backend sh -c "ruff check . && mypy app" && cd frontend && npm run lint --silent
