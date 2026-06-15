# HYBA Φ-Trifecta Benchmark Portfolio: Topological Scaling

## BLUF

The current HENDRIX-Φ solver uses the M32 surface as its production-safe baseline: 32 domains derived from the dodecahedron/icosahedron compound and the H3 icosahedral symmetry group.

The next scaling breakthrough is not merely increasing domain count from 32 to 60. The step-change comes from moving from H3 symmetry to H4 symmetry, where the available φ-preserving transformations expand from 120 to 14,400.

```text
M32 baseline       -> 32 domains, H3 symmetry, 120 transforms
Football surface   -> 60 domains, H3 symmetry, finer partition only
600-cell / H4      -> 120 vertices, H4 symmetry, 14,400 transforms
120-cell / H4      -> 600 vertices, H4 symmetry, fuller 4D φ-manifold
```

## Scaling matrix

| Upgrade | Vertices | Expected gain vs M32 | Interpretation |
|---|---:|---:|---|
| Football / truncated icosahedron | 60 | 1.6-2.2x | Same H3 symmetry class, finer domain cover. Useful but not transformational. |
| 600-cell / H4 | 120 | 6-26x | Symmetry group rises to 14,400; the geometry itself changes class. |
| 120-cell / H4 | 600 | 30-170x | More domains plus full H4 manifold, likely the first true 50x+ scaling tier. |

## Scientific interpretation

The current solver already changes the problem class from flat nonce enumeration to structured traversal over a φ-resonant manifold. The M32 model is the correct first production surface because it is auditable, deterministic, computationally small, and already tied to the HENDRIX-Φ evidence stack.

The football upgrade is attractive because it is visually intuitive and easier to explain, but it does not create a new symmetry class. It gives more domains, not a fundamentally larger transformation group.

The H4 upgrade is qualitatively different. H4 contains the 600-cell and 120-cell structures and expands the φ-preserving symmetry group by 120x relative to H3. That is where the practical roadmap should focus after the M32 production run proves pool-side accepted shares.

## Roadmap

1. Preserve M32 as the production baseline until accepted-share evidence exists.
2. Add an offline M60 football benchmark only as a transitional visual/control surface.
3. Implement H4 600-cell search as the first real scaling experiment.
4. Extend to 120-cell / 600-domain routing only after H4 correctness and cost are established.
5. Keep all higher-dimensional gains labelled as benchmark projections until replayed against matched pool/job evidence.

## Claim boundary

Supported today:

- M32 structured traversal baseline.
- HENDRIX-Φ / PULVINI benchmark comparison against unstructured Grover assumptions.
- Topological explanation for why H4 can be a step-change.

Not claimed until tested:

- Live mining revenue improvement from H4.
- Accepted-share uplift from M60, H4, or 120-cell routing.
- Hardware-level acceleration from higher-dimensional topology.
- Block discovery guarantee.

The correct external wording is:

> HYBA's current production baseline is M32. The benchmark portfolio shows a plausible scaling path from H3 to H4 topology, with the real step-change expected at the 600-cell / 120-cell tier rather than the 60-domain football tier.
