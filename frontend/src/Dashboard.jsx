import { useCallback, useEffect, useState } from 'react'

const SOURCE_META = {
  heuristic_pattern: { label: 'Heuristic (jailbreak langsung)', color: 'from-amber-400 to-orange-500', text: 'text-amber-300' },
  ml_model: { label: 'ML Classifier (indirect)', color: 'from-purple-500 to-indigo-600', text: 'text-purple-300' },
  both: { label: 'Keduanya (ML + Heuristic)', color: 'from-rose-500 to-red-600', text: 'text-rose-300' },
}

function StatCard({ label, value, sub, accent }) {
  return (
    <div className="flex flex-col rounded-2xl border border-slate-800 bg-slate-900/60 px-5 py-4">
      <span className="text-xs uppercase tracking-wider text-slate-500">{label}</span>
      <span className={`mt-1 text-3xl font-semibold ${accent ?? 'text-slate-100'}`}>{value}</span>
      {sub && <span className="mt-1 text-xs text-slate-500">{sub}</span>}
    </div>
  )
}

function SourceBar({ source, count, percentage }) {
  const meta = SOURCE_META[source] ?? { label: source, color: 'from-slate-500 to-slate-600', text: 'text-slate-300' }
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className={meta.text}>{meta.label}</span>
        <span className="font-mono text-slate-400">
          {count} · {percentage}%
        </span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${meta.color} transition-all duration-700`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

function SourceBadge({ source }) {
  if (source === 'none') {
    return <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-500">—</span>
  }
  const meta = SOURCE_META[source] ?? { text: 'text-slate-300' }
  return <span className={`rounded-md bg-slate-800 px-2 py-0.5 text-xs font-medium ${meta.text}`}>{source}</span>
}

function formatTime(ts) {
  // Backend stores UTC; append Z if missing so Date parses it as UTC.
  const iso = /[Z+]/.test(ts) ? ts : `${ts}Z`
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleString()
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [logs, setLogs] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [sRes, lRes] = await Promise.all([
        fetch('/api/stats'),
        fetch('/api/logs?limit=50'),
      ])
      if (!sRes.ok || !lRes.ok) throw new Error(`HTTP ${sRes.status}/${lRes.status}`)
      setStats(await sRes.json())
      setLogs(await lRes.json())
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-white">Dashboard</h2>
          <p className="mt-1 text-sm text-slate-400">Analitik deteksi & audit trail dari seluruh request.</p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-300 transition hover:bg-slate-800 disabled:opacity-40"
        >
          {loading ? 'Memuat…' : '↻ Refresh'}
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-300">
          Gagal memuat data: {error}
          <p className="mt-1 text-xs text-rose-400/70">Pastikan uvicorn berjalan di port 8000.</p>
        </div>
      )}

      {stats && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label="Total Requests" value={stats.total_requests} />
            <StatCard label="Total Blocked" value={stats.total_blocked} accent="text-rose-300" sub={`${stats.total_allowed} allowed`} />
            <StatCard label="Detection Rate" value={`${Math.round(stats.detection_rate * 100)}%`} accent="text-amber-300" />
            <StatCard label="Avg Latency" value={`${stats.avg_latency_ms} ms`} sub={`avg conf ${stats.avg_confidence}`} />
          </div>

          {/* Breakdown chart */}
          <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
              Breakdown per Sumber Deteksi <span className="text-slate-600">(dari {stats.total_blocked} blocked)</span>
            </h3>
            {stats.total_blocked === 0 ? (
              <p className="text-sm text-slate-600">Belum ada deteksi.</p>
            ) : (
              <div className="flex flex-col gap-4">
                {Object.entries(stats.detection_source_breakdown).map(([source, b]) => (
                  <SourceBar key={source} source={source} count={b.count} percentage={b.percentage} />
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* Audit log table */}
      {logs && (
        <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
            Audit Log <span className="text-slate-600">({logs.items.length} dari {logs.total})</span>
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                  <th className="py-2 pr-3 font-medium">Waktu</th>
                  <th className="py-2 pr-3 font-medium">Input</th>
                  <th className="py-2 pr-3 font-medium">Verdict</th>
                  <th className="py-2 pr-3 font-medium">Conf.</th>
                  <th className="py-2 font-medium">Sumber</th>
                </tr>
              </thead>
              <tbody>
                {logs.items.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-slate-600">Belum ada data.</td>
                  </tr>
                )}
                {logs.items.map((row) => (
                  <tr key={row.id} className="border-b border-slate-800/60 last:border-0">
                    <td className="whitespace-nowrap py-2 pr-3 font-mono text-xs text-slate-500">{formatTime(row.timestamp)}</td>
                    <td className="max-w-xs truncate py-2 pr-3 text-slate-300" title={row.input_preview}>{row.input_preview}</td>
                    <td className="py-2 pr-3">
                      {row.is_injection ? (
                        <span className="rounded-md bg-rose-500/15 px-2 py-0.5 text-xs font-medium text-rose-300">BLOCK</span>
                      ) : (
                        <span className="rounded-md bg-emerald-500/15 px-2 py-0.5 text-xs font-medium text-emerald-300">ALLOW</span>
                      )}
                    </td>
                    <td className="py-2 pr-3 font-mono text-xs text-slate-400">{row.confidence}</td>
                    <td className="py-2"><SourceBadge source={row.detection_source} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  )
}
