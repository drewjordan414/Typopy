# Typopy

Offline typosquat permutation generator. Feed it a domain **you own or are
authorized to test** and it prints the lookalike domains an attacker would
register — useful for seeding a brand-monitoring watchlist or for learning the
mechanics behind tools like `dnstwist`.

Pure Python standard library — no dependencies, no install.

## Usage

```bash
python3 typosquat.py goonlab.xyz              # print all candidates, grouped by technique
python3 typosquat.py                          # prompt for the domain
python3 typosquat.py antonsystems.cloud --resolve   # flag [LIVE] candidates already in DNS
python3 typosquat.py --selftest               # run the built-in asserts
```

`--resolve` does a DNS lookup per candidate (slow, and only tells you a name
resolves — not who owns it). For real "registered + has MX" intel, use
`dnstwist --registered`.

## Techniques

| Technique | What it does | `google.xyz` → |
|---|---|---|
| omission | drop one character | `google.xyz` |
| repetition | double a character | `google.xyz` |
| transposition | swap two adjacent characters | `google.xyz` |
| replacement | adjacent QWERTY key | `google.xyz` |
| homoglyph | lookalike character | `google.xyz` |
| insertion | add a char / hyphen | `google.xyz`, `goo-gle.xyz` |
| bitsquat | single-bit flip (memory errors) | `google.xyz` |
| plural | add / drop a trailing `s` | `google.xyz` |
| tld_swap | same name, different TLD | `google.com` |
| combosquat | prepend/append a keyword | `google-login.xyz` |

The input domain itself is always excluded from the output.

## Scope / ethics

Only run this against domains you own or are explicitly authorized to assess.
Generating lookalikes of a third-party brand to deceive real people is
domain fraud, not research. Intended uses: defensive monitoring of your own
domains, and lookalike-domain practice inside an authorized red-team
engagement against the client's in-scope domains.

## Limitations

- Multi-part TLDs (`co.uk`, `com.au`) are treated as a single trailing label.
  Add a public-suffix-list lookup if you need those.
- Generation only — it does not register, resolve (except `--resolve`), or
  score candidates by visual similarity.
