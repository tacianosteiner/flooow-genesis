"""Offline, network-disabled native/JCA review. Never installs crypto or opens a DB.

Prerequisite: gradlew :applications:marketplace-operations:classes --offline.
An observed key-error/false difference is reported separately from comparable
boolean vectors; accepted() fail-closed equivalence is not exact error parity.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / 'applications/marketplace-operations-persistence-postgres/native/flooow_offline_mac32'
BUILDER = 'flooow-0090-crypto-builder:fe0425a2'


def run(args, **kwargs):
    return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs).stdout


def review():
    stdlib = sorted((Path.home()/'.gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib/2.3.21').glob('*/*.jar'))
    if len(stdlib) != 1:
        raise RuntimeError('Require existing pinned Kotlin stdlib 2.3.21')
    classpath = os.pathsep.join([str(ROOT/'applications/marketplace-operations/build/classes/kotlin/main'),str(stdlib[0])])
    with tempfile.TemporaryDirectory(prefix='flooow-0090-ed25519-') as scratch:
        work = Path(scratch)
        run(['javac','-cp',classpath,'-d',scratch,str(ROOT/'scripts/validation/Package0090Ed25519Vectors.java')])
        vectors = run(['java','-cp',scratch+os.pathsep+classpath,'Package0090Ed25519Vectors'])
        (work/'vectors.txt').write_text(vectors,encoding='ascii')
        shutil.copytree(NATIVE,work/'native')
        shutil.copy(NATIVE/'flooow_offline_mac32.c',work)
        shutil.copy(ROOT/'scripts/validation/package_0090_ed25519_native_harness.c',work/'harness.c')
        (work/'access').mkdir()
        for header in ('postgres.h','fmgr.h','varatt.h','access/detoast.h'):
            (work/header).write_text('',encoding='ascii')
        rows = [line.split('|') for line in vectors.splitlines()]
        invalid = next(row for row in rows if row[0]=='point_scalar_255')
        (work/'invalid.der').write_bytes(bytes.fromhex(invalid[1]))
        shell = '''set -eu
cd /review/native
make with_llvm=no > /review/build.txt 2>&1
nm -D --defined-only flooow_offline_mac32.so > /review/exports.txt
nm -D --undefined-only flooow_offline_mac32.so > /review/imports.txt
readelf -dW flooow_offline_mac32.so > /review/dynamic.txt
readelf -lW flooow_offline_mac32.so > /review/segments.txt
ldd flooow_offline_mac32.so > /review/dependencies.txt
cd /review
cc -std=c11 -Wall -Wextra -I. harness.c -lcrypto -o harness
./harness < vectors.txt > results.txt
cc -std=c11 -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer -I. harness.c -lcrypto -o harness-sanitized
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 ./harness-sanitized < vectors.txt > sanitized-results.txt
openssl pkey -pubin -inform DER -in invalid.der -pubcheck -noout > pubcheck.txt 2>&1
pg_config --version > versions.txt
openssl version >> versions.txt
'''
        image_id = run(['docker','image','inspect','--format','{{.Id}}',BUILDER]).strip()
        run(['docker','run','--rm','--network','none','--mount',f'type=bind,source={scratch},target=/review',
             '--entrypoint','sh',image_id,'-c',shell])
        outputs = dict(line.split('|') for line in (work/'results.txt').read_text().splitlines())
        if (work/'results.txt').read_bytes() != (work/'sanitized-results.txt').read_bytes():
            raise RuntimeError('Sanitized parity changed')
        exports = sorted(line.split()[-1] for line in (work/'exports.txt').read_text().splitlines())
        if exports != sorted(['Pg_magic_func','pg_finfo_timing_safe_equal32','timing_safe_equal32',
                              'pg_finfo_canonical_spki_ed25519_verify','canonical_spki_ed25519_verify']):
            raise RuntimeError('Unexpected native exports')
        imports = (work/'imports.txt').read_text()
        if any(symbol in imports for symbol in ('dlopen','socket','connect','fopen','open@@','write@@')):
            raise RuntimeError('Unexpected dynamic/IO import')
        segments = (work/'segments.txt').read_text()
        dynamic = (work/'dynamic.txt').read_text()
        if 'GNU_RELRO' not in segments or 'BIND_NOW' not in dynamic or 'GNU_STACK' not in segments:
            raise RuntimeError('Missing expected hardening')
        if any('RWE' in line for line in segments.splitlines() if 'GNU_STACK' in line):
            raise RuntimeError('Executable stack')
        results = [dict(name=row[0],spki_hex=row[1],message_hex=row[2],signature_hex=row[3],
                        jca=row[4],native=outputs[row[0]],exact_match=row[4]==outputs[row[0]],
                        accepted_fail_closed_match=(row[4]=='true')==(outputs[row[0]]=='true')) for row in rows]
        return dict(baseline='778d2c0687395ca5865611e56b2ddc036b091c96',
                    status='HOLD_EXACT_KEY_ERROR_CONTRACT',builder=image_id,
                    versions=(work/'versions.txt').read_text().splitlines(),
                    native_source_sha256=hashlib.sha256((NATIVE/'flooow_offline_mac32.c').read_bytes()).hexdigest(),
                    native_binary_sha256=hashlib.sha256((work/'native/flooow_offline_mac32.so').read_bytes()).hexdigest(),
                    exports=exports,imports=imports.splitlines(),
                    dependencies=re.sub(r' \(0x[0-9a-f]+\)', '', (work/'dependencies.txt').read_text()).splitlines(),
                    hardening_segments=segments.splitlines(),dynamic=dynamic.splitlines(),
                    invalid_key_openssl_pubcheck=(work/'pubcheck.txt').read_text().strip(),
                    asan_ubsan='PASS_BOUNDED_HARNESS_NOT_INSTRUMENTED_OPENSSL',
                    mac32_regression='EQUAL_AND_UNEQUAL_PASS',
                    vector_count=len(results),exact_match_count=sum(r['exact_match'] for r in results),
                    accepted_fail_closed_match_count=sum(r['accepted_fail_closed_match'] for r in results),
                    vectors=results,postgres_runtime_parity='NOT_RUN',protected_database_mutation=False)


if __name__ == '__main__':
    evidence = review()
    target=ROOT/'docs/evidence/PACKAGE-0090-ED25519-NATIVE-REVIEW.json'
    target.write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in evidence.items() if k in (
        'status','vector_count','exact_match_count','accepted_fail_closed_match_count',
        'native_binary_sha256','asan_ubsan','invalid_key_openssl_pubcheck')},indent=2))
