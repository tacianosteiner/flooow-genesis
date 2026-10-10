# PACKAGE-0090 / G3F.4 — Ambiguous Commit Operational Authorization

Classification: GOVERNED_REHEARSAL_AUTHORIZATION
Scope: G3F4_ISOLATED_DISPOSABLE_REHEARSAL_ONLY
Production authority: NO
Real provider/customer data: FORBIDDEN

User authorization:

AUTORIZO o rehearsal operacional isolado do PACKAGE-0090 / G3F.4 exclusivamente no ambiente G3F4_ISOLATED_DISPOSABLE_REHEARSAL_ONLY, para qualificar single-execution e ambiguous COMMIT.

Autorizo somente dados sintéticos de rehearsal, geração de uma chave Ed25519 efêmera exclusivamente para esta cerimônia, uma única operação de SIGN sobre o payload congelado autorizado, DML necessário da cerimônia no banco descartável e fault injection controlada para produzir ACK de COMMIT ambíguo.

A autorização NÃO se aplica a produção, dados reais, credenciais de providers, volumes protegidos, alteração de migrations/V043, alteração de políticas, password rotation, reutilização da chave, segunda assinatura, novo T0 após início da mesma root, blind retry ou qualquer mutação fora do rehearsal aprovado.

Após COMMIT ambíguo, a primeira ação obrigatória é query-first recovery. É proibido repetir mutação antes da classificação durável do root original.

Resultado exato e completo pode ser classificado como REPLAY_EXISTING somente após as validações independentes previstas, incluindo Adapter JCA quando aplicável. Ausência comprovada deve bloquear a root anterior; estado parcial, conflitante ou não comprovável deve permanecer HOLD/ESCALATE.

Autorizo também medir os tempos do mesmo rehearsal para qualificar o HIGH de ADMIN path budget/margin, desde que nenhuma etapa adicional fora desta autorização seja introduzida.

## Hard boundaries

- ENVIRONMENT = G3F4_ISOLATED_DISPOSABLE_REHEARSAL_ONLY
- SYNTHETIC_DATA_ONLY = YES
- PROVIDER_CALLS = FORBIDDEN
- PRODUCTION_DATA = FORBIDDEN
- PROTECTED_VOLUME = FORBIDDEN
- V043_CHANGE = FORBIDDEN
- POLICY_CHANGE = FORBIDDEN
- PASSWORD_ROTATION = FORBIDDEN
- KEY_GENERATION_MAX = 1
- SIGN_INVOCATION_MAX = 1
- ROOT_T0_MAX = 1
- BLIND_RETRY = FORBIDDEN
- QUERY_FIRST_AFTER_AMBIGUOUS_COMMIT = REQUIRED
- ADAPTER_JCA_REQUIREMENT = PRESERVED
- SECOND_SIGNATURE = FORBIDDEN
- KEY_REUSE = FORBIDDEN