# SPDX-License-Identifier: Apache-2.0
# gate3b.py: first step of job vowel3-coart-a1-v1. It refuses to go on until
# VOWEL3-AMENDMENT-1.md, vowel3b_test.py and its unit tests are public on the main branch of
# munimtechnologies/whale-vowel-test with the same content as the copies shipped with the job,
# so the amended result cannot exist before the amendment is published.
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import hashlib
import os
import sys
import time
import urllib.request

RAW = "https://raw.githubusercontent.com/munimtechnologies/whale-vowel-test/main/"
MUST_MATCH = ("VOWEL3-AMENDMENT-1.md", "vowel3b_test.py", "test_vowel3b_test.py")
UA = "MV2-Munim-research/1.0 (mv2@munimtech.com)"
WAIT_S = 45 * 60


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def norm(b):
    return b.replace(b"\r\n", b"\n")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    local = {}
    for name in MUST_MATCH:
        with open(os.path.join(here, name), "rb") as f:
            local[name] = norm(f.read())
    t0 = time.time()
    while True:
        same = True
        for name in MUST_MATCH:
            try:
                pub = norm(get(RAW + name + "?t=%d" % int(time.time())))
            except Exception as e:  # noqa: BLE001 - not public yet, or a network error
                print("%s not readable yet: %s" % (name, e), flush=True)
                same = False
                continue
            ok = pub == local[name]
            print("%s local %s remote %s %s" % (name, hashlib.md5(local[name]).hexdigest(),
                                                hashlib.md5(pub).hexdigest(),
                                                "same" if ok else "DIFFERENT"), flush=True)
            same = same and ok
        if same:
            print("amendment and code are public and identical", flush=True)
            return 0
        if time.time() - t0 > WAIT_S:
            print("STOP: the amendment is not public; nothing was computed", flush=True)
            return 1
        time.sleep(60)


if __name__ == "__main__":
    sys.exit(main())
