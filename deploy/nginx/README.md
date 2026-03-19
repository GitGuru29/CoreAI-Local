# nginx reverse proxy

This folder contains a local HTTPS reverse-proxy config for `CoreAI-Local`.

Current assumptions:

- backend app listens on `127.0.0.1:8000`
- nginx terminates TLS on `443`
- the install script can use either an explicit LAN IP or the first IP returned by `hostname -I`

Files:

- `coreai-local.conf`
- `generate-self-signed-cert.sh`
- `install-nginx.sh`

Recommended install:

```bash
sudo pacman -S --needed --noconfirm nginx
sudo bash deploy/nginx/install-nginx.sh 10.113.228.6
```

What the installer does:

- ensures `/etc/nginx/conf.d/` exists
- patches `/etc/nginx/nginx.conf` to include `/etc/nginx/conf.d/*.conf` when the host config does not already do so
- installs `coreai-local.conf` with the selected LAN IP
- generates a self-signed certificate for that IP plus `127.0.0.1` and `localhost`
- validates nginx config and reloads nginx

If the host IP changes later, rerun:

```bash
sudo bash deploy/nginx/install-nginx.sh <new-lan-ip>
```
