# nginx reverse proxy

This folder contains a local HTTPS reverse-proxy config for `CoreAI-Local`.

Current assumptions:

- backend app listens on `127.0.0.1:8000`
- nginx terminates TLS on `443`
- current LAN IP is `10.113.228.6`

Files:

- `coreai-local.conf`
- `generate-self-signed-cert.sh`

Install outline:

```bash
sudo mkdir -p /etc/nginx/certs
sudo cp deploy/nginx/coreai-local.conf /etc/nginx/conf.d/coreai-local.conf
sudo bash deploy/nginx/generate-self-signed-cert.sh
sudo systemctl enable --now nginx.service
```

If the host IP changes, update `server_name` and regenerate the cert.
