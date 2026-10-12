import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ApiError,
  demoModeEnabled,
  getCommerceIdentityHealth,
  getOrder,
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

type Availability = 'LOADING' | 'AVAILABLE' | 'UNAVAILABLE'

const ROOM_OPERATIONAL = false

const stateLabel: Record<SalesOrder['state'], string> = {
  CALCULATED_COMPLETE: 'Calculado · Completo',
  CALCULATED_INCOMPLETE: 'Calculado · Incompleto',
  UNRESOLVED: 'Não resolvido',
}

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

const executiveLenses: Lens[] = ['CEO', 'CFO', 'COO', 'CRO']

const institutionalLenses: Lens[] = [
  'TRUTH',
  'RECONCILIATION',
  'DECISIONS',
  'HEALTH',
]

const money = (value?: string, currency = 'BRL') => {
  if (value === undefined) return 'Não disponível'

  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency,
  }).format(Number(value))
}

function App() {
  const demo = demoModeEnabled()

  const [lens, setLens] = useState<Lens>('CEO')
  const [orders, setOrders] = useState<SalesOrder[]>(demo ? demoOrders : [])
  const [nextCursor, setNextCursor] = useState<string | undefined>()
  const [selected, setSelected] = useState<SalesOrder | undefined>()
  const [cases, setCases] = useState<ReconciliationCase[]>([])
  const [signals, setSignals] = useState<SystemicDivergenceSignal[]>([])
  const [identity, setIdentity] = useState<CommerceIdentityHealth | undefined>()

  const [loading, setLoading] = useState(!demo)
  const [detailLoading, setDetailLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const [coreError, setCoreError] = useState<string>()
  const [refreshSuccess, setRefreshSuccess] = useState(false)

  const [reconciliationAvailability, setReconciliationAvailability] =
    useState<Availability>(demo ? 'AVAILABLE' : 'LOADING')
  const [systemicAvailability, setSystemicAvailability] =
    useState<Availability>(demo ? 'AVAILABLE' : 'LOADING')
  const [identityAvailability, setIdentityAvailability] =
    useState<Availability>(demo ? 'AVAILABLE' : 'LOADING')

  const loadOrders = useCallback(
    async (cursor?: string) => {
      if (demo) {
        setOrders(demoPage.orders)
        setNextCursor(demoPage.nextCursor)
        return
      }

      if (!cursor) setLoading(true)
      setCoreError(undefined)

      try {
        const page = await listOrders(cursor)

        setOrders((current) =>
          cursor ? [...current, ...page.orders] : page.orders,
        )

        setNextCursor(page.nextCursor)
      } catch (cause) {
        setCoreError(
          cause instanceof ApiError
            ? cause.message
            : 'Falha ao carregar a projeção econômica.',
        )
      } finally {
        if (!cursor) setLoading(false)
      }
    },
    [demo],
  )

  const loadOptionalSources = useCallback(async () => {
    if (demo) return

    setReconciliationAvailability('LOADING')
    setSystemicAvailability('LOADING')
    setIdentityAvailability('LOADING')

    void listReconciliationCases()
      .then((response) => {
        setCases(response.cases ?? [])
        setReconciliationAvailability('AVAILABLE')
      })
      .catch(() => {
        setCases([])
        setReconciliationAvailability('UNAVAILABLE')
      })

    void listSystemicDivergences()
      .then((response) => {
        setSignals(response.signals ?? [])
        setSystemicAvailability('AVAILABLE')
      })
      .catch(() => {
        setSignals([])
        setSystemicAvailability('UNAVAILABLE')
      })

    void getCommerceIdentityHealth()
      .then((response) => {
        setIdentity(response)
        setIdentityAvailability('AVAILABLE')
      })
      .catch(() => {
        setIdentity(undefined)
        setIdentityAvailability('UNAVAILABLE')
      })
  }, [demo])

  useEffect(() => {
    void loadOrders()

    if (!demo) {
      void loadOptionalSources()
    }
  }, [demo, loadOrders, loadOptionalSources])

  const selectOrder = async (order: SalesOrder) => {
    setDetailLoading(true)
    setCoreError(undefined)

    try {
      const detail = demo
        ? demoOrders.find(
            (item) => item.marketplaceOrderId === order.marketplaceOrderId,
          ) ?? order
        : await getOrder(order.marketplaceOrderId)

      setSelected(detail)
    } catch (cause) {
      setCoreError(
        cause instanceof ApiError
          ? cause.message
          : 'Não foi possível abrir o detalhe do pedido.',
      )
    } finally {
      setDetailLoading(false)
    }
  }

  const refresh = async () => {
    setRefreshing(true)
    setCoreError(undefined)
    setRefreshSuccess(false)

    try {
      if (demo) {
        await Promise.resolve(demoRefresh)
        setOrders(demoPage.orders)
      } else {
        await refreshOrders()
        await loadOrders()
        await loadOptionalSources()
      }

      setRefreshSuccess(true)
    } catch (cause) {
      setCoreError(
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

  const totals = useMemo(
    () =>
      complete.reduce(
        (acc, order) => {
          const result = order.economicResult

          if (!result) return acc

          acc.revenue += Number(result.grossRevenue || 0)
          acc.contribution += Number(result.contribution || 0)
          acc.fees += Number(result.totalMarketplaceFees || 0)
          acc.shipping += Number(result.totalShipping || 0)
          acc.taxes += Number(result.totalTaxes || 0)
          acc.productCost += Number(result.totalProductCost || 0)

          return acc
        },
        {
          revenue: 0,
          contribution: 0,
          fees: 0,
          shipping: 0,
          taxes: 0,
          productCost: 0,
        },
      ),
    [complete],
  )

  const contributionMargin =
    totals.revenue > 0 ? totals.contribution / totals.revenue : undefined

  const coverage =
    orders.length > 0
      ? Math.round((complete.length / orders.length) * 100)
      : 0

  const meta = lensMeta[lens]

  const reconciliationValue =
    reconciliationAvailability === 'AVAILABLE'
      ? String(cases.length)
      : reconciliationAvailability === 'UNAVAILABLE'
        ? 'Indisponível'
        : 'Carregando'

  const systemicValue =
    systemicAvailability === 'AVAILABLE'
      ? String(signals.length)
      : systemicAvailability === 'UNAVAILABLE'
        ? 'Indisponível'
        : 'Carregando'

  const identityUnresolvedValue =
    identityAvailability === 'AVAILABLE'
      ? String(identity?.unresolved ?? 0)
      : identityAvailability === 'UNAVAILABLE'
        ? 'Indisponível'
        : 'Carregando'

  const exceptionCount = incomplete.length + unresolved.length

  const truthPosture =
    loading
      ? 'LOADING'
      : unresolved.length > 0
        ? 'UNRESOLVED'
        : incomplete.length > 0
          ? 'INCOMPLETE'
          : orders.length > 0
            ? 'COMPLETE'
            : 'NO OBSERVATION'

  const evidencePosture =
    orders.length > 0
      ? `${coverage}% COMPLETE`
      : 'NO OBSERVATION'

  const executionPosture =
    ROOM_OPERATIONAL
      ? 'OPERATIONAL'
      : 'BLOCKED'

  const hasTruthExceptions = exceptionCount > 0
  const hasUnresolvedTruth = unresolved.length > 0
  const hasSystemicSignals =
    systemicAvailability === 'AVAILABLE' && signals.length > 0
  const hasOpenReconciliation =
    reconciliationAvailability === 'AVAILABLE' &&
    cases.some((item) => item.status !== 'RESOLVED')

  const executiveSynthesis: Record<
    'CEO' | 'CFO' | 'COO' | 'CRO',
    {
      state: string
      meaning: string
      attention: string
      boundary: string
      tone: 'neutral' | 'good' | 'warn' | 'risk'
    }
  > = {
    CEO: {
      state:
        hasUnresolvedTruth || hasSystemicSignals || hasOpenReconciliation
          ? 'ATTENTION REQUIRED'
          : hasTruthExceptions
            ? 'INCOMPLETE OBSERVATION'
            : 'OBSERVED STATE STABLE',
      meaning:
        hasTruthExceptions
          ? 'A visão executiva está condicionada por exceções na Economic Truth; decisões materiais devem considerar essa incompletude.'
          : 'A leitura executiva atual não apresenta exceções econômicas conhecidas na projeção observada.',
      attention:
        hasUnresolvedTruth
          ? 'Resolver identidade ou verdade não resolvida antes de tratar a leitura como completa.'
          : hasOpenReconciliation
            ? 'Priorizar casos de reconciliação ainda abertos.'
            : hasSystemicSignals
              ? 'Investigar sinais sistêmicos antes de ampliar confiança operacional.'
              : 'Nenhuma exceção material adicional é inferida além do que está observado.',
      boundary:
        'A Room interpreta e prioriza atenção; não concede autoridade de execução.',
      tone:
        hasUnresolvedTruth || hasSystemicSignals || hasOpenReconciliation
          ? 'risk'
          : hasTruthExceptions
            ? 'warn'
            : 'good',
    },
    CFO: {
      state:
        hasTruthExceptions || hasOpenReconciliation
          ? 'FINANCIAL CONFIDENCE CONSTRAINED'
          : 'OBSERVED ECONOMICS COMPLETE',
      meaning:
        hasTruthExceptions
          ? 'Receita e contribuição publicadas permanecem limitadas aos pedidos economicamente completos.'
          : 'A projeção observada está completa para os pedidos atualmente carregados.',
      attention:
        hasOpenReconciliation
          ? 'Revisar divergências persistidas antes de considerar fechamento econômico.'
          : hasTruthExceptions
            ? 'Completar componentes econômicos ausentes antes de ampliar conclusões sobre margem.'
            : 'Manter reconciliação e proveniência como controles de fechamento.',
      boundary:
        'Ausência de evidência não é convertida em zero, estimativa ou vazamento presumido.',
      tone:
        hasTruthExceptions || hasOpenReconciliation ? 'warn' : 'good',
    },
    COO: {
      state:
        hasUnresolvedTruth || hasSystemicSignals
          ? 'OPERATIONAL EXCEPTIONS PRESENT'
          : hasTruthExceptions
            ? 'PROCESS COMPLETENESS LIMITED'
            : 'OBSERVED FLOW STABLE',
      meaning:
        hasUnresolvedTruth
          ? 'Existem ocorrências cuja verdade operacional ainda não pode ser resolvida.'
          : hasSystemicSignals
            ? 'Sinais sistêmicos exigem investigação antes de qualquer recuperação operacional.'
            : 'Nenhum bloqueio operacional adicional é inferido além do estado observado.',
      attention:
        hasUnresolvedTruth
          ? 'Tratar primeiro os itens não resolvidos e suas causas upstream.'
          : hasSystemicSignals
            ? 'Isolar a divergência e sua evidência antes de autorizar recuperação.'
            : 'Preservar monitoramento de exceções e completude.',
      boundary:
        'Detecção de falha ou divergência não concede autorização de recovery.',
      tone:
        hasUnresolvedTruth || hasSystemicSignals
          ? 'risk'
          : hasTruthExceptions
            ? 'warn'
            : 'good',
    },
    CRO: {
      state: 'OBSERVED REVENUE · LIMITED INTELLIGENCE',
      meaning:
        'A Room mostra receita e margem observadas, mas ainda não possui evidência suficiente para transformar isso em previsão ou oportunidade futura.',
      attention:
        hasTruthExceptions
          ? 'Aumentar cobertura econômica antes de comparar pressão comercial com confiança elevada.'
          : 'Usar somente sinais comerciais suportados por evidência quando essa camada estiver disponível.',
      boundary:
        'Forecast, oportunidade e recomendação comercial não são inventados a partir de dados ausentes.',
      tone: 'warn',
    },
  }

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

        <div className="preview-chip">ROOM V2 · EXECUTIVE PREVIEW</div>

        <nav aria-label="Room navigation">
          <div className="nav-group">
            <span className="nav-group-label">EXECUTIVE LENSES</span>

            {executiveLenses.map((key) => (
              <button
                key={key}
                className={lens === key ? 'active' : ''}
                onClick={() => setLens(key)}
              >
                {lensMeta[key].label}
              </button>
            ))}
          </div>

          <div className="nav-group institutional">
            <span className="nav-group-label">INSTITUTIONAL SPINE</span>

            {institutionalLenses.map((key) => (
              <button
                key={key}
                className={lens === key ? 'active' : ''}
                onClick={() => setLens(key)}
              >
                {lensMeta[key].label}
              </button>
            ))}
          </div>
        </nav>

        <div className="rail-footer">
          <strong>Governed environment</strong>
          <span>Preview ≠ operational authority</span>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <span className="breadcrumb">FLOOOW / EXECUTIVE ROOM / V2</span>

          <div className="top-status">
            <span className="status-dot hold" />
            <span>
              ROOM_OPERATIONAL = {ROOM_OPERATIONAL ? 'YES' : 'NO'}
            </span>
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
            Esta superfície não concede autoridade operacional ou de execução.
            Economic Truth permanece governado pelo core.
          </span>
        </div>

        {demo && (
          <div className="preview-warning" role="status">
            <strong>Modo demonstração</strong>
            <span>
              Dados determinísticos locais. Nenhuma chamada ao backend é feita.
            </span>
          </div>
        )}

        <section
          className="institutional-context"
          aria-label="Contexto institucional compartilhado"
        >
          <div className="institutional-context-heading">
            <span>ONE ECONOMIC REALITY</span>
            <strong>Shared institutional context</strong>
            <p>
              CEO, CFO, COO e CRO observam a mesma Economic Truth.
              A lente muda; a realidade institucional não.
            </p>
          </div>

          <div className="institutional-context-grid">
            <ContextFact
              label="Truth posture"
              value={truthPosture}
              state={
                truthPosture === 'COMPLETE'
                  ? 'good'
                  : truthPosture === 'UNRESOLVED'
                    ? 'risk'
                    : 'warn'
              }
            />
            <ContextFact
              label="Truth exceptions"
              value={String(exceptionCount)}
              state={exceptionCount > 0 ? 'warn' : 'good'}
            />
            <ContextFact
              label="Evidence completeness"
              value={evidencePosture}
              state={coverage === 100 ? 'good' : 'warn'}
            />
            <ContextFact
              label="Execution authority"
              value={executionPosture}
              state={ROOM_OPERATIONAL ? 'good' : 'blocked'}
            />
          </div>
        </section>

        {coreError && (
          <div className="error" role="alert">
            <strong>Fail closed</strong>
            <span>{coreError}</span>
          </div>
        )}

        {refreshSuccess && !coreError && (
          <div className="success" role="status">
            <strong>Realidade atualizada com governança</strong>
            <span>A projeção foi recarregada após o refresh governado.</span>
          </div>
        )}

        <div className="section-intro">
          <div>
            <span>SHARED ECONOMIC TRUTH</span>
            <strong>Observed economics</strong>
          </div>
          <p>
            Estes números são compartilhados entre todas as lentes executivas.
            Nenhuma lente redefine a verdade econômica.
          </p>
        </div>

        <section
          className="metrics"
          aria-label="Shared Economic Truth metrics"
        >
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
                ? 'Não disponível'
                : `${(contributionMargin * 100).toFixed(1)}%`
            }
            hint="não estimada quando a verdade está incompleta"
          />
          <Metric
            label="Cobertura"
            value={`${coverage}%`}
            hint={`${complete.length}/${orders.length} pedidos completos`}
          />
        </section>

        {lens === 'CEO' && (
          <>
            <ExecutiveBrief
              lens="CEO"
              synthesis={executiveSynthesis.CEO}
            />

            <ExecutiveGrid>
            <Panel title="Executive pulse" eyebrow="BUSINESS STATE">
              <Signal
                label="Economic coverage"
                value={`${coverage}%`}
                state={coverage === 100 ? 'good' : 'warn'}
              />
              <Signal
                label="Open reconciliation"
                value={reconciliationValue}
                state={
                  reconciliationAvailability !== 'AVAILABLE'
                    ? 'warn'
                    : cases.some((item) => item.status !== 'RESOLVED')
                      ? 'risk'
                      : 'good'
                }
              />
              <Signal
                label="Systemic divergence signals"
                value={systemicValue}
                state={
                  systemicAvailability !== 'AVAILABLE'
                    ? 'warn'
                    : signals.length
                      ? 'risk'
                      : 'good'
                }
              />
              <Signal
                label="Identity unresolved"
                value={identityUnresolvedValue}
                state={
                  identityAvailability !== 'AVAILABLE'
                    ? 'warn'
                    : (identity?.unresolved ?? 0) > 0
                      ? 'warn'
                      : 'good'
                }
              />
            </Panel>

            <Panel title="Decision posture" eyebrow="EXECUTIVE ACTION">
              <Decision
                title="Analyze"
                state="AVAILABLE"
                body="A superfície de leitura continua disponível sem autoridade de execução."
              />
              <Decision
                title="Operate"
                state="BLOCKED"
                body="O Room ainda não possui prova operacional canônica."
              />
              <Decision
                title="Execute"
                state="NO AUTHORITY"
                body="Nenhuma ação econômica é autorizada por esta preview."
              />
            </Panel>
            </ExecutiveGrid>
          </>
        )}

        {lens === 'CFO' && (
          <>
            <ExecutiveBrief
              lens="CFO"
              synthesis={executiveSynthesis.CFO}
            />

            <ExecutiveGrid>
            <Panel title="Economic control" eyebrow="MARGIN & COST">
              <Signal
                label="Gross revenue"
                value={money(totals.revenue.toString())}
              />
              <Signal
                label="Marketplace fees"
                value={money(totals.fees.toString())}
              />
              <Signal
                label="Shipping"
                value={money(totals.shipping.toString())}
              />
              <Signal
                label="Taxes"
                value={money(totals.taxes.toString())}
              />
              <Signal
                label="Product cost"
                value={money(totals.productCost.toString())}
              />
            </Panel>

            <Panel title="Truth exceptions" eyebrow="FINANCIAL CONFIDENCE">
              <Signal
                label="Complete"
                value={String(complete.length)}
                state="good"
              />
              <Signal
                label="Incomplete"
                value={String(incomplete.length)}
                state="warn"
              />
              <Signal
                label="Unresolved"
                value={String(unresolved.length)}
                state="risk"
              />
              <Signal
                label="Reconciliation cases"
                value={reconciliationValue}
                state={
                  reconciliationAvailability === 'AVAILABLE' && cases.length === 0
                    ? 'good'
                    : 'warn'
                }
              />
            </Panel>
            </ExecutiveGrid>
          </>
        )}

        {lens === 'COO' && (
          <>
            <ExecutiveBrief
              lens="COO"
              synthesis={executiveSynthesis.COO}
            />

            <ExecutiveGrid>
            <Panel title="Operational exceptions" eyebrow="OPERATIONS">
              <Signal label="Orders observed" value={String(orders.length)} />
              <Signal
                label="Incomplete"
                value={String(incomplete.length)}
                state="warn"
              />
              <Signal
                label="Unresolved"
                value={String(unresolved.length)}
                state="risk"
              />
              <Signal
                label="Systemic signals"
                value={systemicValue}
                state={
                  systemicAvailability === 'AVAILABLE' && signals.length === 0
                    ? 'good'
                    : 'warn'
                }
              />
            </Panel>

            <Panel title="Operational posture" eyebrow="CONTROL">
              <Decision
                title="Refresh"
                state={demo ? 'DEMO' : 'GOVERNED'}
                body="Refresh permanece separado de autoridade de execução."
              />
              <Decision
                title="Recovery"
                state="NOT AUTHORIZED"
                body="Divergência não concede autorização de recuperação."
              />
            </Panel>
            </ExecutiveGrid>
          </>
        )}

        {lens === 'CRO' && (
          <>
            <ExecutiveBrief
              lens="CRO"
              synthesis={executiveSynthesis.CRO}
            />

            <ExecutiveGrid>
            <Panel title="Revenue posture" eyebrow="GROWTH">
              <Signal
                label="Observed revenue"
                value={money(totals.revenue.toString())}
              />
              <Signal
                label="Contribution margin"
                value={
                  contributionMargin === undefined
                    ? 'Não disponível'
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
                body="Nenhuma oportunidade futura é inventada com dados inexistentes."
              />
              <Decision
                title="Current Room"
                state="TRUTH-FIRST"
                body="Receita observada permanece separada de previsão."
              />
            </Panel>
            </ExecutiveGrid>
          </>
        )}

        {lens === 'TRUTH' && (
          <>
            <Panel title="Economic Truth" eyebrow="CANONICAL EVIDENCE">
              {loading ? (
                <Empty text="Carregando projeção econômica…" />
              ) : orders.length === 0 ? (
                <Empty text="Nenhum pedido projetado" />
              ) : (
                <>
                  <div className="truth-table-scroll">
                    <table className="truth-table">
                      <thead>
                        <tr>
                          <th scope="col">Order</th>
                          <th scope="col">State</th>
                          <th scope="col">Evidence</th>
                          <th scope="col">Policy</th>
                          <th scope="col">Contribution</th>
                          <th scope="col">Detail</th>
                        </tr>
                      </thead>
                      <tbody>
                        {orders.map((order) => (
                          <tr key={order.marketplaceOrderId}>
                            <td>
                              #{order.marketplaceOrderId.slice(0, 8)}
                            </td>
                            <td>{stateLabel[order.state]}</td>
                            <td>{order.sourceEvidenceVersion}</td>
                            <td>{order.assemblyPolicyVersion}</td>
                            <td>
                              {order.economicResult
                                ? money(
                                    order.economicResult.contribution,
                                    order.economicResult.currency,
                                  )
                                : 'Não disponível'}
                            </td>
                            <td>
                              <button
                                className="detail-button"
                                disabled={detailLoading}
                                aria-label={`Abrir #${order.marketplaceOrderId.slice(0, 8)}`}
                                onClick={() => void selectOrder(order)}
                              >
                                Abrir
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {nextCursor && (
                    <button
                      className="pagination-button"
                      onClick={() => void loadOrders(nextCursor)}
                    >
                      Próxima →
                    </button>
                  )}
                </>
              )}
            </Panel>

            {selected && (
              <section className="detail-card" aria-label="Detalhe econômico">
                <div className="detail-heading">
                  <div>
                    <span>DERIVED / NON-CANONICAL</span>
                    <h2>#{selected.marketplaceOrderId.slice(0, 8)}</h2>
                  </div>
                  <button
                    aria-label="Fechar detalhe"
                    onClick={() => setSelected(undefined)}
                  >
                    ×
                  </button>
                </div>

                <div className="boundary">
                  <strong>Derivado · não canônico</strong>
                  <span>
                    Economic Truth permanece a autoridade upstream.
                  </span>
                </div>

                <dl className="detail-grid">
                  <div>
                    <dt>Estado</dt>
                    <dd>{stateLabel[selected.state]}</dd>
                  </div>
                  <div>
                    <dt>Evidence</dt>
                    <dd>{selected.sourceEvidenceVersion}</dd>
                  </div>
                  <div>
                    <dt>Policy</dt>
                    <dd>{selected.assemblyPolicyVersion}</dd>
                  </div>
                  <div>
                    <dt>Receita</dt>
                    <dd>
                      {selected.economicResult
                        ? money(
                            selected.economicResult.grossRevenue,
                            selected.economicResult.currency,
                          )
                        : 'Não disponível'}
                    </dd>
                  </div>
                  <div>
                    <dt>Contribuição</dt>
                    <dd>
                      {selected.economicResult
                        ? money(
                            selected.economicResult.contribution,
                            selected.economicResult.currency,
                          )
                        : 'Não disponível'}
                    </dd>
                  </div>
                  <div>
                    <dt>Margem</dt>
                    <dd>
                      {selected.economicResult?.contributionMargin !== undefined
                        ? `${(
                            Number(
                              selected.economicResult.contributionMargin,
                            ) * 100
                          ).toFixed(1)}%`
                        : 'Não disponível'}
                    </dd>
                  </div>
                </dl>
              </section>
            )}
          </>
        )}

        {lens === 'RECONCILIATION' && (
          <Panel title="Reconciliation" eyebrow="DIVERGENCE MEMORY">
            {reconciliationAvailability === 'UNAVAILABLE' ? (
              <Unavailable text="Fonte de reconciliação indisponível." />
            ) : reconciliationAvailability === 'LOADING' ? (
              <Empty text="Carregando reconciliação…" />
            ) : cases.length === 0 ? (
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
              <Signal
                label="Room operational"
                value={ROOM_OPERATIONAL ? 'YES' : 'NO'}
                state="risk"
              />
              <Signal
                label="Canonical execution"
                value="NOT RUN"
                state="warn"
              />
              <Signal
                label="Preview surface"
                value="AVAILABLE"
                state="good"
              />
            </Panel>

            <Panel title="Identity health" eyebrow="COMMERCE IDENTITY">
              {identityAvailability === 'UNAVAILABLE' ? (
                <Unavailable text="Fonte de identidade indisponível." />
              ) : identityAvailability === 'LOADING' ? (
                <Empty text="Carregando identity health…" />
              ) : (
                <>
                  <Signal
                    label="Coverage"
                    value={
                      identity?.coveragePercentage !== undefined
                        ? `${identity.coveragePercentage}%`
                        : 'Não disponível'
                    }
                  />
                  <Signal
                    label="Exact confirmed"
                    value={String(identity?.exactConfirmed ?? 0)}
                  />
                  <Signal
                    label="Candidates"
                    value={String(identity?.candidate ?? 0)}
                  />
                  <Signal
                    label="Conflicts"
                    value={String(identity?.conflict ?? 0)}
                    state={(identity?.conflict ?? 0) > 0 ? 'risk' : 'good'}
                  />
                </>
              )}
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

function ExecutiveBrief({
  lens,
  synthesis,
}: {
  lens: 'CEO' | 'CFO' | 'COO' | 'CRO'
  synthesis: {
    state: string
    meaning: string
    attention: string
    boundary: string
    tone: 'neutral' | 'good' | 'warn' | 'risk'
  }
}) {
  return (
    <section
      className={`executive-brief ${synthesis.tone}`}
      aria-label={`${lens} executive synthesis`}
    >
      <div className="executive-brief-state">
        <span>EXECUTIVE SYNTHESIS</span>
        <strong>{synthesis.state}</strong>
      </div>

      <div className="executive-brief-item">
        <span>WHY IT MATTERS</span>
        <p>{synthesis.meaning}</p>
      </div>

      <div className="executive-brief-item">
        <span>ATTENTION</span>
        <p>{synthesis.attention}</p>
      </div>

      <div className="executive-brief-item boundary-item">
        <span>BOUNDARY</span>
        <p>{synthesis.boundary}</p>
      </div>
    </section>
  )
}

function ContextFact({
  label,
  value,
  state = 'neutral',
}: {
  label: string
  value: string
  state?: 'neutral' | 'good' | 'warn' | 'risk' | 'blocked'
}) {
  return (
    <div className={`context-fact ${state}`}>
      <span>{label}</span>
      <strong>{value}</strong>
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

function Unavailable({ text }: { text: string }) {
  return (
    <div className="unavailable">
      <strong>Indisponível</strong>
      <span>{text}</span>
    </div>
  )
}

export default App
