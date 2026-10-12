import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ApiError,
  demoModeEnabled,
  getCommerceIdentityHealth,
  listOrders,
  listReconciliationCases,
  listSystemicDivergences,
  refreshOrders,
  type CommerceIdentityHealth,
  type ReconciliationCase,
  type SalesOrder,
  type SystemicDivergenceSignal,
} from './api'
import { demoOrders, demoPage, demoRefresh } from './demo'
import './styles.css'

type Lens =
  | 'CEO'
  | 'CFO'
  | 'COO'
  | 'CRO'
  | 'TRUTH'
  | 'RECONCILIATION'
  | 'DECISIONS'
  | 'HEALTH'

const money = (value?: string, currency = 'BRL') =>
  value === undefined
    ? '—'
    : new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency,
      }).format(Number(value))

const pct = (value?: string) =>
  value === undefined ? '—' : `${(Number(value) * 100).toFixed(1)}%`

const lensMeta: Record<
  Lens,
  { label: string; kicker: string; question: string }
> = {
  CEO: {
    label: 'CEO',
    kicker: 'Executive command',
    question: 'O negócio está saudável e onde preciso agir?',
  },
  CFO: {
    label: 'CFO',
    kicker: 'Economic control',
    question: 'Os números fecham e onde existe perda econômica?',
  },
  COO: {
    label: 'COO',
    kicker: 'Operational control',
    question: 'O que está quebrando a operação agora?',
  },
  CRO: {
    label: 'CRO',
    kicker: 'Revenue intelligence',
    question: 'Onde receita, margem e crescimento estão sob pressão?',
  },
  TRUTH: {
    label: 'Economic Truth',
    kicker: 'Institutional reality',
    question: 'O que sabemos como fato e com qual evidência?',
  },
  RECONCILIATION: {
    label: 'Reconciliation',
    kicker: 'Divergence control',
    question: 'O que divergiu e o que ainda não foi resolvido?',
  },
  DECISIONS: {
    label: 'Decisions',
    kicker: 'Governed eligibility',
    question: 'O que pode ou não pode ser decidido agora?',
  },
  HEALTH: {
    label: 'System Health',
    kicker: 'Governance & readiness',
    question: 'O sistema está em condição segura para operar?',
  },
}

