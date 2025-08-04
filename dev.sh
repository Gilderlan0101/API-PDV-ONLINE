#!/bin/bash

# Formatar código com Blue
poetry run blue .

# Rodar FastAPI com Uvicorn
poetry run uvicorn back-end.Main:app --reload
