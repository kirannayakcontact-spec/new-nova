# Automatic Chrome Launch

The `nova` and `nova restart` commands wait for the Flask dashboard to respond, then open:

```text
http://127.0.0.1:5000
```

Chrome is attempted first with the Android activity manager. If Chrome cannot be launched directly, Titan Nova falls back to `termux-open-url`, which opens the device's default browser.

Disable browser opening for one run with:

```bash
NOVA_OPEN_BROWSER=0 nova
```
