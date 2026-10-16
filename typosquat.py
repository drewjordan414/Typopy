#!/usr/bin/env python3
"""Generate typosquat permutations of a domain

Educational / defensive tool: feed it your own domain to see the lookalikes an
attacker would register, or to seed a brand-monitoring watchlist. For live
"is it registered" checks use dnstwist --registered; this is offline generation.
"""
import argparse
import socket
import sys

# adjacent keys on a QWERTY board, for fat-finger replacements
_QWERTY = {
    "q": "wa", "w": "qeas", "e": "wrsd", "r": "etdf", "t": "ryfg", "y": "tugh",
    "u": "yihj", "i": "uojk", "o": "ipkl", "p": "ol", "a": "qwsz", "s": "awedxz",
    "d": "serfcx", "f": "drtgvc", "g": "ftyhbv", "h": "gyujnb", "j": "huikmn",
    "k": "jiolm", "l": "kop", "z": "asx", "x": "zsdc", "c": "xdfv", "v": "cfgb",
    "b": "vghn", "n": "bhjm", "m": "njk",
    "0": "9o", "1": "2q", "2": "13w", "3": "24e", "4": "35r", "5": "46t",
    "6": "57y", "7": "68u", "8": "79i", "9": "80o",
}
# characters that read as each other at a glance
_HOMOGLYPH = {
    "o": "0", "l": "1i", "i": "1l", "e": "3", "a": "4", "s": "5", "b": "8",
    "g": "9", "t": "7", "z": "2", "0": "o", "1": "l",
}
# common words appended/prepended in combosquats
_COMBO = ("login", "secure", "account", "vpn", "mail", "support", "verify", "portal")


def _split(domain):
    """'antonsystems.cloud' -> ('antonsystems', 'cloud'). ponytail: last-dot split,
    multi-part TLDs (co.uk) not handled — add a PSL lookup if you ever need them."""
    name, _, tld = domain.strip().lower().rstrip(".").rpartition(".")
    if not name:  # no dot at all
        return domain.strip().lower(), ""
    return name, tld


def omission(name):
    return {name[:i] + name[i + 1:] for i in range(len(name))}


def repetition(name):
    return {name[:i + 1] + name[i] + name[i + 1:] for i in range(len(name))}


def transposition(name):
    return {name[:i] + name[i + 1] + name[i] + name[i + 2:] for i in range(len(name) - 1)}


def replacement(name):
    out = set()
    for i, ch in enumerate(name):
        for sub in _QWERTY.get(ch, ""):
            out.add(name[:i] + sub + name[i + 1:])
    return out


def homoglyph(name):
    out = set()
    for i, ch in enumerate(name):
        for sub in _HOMOGLYPH.get(ch, ""):
            out.add(name[:i] + sub + name[i + 1:])
    return out


def insertion(name):
    out = set()
    for i in range(1, len(name)):
        out.add(name[:i] + name[i - 1] + name[i:])  # dup neighbour
        out.add(name[:i] + "-" + name[i:])          # hyphen
    return out


def bitsquat(name):
    out = set()
    for i, ch in enumerate(name):
        for bit in range(8):
            flipped = chr(ord(ch) ^ (1 << bit))
            if flipped.isalnum() and flipped.isascii():
                out.add(name[:i] + flipped + name[i + 1:])
    return out


def plural(name):
    return {name + "s", name[:-1]} if name else set()


# techniques that only touch the name part
_NAME_TECHS = {
    "omission": omission, "repetition": repetition, "transposition": transposition,
    "replacement": replacement, "homoglyph": homoglyph, "insertion": insertion,
    "bitsquat": bitsquat, "plural": plural,
}
_ALT_TLDS = ("com", "net", "org", "io", "co", "xyz", "online", "app")


def generate(domain):
    """Return {technique: sorted[candidate domains]} minus the original."""
    name, tld = _split(domain)
    full = f"{name}.{tld}" if tld else name
    result = {}
    for tech, fn in _NAME_TECHS.items():
        cands = {f"{n}.{tld}" if tld else n for n in fn(name) if n and n != name}
        result[tech] = sorted(cands - {full})
    result["tld_swap"] = sorted({f"{name}.{t}" for t in _ALT_TLDS if t != tld})
    combo = {f"{name}-{w}.{tld}" for w in _COMBO}
    combo |= {f"{w}-{name}.{tld}" for w in _COMBO}
    result["combosquat"] = sorted(c for c in combo if tld)
    return result


def resolves(domain):
    try:
        socket.getaddrinfo(domain, None)
        return True
    except (socket.gaierror, UnicodeError):
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("domain", nargs="?", help="a domain you own, e.g. goonlab.xyz")
    ap.add_argument("--resolve", action="store_true",
                    help="flag candidates that currently resolve in DNS (slow)")
    args = ap.parse_args(argv)

    domain = args.domain or input("Your domain: ").strip()
    if not domain or "." not in domain:
        ap.error("give a real domain with a TLD, e.g. goonlab.xyz")

    groups = generate(domain)
    total = 0
    for tech, cands in groups.items():
        if not cands:
            continue
        print(f"\n# {tech} ({len(cands)})")
        for c in cands:
            total += 1
            if args.resolve:
                print(f"  {'[LIVE]' if resolves(c) else '      '} {c}")
            else:
                print(f"  {c}")
    print(f"\n{total} candidates across {len([g for g in groups.values() if g])} techniques.",
          file=sys.stderr)


def _selftest():
    g = generate("goonlab.xyz")
    assert "oonlab.xyz" in g["omission"]
    assert "gonolab.xyz" in g["transposition"]       # swap o/o->n? check real swap
    assert "g0onlab.xyz" in g["homoglyph"]
    assert "goonlab.com" in g["tld_swap"]
    assert "goonlab-login.xyz" in g["combosquat"]
    assert "goonlabs.xyz" in g["plural"]
    assert all("goonlab.xyz" not in v for v in g.values()), "original must be excluded"
    # single-label input shouldn't crash
    generate("localhost")
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        main()
