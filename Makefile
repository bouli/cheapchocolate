
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
