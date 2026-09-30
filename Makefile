# Kyrgyz ASR chat — FastAPI backend + SvelteKit web UI
# Usage: make help

PYTHON      ?= python3.11
VENV        := .venv
PY          := $(VENV)/bin/python
PIP         := $(VENV)/bin/pip
WEB         := web
JS          ?= bun
API_PORT    := 8010
WEB_PORT    := 5180
FILE        ?= samples/audio.wav

.DEFAULT_GOAL := help
.PHONY: help install install-py install-web dev stop backend web gradio transcribe health check build clean clean-all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: install-py install-web ## Install Python and web dependencies

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

install-py: $(VENV)/bin/activate ## Create .venv and install requirements.txt
	$(PIP) install -r requirements.txt

install-web: ## Install web dependencies
	cd $(WEB) && $(JS) install

dev: ## Run backend and web UI together (Ctrl-C stops both)
	@for p in $(API_PORT) $(WEB_PORT); do \
		if lsof -ti :$$p -sTCP:LISTEN >/dev/null; then \
			echo "Port $$p is already in use — run 'make stop' first."; exit 1; \
		fi; \
	done
	@echo "Web UI: http://localhost:$(WEB_PORT)   API: http://localhost:$(API_PORT)"
	@trap 'kill $$(jobs -p) 2>/dev/null' INT TERM EXIT; \
		$(VENV)/bin/uvicorn backend.server:app --port $(API_PORT) & \
		(cd $(WEB) && $(JS) run dev) & \
		wait

backend: ## Run only the FastAPI backend (auto-reload)
	$(VENV)/bin/uvicorn backend.server:app --port $(API_PORT) --reload --reload-dir backend

web: ## Run only the SvelteKit dev server
	cd $(WEB) && $(JS) run dev

gradio: ## Run the original Gradio demo (backend/gradio_app.py)
	$(PY) -m backend.gradio_app

transcribe: ## Transcribe a file from the CLI: make transcribe FILE=samples/audio.wav
	$(PY) -m backend.cli $(FILE)

stop: ## Stop anything left running on the backend/web ports
	@pids=$$(lsof -ti :$(API_PORT) -ti :$(WEB_PORT) -sTCP:LISTEN); \
	if [ -n "$$pids" ]; then kill $$pids && echo "Stopped $$pids"; else echo "Nothing running"; fi

health: ## Check that the backend is up
	@curl -s localhost:$(API_PORT)/api/health; echo

check: ## Type-check the web UI
	cd $(WEB) && $(JS) run check

build: ## Build the web UI for production
	cd $(WEB) && $(JS) run build

clean: ## Remove caches and build output
	find backend -name __pycache__ -prune -exec rm -rf {} +; rm -rf $(WEB)/.svelte-kit $(WEB)/build

clean-all: clean ## Also remove .venv and node_modules
	rm -rf $(VENV) $(WEB)/node_modules
