import React from 'react';
import { TrendingUp, ShieldCheck, Activity, Zap } from 'lucide-react';

interface ExecutiveSummaryProps {
  readinessScore: number;
  runtimeStatus: string;
  securityStatus: string;
  activePoolCount: number;
  latencyMs: number;
}

export function ExecutiveSummary({ readinessScore, runtimeStatus, securityStatus, activePoolCount, latencyMs }: ExecutiveSummaryProps) {
  const metrics = [
    {
      label: 'System Readiness',
      value: `${readinessScore}%`,
      icon: <Activity className="h-4 w-4" />,
      trend: '+2.4%',
      positive: true
    },
    {
      label: 'Security Posture',
      value: securityStatus.toUpperCase(),
      icon: <ShieldCheck className="h-4 w-4" />,
      trend: 'Stable',
      positive: !securityStatus.toLowerCase().includes('error')
    },
    {
      label: 'Active Operations',
      value: activePoolCount.toString(),
      icon: <Zap className="h-4 w-4" />,
      trend: activePoolCount > 0 ? 'Active' : 'Idle',
      positive: activePoolCount > 0
    },
    {
      label: 'Network Latency',
      value: `${latencyMs.toFixed(0)}ms`,
      icon: <TrendingUp className="h-4 w-4" />,
      trend: latencyMs < 100 ? 'Excellent' : latencyMs < 300 ? 'Good' : 'Acceptable',
      positive: latencyMs < 300
    }
  ];

  return (
    <div className="executive-summary-card rounded-xl p-6">
      <div className="mb-4">
        <h3 className="text-sm font-black uppercase tracking-[0.18em] text-slate-900 executive-typography">Executive Summary</h3>
        <p className="mt-1 text-xs text-slate-500">Real-time operational overview and key performance indicators</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric, idx) => (
          <div key={idx} className="kpi-card rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-[0.14em] text-slate-500">{metric.label}</span>
              <div className="rounded-full bg-slate-50 p-1.5" style={{ color: metric.positive ? '#003666' : '#DC2626' }}>
                {metric.icon}
              </div>
            </div>
            <div className="text-lg font-black tracking-tight" style={{ color: metric.positive ? '#003666' : '#DC2626' }}>
              {metric.value}
            </div>
            <div className="mt-1 text-[10px] font-mono" style={{ color: metric.positive ? '#16A34A' : '#DC2626' }}>
              {metric.trend}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
