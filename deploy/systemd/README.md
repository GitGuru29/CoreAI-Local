# systemd setup

These service files are configured for this machine and repository path:

- `/run/media/msfvenom/28aa095f-4b10-4a14-8ba9-4f2570fb6ce2/CoreAI-Local`
- user: `msfvenom`
- model store: `/var/lib/ollama`

If you move the repository later, update the paths inside both unit files before installing them.
If your local Ollama models are stored somewhere else, update `OLLAMA_MODELS` in `ollama-local.service` before installing it.

## Install

```bash
sudo cp deploy/systemd/ollama-local.service /etc/systemd/system/
sudo cp deploy/systemd/coreai-local.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ollama-local.service
sudo systemctl enable --now coreai-local.service
```

## Check status

```bash
sudo systemctl status ollama-local.service
sudo systemctl status coreai-local.service
```

If `/health` shows `available_models: 0` even though you already pulled models locally, the usual cause is a model-directory mismatch. This unit uses:

```text
/var/lib/ollama
```

Reload the unit after updating it:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama-local.service
sudo systemctl restart coreai-local.service
```

## Follow logs

```bash
journalctl -u ollama-local.service -f
journalctl -u coreai-local.service -f
```
