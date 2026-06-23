/**
 * Pricing Page Component
 * 
 * Transparent tier comparison for QaaS/QIaaS/CIaaS services.
 * No hidden fees, no contact sales, clear compute unit pricing.
 */

import React from 'react';
import { CheckCircle2, Zap, Crown, Rocket } from 'lucide-react';

interface PricingTier {
  name: string;
  description: string;
  price: string;
  computeUnits: string;
  features: string[];
  cta: string;
  popular?: boolean;
  icon: React.ReactNode;
}

export function PricingPage() {
  const tiers: PricingTier[] = [
    {
      name: 'Developer',
      description: 'Get started with quantum intelligence',
      price: '$99',
      computeUnits: '10,000 units/month',
      icon: <Zap className="h-8 w-8" />,
      features: [
        '10,000 compute units/month',
        'QaaS: Up to 10 logical qubits',
        'QIaaS: Predict & explain',
        'Code distance: 3',
        'Community support',
        'Evidence seals included',
        'API access',
        '99.5% uptime SLA',
      ],
      cta: 'Start Free Trial',
    },
    {
      name: 'Production',
      description: 'Scale your quantum workloads',
      price: '$499',
      computeUnits: '100,000 units/month',
      icon: <Rocket className="h-8 w-8" />,
      popular: true,
      features: [
        '100,000 compute units/month',
        'QaaS: Up to 50 logical qubits',
        'QIaaS + CIaaS: Full suite',
        'Quantum Finance: QUBO/QAOA/VaR',
        'Code distance: 5',
        'Dedicated control plane',
        'Email support (4h SLA)',
        '99.9% uptime SLA',
        'Usage analytics dashboard',
      ],
      cta: 'Start Production Trial',
    },
    {
      name: 'Sovereign',
      description: 'Enterprise-grade isolation',
      price: 'Custom',
      computeUnits: 'Unlimited',
      icon: <Crown className="h-8 w-8" />,
      features: [
        'Unlimited compute units',
        'QaaS: Unlimited logical qubits',
        'Sovereign-isolated infrastructure',
        'Custom code distance',
        'Data residency controls',
        'White-glove onboarding',
        '24/7 priority support',
        '99.99% uptime SLA',
        'Custom SLA available',
        'Dedicated account team',
      ],
      cta: 'Contact Sales',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white py-16 px-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-16 text-center">
          <h1 className="mb-4 text-4xl font-black tracking-tight text-slate-950 md:text-5xl">
            Transparent Pricing
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-slate-600">
            Substrate-independent quantum intelligence. Pay for compute units used, nothing hidden.
            Evidence seals included. No trust required.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid gap-8 md:grid-cols-3">
          {tiers.map((tier) => (
            <div
              key={tier.name}
              className={`relative rounded-2xl border ${
                tier.popular
                  ? 'border-blue-600 shadow-2xl shadow-blue-600/20'
                  : 'border-slate-200 shadow-lg'
              } bg-white p-8`}
            >
              {tier.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-blue-600 px-4 py-1 text-sm font-bold text-white">
                  Most Popular
                </div>
              )}

              <div className="mb-6 flex items-center gap-3">
                <div
                  className={`rounded-full p-3 ${
                    tier.popular ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {tier.icon}
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-slate-950">{tier.name}</h3>
                  <p className="text-sm text-slate-600">{tier.description}</p>
                </div>
              </div>

              <div className="mb-6">
                <div className="mb-1 text-4xl font-black text-slate-950">
                  {tier.price}
                  {tier.price !== 'Custom' && <span className="text-lg font-normal text-slate-600">/mo</span>}
                </div>
                <div className="text-sm text-slate-600">{tier.computeUnits}</div>
              </div>

              <button
                className={`mb-6 w-full rounded-lg py-3 text-sm font-medium transition-colors ${
                  tier.popular
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'border border-slate-300 bg-white text-slate-950 hover:bg-slate-50'
                }`}
              >
                {tier.cta}
              </button>

              <div className="space-y-3">
                {tier.features.map((feature) => (
                  <div key={feature} className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-green-600" />
                    <span className="text-sm text-slate-700">{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Compute Unit Explanation */}
        <div className="mt-16 rounded-2xl border border-slate-200 bg-slate-50 p-8">
          <h3 className="mb-4 text-xl font-bold text-slate-950">What's a Compute Unit?</h3>
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <h4 className="mb-2 font-bold text-slate-950">QaaS Operations</h4>
              <ul className="space-y-2 text-sm text-slate-700">
                <li>• Surface code cycle = 1 unit per logical qubit</li>
                <li>• Circuit depth × shots × logical qubits</li>
                <li>• Error correction overhead included</li>
              </ul>
            </div>
            <div>
              <h4 className="mb-2 font-bold text-slate-950">QIaaS/CIaaS Workloads</h4>
              <ul className="space-y-2 text-sm text-slate-700">
                <li>• Prediction = 10 units</li>
                <li>• Explanation = 25 units</li>
                <li>• Optimization = 50 units per iteration</li>
              </ul>
            </div>
          </div>
          <div className="mt-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
            <p className="text-sm text-blue-950">
              <strong>Transparent metering:</strong> Every compute unit is evidence-sealed. Track usage in real-time.
              Export audit logs. No surprise charges.
            </p>
          </div>
        </div>

        {/* FAQ */}
        <div className="mt-16">
          <h3 className="mb-8 text-center text-2xl font-bold text-slate-950">Frequently Asked Questions</h3>
          <div className="space-y-6">
            {[
              {
                q: 'Do I need a quantum computer?',
                a: 'No. HYBA is substrate-independent. Quantum mathematics runs on classical hardware today, with future quantum hardware compatibility.',
              },
              {
                q: 'What happens if I exceed my quota?',
                a: 'You'll receive alerts at 75% and 90% usage. At 100%, requests return HTTP 429 with quota reset time. Upgrade anytime.',
              },
              {
                q: 'Can I verify the results?',
                a: 'Yes. Every API response includes an evidence seal (SHA256 hash) and claim boundary. Audit execution independently.',
              },
              {
                q: 'What's the difference from IBM Quantum / AWS Braket?',
                a: 'HYBA is hardware-agnostic. No QPU wait times. Available now. Evidence-sealed execution. Post-quantum substrate.',
              },
            ].map((faq, idx) => (
              <div key={idx} className="rounded-lg border border-slate-200 bg-white p-6">
                <h4 className="mb-2 font-bold text-slate-950">{faq.q}</h4>
                <p className="text-sm text-slate-700">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-16 rounded-2xl border border-blue-600 bg-gradient-to-br from-blue-50 to-white p-8 text-center shadow-xl">
          <h3 className="mb-4 text-2xl font-bold text-slate-950">Ready to start?</h3>
          <p className="mb-6 text-slate-700">
            14-day free trial. No credit card required. Cancel anytime.
          </p>
          <button className="rounded-lg bg-blue-600 px-8 py-3 text-sm font-medium text-white hover:bg-blue-700">
            Start Free Trial
          </button>
        </div>
      </div>
    </div>
  );
}
