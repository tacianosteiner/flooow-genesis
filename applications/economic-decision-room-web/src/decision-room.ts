import { ApiError, request, type ExactMoney } from './api'

export interface DecisionRoomStage {
  stage: string
  expected: ExactMoney | null
  actual: ExactMoney | null
  signedVariance: ExactMoney | null
  absoluteVariance: ExactMoney | null
  interpretation: string | null
  quantifiedLeakage: ExactMoney | null
  blockingReason: string | null
  expectedEntryIds: string[]
  actualEntryIds: string[]
}

export interface DecisionRoomProjection {
  caseId: string
  marketplaceOrderId: string
  financialTraceId: string
  policyVersion: string
  currency: string
  reconciliationCaseStatus: string
  reconciliationRevision: number
  lastObservedAt: string
  projectionStatus: 'READY' | 'BLOCKED'
  authorityStatus: 'ASSEMBLED' | 'NOT_ASSEMBLED'
  governancePermitted: boolean
  authorityBlockingReasons: string[]
  governanceBlockingReasons: string[]
  projectionBlockingReasons: string[]
  totalQuantifiedLeakage: ExactMoney | null
  evidenceReferences: string[]
  stages: DecisionRoomStage[]
}

const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value)
const strings = (value: unknown): value is string[] =>
  Array.isArray(value) && value.every((item) => typeof item === 'string')
const money = (value: unknown): boolean => value === null ||
  (record(value) && typeof value.currency === 'string' && /^[A-Z]{3}$/.test(value.currency) &&
    typeof value.amount === 'string' && /^-?\d+(\.\d+)?$/.test(value.amount))
const nullableText = (value: unknown): boolean => value === null || typeof value === 'string'

// Validate the read contract, never calculate authority, leakage or readiness.
export async function getDecisionRoomProjection(caseId: string, signal?: AbortSignal): Promise<DecisionRoomProjection> {
  const value = await request<unknown>(`/v1/economic-decision-room/reconciliation/${encodeURIComponent(caseId)}`, {}, signal)
  if (!record(value) || value.caseId !== caseId ||
    (value.projectionStatus !== 'READY' && value.projectionStatus !== 'BLOCKED') ||
    (value.authorityStatus !== 'ASSEMBLED' && value.authorityStatus !== 'NOT_ASSEMBLED') ||
    (value.reconciliationCaseStatus !== 'OPEN' && value.reconciliationCaseStatus !== 'ACKNOWLEDGED' && value.reconciliationCaseStatus !== 'RESOLVED') ||
    !['marketplaceOrderId', 'financialTraceId', 'policyVersion', 'currency', 'lastObservedAt'].every((key) => typeof value[key] === 'string') ||
    !Number.isSafeInteger(value.reconciliationRevision) || (value.reconciliationRevision as number) < 0 ||
    typeof value.governancePermitted !== 'boolean' ||
    !['authorityBlockingReasons', 'governanceBlockingReasons', 'projectionBlockingReasons', 'evidenceReferences'].every((key) => strings(value[key])) ||
    !money(value.totalQuantifiedLeakage) || !Array.isArray(value.stages) ||
    !value.stages.every((stage) => record(stage) && typeof stage.stage === 'string' &&
      ['expected', 'actual', 'signedVariance', 'absoluteVariance', 'quantifiedLeakage'].every((key) => money(stage[key])) &&
      (stage.interpretation === null || ['NO_MATERIAL_VARIANCE', 'UNFAVORABLE_LEAKAGE', 'FAVORABLE_VARIANCE', 'UNQUANTIFIED'].includes(stage.interpretation as string)) && nullableText(stage.blockingReason) &&
      strings(stage.expectedEntryIds) && strings(stage.actualEntryIds))) {
    throw new ApiError('A projeção recebida não corresponde ao contrato ou ao caso solicitado.', 502, 'INVALID_DECISION_ROOM_RESPONSE')
  }
  if (value.totalQuantifiedLeakage !== null && value.stages.some((stage) => record(stage) && stage.interpretation === 'UNQUANTIFIED')) {
    throw new ApiError('A projeção contém quantificação parcial apresentada como total.', 502, 'INVALID_DECISION_ROOM_RESPONSE')
  }
  return value as unknown as DecisionRoomProjection
}
