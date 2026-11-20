# SPDX-License-Identifier: Apache-2.0
# fetch_code.py: first step of job vowel-test-v1. It downloads the analysis code exactly as
# registered (commit eff4365 of munimtechnologies/whale-vowel-test, the commit that published
# VOWEL-PREREG.md), and it refuses to go on until the grader test_vowel_results.py is public on
# the main branch with the same content as the copy shipped with the job. So the result cannot
# exist before its grader is published. Usage: python fetch_code.py <dest dir>
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import hashlib
import os
import sys
import time
import urllib.request

RAW = "https://raw.githubusercontent.com/munimtechnologies/whale-vowel-test/"
PIN = "eff43658502b31ac539877d201592452070a30c0"
CODE = ("describe_vowels.py", "vowel_test.py", "test_vowel_test.py")
GRADER = "test_vowel_results.py"
UA = "MV2-Munim-research/1.0 (mv2@munimtech.com)"
WAIT_S = 45 * 60


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def get_retry(url, tries=4):
    last = None
    for i in range(tries):
        try:
            return get(url)
        except Exception as e:  # noqa: BLE001 - retried, then re-raised
            last = e
            time.sleep(10 * (i + 1))
    raise last


def norm(b):
    return b.replace(b"\r\n", b"\n")


def save(dest, name, b):
    with open(os.path.join(dest, name), "wb") as f:
        f.write(b)
    print("%s md5 %s (%d bytes)" % (name, hashlib.md5(b).hexdigest(), len(b)), flush=True)


def main(argv):
    if len(argv) != 2:
        print("usage: python fetch_code.py <dest dir>")
        return 2
    dest = argv[1]
    os.makedirs(dest, exist_ok=True)
    for name in CODE:
        save(dest, name, get_retry(RAW + PIN + "/" + name))
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, GRADER), "rb") as f:
        local = norm(f.read())
    t0 = time.time()
    while True:
        try:
            pub = norm(get(RAW + "main/" + GRADER + "?t=%d" % int(time.time())))
        except Exception as e:  # noqa: BLE001 - not public yet, or a network error
            pub = None
            print("grader not readable yet: %s" % e, flush=True)
        if pub == local:
            break
        if pub is not None:
            print("public grader differs from the job copy", flush=True)
        if time.time() - t0 > WAIT_S:
            print("STOP: the grader is not public; nothing was computed", flush=True)
            return 1
        time.sleep(60)
    save(dest, GRADER, pub)
    print("grader is public and identical; code pinned at %s" % PIN, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
