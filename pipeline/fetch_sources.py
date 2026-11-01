#!/usr/bin/env python3
"""Unduh semua sumber yang terdaftar di sources.json pada commit yang dikunci.

Hasil: sources/<id>/<berkas> dan sources.lock.json (sha256 tiap berkas).
Jalankan:  python3 pipeline/fetch_sources.py
"""
import hashlib, json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "pipeline", "sources.json"), encoding="utf8"))


def raw_url(repo, commit, path):
    owner_repo = repo.rstrip("/").split("github.com/")[1]
    return f"https://raw.githubusercontent.com/{owner_repo}/{commit}/{path}"


def main():
    lock = {}
    for s in CFG["sumber"]:
        outdir = os.path.join(ROOT, "sources", s["id"])
        os.makedirs(outdir, exist_ok=True)
        for path in s["berkas"]:
            dest = os.path.join(outdir, os.path.basename(path))
            if not os.path.exists(dest):
                url = raw_url(s["repo"], s["commit"], path)
                print("unduh", url, file=sys.stderr)
                with urllib.request.urlopen(url, timeout=120) as r, open(dest + ".part", "wb") as f:
                    f.write(r.read())
                os.replace(dest + ".part", dest)
            h = hashlib.sha256(open(dest, "rb").read()).hexdigest()
            lock[f"{s['id']}/{os.path.basename(path)}"] = {"commit": s["commit"], "sha256": h,
                                                          "bytes": os.path.getsize(dest)}
    json.dump(lock, open(os.path.join(ROOT, "pipeline", "sources.lock.json"), "w"), indent=1, sort_keys=True)
    print(f"{len(lock)} berkas siap", file=sys.stderr)


if __name__ == "__main__":
    main()
