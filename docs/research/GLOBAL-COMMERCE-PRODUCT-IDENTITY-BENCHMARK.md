# Product identity — blind cross-market benchmark

Status: **experiment design; no collector, model or implementation authority**. 2026-10-12. Goal: test whether the same physical product or explicitly defined product family can be linked across Chinese supplier listings, creator posts/lives, TikTok Shop, Amazon and Mercado Livre without dangerous false merges.

## Ground truth and blinding

Build a licensed, time-stamped corpus with source URLs/document IDs, captured listing snapshots, images, specifications and provenance. A trained reviewer pair labels identity using manufacturer/model/SKU or direct physical-spec evidence; adjudicate disagreements without seeing model output or target market popularity. Separate exact physical product from variant/family. Blind the matcher to ground-truth labels, candidate popularity and downstream outcome; hold out suppliers, brands, categories and markets, not just random pairs. Freeze training, calibration and test splits before scoring. No unlabeled pair becomes a negative by default.

Minimum strata: clear positive exact pairs; hard negative same-shape different product; same product under different brand/private label; OEM variants; packaging-only changes; size, material, voltage and technical-feature differences; accessory versus main product; copied imagery; supplier SKU reuse; multilingual/translated titles; listing relabeling; ambiguous bundle quantities. Include China-only, cross-border and Brazil pairs, and cases with missing dimensions/images. Record class prevalence and source provenance so duplicate syndicated listings cannot inflate independent evidence.

Candidate signals: image similarity, title tokens/translation, dimensions, materials, model number, technical attributes, supplier/factory SKU, brand, packaging, price and HS/category. HS and price are weak context, never exact identity. Every signal retains origin and missingness; a scalar score alone cannot grant `EXACT`.

## Identity adjudication

`EXACT` requires matching hard identifiers or independently reviewed distinctive physical attributes with no material conflict. `CANDIDATE` means plausible but insufficient. `CONFLICT` records a material incompatible attribute or contradictory authoritative identifier. `UNRESOLVED` covers sparse or unreliable inputs. Family/variant relationship is explicit and must not be silently collapsed into exact. False merge is costlier than missed merge; threshold selection should minimize false merges under a predeclared bound, with human review for high-impact transitions.

Report pairwise precision/recall by stratum, false-merge rate with confidence interval, false-split rate, candidate-review workload, abstention, calibration, source-specific error and performance under withheld images/identifiers. Also test transitive closure: A≈B and B≈C must not force A=C. A single false bridge can contaminate a market diffusion graph. Freeze an error ledger with adjudicated examples; no success claim before an independently held-out evaluation.

Experiment exit: promote only the evidence-backed identity edges into a future *research graph*; no OpportunityCase, sourcing decision or import authority follows automatically. Licensing and retention approval precede data acquisition.
