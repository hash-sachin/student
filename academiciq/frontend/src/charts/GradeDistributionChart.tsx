/**
 * GradeDistributionChart — bar chart of grade distribution.
 * Colorblind-safe named palette. Data-table alternative for screen readers.
 * Label: CALCULATED.
 */
import React, { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
} from 'recharts'

// Colorblind-safe palette — not color alone, grades are text labels too
const GRADE_COLORS: Record<string, string> = {
  O:   '#0284c7',
  'A+':'#0ea5e9',
  A:   '#22c55e',
  'B+':'#84cc16',
  B:   '#f59e0b',
  C:   '#f97316',
  F:   '#ef4444',
}
const DEFAULT_COLOR = '#6b7280'

interface GradeDistributionChartProps {
  distribution: Record<string, number>
  title?: string
}

export function GradeDistributionChart({ distribution, title }: GradeDistributionChartProps) {
  const [showTable, setShowTable] = useState(false)

  const data = Object.entries(distribution)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([grade, count]) => ({ grade, count }))

  const total = data.reduce((s, d) => s + d.count, 0)

  return (
    <div>
      {title && <p className="text-sm font-medium text-gray-600 mb-2">{title}</p>}

      <div className="flex justify-end mb-1">
        <button
          onClick={() => setShowTable(t => !t)}
          className="text-xs text-primary-600 hover:underline focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
          aria-pressed={showTable}
        >
          {showTable ? 'Show chart' : 'Show data table'}
        </button>
      </div>

      {!showTable && (
        <div aria-hidden="true">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="grade" tick={{ fontSize: 11, fill: '#6b7280' }} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} tickLine={false} axisLine={false} allowDecimals={false} />
              <Tooltip
                contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
                formatter={(value: number, name, props) => [
                  `${value} students (${total > 0 ? ((value / total) * 100).toFixed(1) : 0}%)`,
                  'Count [CALCULATED]',
                ]}
              />
              <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                {data.map((entry, index) => (
                  <Cell key={index} fill={GRADE_COLORS[entry.grade] ?? DEFAULT_COLOR} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {showTable && (
        <div role="region" aria-label="Grade distribution data table">
          <table className="min-w-full text-xs border border-gray-200 rounded-lg overflow-hidden">
            <caption className="sr-only">Grade distribution — CALCULATED metric</caption>
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-3 py-2 text-left font-semibold text-gray-500">Grade</th>
                <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-500">Count</th>
                <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-500">Percentage [CALCULATED]</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map(d => (
                <tr key={d.grade}>
                  <td className="px-3 py-2 font-semibold">{d.grade}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{d.count}</td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {total > 0 ? ((d.count / total) * 100).toFixed(1) : '0.0'}%
                  </td>
                </tr>
              ))}
              <tr className="font-semibold bg-gray-50">
                <td className="px-3 py-2">Total</td>
                <td className="px-3 py-2 text-right tabular-nums">{total}</td>
                <td className="px-3 py-2 text-right">100%</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
