#!/usr/bin/env python3
from __future__ import annotations

import sys
from typing import Tuple

try:
    import pyotp
except Exception:
    pyotp = None


def generate_secret() -> Tuple[str, str]:
    if pyotp is None:
        raise RuntimeError("pyotp not installed")
    secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name="aios@local", issuer_name="AIOS")
    return secret, uri


def verify_code(secret: str, code: str) -> bool:
    if pyotp is None:
        raise RuntimeError("pyotp not installed")
    totp = pyotp.TOTP(secret)
    return totp.verify(code.strip())


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: aios-2fa.py generate|verify <secret> <code>")
        return 2
    cmd = argv[1]
    if cmd == "generate":
        secret, uri = generate_secret()
        print(secret)
        print(uri)
        return 0
    if cmd == "verify":
        if len(argv) < 4:
            print("verify requires <secret> <code>")
            return 2
        secret = argv[2]
        code = argv[3]
        ok = verify_code(secret, code)
        print("ok" if ok else "fail")
        return 0 if ok else 1
    print("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
