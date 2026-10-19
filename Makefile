PY ?= .venv/bin/python
SMK ?= .venv/bin/snakemake

.PHONY: venv lint test rule-tests run report image clean-test

venv:
	python3 -m venv .venv && $(PY) -m pip install -e ".[dev]"

lint:
	$(PY) -m ruff check src tests workflow/scripts
	$(PY) -m ruff format --check src tests workflow/scripts
	$(PY) -m mypy
	$(SMK) --lint
	.venv/bin/snakefmt --check workflow

test:
	$(PY) -m pytest --cov=mavecal --cov-report=term

rule-tests:
	$(PY) -m pytest .tests/unit -p no:cacheprovider

# Needs MAVECAL_DATA_DIR pointing at the downloaded ClinVar releases (see README).
run:
	nice -n 10 $(SMK) --profile profiles/local

report:
	$(SMK) --report results/snakemake_report.html

image:
	docker build -t mave-clinvar-calibration:1.0.0 .

clean-test:
	rm -rf .tests/integration/data .tests/integration/results
