test:
	py.test -vv --pep8 --flakes --cov=ctf --cov-report=term-missing ctf/ tests/

.PHONY: test
