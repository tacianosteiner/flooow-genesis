# Disposable native qualification prototype

This is an experimental PostgreSQL 18.4 shared-preload/login component, supervisor and receiver. It implements bounded native enrollment mechanisms against synthetic fixtures only. Read the qualification review under docs/evidence/package-0090-g3f4-disposable-native-qualification before interpreting results. No production or full-watchdog PASS is claimed.

Prerequisites: Python, Docker with the pinned image already available, network access to the SHA256-pinned official PostgreSQL client header, and the explicit disposable implementation authority. The frozen scoped seccomp profile permits clone3; it does not disable seccomp. No host database or production credentials are needed. The local temporary directory currently follows this workspace's Windows account path.

From the repository root, use a fresh evidence destination outside frozen evidence:

```powershell
python scripts/validation/package_0090_native_qualification/run_round3.py --evidence-output C:\Users\xmz_r\AppData\Local\Temp\flooow-native-new-run
```

Add `--measure` for the shorter measurement scenario. Existing names or evidence directories are rejected. The builder compiles in an owned network-none container and removes it in cleanup. The fixture uses no plaintext password files. Failure evidence is retained and a failed harness or case returns nonzero. Abrupt termination of the host process can prevent finally cleanup; inspect only the experiment ownership label before any manual removal. No canonical container is an allowed cleanup target.

The 5 s abort budget, registry capacity, polling intervals, injected delays and CPU/I/O generators are harness controls, never policy authority. Request/load overlap is not measured. Runtime records retain compiled source snapshots; final driver output/exit handling changes were syntax checked after the recorded runs. Re-running creates new evidence and must never overwrite or silently promote the archived qualification.
