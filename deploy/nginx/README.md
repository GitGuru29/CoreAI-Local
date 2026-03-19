# nginx reverse proxy

This folder contains a local HTTPS reverse-proxy config for `CoreAI-Local`.

Current assumptions:

- backend app listens on `127.0.0.1:8000`
- nginx terminates TLS on `443`
- the install script can use either an explicit LAN IP or the first IP returned by `hostname -I`
- preferred stable hostname: `coreai-local.local`

Files:

- `coreai-local.conf`
- `generate-self-signed-cert.sh`
- `install-nginx.sh`

Recommended install:

```bash
sudo pacman -S --needed --noconfirm nginx
sudo bash deploy/nginx/install-nginx.sh 10.113.228.6 coreai-local.local
```

What the installer does:

- ensures `/etc/nginx/conf.d/` exists
- patches `/etc/nginx/nginx.conf` to include `/etc/nginx/conf.d/*.conf` when the host config does not already do so
- installs `coreai-local.conf` with the selected LAN IP and hostname alias
- generates a self-signed certificate for that hostname plus the current LAN IP, `127.0.0.1`, and `localhost`
- validates nginx config and reloads nginx

If the host IP changes later but the Mac uses `https://coreai-local.local`, only the mDNS publisher needs to keep tracking the new IP. Rerun the nginx installer when you want to refresh the fallback IP entry in the certificate as well:

```bash
sudo bash deploy/nginx/install-nginx.sh <new-lan-ip> coreai-local.local
```

## Trust the certificate on macOS

Copy the generated certificate from the Linux host:

```bash
scp msfvenom@coreai-local.local:/etc/nginx/certs/coreai-local.crt ~/Downloads/coreai-local.crt
```

Import it into the macOS System keychain:

```bash
sudo security add-trusted-cert \
  -d \
  -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/Downloads/coreai-local.crt
```

After that, HTTPS requests from the Mac can be made without `--insecure`.
