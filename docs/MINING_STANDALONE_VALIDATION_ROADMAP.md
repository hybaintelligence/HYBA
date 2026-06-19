# Mining Standalone Validation Roadmap

**Date:** 2026-06-19  
**Status:** Extraction plan and evidence boundary  
**Current tier:** HYPOTHETICAL for external hashrate, ASIC-efficiency, and revenue claims

## Current repository state

Mining is **not yet a standalone product repository**. The current implementation is still entangled with HYBA_FULLSTACK through `python_backend/pythia_mining/`, shared operational scripts, shared docs, and the repository-level claim evidence manifest. That means mining claims must still obey the HYBA_FULLSTACK validation protocol until a separate repository, CI pipeline, and evidence manifest exist.

## Standalone extraction criteria

Mining may be described as standalone only after it has all of the following:

1. a dedicated package or repository boundary for PULVINI/HENDRIX-Φ mining code;
2. independent CI running mining unit, integration, and benchmark checks;
3. a mining-specific evidence manifest with tiered claims and explicit boundaries;
4. a real double-SHA-256 nonce loop benchmark against a fixed Bitcoin or testnet header fixture;
5. repeated-run statistics for classical enumeration versus Φ-guided ordering;
6. power and hashrate measurements on the declared host hardware;
7. comparison to published ASIC specifications without claiming ASIC replacement unless measured on comparable hardware;
8. no dependence on PROMETHEUS, GAEA, COGITO, finance, or sovereign pitch materials for mining validation.

## Current admissible mining claim

The repository may claim only that it contains deterministic mining-adjacent components, local proof-of-work validation surfaces, PULVINI/HENDRIX-Φ proposal logic, and governance gates. It may **not** claim that PULVINI/HENDRIX-Φ beats Antminer S21, produces revenue, improves accepted-share rates, or accelerates random SHA-256 search until the mining evidence manifest records real benchmark results.

## Validation phases

| Phase | Target tier | Required evidence | External wording after pass |
| --- | --- | --- | --- |
| Real SHA-256 loop | PROTOTYPE_VALIDATED | Fixed real/testnet header, actual double-SHA-256, classical baseline, Φ-guided ordering, repeated-run stats | "Prototype benchmark on disclosed headers and hardware." |
| Host hashrate/power | PROTOTYPE_VALIDATED | Sustained hash attempts/sec, watts, J/TH, measurement method, hardware details | "Measured host efficiency; not ASIC-equivalent." |
| ASIC comparison | PROTOTYPE_VALIDATED only if measured or integration tested | Published ASIC specs cited separately from local results; firmware integration evidence if claimed | "Compared to published ASIC specs; no replacement claim." |
| Live pool economics | FORMALISM_VALIDATED is insufficient; operational evidence required | Pool-side accepted-share logs, stale/reject rates, power cost, duration, variance | "Operational result for the recorded pool/window only." |

## Extraction messaging

Use this internal wording until the criteria above pass:

> Mining is being separated into an independent validation track. Today it remains inside HYBA_FULLSTACK and is externally HYPOTHETICAL for hashrate, ASIC-efficiency, and revenue claims. The next gate is a real double-SHA-256 loop benchmark with repeated-run statistics and explicit ASIC comparison boundaries.
