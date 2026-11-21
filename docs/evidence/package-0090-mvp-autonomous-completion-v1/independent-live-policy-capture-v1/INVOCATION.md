Use only while the owned custodian is held at the explicit pre-Reader live barrier. All arguments must come from the actual published managed-container/kernel record, not guessed values. The SHA is a byte binding only. This invocation creates one offline helper and removes only that helper; it does not mutate or signal the target.

```powershell
python -B docs/evidence/package-0090-mvp-autonomous-completion-v1/independent-live-policy-capture-v1/capture.py --container <FULL_OWNED_CONTAINER_ID> --image <EXACT_SHA256_IMAGE_ID> --label-key <OWNERSHIP_LABEL_KEY> --label-value <EXACT_OWNERSHIP_LABEL_VALUE> --daemon <ACTUAL_DAEMON_UUID> --pid <CUSTODIAN_PID> --fd <POLICY_FD> --start-ticks <ORIGINAL_START_TICKS> --device <DEVICE> --inode <INODE> --size <SIZE_1_TO_4096> --sha256 <ORIGINAL_RECORD_SHA256>
```

No real invocation has been executed yet. The fixed helper uses the local pinned07fc image, no pull, networknone, rootfsRO, no host binds, explicit target-container PID namespace, cap-dropALL+SYS_PTRACE and noNewPrivs. Source arrives over Docker stdin; compiler scratch is private tmpfs. An unused anonymous volume declared by the base image is not a host bind and is removed with the helper.

The capture checks original FD flags, process birth, regular inode ownership UID10003, exact device/inode/size, all four seals, read-only open and byte hash. It records only that nonsecret record as hex plus stat/seal/hash metadata. It cannot issue approval or acceptance. Do not feed secret records to this purpose-bound harness.
