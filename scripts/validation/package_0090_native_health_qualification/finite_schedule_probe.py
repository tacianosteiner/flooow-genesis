"""Finite model schedules compile exact current observer; not universal proof."""
def run(q):
    q.ex('gcc','-D_GNU_SOURCE','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I/usr/include/postgresql/18/server','-I/usr/local/src-full','/usr/local/src-full/population_state_tests.c','-o','/usr/local/bin/population-state-tests','-l:libpq.so.5','-lcrypto','-ldl',user='0')
    result=q.ex('/usr/local/bin/population-state-tests',ok=False)
    (q.OUT/'FINITE-SCHEDULE-RAW.txt').write_text(result.stdout+result.stderr)
    q.case('finite_schedule','exact_current_observer_17_named_schedules',result.returncode==0 and result.stdout.count('FINITE_OBSERVATION_SCHEDULE_')==17,{'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'model_catalog_rows':True,'owned_atomic_kernel_children':True,'pid_reuse_scope':'model tuple reuse, not forced Linux PID allocator wrap','universal_schedule_claim':False})
    q.case('finite_schedule','unknown_type_fail_closed',result.returncode==0 and 'UNKNOWN_PROCESS_CLASS_FAIL_CLOSED=PASS' in result.stdout,'Explicit classification cannot silently fall through')
