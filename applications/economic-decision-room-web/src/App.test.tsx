import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const complete = {
  marketplaceOrderId: '11111111-1111-4111-8111-111111111111',
  sourceEvidenceVersion: 'V023',
  projectedAt: '2026-01-01T00:00:00Z',
  assemblyPolicyVersion: 'v1',
  state: 'CALCULATED_COMPLETE',
  economicResult: {
    orderOccurredAt: '2026-01-01T00:00:00Z',
    currency: 'BRL',
    grossRevenue: '100.00',
    totalMarketplaceFees: '10.00',
    totalShipping: '0.00',
    totalAdvertising: '0.00',
    totalTaxes: '0.00',
    totalProductCost: '20.00',
    totalFinancialCost: '0.00',
    totalOtherAdjustments: '0.00',
    contribution: '70.00',
    contributionMargin: '0.7',
    truthQuality: 'COMPLETE',
  },
}

const incomplete = {
  marketplaceOrderId: '22222222-2222-4222-8222-222222222222',
  sourceEvidenceVersion: 'V023',
  projectedAt: '2026-01-01T00:00:00Z',
  assemblyPolicyVersion: 'v1',
  state: 'CALCULATED_INCOMPLETE',
  missingComponentTypes: ['PRODUCT_COST'],
}

const unresolved = {
  marketplaceOrderId: '33333333-3333-4333-8333-333333333333',
  sourceEvidenceVersion: 'V023',
  projectedAt: '2026-01-01T00:00:00Z',
  assemblyPolicyVersion: 'v1',
  state: 'UNRESOLVED',
  unresolvedReasons: ['ORDER_IDENTITY_UNRESOLVED'],
}

function response(body: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  )
}

function installHealthyBackend() {
  vi.stubGlobal(
    'fetch',
    vi.fn((input: string | URL, init?: RequestInit) => {
      const url = String(input)
      const parsed = new URL(url)
      const path = parsed.pathname

      if (
        path === '/v1/sales-intelligence/orders' &&
        (init?.method ?? 'GET') === 'GET'
      ) {
        return response({
          orders: [complete, incomplete, unresolved],
          nextCursor: 'opaque-next',
        })
      }

      if (path.startsWith('/v1/sales-intelligence/orders/')) {
        return response(complete)
      }

      if (
        path === '/v1/sales-intelligence/refresh' &&
        init?.method === 'POST'
      ) {
        return response({
          status: 'COMPLETED',
          source: {
            status: 'EXHAUSTED',
            invocations: 1,
            committedPages: 1,
            alreadyCommittedPages: 0,
            records: 3,
          },
          occurrence: {
            batches: 1,
            examined: 3,
            promoted: 3,
            duplicates: 0,
            identityConflicts: 0,
            evidenceConflicts: 0,
            drained: true,
          },
          revenue: {
            batches: 1,
            examined: 3,
            promoted: 2,
            duplicates: 0,
            identityConflicts: 0,
            evidenceConflicts: 0,
            drained: true,
          },
          projection: {
            batches: 1,
            processedChanges: 3,
            drained: true,
          },
        })
      }

      if (path === '/v1/reconciliation/cases') {
        return response({ cases: [] })
      }

      if (path === '/v1/reconciliation/systemic-divergences') {
        return response({ signals: [] })
      }

      if (path === '/v1/commerce-identity/health') {
        return response({
          available: true,
          exactConfirmed: 2,
          candidate: 1,
          conflict: 0,
          unresolved: 0,
          coveragePercentage: '100',
        })
      }

      return response({}, 404)
    }),
  )
}

beforeEach(() => {
  vi.unstubAllGlobals()
  vi.stubEnv('VITE_DEMO_MODE', 'false')
  installHealthyBackend()
})

