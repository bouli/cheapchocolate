.PHONY: build, tests
CURRENT_FOLDER := $(notdir $(CURDIR))
sync:
	uv add -r requirements.txt
	uv sync

tests:
	uv run --dev coverage run --omit="./tests/*" -m pytest -s

report:
	uv run coverage report

prepare:
	rm -rf dist
	rm -rf build
	git log v0.6.2..HEAD --oneline --format="* %h %s (%an)" > CHANGELOG.md

start-codex:
	@if sbx secret ls | grep -qi "openai"; then\
		echo "using the open ai config you have in sbx";\
	else\
		sbx secret set -g openai --oauth;\
	fi

	sbx create --name codex-$(CURRENT_FOLDER) codex . || echo "starting codex in sandbox"
	sbx run codex-$(CURRENT_FOLDER)

version:
	uv run ./src/cheapchocolate/__init__.py --version

start:
	uv run ./src/cheapchocolate/__init__.py start

folders:
	uv run ./src/cheapchocolate/__init__.py folders

build:
	mkdir -p dist
	uv sync
	rm -r dist
	uv build
