/**
 * AIInsightsPage — generate and display AI insights with guardrail status.
 * Shows: rendered text, evidence IDs, guardrail pass/fail, fallback template flag.
 * Label: ESTIMATED. Privacy note visible.
 */
import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { aiApi, evidenceApi } from '@/api/endpoints'
import { PageHeader } from '@/components/PageHeader'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { MetricBadge } from '@/components/MetricBadge'
import type { AIInsight } from '@/types'

export default function AIInsightsPage() {
  const [entityType, setEntityType] = useState('student')
  const [entityId, setEntityId] = useState('')
  const [examinationId, setExaminationId] = useState('')
  const [viewingEvidence, setViewingEvidence] = useState<string | null>(null)
  const qc = useQueryClient()

  const { data: insights, isLoading } = useQuery({
    queryKey: ['ai-insights', entityType, entityId],
    queryFn: () => aiApi.list(entityType, entityId).then(r => r.data),
    enabled: !!entityId,
  })

  const { mutate: generate, isPending: generating } = useMutation({
    mutationFn: () =>
      aiApi.generate(entityType, entityId, examinationId || undefined).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai-insights', entityType, entityId] }),
  })

  const { data: evidenceChain, isLoading: evidenceLoading } = useQuery({
    queryKey: ['evidence-chain', viewingEvidence],
    queryFn: () => evidenceApi.getInsightChain(viewingEvidence!).then(r => r.data),
    enabled: !!viewingEvidence,
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Insights"
        subtitle="Evidence-grounded insights generated from verified analytics data"
      />

      {/* Privacy and label notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-xs text-blue-800 space-y-1">
        <p className="font-semibold">About AI Insights</p>
        <ul className="list-disc list-inside space-y-0.5 text-blue-700">
          <li>All insights are labeled <MetricBadge label="ESTIMATED" className="mx-1" /> — not official calculations.</li>
          <li>Every numeric claim is verified against the evidence payload before display (guardrail G1).</li>
          <li>No student names or register numbers are sent to the LLM (privacy by design).</li>
          <li>Causal claims ("because", "due to") are filtered out (guardrail G3).</li>
          <li>Mental health, family, financial, or personal inferences are blocked (guardrail G4).</li>
          <li>If AI output fails verification twice, a deterministic template summary is shown instead.</li>
        </ul>
      </div>

      {/* Input form */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="entity-type" className="block text-xs font-medium text-gray-500 mb-1">Entity type</label>
            <select
              id="entity-type"
              value={entityType}
              onChange={e => setEntityType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="student">Student</option>
              <option value="class">Class / Section</option>
              <option value="department">Department</option>
            </select>
          </div>
          <div>
            <label htmlFor="entity-id-ai" className="block text-xs font-medium text-gray-500 mb-1">Entity ID (UUID)</label>
            <input
              id="entity-id-ai"
              type="text"
              value={entityId}
              onChange={e => setEntityId(e.target.value.trim())}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label htmlFor="exam-id-ai" className="block text-xs font-medium text-gray-500 mb-1">Examination ID (optional)</label>
            <input
              id="exam-id-ai"
              type="text"
              value={examinationId}
              onChange={e => setExaminationId(e.target.value.trim())}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
        <button
          onClick={() => generate()}
          disabled={generating || !entityId}
          className="px-5 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
        >
          {generating ? 'Generating insight…' : '✦ Generate Insight'}
        </button>
      </div>

      {/* Insight list */}
      {isLoading && entityId && <LoadingSpinner label="Loading insights…" />}

      {insights && insights.length === 0 && entityId && (
        <p className="text-sm text-gray-400 text-center py-8">No insights yet for this entity. Generate one above.</p>
      )}

      {insights && insights.map((insight: AIInsight) => (
        <div key={insight.id} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <MetricBadge label="ESTIMATED" />
              {insight.guardrail_passed ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded">
                  ✓ Guardrails passed
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-100 text-red-700 text-xs font-medium rounded">
                  ✗ Guardrail failed
                </span>
              )}
              {insight.is_fallback_template && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs font-medium rounded">
                  ⚠ Deterministic template (AI output failed verification)
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-400">Model: {insight.model_version}</span>
              <span className="text-xs text-gray-400">{new Date(insight.created_at).toLocaleString()}</span>
              <button
                onClick={() => setViewingEvidence(viewingEvidence === insight.id ? null : insight.id)}
                className="text-xs text-primary-600 hover:underline focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
                aria-expanded={viewingEvidence === insight.id}
              >
                {viewingEvidence === insight.id ? 'Hide Evidence' : 'View Evidence'}
              </button>
            </div>
          </div>

          {/* Rendered insight text */}
          <div className="px-5 py-4">
            <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">
              {insight.rendered_text}
            </pre>
          </div>

          {/* Evidence chain */}
          {viewingEvidence === insight.id && (
            <div className="border-t border-gray-100 px-5 py-4 bg-gray-50">
              <h4 className="text-xs font-semibold text-gray-600 mb-2">Evidence Chain</h4>
              {evidenceLoading && <LoadingSpinner label="Loading evidence chain…" />}
              {evidenceChain && (
                <div className="space-y-1">
                  {evidenceChain.chain?.length === 0 && (
                    <p className="text-xs text-gray-400">No evidence chain found for this insight.</p>
                  )}
                  {evidenceChain.chain?.map((node: any) => (
                    <div
                      key={node.id}
                      className="flex items-center gap-2 text-xs"
                      style={{ paddingLeft: `${node.depth * 1.5}rem` }}
                    >
                      <span className="text-gray-300" aria-hidden="true">{'└ '.repeat(Math.min(node.depth, 1))}</span>
                      <span className="font-mono text-gray-500">[{node.node_type}]</span>
                      <span className="text-gray-700">{node.label}</span>
                    </div>
                  ))}
                  <p className="text-xs text-gray-400 mt-2">
                    Chain complete: {evidenceChain.chain_complete ? '✓ Yes' : '✗ No'}
                  </p>
                </div>
              )}

              {/* Evidence IDs */}
              <div className="mt-3">
                <p className="text-xs font-semibold text-gray-500 mb-1">Evidence metric IDs</p>
                <div className="flex flex-wrap gap-1">
                  {insight.evidence_ids?.map((id: string) => (
                    <code key={id} className="text-xs bg-white border border-gray-200 rounded px-1.5 py-0.5 font-mono text-gray-600">
                      {id.slice(0, 8)}…
                    </code>
                  )) ?? <span className="text-xs text-gray-400">None</span>}
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