describe('FLOOOW Executive Room V2', () => {
  it('renders CEO lens by default', async () => {
    render(<App />)
    expect(await screen.findByRole('heading', { name: 'CEO Room' })).toBeInTheDocument()
  })

  it('separates executive lenses from the institutional spine', async () => {
    render(<App />)

    expect(await screen.findByText('EXECUTIVE LENSES')).toBeInTheDocument()
    expect(screen.getByText('INSTITUTIONAL SPINE')).toBeInTheDocument()
    expect(
      screen.getByRole('navigation', { name: 'Room navigation' }),
    ).toBeInTheDocument()
  })

  it('shows shared institutional context without granting authority', async () => {
    render(<App />)

    const context = await screen.findByRole('region', {
      name: 'Contexto institucional compartilhado',
    })

    expect(
      within(context).getByText('Shared institutional context'),
    ).toBeInTheDocument()
    expect(within(context).getByText('Execution authority')).toBeInTheDocument()
    expect(within(context).getByText('BLOCKED')).toBeInTheDocument()
    expect(
      screen.getByRole('region', { name: 'Loaded economic projection metrics' }),
    ).toBeInTheDocument()
  })

  it('renders truthful executive synthesis for all executive lenses', async () => {
    render(<App />)

    expect(
      await screen.findByRole('region', { name: 'CEO executive synthesis' }),
    ).toHaveTextContent('ATTENTION REQUIRED')

    await userEvent.click(screen.getByRole('button', { name: 'CFO' }))
    expect(
      screen.getByRole('region', { name: 'CFO executive synthesis' }),
    ).toHaveTextContent('FINANCIAL CONFIDENCE CONSTRAINED')

    await userEvent.click(screen.getByRole('button', { name: 'COO' }))
    expect(
      screen.getByRole('region', { name: 'COO executive synthesis' }),
    ).toHaveTextContent('OPERATIONAL EXCEPTIONS PRESENT')

    await userEvent.click(screen.getByRole('button', { name: 'CRO' }))
    expect(
      screen.getByRole('region', { name: 'CRO executive synthesis' }),
    ).toHaveTextContent('OBSERVED REVENUE · LIMITED INTELLIGENCE')
  })

  it('surfaces decision pressure without inventing monetary materiality', async () => {
    render(<App />)

    const pressure = await screen.findByRole('region', {
      name: 'Decision pressure',
    })

    expect(within(pressure).getByText('Truth unresolved')).toBeInTheDocument()
    expect(
      within(pressure).getByText('Economic incompleteness'),
    ).toBeInTheDocument()
    expect(within(pressure).getAllByText('UNQUANTIFIED').length).toBeGreaterThanOrEqual(2)
    expect(within(pressure).getByText('Execution authority')).toBeInTheDocument()
    expect(within(pressure).getByText('BLOCKED')).toBeInTheDocument()
    expect(within(pressure).queryByText(/R\$/)).not.toBeInTheDocument()
  })

  it('drills from unresolved and incomplete pressure into loaded evidence only', async () => {
    render(<App />)
    await screen.findByRole('region', { name: 'Decision pressure' })

    await userEvent.click(screen.getByRole('button', { name: 'Inspect evidence for Truth unresolved' }))
    let path = screen.getByRole('region', { name: 'Executive evidence path' })
    expect(within(path).getByText(/33333333-3333-4333-8333-333333333333/)).toBeInTheDocument()
    expect(within(path).getByText('ORDER_IDENTITY_UNRESOLVED')).toBeInTheDocument()
    expect(within(path).getByText('V023')).toBeInTheDocument()
    expect(within(path).getByText('v1')).toBeInTheDocument()
    expect(within(path).getByText('READ ONLY · DERIVED / NON-CANONICAL')).toBeInTheDocument()
    expect(within(path).getByText(/NOT ORGANIZATION-WIDE/)).toBeInTheDocument()
    expect(within(path).queryByText(/22222222-2222/)).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Inspect evidence for Economic incompleteness' }))
    path = screen.getByRole('region', { name: 'Executive evidence path' })
    expect(within(path).getByText(/22222222-2222-4222-8222-222222222222/)).toBeInTheDocument()
    expect(within(path).getByText('PRODUCT_COST')).toBeInTheDocument()
    expect(within(path).getByText('Unavailable / incomplete')).toBeInTheDocument()
    expect(within(path).queryByText(/33333333-3333/)).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Inspect evidence for Execution authority' }))
    path = screen.getByRole('region', { name: 'Executive evidence path' })
    expect(within(path).getByText('Execution remains BLOCKED. ROOM_OPERATIONAL = NO.')).toBeInTheDocument()
  })

  it('makes loaded scope and provenance explicit without claiming organization-wide truth', async () => {
    render(<App />)

    const scope = await screen.findByRole('region', {
      name: 'Projection scope and provenance',
    })

    expect(within(scope).getByText('LOADED PAGE · MORE AVAILABLE')).toBeInTheDocument()
    expect(within(scope).getByText('MORE AVAILABLE')).toBeInTheDocument()
    expect(within(scope).getByText('CONSISTENT LOADED LINEAGE')).toBeInTheDocument()
    expect(within(scope).getByText('V023')).toBeInTheDocument()
    expect(within(scope).getByText('v1')).toBeInTheDocument()
    expect(within(scope).getByText('NOT ORGANIZATION-WIDE')).toBeInTheDocument()
    expect(
      screen.getByRole('region', { name: 'Loaded economic projection metrics' }),
    ).toBeInTheDocument()
    expect(screen.queryByText('SHARED ECONOMIC TRUTH')).not.toBeInTheDocument()
  })

  it('renders CFO lens', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: 'CFO' }))
    expect(await screen.findByRole('heading', { name: 'CFO Room' })).toBeInTheDocument()
  })

  it('renders COO lens', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: 'COO' }))
    expect(await screen.findByRole('heading', { name: 'COO Room' })).toBeInTheDocument()
  })

  it('renders CRO lens', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: 'CRO' }))
    expect(await screen.findByRole('heading', { name: 'CRO Room' })).toBeInTheDocument()
  })

  it('renders Reconciliation lens', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: 'Reconciliation' }))
    expect(await screen.findByRole('heading', { name: 'Reconciliation Room' })).toBeInTheDocument()
  })

  it('renders Decisions lens', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: 'Decisions' }))
    expect(await screen.findByRole('heading', { name: 'Decisions Room' })).toBeInTheDocument()
  })

  it('renders System Health lens', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: 'System Health' }))
    expect(await screen.findByRole('heading', { name: 'System Health Room' })).toBeInTheDocument()
  })

  it('maps all three economic states and preserves missing versus zero', async () => {
    render(<App />)

    await userEvent.click(
      screen.getByRole('button', { name: 'Economic Truth' }),
    )

    expect(
      await screen.findByText('Calculado · Completo'),
    ).toBeInTheDocument()

    expect(
      screen.getByText('Calculado · Incompleto'),
    ).toBeInTheDocument()

    expect(screen.getByText('Não resolvido')).toBeInTheDocument()

    expect(screen.getAllByText(/R\$\s*70,00/).length).toBeGreaterThan(0)

    expect(
      screen.getAllByText('Não disponível').length,
    ).toBeGreaterThanOrEqual(2)
  })

  it('shows selected order detail and derived authority boundary', async () => {
    render(<App />)

    await userEvent.click(
      screen.getByRole('button', { name: 'Economic Truth' }),
    )

    const button = await screen.findByRole('button', {
      name: 'Abrir #11111111',
    })

    await userEvent.click(button)

    expect(
      await screen.findByText('Derivado · não canônico'),
    ).toBeInTheDocument()

    expect(
      screen.getByText(
        'Economic Truth permanece a autoridade upstream.',
      ),
    ).toBeInTheDocument()
  })

  it('uses the governed refresh endpoint and reports success', async () => {
    render(<App />)

    const button = await screen.findByRole('button', {
      name: /Atualizar realidade/,
    })

    await userEvent.click(button)

    expect(
      await screen.findByText('Realidade atualizada com governança'),
    ).toBeInTheDocument()

    const calls = vi.mocked(fetch).mock.calls.map(([url, init]) => ({
      url: String(url),
      method: init?.method ?? 'GET',
    }))

    expect(
      calls.some(
        (call) =>
          call.url.endsWith('/v1/sales-intelligence/refresh') &&
          call.method === 'POST',
      ),
    ).toBe(true)

    expect(
      calls.every(
        (call) =>
          !call.url.includes('organizationId') &&
          !call.url.includes('connectionId'),
      ),
    ).toBe(true)
  })

  it('surfaces refresh failure without inventing success', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: string | URL, init?: RequestInit) => {
        const url = String(input)
        const path = new URL(url).pathname

        if (
          path === '/v1/sales-intelligence/refresh' &&
          init?.method === 'POST'
        ) {
          return response({ code: 'LIVE_REFRESH_UNAVAILABLE' }, 503)
        }

        if (path === '/v1/sales-intelligence/orders') {
          return response({ orders: [complete], nextCursor: undefined })
        }

        if (path === '/v1/reconciliation/cases') {
          return response({ cases: [] })
        }

        if (path === '/v1/reconciliation/systemic-divergences') {
          return response({ signals: [] })
        }

        if (path === '/v1/commerce-identity/health') {
          return response({ available: true })
        }

        return response({}, 404)
      }),
    )

    render(<App />)

    const button = await screen.findByRole('button', {
      name: /Atualizar realidade/,
    })

    await userEvent.click(button)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'O backend está indisponível',
    )

    expect(
      screen.queryByText('Realidade atualizada com governança'),
    ).not.toBeInTheDocument()
  })

  it('supports opaque pagination', async () => {
    render(<App />)

    await userEvent.click(
      screen.getByRole('button', { name: 'Economic Truth' }),
    )

    expect(
      await screen.findByRole('button', { name: 'Próxima →' }),
    ).toBeVisible()
  })

  it('renders a semantic accessible table', async () => {
    render(<App />)

    await userEvent.click(
      screen.getByRole('button', { name: 'Economic Truth' }),
    )

    const table = await screen.findByRole('table')

    expect(
      within(table).getAllByRole('columnheader'),
    ).toHaveLength(6)
  })

  it('renders truthful empty order state', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: string | URL) => {
        const path = new URL(String(input)).pathname

        if (path === '/v1/sales-intelligence/orders') {
          return response({ orders: [] })
        }

        if (path === '/v1/reconciliation/cases') {
          return response({ cases: [] })
        }

        if (path === '/v1/reconciliation/systemic-divergences') {
          return response({ signals: [] })
        }

        if (path === '/v1/commerce-identity/health') {
          return response({ available: true })
        }

        return response({}, 404)
      }),
    )

    render(<App />)

    await userEvent.click(
      screen.getByRole('button', { name: 'Economic Truth' }),
    )

    expect(
      await screen.findByText('Nenhum pedido projetado'),
    ).toBeInTheDocument()
  })

  it('does not implicitly enter demo mode', async () => {
    render(<App />)

    expect(
      await screen.findByText('ROOM V2 · EXECUTIVE PREVIEW'),
    ).toBeInTheDocument()

    expect(
      screen.queryByText('Modo demonstração'),
    ).not.toBeInTheDocument()
  })

  it('keeps core orders visible when optional sources fail', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: string | URL) => {
        const path = new URL(String(input)).pathname

        if (path === '/v1/sales-intelligence/orders') {
          return response({ orders: [complete] })
        }

        if (
          path === '/v1/reconciliation/cases' ||
          path === '/v1/reconciliation/systemic-divergences' ||
          path === '/v1/commerce-identity/health'
        ) {
          return response({ code: 'UNAVAILABLE' }, 503)
        }

        if (path.startsWith('/v1/sales-intelligence/orders/')) {
          return response(complete)
        }

        return response({}, 404)
      }),
    )

    render(<App />)

    await userEvent.click(
      screen.getByRole('button', { name: 'Economic Truth' }),
    )

    expect(
      await screen.findByText('#11111111'),
    ).toBeInTheDocument()

    await userEvent.click(
      screen.getByRole('button', { name: 'CEO' }),
    )

    expect(
      await screen.findAllByText('Indisponível'),
    ).not.toHaveLength(0)

    await userEvent.click(screen.getByRole('button', { name: 'Inspect evidence for Execution authority' }))
    expect(screen.getByRole('region', { name: 'Executive evidence path' })).toHaveTextContent(
      'Optional sources: reconciliation UNAVAILABLE; systemic divergence UNAVAILABLE.',
    )
  })

  it('keeps ROOM_OPERATIONAL fail closed in preview', async () => {
    render(<App />)

    expect(
      await screen.findByText('ROOM_OPERATIONAL = NO'),
    ).toBeInTheDocument()
  })
})
