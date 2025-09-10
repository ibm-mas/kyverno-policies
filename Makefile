.PHONY: venv install test

venv:
	python3 -m venv .venv

install: venv
	. .venv/bin/activate && python -m pip install -r requirements.txt

test: install
	. .venv/bin/activate && pytest -q -r A test_policies.py