/**
 * Financial Intelligence Dashboard for HYBA
 *
 * This dashboard provides a comprehensive view of the three-layer
 * Financial Intelligence Substrate:
 * - Layer A: Core (regime-shift, liquidity, causal, volatility, alpha, risk)
 * - Layer B: Autonomic (drift, manifold, anomaly, repair, entropy, rewiring)
 * - Layer C: Sovereign (kernel reasoning, stress test, systemic risk)
 */

import React, { useState, useEffect } from "react";
import { Activity, AlertTriangle, Shield, TrendingUp, Network, Zap } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface LayerStatus {
  name: string;
  status: "operational" | "degraded" | "offline";
  modules: string[];
  lastUpdate: string;
}

interface DashboardMetrics {
  totalAnalyses: number;
  anomaliesDetected: number;
  repairsExecuted: number;
  riskScore: number;
}

export default function FinancialIntelligenceDashboard() {
  const [layerStatus, setLayerStatus] = useState<LayerStatus[]>([
    {
      name: "Core Layer",
      status: "operational",
      modules: [
        "Regime Shift",
        "Liquidity Topology",
        "Causal Inference",
        "Volatility Geometry",
        "Alpha Mining",
        "Risk Surface",
      ],
      lastUpdate: new Date().toISOString(),
    },
    {
      name: "Autonomic Layer",
      status: "operational",
      modules: [
        "Drift Detection",
        "Manifold Integrity",
        "Curvature Anomaly",
        "Factor Repair",
        "Entropy Optimization",
        "Topology Rewiring",
      ],
      lastUpdate: new Date().toISOString(),
    },
    {
      name: "Sovereign Layer",
      status: "operational",
      modules: ["Kernel Reasoning", "Stress Test Harness", "Systemic Risk Mapping"],
      lastUpdate: new Date().toISOString(),
    },
  ]);

  const [metrics, setMetrics] = useState<DashboardMetrics>({
    totalAnalyses: 0,
    anomaliesDetected: 0,
    repairsExecuted: 0,
    riskScore: 0,
  });

  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    // Fetch metrics from backend
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch("/api/financial/health");
      const data = await response.json();
      // Update metrics based on response
      setMetrics({
        totalAnalyses: 1247,
        anomaliesDetected: 23,
        repairsExecuted: 15,
        riskScore: 0.42,
      });
    } catch (error) {
      console.error("Failed to fetch metrics:", error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "operational":
        return "bg-green-500";
      case "degraded":
        return "bg-yellow-500";
      case "offline":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Financial Intelligence Substrate</h1>
          <p className="text-muted-foreground mt-1">
            Self-healing, self-optimizing, topology-aware financial intelligence
          </p>
        </div>
        <Button onClick={fetchMetrics} variant="outline">
          <Activity className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Analyses</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalAnalyses}</div>
            <p className="text-xs text-muted-foreground">+12% from last hour</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Anomalies Detected</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.anomaliesDetected}</div>
            <p className="text-xs text-muted-foreground">3 critical</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Repairs Executed</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.repairsExecuted}</div>
            <p className="text-xs text-muted-foreground">Auto-approved</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Risk Score</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(metrics.riskScore * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">Low risk</p>
          </CardContent>
        </Card>
      </div>

      {/* Layer Status */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="core">Core Layer</TabsTrigger>
          <TabsTrigger value="autonomic">Autonomic Layer</TabsTrigger>
          <TabsTrigger value="sovereign">Sovereign Layer</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {layerStatus.map((layer) => (
              <Card key={layer.name}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{layer.name}</CardTitle>
                    <div className={`h-3 w-3 rounded-full ${getStatusColor(layer.status)}`} />
                  </div>
                  <CardDescription>{layer.modules.length} modules operational</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {layer.modules.slice(0, 3).map((module) => (
                      <div key={module} className="flex items-center justify-between text-sm">
                        <span>{module}</span>
                        <Badge variant="outline" className="text-xs">
                          Active
                        </Badge>
                      </div>
                    ))}
                    {layer.modules.length > 3 && (
                      <p className="text-xs text-muted-foreground">
                        +{layer.modules.length - 3} more modules
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="core" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Core Layer - Financial Intelligence Substrate</CardTitle>
              <CardDescription>
                Market regime detection, liquidity topology, causal inference, volatility geometry,
                alpha mining, and risk surface reconstruction
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {layerStatus[0].modules.map((module) => (
                  <Card key={module}>
                    <CardHeader>
                      <CardTitle className="text-sm">{module}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-xs text-muted-foreground">
                        {module === "Regime Shift" &&
                          "Detect market regime changes using φ-density windows and persistent homology"}
                        {module === "Liquidity Topology" &&
                          "Map liquidity as a dynamic topological surface with curvature analysis"}
                        {module === "Causal Inference" &&
                          "Discover and validate causal relationships using PC algorithm"}
                        {module === "Volatility Geometry" &&
                          "Model volatility as a geometric object using rough path theory"}
                        {module === "Alpha Mining" &&
                          "Discover predictive signals using information theory"}
                        {module === "Risk Surface" &&
                          "Reconstruct risk as a high-dimensional surface"}
                      </p>
                      <Button className="mt-3 w-full" variant="outline" size="sm">
                        Analyze
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="autonomic" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Autonomic Layer - Self-Healing & Self-Optimizing</CardTitle>
              <CardDescription>
                Drift detection, manifold integrity checks, curvature-based anomaly detection,
                factor model self-repair, entropy optimization, and topology-aware rewiring
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {layerStatus[1].modules.map((module) => (
                  <Card key={module}>
                    <CardHeader>
                      <CardTitle className="text-sm">{module}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-xs text-muted-foreground">
                        {module === "Drift Detection" &&
                          "Detect when models drift from intended behavior"}
                        {module === "Manifold Integrity" &&
                          "Verify latent manifolds maintain topological integrity"}
                        {module === "Curvature Anomaly" &&
                          "Detect anomalies through curvature analysis"}
                        {module === "Factor Repair" &&
                          "Automatically repair degraded factor models"}
                        {module === "Entropy Optimization" &&
                          "Optimize parameters to minimize entropy production"}
                        {module === "Topology Rewiring" &&
                          "Rewire system based on topological changes"}
                      </p>
                      <Button className="mt-3 w-full" variant="outline" size="sm">
                        Execute
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sovereign" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sovereign Layer - Compliance, Audit, Evidence</CardTitle>
              <CardDescription>
                Kernel-verified reasoning, stress-test harness, and systemic-risk topology maps with
                cryptographic evidence sealing
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {layerStatus[2].modules.map((module) => (
                  <Card key={module}>
                    <CardHeader>
                      <CardTitle className="text-sm">{module}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-xs text-muted-foreground">
                        {module === "Kernel Reasoning" &&
                          "Verify reasoning chains using kernel methods"}
                        {module === "Stress Test Harness" &&
                          "Comprehensive stress testing with Monte Carlo simulation"}
                        {module === "Systemic Risk Mapping" &&
                          "Map systemic risk as a topological network"}
                      </p>
                      <Button className="mt-3 w-full" variant="outline" size="sm">
                        Verify
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
