# Exact-byte publication requirements

Three generated evidence-helper `.pyc` files are preserved on disk and excluded
through exact local `info/exclude` entries. They are not source/evidence inputs;
no tracked ignore configuration or historical artifact is modified. Frozen
inventories exclude generated `__pycache__` consistently.

Frozen source inventories use exact worktree bytes, not normalized Git text.
Existing evidence attributes preserve public binary/vector/raw evidence bytes.
Publish only the six experimental successor code/evidence directories, using
`git -c core.autocrlf=false add -- <explicit directories>` to retain exact source
bytes. Validate every staged Git blob against its actual worktree SHA256 before
commit. An index-only PASS is insufficient if bytes were normalized.

Reproduction checkouts must use `core.autocrlf=false` and verify the recorded exact
source and evidence hashes before compilation. No frozen historical file is edited
to accommodate a line-ending conversion. Root attributes, canonical artifacts,
migrations and application runtime code remain unchanged.

The package captures a pre-publication audit at input HEAD. Publication commit IDs
cannot be embedded in their own content. Final local/remote HEAD, push result and
clean-worktree verification are reported after publication, separately from the
immutable pre-publication evidence snapshot. No historical PASS changes meaning
merely because its evidence is later committed.
