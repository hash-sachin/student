/**
 * WhatIfPage — hypothetical scenario simulator.
 * ALL outputs stamped HYPOTHETICAL. Hatched banner always visible.
 * Never modifies official records. Validates marks against limits.
 */
import React, { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { simulationApi } from '@/api/endpoints'
import { PageHeader } from '@/components/PageHeader'
import { HypotheticalBanner } from '@/components/HypotheticalBanner'
import { MetricBadge } from '@/components/MetricBadge'
import type { WhatIfResult } from '@/types'

interface SubjectEntry {
  subject_id: string
  hypothetical_total_marks: string
}

export default function WhatIfPage() {
  const [searchParams] = useSearchParams()
  const prefillStudentId = searchParams.get('student_id') ?? ''

  const [studentId, setStudentId] = useState(prefillStudentId)
  const [examinationId, setExaminationId] = useState('')
  const [changes, setChanges] = useState<SubjectEntry[]>([
    { subject_id: '', hypothetical_total_marks: '' },
  ])
  const [result, setResult] = useState<WhatIfResult | null>(null)

  const { mutate, isPending, error } = useMutation({
    mutationFn: () =>
      simulationApi
        .whatIf({
          student_id: studentId,
          examination_id: examinationId,
          changes: changes
            .filter(c => c.subject_id && c.hypothetical_total_marks)
            .map(c => ({
              subject_id: c.subject_id,
              hypothetical_total_marks: parseFloat(c.hypothetical_total_marks),
            })),
        })
        .then(r => r.data),
    onSuccess: data => setResult(data),
  })

  const addRow = () =>
    setChanges(prev => [...prev, { subject_id: '', hypothetical_total_marks: '' }])

  const updateRow = (idx: number, field: keyof SubjectEntry, value: string) =>
    setChanges(prev => prev.map((r, i) => (i === idx ? { ...r, [field]: value } : r)))

  const removeRow = (idx: number) =>
    setChanges(prev => prev.filter((_, i) => i !== idx))

  const errMsg = (error as any)?.response?.data?.error?.message ?? String(error ?? '')

  return (
    <div className="space-y-6">
      <PageHeader
        title="What-If Simulator"
        subtitle="Explore hypothetical mark changes and see the arithmetic consequences."
      />

      {/* Always-visible hypothetical warning */}
      <HypotheticalBanner />

      {/* Instructions */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-xs text-gray-600 space-y-1">
        <p className="font-semibold text-gray-700">How this works</p>
        <ul className="list-disc list-inside space-y-0.5">
          <li>Enter the student ID, examination ID, and the subject(s) you want to change.</li>
          <li>The simulator recomputes the average, pass/fail status, and grade purely arithmetically.</li>
          <li>Official records are <strong>never modified</strong>.</li>
          <li>All outputs are stamped <MetricBadge label="HYPOTHETICAL" className="mx-1" /> and cannot be used as official results.</li>
          <li>No causal or likelihood claims are made ("will improve" is never stated).</li>
        </ul>
      </div>

      {/* Input form */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="sim-student-id" className="block text-xs font-medium text-gray-500 mb-1">
              Student ID (UUID)
            </label>
            <input
              id="sim-student-id"
              type="text"
              value={studentId}
              onChange={e => setStudentId(e.target.value.trim())}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label htmlFor="sim-exam-id" className="block text-xs font-medium text-gray-500 mb-1">
              Examination ID (UUID)
            </label>
            <input
              id="sim-exam-id"
              type="text"
              value={examinationId}
              onChange={e => setExaminationId(e.target.value.trim())}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        {/* Subject changes */}
        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">Hypothetical mark changes</p>
          <div className="space-y-2">
            {changes.map((row, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <label className="sr-only" htmlFor={`subj-id-${idx}`}>Subject ID</label>
                <input
                  id={`subj-id-${idx}`}
                  type="text"
                  value={row.subject_id}
                  onChange={e => updateRow(idx, 'subject_id', e.target.value.trim())}
                  placeholder="Subject UUID"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <label className="sr-only" htmlFor={`hyp-marks-${idx}`}>Hypothetical marks</label>
                <input
                  id={`hyp-marks-${idx}`}
                  type="number"
                  min={0}
                  max={100}
                  step={0.5}
                  value={row.hypothetical_total_marks}
                  onChange={e => updateRow(idx, 'hypothetical_total_marks', e.target.value)}
                  placeholder="New marks (0–100)"
                  className="w-36 px-3 py-2 border border-gray-300 rounded-lg text-sm tabular-nums focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                {changes.length > 1 && (
                  <button
                    onClick={() => removeRow(idx)}
                    className="text-gray-400 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-red-500 rounded"
                    aria-label={`Remove row ${idx + 1}`}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            onClick={addRow}
            className="mt-2 text-xs text-primary-600 hover:underline focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
          >
            + Add another subject
          </button>
        </div>

        {errMsg && (
          <div role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">
            {errMsg}
          </div>
        )}

        <button
          onClick={() => mutate()}
          disabled={isPending || !studentId || !examinationId}
          className="px-6 py-2.5 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 transition-colors"
        >
          {isPending ? 'Running simulation…' : 'Run What-If Simulation'}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Mandatory banner — re-shown on result */}
          <HypotheticalBanner />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Current */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-sm font-semibold text-gray-700">Current (Actual)</h3>
                <MetricBadge label="OFFICIAL" />
              </div>
              <p className="text-2xl font-bold text-gray-900 tabular-nums">
                {result.current.average?.toFixed(2) ?? '—'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Passed: {result.current.subjects_passed} · Failed: {result.current.subjects_failed}
              </p>
            </div>

            {/* Hypothetical */}
            <div className="bg-white rounded-xl border-2 border-purple-300 p-5 shadow-sm hypothetical-banner">
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-sm font-semibold text-purple-700">Hypothetical</h3>
                <MetricBadge label="HYPOTHETICAL" />
              </div>
              <p className="text-2xl font-bold text-purple-800 tabular-nums">
                {result.hypothetical.average?.toFixed(2) ?? '—'}
              </p>
              <p className="text-xs text-purple-600 mt-1">
                Passed: {result.hypothetical.subjects_passed} · Failed: {result.hypothetical.subjects_failed}
              </p>
            </div>

            {/* Delta */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-sm font-semibold text-gray-700">Difference</h3>
                <MetricBadge label="HYPOTHETICAL" />
              </div>
              {result.delta.average != null && (
                <p className={`text-2xl font-bold tabular-nums ${result.delta.average >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {result.delta.average >= 0 ? '+' : ''}{result.delta.average.toFixed(2)}
                </p>
              )}
              <p className="text-xs text-gray-500 mt-1">
                Failed change: {result.delta.failed_change >= 0 ? '+' : ''}{result.delta.failed_change}
              </p>
            </div>
          </div>

          {/* Subject detail table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
              <h3 className="text-sm font-semibold text-gray-700">Subject-level comparison</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs" aria-label="Hypothetical subject comparison">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th scope="col" className="px-4 py-2 text-left font-semibold text-gray-500 uppercase">Subject</th>
                    <th scope="col" className="px-4 py-2 text-right font-semibold text-gray-500 uppercase">Current [OFFICIAL]</th>
                    <th scope="col" className="px-4 py-2 text-right font-semibold text-purple-500 uppercase">Hypothetical</th>
                    <th scope="col" className="px-4 py-2 text-center font-semibold text-gray-500 uppercase">Changed?</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {result.hypothetical.subject_details.map((hyp, i) => {
                    const cur = result.current.subject_details.find(c => c.subject_id === hyp.subject_id)
                    return (
                      <tr key={i} className={hyp.changed ? 'bg-purple-50' : ''}>
                        <td className="px-4 py-2 font-mono text-gray-600">{hyp.subject_code}</td>
                        <td className="px-4 py-2 text-right tabular-nums text-gray-700">
                          {cur?.total_marks?.toFixed(1) ?? '—'}
                          {' '}
                          <span className={`text-xs font-medium ${cur?.result_status === 'PASS' ? 'text-green-600' : 'text-red-600'}`}>
                            ({cur?.result_status})
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right tabular-nums font-semibold text-purple-700">
                          {hyp.total_marks?.toFixed(1) ?? '—'}
                          {' '}
                          <span className={`text-xs font-medium ${hyp.result_status === 'PASS' ? 'text-green-600' : 'text-red-600'}`}>
                            ({hyp.result_status})
                          </span>
                        </td>
                        <td className="px-4 py-2 text-center">
                          {hyp.changed ? <span className="text-purple-600 font-medium">✎</span> : ''}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <div className="px-4 py-3 border-t border-gray-100 bg-purple-50">
              <p className="text-xs text-purple-700 font-semibold">{result.hypothetical_banner}</p>
              <p className="text-xs text-purple-600 mt-0.5">
                Scenario ID: <code className="font-mono">{result.scenario_id}</code> ·
                Algorithm: {result.algorithm_version}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
