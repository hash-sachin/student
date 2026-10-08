/**
 * SemesterTrendChart — line chart of semester averages over time.
 * Colorblind-safe palette. Provides data-table alternative for screen readers.
 * Uses Recharts. Label: CALCULATED.
 */
import React, { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts'

interface DataPoint {
  label: string
  average: number | null
  passed?: number
  failed?: number
}

interface SemesterTrendChartProps {
  data: DataPoint[]
  passMarkLine?: number
}

export function SemesterTrendChart({ data, passMarkLine = 50 }: SemesterTrendChartProps) {
  const [showTable, setShowTable] = useState(false)

  // Filter out null averages for the chart
  const chartData = data.map(d => ({ ...d, average: d.average ?? undefined }))

  return (
    <div>
      {/* Toggle data table */}
      <div className="flex justify-end mb-2">
        <button
          onClick={() => setShowTable(t => !t)}
          className="text-xs text-primary-600 hover:underline focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
          aria-pressed={showTable}
        >
          {showTable ? 'Hide data table' : 'Show data table (accessible alternative)'}
        </button>
      </div>

      {/* Chart */}
      <div aria-hidden={showTable} style={{ display: showTable ? 'none' : 'block' }}>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: '#6b7280' }}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 11, fill: '#6b7280' }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
              formatter={(value: number) => [`${value?.toFixed(2)}`, 'Avg [CALCULATED]']}
            />
            <Legend
              formatter={() => 'Semester Average [CALCULATED]'}
              wrapperStyle={{ fontSize: 11 }}
            />
            {/* Pass mark reference line */}
            <ReferenceLine
              y={passMarkLine}
              stroke="#f59e0b"
              strokeDasharray="4 2"
              label={{ value: `Pass mark (${passMarkLine})`, fontSize: 10, fill: '#92400e', position: 'insideTopRight' }}
            />
            {/* Colorblind-safe blue — not color alone, also uses data labels */}
            <Line
              type="monotone"
              dataKey="average"
              stroke="#0284c7"
              strokeWidth={2}
              dot={{ r: 4, fill: '#0284c7', stroke: '#fff', strokeWidth: 2 }}
              activeDot={{ r: 6 }}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Accessible data table alternative */}
      {showTable && (
        <div role="region" aria-label="Semester trend data table">
          <table className="min-w-full text-xs border border-gray-200 rounded-lg overflow-hidden">
            <caption className="sr-only">Semester average trend — CALCULATED metric</caption>
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-3 py-2 text-left font-semibold text-gray-500">Semester</th>
                <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-500">Average [CALCULATED]</th>
                <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-500">Passed</th>
                <th scope="col" className="px-3 py-2 text-right font-semibold text-gray-500">Failed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map((d, i) => (
                <tr key={i}>
                  <td className="px-3 py-2">{d.label}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{d.average?.toFixed(2) ?? '—'}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-green-700">{d.passed ?? '—'}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-red-700">{d.failed ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
