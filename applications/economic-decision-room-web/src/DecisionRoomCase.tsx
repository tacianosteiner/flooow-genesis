import { useEffect, useState } from 'react'
import { getDecisionRoomProjection, type DecisionRoomProjection } from './decision-room'
import type { ExactMoney } from './api'

const exactAmount = (value: ExactMoney | null): string =>
  value === null ? 'Não quantificado' : `${value.currency} ${value.amount}`

export function DecisionRoomCase({ caseId }: { caseId: string }) {
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState<{ caseId?: string; attempt?: number; projection?: DecisionRoomProjection; error?: string }>({})
  useEffect(() => {
    const controller = new AbortController()
    let active = true
    getDecisionRoomProjection(caseId, controller.signal).then(
      (projection) => { if (active) setState({ caseId, attempt, projection }) },
      (error: unknown) => { if (active) setState({ caseId, attempt, error: error instanceof Error ? error.message : 'Projeção indisponível.' }) },
    )
    return () => { active = false; controller.abort() }
  }, [caseId, attempt])

  const current = state.caseId === caseId && state.attempt === attempt
  const projection = current ? state.projection : undefined
  const error = current ? state.error : undefined
  return <section className="reconciliation-panel panel" aria-label="Projeção governada do caso">
    <div className="panel-heading"><div><h2>Decision Room · caso</h2><small>{caseId}</small></div></div>
    {error ? <div role="alert"><b>Projeção indisponível</b><p>{error}</p>
      <button className="secondary-button" onClick={() => { setState({}); setAttempt((value) => value + 1) }}>Tentar leitura novamente</button></div>
      : !projection ? <p role="status">Consultando projeção governada…</p>
        : <>
          <p>Projeção: <strong>{projection.projectionStatus}</strong> · Autoridade: <strong>{projection.authorityStatus}</strong></p>
          <p>Governança permitida pelo backend: {projection.governancePermitted ? 'Sim' : 'Não'}</p>
          <p>Perda total quantificada: <strong>{exactAmount(projection.totalQuantifiedLeakage)}</strong></p>
          <p>Revisão {projection.reconciliationRevision} · Política {projection.policyVersion}</p>
          <ul aria-label="Bloqueios da projeção">{[
            ...projection.authorityBlockingReasons.map((reason) => `Autoridade: ${reason}`),
            ...projection.governanceBlockingReasons.map((reason) => `Governança: ${reason}`),
            ...projection.projectionBlockingReasons.map((reason) => `Projeção: ${reason}`),
          ].map((reason, index) => <li key={`${index}:${reason}`}>{reason}</li>)}</ul>
          <div className="case-list">{projection.stages.map((stage, index) => <div className="case-row" key={`${index}:${stage.stage}`}>
            <div><b>{stage.stage}</b><small>{stage.interpretation ?? 'Interpretação indisponível'}</small></div>
            <span>Variação: {stage.signedVariance === null ? 'Indisponível' : exactAmount(stage.signedVariance)}</span>
            <span>Perda: {exactAmount(stage.quantifiedLeakage)}</span>
            {stage.blockingReason && <span>{stage.blockingReason}</span>}
          </div>)}</div>
          <details><summary>Referências de evidência</summary><ul>{projection.evidenceReferences.map((ref, index) => <li key={`${index}:${ref}`}>{ref}</li>)}</ul></details>
          <p>Leitura derivada do backend. Esta tela não concede autoridade nem executa ações econômicas.</p>
        </>}
  </section>
}
