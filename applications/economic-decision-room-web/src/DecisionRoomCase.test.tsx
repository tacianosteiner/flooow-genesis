import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DecisionRoomCase } from './DecisionRoomCase'

const caseId = '11111111-1111-4111-8111-111111111111'
// Synthetic contract fixtures only; no claim of accepted economic evidence.
const projection = (id = caseId) => ({
  caseId: id, marketplaceOrderId: 'order', financialTraceId: 'trace', policyVersion: 'policy/1',
  currency: 'BRL', reconciliationCaseStatus: 'OPEN', reconciliationRevision: 1,
  lastObservedAt: '2026-01-01T00:00:00Z', projectionStatus: 'READY', authorityStatus: 'ASSEMBLED',
  governancePermitted: true, authorityBlockingReasons: [], governanceBlockingReasons: [],
  projectionBlockingReasons: [], evidenceReferences: ['synthetic-source-ref'],
  totalQuantifiedLeakage: { currency: 'BRL', amount: '10.00' },
  stages: [{ stage: 'SALE', expected: null, actual: null, signedVariance: { currency: 'BRL', amount: '-10.00' },
    absoluteVariance: { currency: 'BRL', amount: '10.00' }, interpretation: 'UNFAVORABLE_LEAKAGE',
    quantifiedLeakage: { currency: 'BRL', amount: '10.00' }, blockingReason: null,
    expectedEntryIds: [], actualEntryIds: [] }],
})
const response = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status })

beforeEach(() => { window.__FLOOOW_CONFIG__ = {}; vi.stubGlobal('fetch', vi.fn()) })

describe('Governed case projection', () => {
  it('uses the backend projection and exact amount without deriving authority', async () => {
    vi.mocked(fetch).mockResolvedValue(response(projection()))
    render(<DecisionRoomCase caseId={caseId} />)
    expect(await screen.findByText('READY')).toBeInTheDocument()
    expect(screen.getByText('ASSEMBLED')).toBeInTheDocument()
    expect(screen.getByText(/Perda total quantificada:/)).toHaveTextContent('BRL 10.00')
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain(`/v1/economic-decision-room/reconciliation/${caseId}`)
    expect(vi.mocked(fetch).mock.calls[0][1]?.method).toBeUndefined()
  })

  it('keeps a partial quantified stage separate from a null total and explicit blockers', async () => {
    const value = { ...projection(), projectionStatus: 'BLOCKED', authorityStatus: 'NOT_ASSEMBLED',
      governancePermitted: false, authorityBlockingReasons: ['AUTHORITY_UNAVAILABLE'], totalQuantifiedLeakage: null,
      stages: [...projection().stages, { ...projection().stages[0], stage: 'FEE', interpretation: 'UNQUANTIFIED',
        quantifiedLeakage: null, blockingReason: 'MISSING_ACTUAL' }] }
    vi.mocked(fetch).mockResolvedValue(response(value))
    render(<DecisionRoomCase caseId={caseId} />)
    expect(await screen.findByText('BLOCKED')).toBeInTheDocument()
    expect(screen.getByText('NOT_ASSEMBLED')).toBeInTheDocument()
    expect(screen.getByText(/Perda total quantificada:/)).toHaveTextContent('Não quantificado')
    expect(screen.getByText('UNQUANTIFIED')).toBeInTheDocument()
    expect(screen.getByText('MISSING_ACTUAL')).toBeInTheDocument()
    expect(screen.getByText('Autoridade: AUTHORITY_UNAVAILABLE')).toBeInTheDocument()
  })

  it('makes dependency failure visible and retries only the read', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(response({}, 503)).mockResolvedValueOnce(response(projection()))
    render(<DecisionRoomCase caseId={caseId} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Projeção indisponível')
    expect(screen.queryByText('READY')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Tentar leitura novamente' }))
    expect(await screen.findByText('READY')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(2)
    expect(vi.mocked(fetch).mock.calls.every(([, init]) => !init?.method || init.method === 'GET')).toBe(true)
  })

  it('rejects another case instead of displaying foreign economic output', async () => {
    vi.mocked(fetch).mockResolvedValue(response(projection('22222222-2222-4222-8222-222222222222')))
    render(<DecisionRoomCase caseId={caseId} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('não corresponde ao contrato ou ao caso solicitado')
    expect(screen.queryByText('READY')).not.toBeInTheDocument()
  })

  it('rejects malformed states or missing totals instead of silently defaulting', async () => {
    vi.mocked(fetch).mockResolvedValue(response({ ...projection(), projectionStatus: 'UNKNOWN', totalQuantifiedLeakage: undefined }))
    render(<DecisionRoomCase caseId={caseId} />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.queryByText(/Perda total quantificada:/)).not.toBeInTheDocument()
  })

  it('ignores a late response after case selection changes', async () => {
    // eslint-disable-next-line no-unused-vars
    let finishOld: (value: Response) => void = () => { throw new Error('Old request not started') }
    vi.mocked(fetch).mockImplementationOnce(() => new Promise((resolve) => { finishOld = resolve }))
      .mockResolvedValueOnce(response(projection('22222222-2222-4222-8222-222222222222')))
    const view = render(<DecisionRoomCase caseId={caseId} />)
    view.rerender(<DecisionRoomCase caseId="22222222-2222-4222-8222-222222222222" />)
    expect(await screen.findByText('READY')).toBeInTheDocument()
    finishOld(response({ ...projection(), projectionStatus: 'BLOCKED' }))
    expect(screen.queryByText('BLOCKED')).not.toBeInTheDocument()
  })
})


it('does not publish a subtotal as total when any stage is unquantified', async () => {
  vi.mocked(fetch).mockResolvedValue(response({ ...projection(), stages: [
    ...projection().stages, { ...projection().stages[0], stage: 'FEE', interpretation: 'UNQUANTIFIED', quantifiedLeakage: null },
  ] }))
  render(<DecisionRoomCase caseId={caseId} />)
  expect(await screen.findByRole('alert')).toHaveTextContent('quantificação parcial apresentada como total')
  expect(screen.queryByText(/Perda total quantificada:/)).not.toBeInTheDocument()
})
