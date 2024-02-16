# Pluxee API

![Tests](https://github.com/Tib612/pluxee-api/actions/workflows/python-tests.yml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/pluxee-api)](https://pypi.org/project/pluxee-api/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/pluxee-api.svg)](https://pypi.org/project/pluxee-api/)
[![Documentation status](https://readthedocs.org/projects/pluxee-api/badge/?version=latest)](https://pluxee-api.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/tib612/pluxee-api/blob/master/LICENSE)


The pluxee-api Python library (unofficial) provides easy access to Pluxee (Sodexo) balance and transaction data. This library allows users to retrieve information such as account balances and transaction history from the Pluxee platform. It offers both synchronous and asynchronous versions for installation.

## Features
- Retrieve account balance
- Fetch transaction history

## Installation
You can install pluxee-api via pip
For normal install:

```python
pip install pluxee-api
```

For asynchronous version:

```python
pip install pluxee-api[async]
```

Alternatively, you can clone the repository from GitHub:
```python
git clone git://github.com/Tib612/pluxee-api.git
cd pluxee-api
pip install -e .
```


## Usage

To use the pluxee-api library, you need to provide your Pluxee username and password or set them as environment variables PLUXEE_USERNAME and PLUXEE_PASSWORD. No registration of keys is required.

You can find examples in the example folder.

## Documentation

Documentation for pluxee-api is available at https://pluxee-api.readthedocs.io/en/latest/

## Questions, Comments, etc?
If you have any questions, comments, or suggestions regarding pluxee-api, feel free to contact me on LinkedIn https://www.linkedin.com/in/thibaut-capuano/



## Contributing
Contributions to pluxee-api are welcome! Whether it's adding features, fixing bugs, or improving documentation, your contributions are appreciated. Simply fork the repository, make your changes, and submit a pull request. Let's make accessing Pluxee data easier together!


## License
This project is licensed under the MIT License
