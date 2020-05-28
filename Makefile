DEV_SECRET_KEY = eba808940270398dbecc1b8ca7f77b74525c39627ed26ff4d6a5408fd3e542aa

DJANGO_SECRET_KEY ?= $(DEV_SECRET_KEY)

all: build

build: requirements.txt
	docker build -t gunaha --build-arg DJANGO_SECRET_KEY=$(DJANGO_SECRET_KEY) .

env: .env

.PHONY: all build env

.env:
	python -c 'import secrets; print("export SECRET_KEY=" + secrets.token_hex())' > $@

requirements.txt:
	poetry run pip freeze > $@