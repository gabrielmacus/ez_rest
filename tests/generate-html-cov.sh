python3 -m pytest --cov-report html --cov ./ez_rest
python3 -m http.server 8080 --bind 127.0.0.1 --directory ./htmlcov