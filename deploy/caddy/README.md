# caddy reverse proxy

This folder contains the preferred local HTTPS deployment for `CoreAI-Local`.

Why Caddy is preferred over the older nginx path:

- it uses a persistent local CA with `tls internal`
- you trust the Caddy root on the Mac once, not every time a new leaf certificate is generated
- it survives device reboots more cleanly
- it works well with the stable `coreai-local.local` hostname

## Files

- `Caddyfile`
- `install-caddy.sh`

## Install on Linux

```bash
sudo pacman -S --needed --noconfirm caddy
sudo bash deploy/caddy/install-caddy.sh coreai-local.local
```

If you also want automatic hostname discovery across Wi-Fi reconnects:

```bash
sudo pacman -S --needed --noconfirm avahi nss-mdns
sudo bash deploy/mdns/install-mdns.sh
```

## What the installer does

- installs the CoreAI `Caddyfile` into `/etc/caddy/Caddyfile`
- disables `nginx.service` if it is still active
- enables and restarts `caddy.service`
- runs `caddy trust` on Linux so the local machine can trust Caddy's internal CA

## Boot behavior

With `caddy.service`, `avahi-daemon.service`, `coreai-local.service`, and `ollama-local.service` enabled, the Lenovo should recover automatically after reboot, assuming both devices rejoin the same LAN.

## Trust the root CA on macOS

Trust the Caddy local root CA once on the Mac:

```bash
scp msfvenom@coreai-local.local:/var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt \
  ~/Downloads/coreai-local-root.crt

sudo security add-trusted-cert \
  -d \
  -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/Downloads/coreai-local-root.crt
```

After that, use:

```bash
curl https://coreai-local.local/health
```

without `--insecure`.

## Verify on Linux

```bash
sudo systemctl status caddy.service --no-pager
curl https://coreai-local.local/health
```

## Verify on macOS

```bash
curl https://coreai-local.local/health
curl https://coreai-local.local/models \
  -H "X-API-Key: replace-with-your-secret"
```
