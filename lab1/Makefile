
PYTHON=python
SRC_DIR=src

# Пути к скриптам
SERVER=$(SRC_DIR)/server/main.py
CLIENT=$(SRC_DIR)/client/main.py

RUFF=ruff
PYRIGHT=pyright
MYPY=mypy

# Сетевые параметры
HOST?=0.0.0.0
PORT?=8000


# ------------------------------------------------------------------
# Запуск сервера и клиента через -m, из корня проекта
# ------------------------------------------------------------------
run-server:
	$(PYTHON) -m src.server.main

run-client:
	$(PYTHON) -m src.client.main

# Запуск для локальной сети
local-server:
	$(PYTHON) -m src.server.main $(PORT) $(HOST)

local-client:
	$(PYTHON) -m src.client.main $(PORT) $(HOST)

# ------------------------------------------------------------------
# Проверка кода
# ------------------------------------------------------------------
check:
	$(RUFF) check $(SRC_DIR)
	$(PYRIGHT)
	$(MYPY) $(SRC_DIR)

clean:
	find $(SRC_DIR) -name "__pycache__" -type d -exec rm -rf {} +

.PHONY: run-server run-client local-server local-client check clean
