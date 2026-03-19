# mDNS hostname

This folder publishes a stable Bonjour/mDNS hostname for `CoreAI-Local` so Macs can use:

```text
https://coreai-local.local
```

instead of a changing raw LAN IP.

## Why this matters

If the Linux host disconnects from Wi-Fi for a while and reconnects later, the LAN IP can change. A stable `.local` hostname avoids hardcoding the old address in the Mac client.

## Files

- `publish-mdns-host.sh`
- `install-mdns.sh`
- `../systemd/coreai-local-mdns.service`

## Install

```bash
sudo pacman -S --needed --noconfirm avahi nss-mdns
sudo bash deploy/mdns/install-mdns.sh
```

## What it does

- enables `avahi-daemon.service`
- enables `coreai-local-mdns.service`
- patches `/etc/nsswitch.conf` to add `mdns_minimal [NOTFOUND=return]` to the `hosts:` resolver line when it is missing
- continuously republishes `coreai-local.local` to the Linux host's current IPv4 address
- survives Wi-Fi disconnect and reconnect events by updating the published IP automatically

## Verify from Linux

```bash
systemctl status avahi-daemon.service coreai-local-mdns.service --no-pager
grep '^hosts:' /etc/nsswitch.conf
avahi-resolve-host-name coreai-local.local
```

## Verify from macOS

```bash
curl https://coreai-local.local/health
```

## Notes

- The nginx certificate installer should also be run with the hostname:

```bash
sudo bash deploy/nginx/install-nginx.sh 10.113.228.6 coreai-local.local
```

- If the hostname alias changes later, rerun both the nginx installer and the mDNS install.