function App() {
  const demo = demoModeEnabled()

  const [lens, setLens] = useState<Lens>('CEO')
  const [orders, setOrders] = useState<SalesOrder[]>(demo ? demoOrders : [])
  const [cases, setCases] = useState<ReconciliationCase[]>([])
  const [signals, setSignals] = useState<SystemicDivergenceSignal[]>([])
  const [identity, setIdentity] = useState<CommerceIdentityHealth | undefined>()
  const [loading, setLoading] = useState(!demo)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string>()

  const load = useCallback(async () => {
    if (demo) {
      setOrders(demoPage.orders)
      return
    }

    setLoading(true)
    setError(undefined)

    try {
      const [orderPage, reconciliation, systemic, health] =
        await Promise.all([
          listOrders(),
          listReconciliationCases(),
          listSystemicDivergences(),
          getCommerceIdentityHealth(),
        ])

      setOrders(orderPage.orders)
      setCases(reconciliation.cases ?? [])
      setSignals(systemic.signals ?? [])
      setIdentity(health)
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : 'Não foi possível montar a projeção executiva.',
      )
    } finally {
      setLoading(false)
    }
  }, [demo])

  useEffect(() => {
    if (!demo) void load()
  }, [demo, load])

  const refresh = async () => {
    setRefreshing(true)
    setError(undefined)

    try {
      if (demo) {
        await Promise.resolve(demoRefresh)
      } else {
        await refreshOrders()
        await load()
      }
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : 'A atualização governada falhou com segurança.',
      )
    } finally {
      setRefreshing(false)
    }
  }

  const complete = orders.filter(
    (order) => order.state === 'CALCULATED_COMPLETE',
  )

  const incomplete = orders.filter(
    (order) => order.state === 'CALCULATED_INCOMPLETE',
  )

  const unresolved = orders.filter(
    (order) => order.state === 'UNRESOLVED',
  )

  const totals = useMemo(() => {
    return complete.reduce(
      (acc, order) => {
        const result = order.economicResult
        if (!result) return acc

        acc.revenue += Number(result.grossRevenue || 0)
        acc.contribution += Number(result.contribution || 0)
        acc.fees += Number(result.totalMarketplaceFees || 0)
        acc.shipping += Number(result.totalShipping || 0)
        acc.taxes += Number(result.totalTaxes || 0)
        acc.cost += Number(result.totalProductCost || 0)

        return acc
      },
      {
        revenue: 0,
        contribution: 0,
        fees: 0,
        shipping: 0,
        taxes: 0,
        cost: 0,
      },
    )
  }, [complete])

  const contributionMargin =
    totals.revenue > 0 ? totals.contribution / totals.revenue : undefined

  const coverage =
    orders.length > 0
      ? Math.round((complete.length / orders.length) * 100)
      : 0

  const meta = lensMeta[lens]

  return (
    <div className="shell">
      <aside className="rail">
        <div className="brand">
          <div className="mark">F</div>
          <div>
            <strong>FLOOOW</strong>
            <span>Decision Infrastructure</span>
          </div>
        </div>

        <div className="preview-chip">ROOM V1 · PREVIEW</div>

        <nav>
          {(Object.keys(lensMeta) as Lens[]).map((key) => (
            <button
              key={key}
              className={lens === key ? 'active' : ''}
              onClick={() => setLens(key)}
            >
              <span>{lensMeta[key].label}</span>
            </button>
          ))}
        </nav>

        <div className="rail-footer">
          <strong>Governed environment</strong>
          <span>Preview ≠ operational authority</span>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div>
            <span className="breadcrumb">FLOOOW / EXECUTIVE ROOM</span>
          </div>

          <div className="top-status">
            <span className="status-dot hold" />
            <span>ROOM_OPERATIONAL = NO</span>
          </div>
        </header>

        <section className="hero">
          <div>
            <span className="kicker">{meta.kicker}</span>
            <h1>{meta.label} Room</h1>
            <p>{meta.question}</p>
          </div>

          <button
            className="refresh"
            disabled={refreshing || loading}
            onClick={() => void refresh()}
          >
            {refreshing ? 'Atualizando…' : 'Atualizar realidade'}
          </button>
        </section>

        <div className="preview-warning">
          <strong>Executive Preview</strong>
          <span>
            Esta interface evolui o Room sem declarar prontidão operacional.
            Economic Truth, autoridade e execução continuam governados pelo core.
          </span>
        </div>

        {error && (
          <div className="error">
            <strong>Fail closed</strong>
            <span>{error}</span>
          </div>
        )}

        <section className="metrics">
          <Metric
            label="Receita observada"
            value={money(totals.revenue.toString())}
            hint="somente pedidos economicamente completos"
          />
          <Metric
            label="Contribuição"
            value={money(totals.contribution.toString())}
            hint="resultado econômico observado"
          />
          <Metric
            label="Margem de contribuição"
            value={
              contributionMargin === undefined
                ? '—'
                : `${(contributionMargin * 100).toFixed(1)}%`
            }
            hint="não estimada quando verdade incompleta"
          />
          <Metric
            label="Cobertura"
            value={`${coverage}%`}
            hint={`${complete.length}/${orders.length} ordens completas`}
          />
        </section>

        {lens === 'CEO' && (
          <ExecutiveGrid>
            <Panel title="Executive pulse" eyebrow="BUSINESS STATE">
              <Signal
                label="Economic coverage"
                value={`${coverage}%`}
                state={coverage === 100 ? 'good' : 'warn'}
              />
              <Signal
                label="Open reconciliation"
                value={String(cases.filter((item) => item.status !== 'RESOLVED').length)}
                state={cases.some((item) => item.status !== 'RESOLVED') ? 'risk' : 'good'}
              />
              <Signal
                label="Systemic divergence signals"
                value={String(signals.length)}
                state={signals.length ? 'risk' : 'good'}
              />
              <Signal
                label="Identity unresolved"
                value={String(identity?.unresolved ?? 0)}
                state={(identity?.unresolved ?? 0) > 0 ? 'warn' : 'good'}
              />
            </Panel>

            <Panel title="Decision posture" eyebrow="EXECUTIVE ACTION">
              <Decision
                title="Operate"
                state="BLOCKED"
                body="O Room ainda não possui prova operacional canônica."
              />
              <Decision
                title="Analyze"
                state="AVAILABLE"
                body="A camada de leitura e análise pode continuar evoluindo."
              />
              <Decision
                title="Execute"
                state="NO AUTHORITY"
                body="Nenhuma ação econômica é autorizada por esta preview."
              />
            </Panel>
          </ExecutiveGrid>
        )}

        {lens === 'CFO' && (
          <ExecutiveGrid>
            <Panel title="Economic control" eyebrow="MARGIN & COST">
              <Signal label="Gross revenue" value={money(totals.revenue.toString())} />
              <Signal label="Marketplace fees" value={money(totals.fees.toString())} />
              <Signal label="Shipping" value={money(totals.shipping.toString())} />
              <Signal label="Taxes" value={money(totals.taxes.toString())} />
              <Signal label="Product cost" value={money(totals.cost.toString())} />
            </Panel>

            <Panel title="Truth exceptions" eyebrow="FINANCIAL CONFIDENCE">
              <Signal label="Complete" value={String(complete.length)} state="good" />
              <Signal label="Incomplete" value={String(incomplete.length)} state="warn" />
              <Signal label="Unresolved" value={String(unresolved.length)} state="risk" />
              <Signal
                label="Reconciliation cases"
                value={String(cases.length)}
                state={cases.length ? 'warn' : 'good'}
              />
            </Panel>
          </ExecutiveGrid>
        )}

        {lens === 'COO' && (
          <ExecutiveGrid>
            <Panel title="Operational exceptions" eyebrow="OPERATIONS">
              <Signal label="Orders observed" value={String(orders.length)} />
              <Signal label="Incomplete" value={String(incomplete.length)} state="warn" />
              <Signal label="Unresolved" value={String(unresolved.length)} state="risk" />
              <Signal label="Systemic signals" value={String(signals.length)} state={signals.length ? 'risk' : 'good'} />
            </Panel>

            <Panel title="Operational posture" eyebrow="CONTROL">
              <Decision
                title="Refresh"
                state={demo ? 'DEMO' : 'GOVERNED'}
                body="Atualização permanece separada de autoridade de execução."
              />
              <Decision
                title="Recovery"
                state="NOT AUTHORIZED"
                body="Recuperação automática não é inferida por divergência."
              />
            </Panel>
          </ExecutiveGrid>
        )}

        {lens === 'CRO' && (
          <ExecutiveGrid>
            <Panel title="Revenue posture" eyebrow="GROWTH">
              <Signal label="Observed revenue" value={money(totals.revenue.toString())} />
              <Signal
                label="Contribution margin"
                value={
                  contributionMargin === undefined
                    ? '—'
                    : `${(contributionMargin * 100).toFixed(1)}%`
                }
              />
              <Signal
                label="Commercial signal coverage"
                value="LIMITED"
                state="warn"
              />
            </Panel>

            <Panel title="Boundary" eyebrow="REVENUE INTELLIGENCE">
              <Decision
                title="Opportunity Intelligence"
                state="POST-MVP"
                body="Não será simulada com dados inexistentes nesta versão."
              />
              <Decision
                title="Current Room"
                state="TRUTH-FIRST"
                body="Receita observada permanece separada de oportunidade prevista."
              />
            </Panel>
          </ExecutiveGrid>
        )}

        {lens === 'TRUTH' && (
          <Panel title="Economic Truth" eyebrow="CANONICAL EVIDENCE">
            <Table
              rows={orders.map((order) => ({
                id: order.marketplaceOrderId,
                state: order.state,
                version: order.sourceEvidenceVersion,
                policy: order.assemblyPolicyVersion,
                value: order.economicResult
                  ? money(
                      order.economicResult.contribution,
                      order.economicResult.currency,
                    )
                  : 'Não disponível',
              }))}
            />
          </Panel>
        )}

        {lens === 'RECONCILIATION' && (
          <Panel title="Reconciliation" eyebrow="DIVERGENCE MEMORY">
            {cases.length === 0 ? (
              <Empty text="Nenhum caso persistido nesta projeção." />
            ) : (
              cases.map((item) => (
                <Row
                  key={item.caseId}
                  title={item.caseId}
                  subtitle={`Order ${item.marketplaceOrderId} · rev ${item.revision}`}
                  value={`${item.absoluteDifferenceSummary.currency} ${item.absoluteDifferenceSummary.amount}`}
                  badge={item.status}
                />
              ))
            )}
          </Panel>
        )}

        {lens === 'DECISIONS' && (
          <Panel title="Decision eligibility" eyebrow="GOVERNED DECISION">
            <Decision
              title="Economic analysis"
              state="AVAILABLE"
              body="Leitura derivada pode ser apresentada com provenance."
            />
            <Decision
              title="Recovery action"
              state="BLOCKED"
              body="Divergência não concede autoridade de recuperação."
            />
            <Decision
              title="Canonical execution"
              state="BLOCKED"
              body="Aguardando ROOM_OPERATIONAL=YES e cerimônia governada."
            />
          </Panel>
        )}

        {lens === 'HEALTH' && (
          <ExecutiveGrid>
            <Panel title="System health" eyebrow="READINESS">
              <Signal label="Room engineering" value="HOLD" state="warn" />
              <Signal label="Room operational" value="NO" state="risk" />
              <Signal label="Canonical execution" value="NOT RUN" state="warn" />
              <Signal label="Preview surface" value="AVAILABLE" state="good" />
            </Panel>

            <Panel title="Identity health" eyebrow="COMMERCE IDENTITY">
              <Signal
                label="Coverage"
                value={
                  identity?.coveragePercentage
                    ? `${identity.coveragePercentage}%`
                    : '—'
                }
              />
              <Signal label="Exact confirmed" value={String(identity?.exactConfirmed ?? 0)} />
              <Signal label="Candidates" value={String(identity?.candidate ?? 0)} />
              <Signal
                label="Conflicts"
                value={String(identity?.conflict ?? 0)}
                state={(identity?.conflict ?? 0) ? 'risk' : 'good'}
              />
            </Panel>
          </ExecutiveGrid>
        )}

        <footer>
          <span>FLOOOW · EXECUTIVE DECISION ROOM</span>
          <span>Preview surface · no execution authority</span>
        </footer>
      </main>
    </div>
  )
}

