"""Negative source tests; no database or runtime integration is used."""

import unittest

import package_0090_source_gate as gate


class SourceGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (gate.ROOT / gate.V043).read_text(encoding="utf-8-sig")
        cls.spec = (gate.ROOT / gate.SPEC).read_text(encoding="utf-8-sig")

    def reject(self, source):
        with self.assertRaises(ValueError):
            gate.prerequisite_checks(source, self.spec)

    def test_current_column_acl_matches_independent_normative_matrix(self):
        self.assertEqual(gate.prerequisite_checks(self.source, self.spec)["exact_column_grants"], 1040)

    def test_public_grant_denied(self):
        self.reject(self.source + "\nGRANT SELECT (effective_from) ON public.offline_deadline_policy TO PUBLIC;")

    def test_whole_table_grant_denied(self):
        self.reject(self.source + "\nGRANT SELECT ON public.offline_deadline_policy TO flooow_offline_audit_owner;")

    def test_grant_option_denied(self):
        self.reject(self.source + "\nGRANT SELECT (effective_from) ON public.offline_deadline_policy TO flooow_offline_audit_owner WITH GRANT OPTION;")

    def test_auditor_possession_digest_read_denied(self):
        self.reject(self.source + "\nGRANT SELECT (possession_digest) ON public.offline_execution TO flooow_offline_audit_owner;")

    def test_auditor_activation_write_denied(self):
        self.reject(self.source + "\nGRANT UPDATE (effective_from) ON public.offline_deadline_policy TO flooow_offline_audit_owner;")

    def test_missing_activation_read_denied(self):
        self.reject(self.source.replace(
            "GRANT SELECT (effective_from) ON TABLE public.offline_deadline_policy TO flooow_offline_intent_audit_owner;", ""))

    def test_duplicate_physical_grant_denied(self):
        self.reject(self.source + "\nGRANT SELECT (effective_from) ON public.offline_deadline_policy TO flooow_offline_audit_owner;")

    def test_missing_interlock_denied(self):
        self.reject(self.source.replace("RAISE EXCEPTION USING ERRCODE = '55000',", "RAISE NOTICE USING ERRCODE = '55000',", 1))

    def test_admin_creation_denied(self):
        self.reject(self.source.replace(
            "-- V043 never creates, alters or repairs this identity.",
            "CREATE ROLE flooow_offline_control_owner NOLOGIN INHERIT;"))

    def test_admin_noinherit_denied(self):
        self.reject(self.source.replace("OR NOT owner_role.rolinherit", "OR owner_role.rolinherit", 1))

    def test_activation_default_denied(self):
        self.reject(self.source.replace("effective_from pg_catalog.timestamptz(6) NOT NULL,",
                                       "effective_from pg_catalog.timestamptz(6) NOT NULL DEFAULT now(),"))

    def test_activation_precision_denied(self):
        self.reject(self.source.replace("effective_from pg_catalog.timestamptz(6) NOT NULL,",
                                       "effective_from pg_catalog.timestamptz(3) NOT NULL,"))

    def test_policy_seed_denied(self):
        self.reject(self.source + "\nINSERT INTO public.offline_deadline_policy VALUES ('unapproved');")

    def test_unapproved_control_table_denied(self):
        self.reject(self.source.replace("CREATE TABLE public.offline_diagnostic_evidence (",
                                       "CREATE TABLE public.offline_extra_control ("))

    def test_crypto_installation_denied(self):
        self.reject(self.source + "\nCREATE EXTENSION pgcrypto;")

    def test_live_role_hidden_in_do_denied(self):
        self.reject(self.source + "\nDO $$ BEGIN CREATE ROLE unapproved_login LOGIN; END; $$;")

    def test_domain_write_hidden_in_do_denied(self):
        self.reject(self.source + "\nDO $$ BEGIN DELETE FROM public.command_principal; END; $$;")

    def test_dynamic_sql_denied(self):
        self.reject(self.source + "\nDO $$ BEGIN EXECUTE 'SELECT 1'; END; $$;")

    def test_frozen_table_ddl_denied(self):
        self.reject(self.source + "\nALTER TABLE public.command_principal ADD COLUMN forbidden int4;")

    def test_incomplete_source_never_reports_full_closure(self):
        self.assertEqual(len(gate.closure_gaps(self.source, self.spec)), 3)

    def test_fixture_approval_does_not_close_implementation(self):
        gaps = gate.closure_gaps(self.source, self.spec)
        self.assertFalse(any('TTL/maximum approval' in gap for gap in gaps))
        self.assertTrue(any('golden' in gap for gap in gaps))
        for marker in ('TAG28_PREFLIGHT_RECEIPT_TTL_US=1000000',
                       'TAG29_PREFLIGHT_RECEIPT_TTL_APPROVED_MAX_US=2000000',
                       'PRODUCTION_POLICY_PROVISIONING=NO'):
            self.assertEqual(len(gate.closure_gaps(self.source, self.spec.replace(marker, 'INVALID'))), 4)

    def test_internal_p_signature_and_acl_static_manifest(self):
        result=gate.prerequisite_checks(self.source,self.spec)
        self.assertEqual(result['internal_p_read_columns'],60)
        self.assertEqual(result['internal_p_execute_grants'],2)

    def test_internal_p_security_options_denied(self):
        for before,after in (('LANGUAGE plpgsql VOLATILE SECURITY DEFINER CALLED ON NULL INPUT',
                              'LANGUAGE plpgsql STABLE SECURITY DEFINER CALLED ON NULL INPUT'),
                             ('LANGUAGE plpgsql VOLATILE SECURITY DEFINER CALLED ON NULL INPUT',
                              'LANGUAGE plpgsql VOLATILE SECURITY INVOKER CALLED ON NULL INPUT'),
                             ('LANGUAGE plpgsql VOLATILE SECURITY DEFINER CALLED ON NULL INPUT',
                              'LANGUAGE plpgsql VOLATILE SECURITY DEFINER STRICT'),
                             ('possession_secret pg_catalog.bytea\n)', 'possession_secret pg_catalog.bytea DEFAULT NULL\n)')):
            with self.subTest(after=after):self.reject(self.source.replace(before,after,1))

    def test_internal_p_extra_privileged_call_denied(self):
        self.reject(self.source.replace('    RETURN TRUE;',
                    '    PERFORM public.transaction_identity_progress_lock(header_record.organization_id,header_record.omie_connection_id);\n    RETURN TRUE;',1))
        self.reject(self.source.replace('    RETURN TRUE;',
                    "    PERFORM pg_catalog.set_config('statement_timeout','0',false);\n    RETURN TRUE;",1))

    def test_internal_p_dynamic_sql_and_dml_denied(self):
        self.reject(self.source.replace('    RETURN TRUE;',"    EXECUTE 'SELECT 1';\n    RETURN TRUE;",1))
        self.reject(self.source.replace('    RETURN TRUE;',
                    '    UPDATE public.offline_binding_lifecycle SET state=\'ACTIVE\' WHERE binding_id=$1;\n    RETURN TRUE;',1))

    def test_internal_p_raw_read_and_wildcard_denied(self):
        self.reject(self.source.replace('SELECT p.principal_id INTO principal_found',
                                       'SELECT p.reason INTO principal_found',1))
        self.reject(self.source.replace('SELECT p.principal_id INTO principal_found',
                                       'SELECT p.* INTO principal_found',1))

    def test_internal_p_public_and_service_execute_denied(self):
        signature='public.offline_lock_bound_principal(pg_catalog.uuid,pg_catalog.bytea,pg_catalog.uuid,pg_catalog.text,pg_catalog.uuid,pg_catalog.int8,pg_catalog.uuid,pg_catalog.uuid,pg_catalog.bytea)'
        for recipient in ('PUBLIC','flooow_offline_audit_owner','unapproved_service'):
            self.reject(self.source+'\nGRANT EXECUTE ON FUNCTION '+signature+' TO '+recipient+';')

    def test_internal_p_owner_and_namespace_denied(self):
        self.reject(self.source.replace(') OWNER TO flooow_offline_principal_lock_owner;',
                                       ') OWNER TO flooow_offline_execution_owner;',1))
        self.reject(self.source.replace('ALTER FUNCTION public.offline_lock_bound_principal(',
                                       'ALTER FUNCTION public.other_capability(',1))


if __name__ == "__main__":
    unittest.main()
