"""Disposable direct-catalog OID reuse injection with permanent binding tombstone.
Not an ordinary PostgreSQL allocator guarantee or a production role API.
"""
import uuid
def run(q):
    def denied(name):
        r=q.sql('SELECT 42;','test_auditor',ok=False)
        q.case('tombstone',name,r.returncode!=0,{'role':'test_auditor','stderr':r.stderr,'exit':r.returncode})
    role='test_auditor';old=int(q.sql("SELECT oid FROM pg_roles WHERE rolname='test_auditor';").stdout)
    binding=q.expected_header['binding_id'];allocation=str(uuid.uuid4())
    q.sql("INSERT INTO flooow_test_tombstone VALUES('"+binding+"',"+str(old)+",'test_auditor','"+allocation+"','TEST_ONLY_NONCANONICAL_DROPPED'); DROP ROLE test_auditor;")
    q.case('tombstone','dropped_identity_tombstoned',q.sql("SELECT count(*) FROM flooow_test_tombstone WHERE role_oid="+str(old)+";").stdout.strip()=='1','Protected tombstone committed before DROP')
    q.sql('CREATE ROLE test_auditor LOGIN NOINHERIT;')
    new=int(q.sql("SELECT oid FROM pg_roles WHERE rolname='test_auditor';").stdout)
    denied('same_name_new_oid_denied')
    q.sql("ALTER ROLE test_auditor RENAME TO test_oid_replacement; SET allow_system_table_mods=on; UPDATE pg_catalog.pg_authid SET oid="+str(old)+" WHERE oid="+str(new)+";")
    actual=int(q.sql("SELECT oid FROM pg_roles WHERE rolname='test_oid_replacement';").stdout)
    q.case('tombstone','forced_reuse_actual_catalog',actual==old,{'old_oid':old,'replacement_oid':actual,'method':'Disposable superuser catalog injection; not allocator behavior'})
    r=q.sql('SELECT 42;','test_oid_replacement',ok=False)
    q.case('tombstone','old_oid_new_name_denied',r.returncode!=0,{'stderr':r.stderr})
    q.sql('ALTER ROLE test_oid_replacement RENAME TO test_auditor;')
    denied('same_name_same_oid_old_binding_denied')
    q.case('tombstone','no_implicit_reallocation',q.sql('SELECT count(*) FROM flooow_test_tombstone;').stdout.strip()=='1','No tombstone erasure or old allocation reuse')
    q.record['cases'].append({'group':'tombstone','name':'explicit_fresh_allocation_entire_new_binding','result':'NOT_RUN','detail':'Fresh governed allocation/full approval rebuild remains unqualified; old binding deliberately remains ineligible'})
