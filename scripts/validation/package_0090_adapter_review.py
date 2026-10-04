"""Independent normative SPEC -> actual Kotlin statement/tuple review.

No implementation-generator imports or maps. SQL owner/ACL/AST review is run
separately by package_0090_independent_review. This proves source contracts,
not installed PostgreSQL privileges or honest deployment identities.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony'
SPEC = ROOT / 'docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md'


def review(overrides=None):
    overrides = overrides or {}
    def source(name):
        return overrides.get(name, (SOURCE / name).read_text(encoding='utf-8-sig'))
    spec = SPEC.read_text(encoding='utf-8-sig')
    contract = source('GovernedCall.kt')
    normative = re.findall(r'\*\*(S\d+)\*\* CALLER_SLOT=(\w+).*?`public\.(\w+)\(([^`]+)\)`', spec, re.S)
    actual = re.findall(r'(S\d+)\(GovernedSlot\.(\w+), "(\w+)", "([^"]+)"\)', contract)
    if len(normative) != 18 or actual != normative:
        raise ValueError('Normative stage/slot/name/input-name/order/type mismatch')
    if 'fields.joinToString(",") { "?::pg_catalog.${it.type}" }' not in contract:
        raise ValueError('Explicit JDBC type vector missing')
    tuples = dict(re.findall(r'val (S\d+_(?:INPUT|OUTPUT)) = GovernedFrame.fields\("([^"]+)"\)', contract))
    reviewed = []
    for stage in ('S05','S06','S07','S08','S09','S10','S11','S12','S18'):
        block = spec.split('**'+stage+' frozen tuple contract**',1)[1].split('**S',1)[0]
        for direction in ('INPUT','OUTPUT'):
            if stage == 'S18' and direction == 'INPUT':
                # SPEC22.2 overrides the frozen private 73-field scratch tuple.
                if 'S18_INPUT' in tuples:
                    raise ValueError('Private S18 facts exposed as a client tuple')
                continue
            declaration = re.search(direction+r': ([^\n]+)', block)[1].strip().rstrip('.')
            fields = []
            for entry in declaration.split('; '):
                name, kind = re.fullmatch(r'\d+=(\w+) (.+)',entry).groups()
                kind = kind.replace('timestamptz(6)','timestamptz').replace('integer','int4').replace('bigint','int8')
                fields.append(name+' '+kind)
            key = stage+'_'+direction
            if tuples.get(key) != ','.join(fields):
                raise ValueError('Frozen normative tuple mismatch '+key)
            reviewed.append(key)
    names = ['GovernedCall.kt','GovernedFrame.kt','GovernedJdbc.kt','GovernedAttestation.kt','GovernedOfflineFieldProofLauncher.kt']
    main = source('PostgresCeremonyComposition.kt').split('fun main(args: Array<String>)',1)[1]
    operational = main+'\n'+'\n'.join(source(name) for name in names)
    prohibited = re.findall(r'\b(?:s2a_(?:begin|persist|v042_)\w*|command_principal|command_credential_revision|command_permission_grant|transaction_identity_locks|Postgres(?:AcceptedAttestationVerifier|AttestedCommandAuthorityIssuer|TransactionIdentityWriter|CommandAuthorization|OfflineFieldProofBoundaryVerifier|OfflineFieldProofReconciler)|PostgresCeremonyComposition\s*\()',operational)
    if prohibited:
        raise ValueError('Direct legacy/raw production dependency '+str(prohibited))
    if 'GovernedOfflineFieldProofLauncher(' not in main or 'GovernedDeployment.environment(environment)' not in main:
        raise ValueError('Governed launcher is not the executable composition')
    jdbc = source('GovernedJdbc.kt')
    if 'Connection.TRANSACTION_READ_COMMITTED' not in jdbc or 'Connection.TRANSACTION_REPEATABLE_READ' not in jdbc or 'connection.rollback()' not in jdbc:
        raise ValueError('Transaction policy missing')
    for invariant in ('verify(envelope.copyOf())','"verified_decision_request" to envelope','check(decisionActive && prepared)','check(decisionActive && !prepared)','finally { decisionActive = false }'):
        if invariant not in jdbc:
            raise ValueError('Decision connection/unchanged-envelope invariant missing')
    # Every dynamic SQL call is sourced from the eighteen closed enum members.
    for name in names:
        for expression in re.findall(r'prepareStatement\(([^\n]+)',source(name)):
            if not expression.startswith('call.sql)'):
                raise ValueError('Unreviewed SQL selector '+name)
    hashes = {name:hashlib.sha256(source(name).encode()).hexdigest() for name in names}
    bridge=(ROOT/'applications/marketplace-operations/src/main/kotlin/io/flooow/marketplace/operations/authorization/GovernedCredentialProof.kt').read_text()
    if 'fun derive(credential: CommandCredential): ByteArray = credential.digest()' not in bridge or 'java.sql' in bridge:
        raise ValueError('Retained protected credential derivation changed')
    hashes['GovernedCredentialProof.kt']=hashlib.sha256(bridge.encode()).hexdigest()
    hashes['production_main'] = hashlib.sha256(main.encode()).hexdigest()
    return dict(method='INDEPENDENT_NORMATIVE_SPEC_AND_ACTUAL_KOTLIN_NO_GENERATOR_MAPS',public_statement_contracts='18/18',frozen_transport_schemas=reviewed,direct_legacy_service_call_count=0,governed_executable_composition=True,same_connection_decision_handoff=True,source_hashes=hashes,scope='SOURCE_AND_RECORDING_JDBC_ONLY',installed_runtime='M04_RUNTIME_VALIDATION_REQUIRED')


if __name__ == '__main__':
    cli=argparse.ArgumentParser(); cli.add_argument('--output', required=True); args=cli.parse_args()
    result=review(); Path(args.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_hashes','frozen_transport_schemas')},indent=2))
