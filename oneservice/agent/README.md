# OneService Agent (Python)

A lightweight Python agent that can deploy and run popular Prometheus exporters on a host, with a single YAML config. Inspired by Datadog Agent.

- Single binary/script install on target machines
- Manages exporters via YAML: node_exporter, mysqld_exporter (and extensible)
- Registers the target with OneService Backend so Prometheus/Thanos start scraping automatically

## Quick start

1) Edit `agent.yaml` to enable exporters and set ports/labels.
2) Run the agent:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python agent.py --config agent.yaml --backend http://localhost:8000 --token tok-demo
```

3) Verify in Grafana (http://localhost:3000) and in the OneService UI under Dashboard.

One-liner (on a target host with Python 3):

```bash
curl -sL https://raw.githubusercontent.com/realra1n/ai-monitoring-and-operating-system/main/oneservice/agent/agent.py -o agent.py \
	&& curl -sL https://raw.githubusercontent.com/realra1n/ai-monitoring-and-operating-system/main/oneservice/agent/agent.yaml -o agent.yaml \
	&& python3 -m venv .venv && . .venv/bin/activate && pip install pyyaml requests psutil \
	&& python3 agent.py --config agent.yaml --backend http://<backend-host>:8000 --token <token>
```

## Supported exporters
- node_exporter (Go binary)
- mysqld_exporter (Go binary)

The agent will download the exporter binaries for your OS/arch on first run into `~/.oneservice/exporters` and keep them managed.
