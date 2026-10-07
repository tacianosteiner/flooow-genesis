# EXP-0016 â€” Findings

## Hypothesis

Flooow should not merely say "confidence is low".

It should be able to say:

- exactly what is unknown;
- why that unknown matters;
- what evidence could resolve it;
- what it costs to acquire;
- what decision could improve;
- whether learning is worth the cost.

## Success criteria

- gaps are explicit and scoped;
- missing evidence is distinct from zero;
- unsupported guesses cannot satisfy a gap;
- acquisition methods declare required evidence;
- VoI uses governed economic inputs;
- negative or weak VoI blocks acquisition;
- high expected improvement can justify acquisition;
- hard deadlines and delay cost matter;
- result remains non-canonical and non-executable;
- model prose cannot override policy.

## Architectural consequence

Belief revision now feeds an active learning loop:

belief
  â†“
uncertainty
  â†“
information gap
  â†“
VoI
  â†“
experiment / evidence acquisition
  â†“
new evidence
  â†“
belief revision