function Metric({
  label,
  value,
  hint,
}: {
  label: string
  value: string
  hint: string
}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{hint}</small>
    </div>
  )
}

function Panel({
  title,
  eyebrow,
  children,
}: {
  title: string
  eyebrow: string
  children: React.ReactNode
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span>{eyebrow}</span>
          <h2>{title}</h2>
        </div>
      </div>
      <div className="panel-body">{children}</div>
    </section>
  )
}

function ExecutiveGrid({ children }: { children: React.ReactNode }) {
  return <div className="executive-grid">{children}</div>
}

function Signal({
  label,
  value,
  state = 'neutral',
}: {
  label: string
  value: string
  state?: 'neutral' | 'good' | 'warn' | 'risk'
}) {
  return (
    <div className={`signal ${state}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function Decision({
  title,
  state,
  body,
}: {
  title: string
  state: string
  body: string
}) {
  return (
    <div className="decision">
      <div>
        <strong>{title}</strong>
        <p>{body}</p>
      </div>
      <span>{state}</span>
    </div>
  )
}

function Row({
  title,
  subtitle,
  value,
  badge,
}: {
  title: string
  subtitle: string
  value: string
  badge: string
}) {
  return (
    <div className="row">
      <div>
        <strong>{title}</strong>
        <small>{subtitle}</small>
      </div>
      <span className="badge">{badge}</span>
      <b>{value}</b>
    </div>
  )
}

function Empty({ text }: { text: string }) {
  return <div className="empty">{text}</div>
}

function Table({
  rows,
}: {
  rows: Array<{
    id: string
    state: string
    version: string
    policy: string
    value: string
  }>
}) {
  return (
    <div className="table">
      <div className="table-head">
        <span>Order</span>
        <span>State</span>
        <span>Evidence</span>
        <span>Policy</span>
        <span>Contribution</span>
      </div>
      {rows.map((row) => (
        <div className="table-row" key={row.id}>
          <span>{row.id.slice(0, 12)}…</span>
          <span>{row.state}</span>
          <span>{row.version}</span>
          <span>{row.policy}</span>
          <strong>{row.value}</strong>
        </div>
      ))}
    </div>
  )
}

export default App
