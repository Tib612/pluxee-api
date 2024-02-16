Welcome to pluxee-api's documentation!
======================================

=============
Installation
=============

You can install pluxee-api via pip
For normal install:

.. code-block::

   pip install pluxee-api

For asynchronous version:

.. code-block::

   pip install pluxee-api[async]

Alternatively, you can clone the repository from GitHub:

.. code-block::

   git clone git://github.com/Tib612/pluxee-api.git
   cd pluxee-api
   pip install -e .

=============
Usage example
=============

You can use pluxee-api as follow

.. literalinclude:: ../../examples/example_usage_async.py

For asynchronous version:

.. literalinclude:: ../../examples/example_usage_async.py

=============
API Reference
=============

:mod:`pluxee`: Pluxee
-----------------------

.. automodule:: pluxee
    :no-members:
    :no-inherited-members:

Classes
--------------
.. currentmodule:: pluxee

.. autosummary::
    :template: class.rst

    pluxee.base_pluxee_client.PluxeeBalance
    pluxee.base_pluxee_client.PluxeeTransaction
    pluxee.pluxee_client.PluxeeClient
    pluxee.pluxee_async_client.PluxeeAsyncClient

Enums
--------------
.. currentmodule:: pluxee

.. autosummary::
    :template: class.rst

    pluxee.base_pluxee_client.PassType

Functions
--------------
.. currentmodule:: pluxee

.. autosummary::

    pluxee.pluxee_client.PluxeeClient.get_balance
    pluxee.pluxee_client.PluxeeClient.get_transactions
    pluxee.pluxee_async_client.PluxeeAsyncClient.get_balance
    pluxee.pluxee_async_client.PluxeeAsyncClient.get_transactions

Exceptions
--------------
.. currentmodule:: pluxee

.. autosummary::

    pluxee.exceptions.PluxeeLoginError
    pluxee.exceptions.PluxeeAPIError


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

:doc:`Auto-generated API reference </api_reference>`.
:doc:`Auto-generated module </module>`.