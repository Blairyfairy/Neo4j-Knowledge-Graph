install:
	python -m pip install -r requirements.txt

parse:
	python scripts/parse_sources.py

validate:
	python scripts/validate_graph.py

import:
	python scripts/import_neo4j.py

up:
	docker compose up -d

down:
	docker compose down

check:
	python scripts/validate_graph.py
