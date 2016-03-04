test:
	py.test -vv --cov=app --cov-report=term-missing
snoop:
	@open -b com.google.chrome `openssl enc -aes-256-cbc -pass pass:foo -d < snoop.enc`
