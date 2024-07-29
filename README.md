![Tests](https://github.com/asynq-io/eventiq-exporter/workflows/Tests/badge.svg)
![Build](https://github.com/asynq-io/eventiq-exporter/workflows/Publish/badge.svg)
![License](https://img.shields.io/github/license/asynq-io/eventiq-exporter)
![Python](https://img.shields.io/pypi/pyversions/eventiq-exporter)
![Format](https://img.shields.io/pypi/format/eventiq-exporter)
![PyPi](https://img.shields.io/pypi/v/eventiq-exporter)
![Mypy](https://img.shields.io/badge/mypy-checked-blue)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

# eventiq-exporter

Prometheus metrics exporter for eventiq

## Installation
```shell
pip install eventiq-exporter
```

## Usage

```python
from eventiq import Service
from eventiq_exporter import PrometheusExporter

service = Service(...)
service.add_middleware(PrometheusMiddleware, run_server=True)

```
