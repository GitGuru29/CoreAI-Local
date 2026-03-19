# systemd setup

These service files are configured for this machine and repository path:

- `/run/media/msfvenom/28aa095f-4b10-4a14-8ba9-4f2570fb6ce2/CoreAI-Local`
- user: `msfvenom`
- model store: `/var/lib/ollama`
- mDNS hostname: `coreai-local.local`
- preferred reverse proxy: `caddy.service`

If you move the repository later, update the paths inside both unit files before installing them.
If your local Ollama models are stored somewhere else, update `OLLAMA_MODELS` in `ollama-local.service` before installing it.

## Install

```bash
sudo cp deploy/systemd/ollama-local.service /etc/systemd/system/
sudo cp deploy/systemd/coreai-local.service /etc/systemd/system/
sudo cp deploy/systemd/coreai-local-mdns.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ollama-local.service
sudo systemctl enable --now coreai-local.service
```

The preferred HTTPS entrypoint is the package-provided `caddy.service`, not a custom unit in this repo:

```bash
sudo pacman -S --needed --noconfirm caddy
sudo bash deploy/caddy/install-caddy.sh coreai-local.local
sudo systemctl status caddy.service --no-pager
```

## Check status

```bash
sudo systemctl status ollama-local.service
sudo systemctl status coreai-local.service
```

If you also want a stable Bonjour/mDNS hostname for Mac clients, install `avahi` and enable the mDNS publisher:

```bash
sudo pacman -S --needed --noconfirm avahi nss-mdns
sudo bash deploy/mdns/install-mdns.sh
grep '^hosts:' /etc/nsswitch.conf
sudo systemctl status avahi-daemon.service coreai-local-mdns.service --no-pager
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
journalctl -u coreai-local-mdns.service -f
journalctl -u caddy.service -f
```
