# SPDX-License-Identifier: Apache-2.0
# gate.py: first step of job vowel2-test-v1. It downloads the shared helpers exactly as first
# registered (describe_vowels.py and vowel_test.py at commit eff4365 of
# munimtechnologies/whale-vowel-test), and it refuses to go on until VOWEL2-PREREG.md, the
# analysis vowel2_test.py, its unit tests and the grader test_vowel2_results.py are public on the
# main branch with the same content as the copies shipped with the job. So the result cannot
# exist before its registration and grader are published. Usage: python gate.py <dest dir>
# MV2, Munim, Inc. (mv2@munimtech.com). Made with AI agents. Apache-2.0.
import hashlib
import os
import sys
import time
import urllib.request

RAW = "https://raw.githubusercontent.com/munimtechnologies/whale-vowel-test/"
PIN = "eff43658502b31ac539877d201592452070a30c0"
PINNED = ("describe_vowels.py", "vowel_test.py")
MUST_MATCH = ("VOWEL2-PREREG.md", "vowel2_test.py", "test_vowel2_test.py",
              "test_vowel2_results.py")
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
        print("usage: python gate.py <dest dir>")
        return 2
    dest = argv[1]
    os.makedirs(dest, exist_ok=True)
    for name in PINNED:
        save(dest, name, get_retry(RAW + PIN + "/" + name))
    here = os.path.dirname(os.path.abspath(__file__))
    local = {}
    for name in MUST_MATCH:
        with open(os.path.join(here, name), "rb") as f:
            local[name] = norm(f.read())
    t0 = time.time()
    while True:
        pub, same = {}, True
        for name in MUST_MATCH:
            try:
                pub[name] = norm(get(RAW + "main/" + name + "?t=%d" % int(time.time())))
            except Exception as e:  # noqa: BLE001 - not public yet, or a network error
                pub[name] = None
                print("%s not readable yet: %s" % (name, e), flush=True)
            if pub[name] != local[name]:
                same = False
                if pub[name] is not None:
                    print("public %s differs from the job copy" % name, flush=True)
        if same:
            break
        if time.time() - t0 > WAIT_S:
            print("STOP: the registration is not public; nothing was computed", flush=True)
            return 1
        time.sleep(60)
    for name in MUST_MATCH:
        save(dest, name, pub[name])
    print("registration, code and grader are public and identical; helpers pinned at %s" % PIN,
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
