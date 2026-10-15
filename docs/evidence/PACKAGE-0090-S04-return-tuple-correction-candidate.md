# Package 0090 S04 return-tuple correction candidate

SOURCE_CORRECTION_CANDIDATE_READY=YES. This is a proved, frozen candidate only. Canonical V043 was neither written, staged, committed nor executed. The patch was generated from frozen Git-LF bytes, applied only in memory for hashes/AST comparison, and checked read-only with git apply --check --cached; the actual index entry remained unchanged. No corrected or original S04 invocation, READY or authority promotion occurred.

The correction adds exactly ::pg_catalog.text to h.version, h.type and h.script in the existing RETURN QUERY. All three expressions occupy ONE physical source line. Therefore the exact minimal patch replaces one line, with three expression changes; reporting three physical changed lines would be false, and reformatting to force that count would add forbidden whitespace churn. No other source bytes change. The API/attributes outside the body are AST-identical, and the SELECT trees differ only by the three expected TypeCast nodes. Removing those nodes recovers the exact prior SELECT; reversing the one source replacement recovers the entire prior V043 byte-for-byte, including the fence, exceptions, guards, owner and ACL statements.

Two fresh owned PostgreSQL 18.4 targets reproduced raw 42804 for the full projection and each version/type/script position. The QUALIFIED candidate pg_temp helper returned 00000 and exactly the independent 42 six-field history rows on both targets. WITH ORDINALITY retained actual helper delivery order 1..42 rather than sorting results to manufacture order. All three outputs are exactly pg_catalog.text; raw varchar and candidate text binary-send payloads matched on every row under UTF8. NULL remained NULL.

Both targets created pg_temp.text and public.text composite shadow types and put pg_temp,public before pg_catalog in search_path. Unqualified text resolved to a different OID, proving the lure was effective, while the three qualified casts still resolved to provider text OID 25 and the candidate helper returned exactly 42 rows. Public shadow types were removed; temporary helpers/types vanished with their own sessions; both owned targets and credentials were destroyed. These are candidate type/tuple proofs, not S04 authorization or security-negative runtime tests.

Ten new candidate assertions per target passed, with nine reused raw compatibility and 93 reused foundation assertions (112 per target), using normal Python and Python -O. Static source/API/SELECT/inverse/index/applicability assertions also passed. There were no accepted runtime failures. No Kotlin/Java code changed; consumer inspection is not represented as an executed S04 application test.

The exact correction implements the already intended contract: SPEC-0090 sections 21.1/S04 and lines 284,314–320,819 declare text outputs and unchanged history ordering; ADR-0090 auditor/history authority stays unchanged. The section21.7 inventory is output/type traceability, not authority to change Flyway columns. No ADR or SPEC amendment is required for these three casts. No normative document was edited. The narrower-character unqualified ::text is expressly rejected because it is search-path dependent; CAST(... AS pg_catalog.text) is equivalent but longer; changing the return API or Flyway columns is forbidden and broader.

The source hash and future Flyway checksum DO change if the candidate is later adopted. This does not authorize migration mutation or repair. Current qualification evidence shows no canonical migration application; shared/production execution history was not independently queried. Before adoption, explicit source authority and release coordination must rebaseline source/body/derived qualification hashes, AST/semantic/currentness/ACL/native fixtures and release records; old source-hash validators correctly remain pinned now. The fence is retained. No 190-site work or T10 work continued.

The three direct S04 application/test consumer files retain the same arguments and six-column contract; GovernedJdbc.history reads the three textual positions with getString. Broader history readers, baseline tests and validation/hash consumers are listed separately. No downstream public contract break is expected; generated source/body/AST identity expectations do require coordinated refresh after authority. No consumers were modified.

NEXT, not executed: obtain explicit authority to apply exactly the frozen three-expression patch. Candidate readiness is not mutation authority.

Frozen current Git-LF SHA256: b0ea86b6ba355fdf25fe09836bd4b75e4a4a2ad88ab7ef0e4724ca0d5a013e7d

Hypothetical candidate Git-LF SHA256: 007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a

Computed future Flyway CRC32: 1665026701 -> 1279591798

Direct S04 consumer files: 3; broader history files: 16 (overlap retained).
