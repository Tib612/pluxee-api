# Pluxee API

![Tests](https://github.com/Tib612/pluxee-TestingStarterProject/actions/workflows/python-tests.yml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/tox)](https://pypi.org/project/tox/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/tox.svg)](https://pypi.org/project/tox/)
[![Downloads](https://static.pepy.tech/badge/tox/month)](https://pepy.tech/project/tox)
[![Documentation status](https://readthedocs.org/projects/tox/badge/?version=latest)](https://tox.readthedocs.io/en/latest/?badge=latest)

This is a Python package that provides a simple API to access Pluxee data, including current balance and transactions.

## Installation
```python
pip install pluxee-api
```

## Installation dev
do not do that else it breaks everything on commit and undo all yout code changes...
pre-commit install


## Usage

```python
from pluxee_api.pluxee_client import PluxeeClient

client = PluxeeClient()
client.login()
balance = client.get_balance()
transactions = client.get_transactions()

for transaction in transactions:
    print(transaction)
```

## Contributing
Feel free to contribute by opening issues or pull requests.

## License
This project is licensed under the MIT License

python3 -m pytest --cov=pluxee-api --cov-report term-missing

pre-commit run --all-files --show-diff-on-failure