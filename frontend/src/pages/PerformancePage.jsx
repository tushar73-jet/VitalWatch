import { useState, useEffect, useCallback } from 'react';
import { getModelMetrics } from '../lib/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area
} from 'recharts';
import { motion } from 'framer-motion';

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-950 border border-gray-700 rounded px-3 py-2 text-xs font-mono">
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || p.stroke }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toFixed(3) : p.value}
        </div>
      ))}
    </div>
  );
};

function SkeletonBlock({ h = 'h-64' }) {
  return (
    <div className={`${h} bg-gray-900 rounded-lg animate-pulse`} />
  );
}

export default function PerformancePage() {
  const [metricsData, setMetricsData]     = useState(null);
  const [loading, setLoading]             = useState(true);
  const [error, setError]                 = useState(null);
  const [threshold, setThreshold]         = useState(0.5);
  const [animateFeatures, setAnimateFeatures] = useState(false);

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getModelMetrics();
      setMetricsData(data);
      setTimeout(() => setAnimateFeatures(true), 400);
    } catch (e) {
      setError('Could not load model metrics. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchMetrics(); }, [fetchMetrics]);

  // Find sensitivity row nearest to current threshold
  const sensRow = metricsData?.sensitivity?.reduce((best, row) =>
    Math.abs(row.threshold - threshold) < Math.abs(best.threshold - threshold) ? row : best,
    metricsData?.sensitivity?.[0] ?? {}
  ) ?? {};

  // Derive live confusion matrix counts from sensitivity row + dataset totals
  const totalRows = metricsData?.total_rows ?? 0;
  const iohRate   = metricsData?.ioh_rate   ?? 0;
  const P  = Math.round(totalRows * iohRate);
  const N  = totalRows - P;
  const TP = Math.round(P * (sensRow.recall    ?? 0));
  const FN = P - TP;
  const FP = sensRow.precision > 0
    ? Math.round(TP * (1 - sensRow.precision) / sensRow.precision)
    : 0;
  const TN = N - FP;

  const maxImp = metricsData?.feature_importance
    ? Math.max(...metricsData.feature_importance.map(f => f.importance))
    : 1;

  return (
    <div className="min-h-screen bg-black pt-16">
      {/* Header */}
      <div className="border-b border-gray-900 px-8 py-10">
        <div className="text-xs text-cyan-400 tracking-widest uppercase mb-2">Model Evaluation</div>
        <h1 className="text-3xl font-bold text-white font-mono">Performance Laboratory</h1>
        <p className="text-gray-500 text-sm mt-1">
          Logistic Regression trained on 6,388 surgical patients · VitalDB dataset
          {metricsData && (
            <span className="ml-3 text-cyan-400/60">
              · {metricsData.total_rows.toLocaleString()} test rows · IOH rate {(metricsData.ioh_rate * 100).toFixed(1)}%
            </span>
          )}
        </p>
      </div>

      {/* Error state */}
      {error && (
        <div className="mx-8 mt-8 bg-red-950/40 border border-red-800/50 rounded-lg p-6 flex items-center justify-between">
          <div>
            <div className="text-red-400 font-mono text-sm font-bold mb-1">⚠ Failed to load metrics</div>
            <div className="text-gray-500 text-xs">{error}</div>
          </div>
          <button
            onClick={fetchMetrics}
            className="text-xs border border-gray-700 text-gray-300 px-4 py-2 rounded hover:border-cyan-400 hover:text-cyan-400 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Hero metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-gray-900 border-b border-gray-900">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-black px-8 py-8">
              <div className="h-10 w-20 bg-gray-800 rounded animate-pulse mb-2" />
              <div className="h-3 w-16 bg-gray-900 rounded animate-pulse" />
            </div>
          ))
        ) : metricsData ? (
          [
            { label: 'AUC-ROC',   val: metricsData.auc_roc.toFixed(4),          highlight: true },
            { label: 'F1 Score',  val: (sensRow.f1 ?? 0).toFixed(3),            highlight: false },
            { label: 'Precision', val: (sensRow.precision ?? 0).toFixed(3),     highlight: false },
            { label: 'Recall',    val: (sensRow.recall ?? 0).toFixed(3),        highlight: false },
          ].map(({ label, val, highlight }) => (
            <motion.div
              key={label}
              className="bg-black px-8 py-8"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className={`text-4xl font-mono font-bold ${highlight ? 'text-cyan-400' : 'text-white'}`}>
                {val}
              </div>
              <div className="text-gray-500 text-xs uppercase tracking-widest mt-2">{label}</div>
            </motion.div>
          ))
        ) : null}
      </div>

      <div className="px-8 py-8 space-y-6">

        {/* ROC + Confusion Matrix */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* ROC Curve */}
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-xs text-cyan-400 tracking-widest uppercase mb-1">ROC Curve</div>
            {loading ? <SkeletonBlock /> : metricsData ? (
              <>
                <div className="text-gray-500 text-xs mb-4">
                  AUC = {metricsData.auc_roc.toFixed(4)} · computed from {metricsData.total_rows.toLocaleString()} test rows
                </div>
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={metricsData.roc_curve} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                    <defs>
                      <linearGradient id="rocGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#00E5FF" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#00E5FF" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#111" />
                    <XAxis dataKey="fpr" stroke="#444" tick={{ fill: '#555', fontSize: 10 }}
                      label={{ value: 'FPR %', position: 'insideBottom', fill: '#555', fontSize: 10, dy: 10 }} />
                    <YAxis stroke="#444" tick={{ fill: '#555', fontSize: 10 }}
                      label={{ value: 'TPR %', angle: -90, position: 'insideLeft', fill: '#555', fontSize: 10 }} />
                    <Tooltip content={<CustomTooltip />} />
                    {/* Random-classifier baseline */}
                    <Line type="linear"
                      data={[{ fpr: 0, tpr: 0 }, { fpr: 100, tpr: 100 }]}
                      dataKey="tpr" stroke="#333" strokeDasharray="4 4" dot={false} strokeWidth={1} />
                    <Area type="monotone" dataKey="tpr" stroke="#00E5FF" strokeWidth={2}
                      fill="url(#rocGrad)" dot={false} name="TPR" />
                  </AreaChart>
                </ResponsiveContainer>
              </>
            ) : null}
          </div>

          {/* Confusion Matrix */}
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-xs text-cyan-400 tracking-widest uppercase mb-1">Confusion Matrix</div>
            {loading ? <SkeletonBlock /> : metricsData ? (
              <>
                <div className="text-gray-500 text-xs mb-6">
                  At threshold = {threshold.toFixed(2)} · live from test dataset
                </div>
                <div className="flex flex-col items-center gap-2 mt-4">
                  <div className="grid grid-cols-3 w-full max-w-xs gap-1">
                    <div />
                    <div className="text-center text-xs text-gray-500 pb-1">Pred: No IOH</div>
                    <div className="text-center text-xs text-gray-500 pb-1">Pred: IOH</div>
                  </div>
                  <div className="grid grid-cols-3 w-full max-w-xs gap-1">
                    <div className="flex items-center text-xs text-gray-500 pr-2">True: No IOH</div>
                    <div className="bg-cyan-400/10 border border-cyan-400/30 rounded p-4 text-center">
                      <div className="text-2xl font-mono text-cyan-400 font-bold">{TN.toLocaleString()}</div>
                      <div className="text-xs text-gray-500 mt-1">TN</div>
                    </div>
                    <div className="bg-red-400/5 border border-red-400/20 rounded p-4 text-center">
                      <div className="text-2xl font-mono text-red-400 font-bold">{FP.toLocaleString()}</div>
                      <div className="text-xs text-gray-500 mt-1">FP</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 w-full max-w-xs gap-1">
                    <div className="flex items-center text-xs text-gray-500 pr-2">True: IOH</div>
                    <div className="bg-red-400/5 border border-red-400/20 rounded p-4 text-center">
                      <div className="text-2xl font-mono text-red-400 font-bold">{FN.toLocaleString()}</div>
                      <div className="text-xs text-gray-500 mt-1">FN</div>
                    </div>
                    <div className="bg-cyan-400/20 border border-cyan-400/40 rounded p-4 text-center">
                      <div className="text-2xl font-mono text-cyan-400 font-bold">{TP.toLocaleString()}</div>
                      <div className="text-xs text-gray-500 mt-1">TP</div>
                    </div>
                  </div>
                </div>
              </>
            ) : null}
          </div>
        </div>

        {/* Feature Importance */}
        <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
          <div className="text-xs text-cyan-400 tracking-widest uppercase mb-1">Feature Importance</div>
          <div className="text-gray-500 text-xs mb-6">Top 15 features by absolute model coefficient (normalised)</div>
          {loading ? <SkeletonBlock h="h-80" /> : metricsData ? (
            <div className="space-y-2">
              {metricsData.feature_importance.map((f, i) => (
                <motion.div
                  key={f.name}
                  className="flex items-center gap-3"
                  initial={{ opacity: 0, x: -20 }}
                  animate={animateFeatures ? { opacity: 1, x: 0 } : {}}
                  transition={{ delay: i * 0.04, duration: 0.3 }}
                >
                  <div className="w-44 text-xs font-mono text-gray-400 text-right truncate">{f.name}</div>
                  <div className="flex-1 h-5 bg-gray-900 rounded overflow-hidden">
                    <motion.div
                      className="h-full rounded"
                      style={{ background: `rgba(0,229,255,${0.3 + (f.importance / maxImp) * 0.7})` }}
                      initial={{ width: 0 }}
                      animate={animateFeatures ? { width: `${(f.importance / maxImp) * 100}%` } : {}}
                      transition={{ delay: i * 0.04 + 0.2, duration: 0.5 }}
                    />
                  </div>
                  <div className="w-12 text-xs font-mono text-gray-500 text-right">
                    {(f.importance * 100).toFixed(1)}%
                  </div>
                </motion.div>
              ))}
            </div>
          ) : null}
        </div>

        {/* Threshold Sensitivity */}
        <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
          <div className="text-xs text-cyan-400 tracking-widest uppercase mb-1">Threshold Sensitivity</div>
          <div className="text-gray-500 text-xs mb-6">
            Adjust decision threshold → precision, recall and F1 recomputed from test dataset
          </div>
          {loading ? <SkeletonBlock h="h-72" /> : metricsData ? (
            <div className="flex flex-col md:flex-row gap-8">
              <div className="md:w-1/3">
                <div className="mb-4">
                  <label className="text-gray-400 text-xs uppercase tracking-widest block mb-3">
                    Threshold: <span className="text-cyan-400 font-bold">{threshold.toFixed(2)}</span>
                  </label>
                  <input
                    type="range" min="0.05" max="0.95" step="0.05"
                    value={threshold}
                    onChange={e => setThreshold(parseFloat(e.target.value))}
                    className="w-full accent-cyan-400"
                  />
                  <div className="flex justify-between text-xs text-gray-600 mt-1">
                    <span>0.05</span><span>0.95</span>
                  </div>
                </div>
                <div className="space-y-3 mt-6">
                  {[
                    { label: 'Precision', val: sensRow.precision ?? 0, color: '#00E5FF' },
                    { label: 'Recall',    val: sensRow.recall    ?? 0, color: '#4ade80' },
                    { label: 'F1 Score',  val: sensRow.f1        ?? 0, color: '#f59e0b' },
                  ].map(({ label, val, color }) => (
                    <div key={label} className="bg-gray-900 rounded p-3">
                      <div className="text-xs text-gray-500 mb-1">{label}</div>
                      <div className="text-2xl font-mono font-bold" style={{ color }}>{val.toFixed(3)}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 text-xs text-gray-600 leading-relaxed">
                  Lower threshold → higher recall (catches more IOH events) but more false alarms.
                  Higher threshold → fewer false alarms but may miss events.
                </div>
              </div>
              <div className="md:flex-1">
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={metricsData.sensitivity} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#111" />
                    <XAxis dataKey="threshold" stroke="#444" tick={{ fill: '#555', fontSize: 10 }}
                      label={{ value: 'Threshold', position: 'insideBottom', fill: '#555', fontSize: 10, dy: 10 }} />
                    <YAxis stroke="#444" tick={{ fill: '#555', fontSize: 10 }} domain={[0, 1]} />
                    <Tooltip content={<CustomTooltip />} />
                    <Line type="monotone" dataKey="precision" stroke="#00E5FF" strokeWidth={2} dot={false} name="Precision" />
                    <Line type="monotone" dataKey="recall"    stroke="#4ade80" strokeWidth={2} dot={false} name="Recall" />
                    <Line type="monotone" dataKey="f1"        stroke="#f59e0b" strokeWidth={2} dot={false} name="F1" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : null}
        </div>

      </div>
    </div>
  );
}
