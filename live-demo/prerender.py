#!/usr/bin/env python3
"""Pre-render the Grantmother interviewer's question clips with Masky (stdlib only).

Usage:  python3 live-demo/prerender.py
- Uses MASKY_API_KEY from env or config.js. If neither, runs Masky's device-connect
  flow: open the printed link, sign in, press Allow; the key is saved into config.js.
- Uses AVATAR_ID from config.js, else your first Masky avatar.
- Renders q1, q2, q3, closer as lip-synced video turns (mode "speak"), downloads them to
  live-demo/clips/, and writes clips/manifest.json. The page plays these local files,
  so the stage demo does not depend on venue Wi-Fi.
"""
import json, os, re, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "config.js")
CLIPS = os.path.join(HERE, "clips")
API = "https://masky.ai/api"


def cfg_get(name):
    m = re.search(name + r'\s*:\s*"([^"]*)"', open(CFG).read())
    return m.group(1) if m else ""


def cfg_set(name, value):
    s = open(CFG).read()
    s = re.sub(name + r'(\s*:\s*)"[^"]*"', lambda m: f'{name}{m.group(1)}"{value}"', s, count=1)
    open(CFG, "w").write(s)


def lines():
    s = open(CFG).read()
    return {k: re.search(k + r'\s*:\s*"([^"]*)"', s).group(1) for k in ("q1", "q2", "q3", "closer")}


def call(path, key=None, body=None, method=None):
    req = urllib.request.Request(API + path, method=method or ("POST" if body is not None else "GET"),
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **({"Authorization": "Bearer " + key} if key else {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def device_connect():
    st, d = call("/oauth/device", body={"client_name": "Grantmother live demo"})
    if st != 200:
        sys.exit(f"device flow failed: {st} {d}")
    print(f"\n>>> Open {d['verification_uri_complete']}\n>>> Check the code is {d['user_code']}, sign in, press Allow.\n")
    interval = d.get("interval", 5)
    while True:
        time.sleep(interval)
        st, t = call("/oauth/token", body={"grant_type": "urn:ietf:params:oauth:grant-type:device_code", "device_code": d["device_code"]})
        if st == 200:
            return t["access_token"]
        err = t.get("error")
        if err == "slow_down":
            interval = t.get("interval", interval + 5)
        elif err != "authorization_pending":
            sys.exit(f"connect stopped: {err}")


def main():
    key = os.environ.get("MASKY_API_KEY") or cfg_get("MASKY_API_KEY")
    if not key:
        key = device_connect()
        cfg_set("MASKY_API_KEY", key)
        print("Saved key into config.js")
    st, d = call("/avatars", key)
    if st != 200:
        sys.exit(f"/avatars -> {st} {d}")
    avatars = d.get("avatars", [])
    want = cfg_get("AVATAR_ID")
    av = next((a for a in avatars if a["avatarId"] == want), avatars[0] if avatars else None)
    if not av:
        sys.exit("No Masky avatar on this account. Create one at https://masky.ai (Avatars page, pick a voice), then rerun.")
    print("Avatar:", av.get("displayName"), av["avatarId"])
    if not want:
        cfg_set("AVATAR_ID", av["avatarId"])
    st, conv = call("/conversations", key, {"avatarOwnerUserId": av["avatarOwnerUserId"], "avatarId": av["avatarId"]})
    if st >= 300:
        sys.exit(f"/conversations -> {st} {conv}")
    print("Conversation (watch it render live):", conv.get("liveUrl"))
    os.makedirs(CLIPS, exist_ok=True)
    manifest = {"conversation": conv.get("shareSlug"), "clips": {}}
    for k, text in lines().items():
        st, r = call(f"/conversations/{conv['conversationId']}/turn", key, {"userText": text, "mode": "speak", "output": "video"})
        if st >= 300:
            sys.exit(f"turn {k} -> {st} {r}")
        tid = r["turn"]["id"]
        print(f"[{k}] rendering…", end="", flush=True)
        for _ in range(120):
            _, c = call(f"/conversations/by-slug/{conv['shareSlug']}", key)
            t = next((x for x in c.get("turns", []) if x.get("id") == tid), {})
            if t.get("status") == "error":
                sys.exit(f"\n[{k}] error: {t.get('errorMessage')}")
            if t.get("videoUrl"):
                fn = f"{k}.mp4"
                urllib.request.urlretrieve(t["videoUrl"], os.path.join(CLIPS, fn))
                manifest["clips"][k] = fn
                print(" saved", fn)
                break
            print(".", end="", flush=True)
            time.sleep(3)
        else:
            sys.exit(f"\n[{k}] timed out")
        json.dump(manifest, open(os.path.join(CLIPS, "manifest.json"), "w"), indent=2)
    print("Done. Refresh the page.")


if __name__ == "__main__":
    main()
