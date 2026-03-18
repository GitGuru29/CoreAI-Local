# systemd setup

These service files are configured for this machine and repository path:

- `/run/media/msfvenom/28aa095f-4b10-4a14-8ba9-4f2570fb6ce2/CoreAI-Local`
- user: `msfvenom`

If you move the repository later, update the paths inside both unit files before installing them.

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

## Follow logs

```bash
journalctl -u ollama-local.service -f
journalctl -u coreai-local.service -f
```
