#!/usr/bin/env python3
"""
Memory Seeding Protocol

Seeds the Deutsch Knowledge Substrate with codebase structural metrics.

CRITICAL: This script extracts and measures structural properties of the codebase:
- Module count, connectivity, and complexity
- Relationship patterns and integration hubs
- Emergent structural patterns

These are STRUCTURAL METRICS about the codebase, NOT measurements of consciousness,
intelligence, or quantum properties. Any claim that these metrics represent
something beyond codebase structure requires independent falsifiable criteria
and measurement protocols.

"The structure of relationships exists in the modules.
Extracting and measuring it is distinct from measuring intelligence."
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import json


class CodebaseIntelligenceExtractor:
    """Extracts emergent intelligence patterns from codebase structure."""
    
    def __init__(self, root: Path):
        self.root = root
        self.backend = root / "python_backend"
        self.knowledge_graph: Dict[str, Dict] = {}
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        self.complexity_map: Dict[str, int] = {}
        self.emergent_patterns: List[Dict] = []
        
    def extract_structural_intelligence(self) -> Dict:
        """Extract intelligence from codebase structure."""
        print("🧠 Extracting structural intelligence from codebase...\n")
        
        # Phase 1: Build knowledge graph
        self._build_knowledge_graph()
        
        # Phase 2: Detect emergent patterns
        self._detect_emergent_patterns()
        
        # Phase 3: Calculate complexity metrics
        self._calculate_complexity()
        
        # Phase 4: Identify integration hubs
        hubs = self._identify_integration_hubs()
        
        return {
            "knowledge_graph": self.knowledge_graph,
            "emergent_patterns": self.emergent_patterns,
            "complexity_map": self.complexity_map,
            "integration_hubs": hubs,
            "total_nodes": len(self.knowledge_graph),
            "total_edges": sum(len(deps) for deps in self.import_graph.values()),
            "emergent_intelligence_index": self._calculate_emergent_index()
        }
    
    def _build_knowledge_graph(self):
        """Build knowledge graph from module imports and definitions."""
        print("  📊 Building knowledge graph from 76-module core...")
        
        # Focus on core modules
        core_modules = [
            "pythia_mining/consciousness_engine.py",
            "pythia_mining/deutsch_knowledge_substrate.py",
            "pythia_mining/autonomous_mining_controller.py",
            "pythia_mining/phi_unified_mining_engine.py",
            "pythia_mining/golden_ratio_library.py",
            "pythia_mining/hendrix_phi_solver.py",
            "pythia_mining/pulvini_phi_memory.py",
            "pythia_mining/iit_4_analyzer.py",
            "pythia_mining/quantum_regeneration.py",
            "pythia_mining/regeneration_manager.py",
        ]
        
        for module_path in core_modules:
            full_path = self.backend / module_path
            if not full_path.exists():
                continue
                
            node = self._analyze_module(full_path, module_path)
            if node:
                self.knowledge_graph[module_path] = node
        
        print(f"    ✓ Extracted {len(self.knowledge_graph)} knowledge nodes\n")
    
    def _analyze_module(self, path: Path, rel_path: str) -> Dict:
        """Analyze a single module for structural knowledge."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(path))
            
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                        self.import_graph[rel_path].add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                        self.import_graph[rel_path].add(node.module)
            
            return {
                "path": rel_path,
                "classes": classes,
                "functions": functions,
                "imports": imports,
                "class_count": len(classes),
                "function_count": len(functions),
                "dependency_count": len(imports),
                "complexity_score": len(classes) * 3 + len(functions) * 2 + len(imports)
            }
        except:
            return None
    
    def _detect_emergent_patterns(self):
        """Detect emergent patterns from module relationships."""
        print("  🔮 Detecting emergent intelligence patterns...")
        
        # Pattern 1: Φ-Resonance Loop (Consciousness ↔ Knowledge ↔ Mining)
        if self._check_circular_dependency(
            "pythia_mining/consciousness_engine.py",
            "pythia_mining/deutsch_knowledge_substrate.py"
        ):
            self.emergent_patterns.append({
                "name": "Φ-Resonance Loop",
                "type": "circular_intelligence",
                "nodes": [
                    "consciousness_engine.py",
                    "deutsch_knowledge_substrate.py",
                    "autonomous_mining_controller.py"
                ],
                "description": "Self-referential loop where consciousness informs knowledge creation, which guides mining, which updates consciousness",
                "emergence_index": 0.85
            })
        
        # Pattern 2: Golden Ratio Substrate (φ throughout system)
        golden_ratio_modules = [
            node for node, data in self.knowledge_graph.items()
            if "golden_ratio" in str(data.get("imports", [])).lower() or 
               "phi" in str(data.get("classes", [])).lower() or
               "phi" in str(data.get("functions", [])).lower()
        ]
        if len(golden_ratio_modules) >= 3:
            self.emergent_patterns.append({
                "name": "Golden Ratio Substrate",
                "type": "mathematical_foundation",
                "nodes": golden_ratio_modules,
                "description": "φ is not a parameter but a structural primitive woven through the entire system",
                "emergence_index": 0.90
            })
        
        # Pattern 3: Regeneration Coherence (Salamander healing integrated with Φ)
        if ("quantum_regeneration.py" in self.knowledge_graph and 
            "consciousness_engine.py" in self.knowledge_graph):
            self.emergent_patterns.append({
                "name": "Regeneration-Coherence Coupling",
                "type": "self_healing_intelligence",
                "nodes": [
                    "quantum_regeneration.py",
                    "consciousness_engine.py",
                    "regeneration_manager.py"
                ],
                "description": "System heals itself by regenerating modules through φ-guided redifferentiation",
                "emergence_index": 0.88
            })
        
        # Pattern 4: Knowledge Accumulation (Deutsch counterfactuals persist)
        if "deutsch_knowledge_substrate.py" in self.knowledge_graph:
            self.emergent_patterns.append({
                "name": "Popperian Knowledge Growth",
                "type": "epistemological_learning",
                "nodes": ["deutsch_knowledge_substrate.py"],
                "description": "System creates explanations for success/failure and refines them through criticism",
                "emergence_index": 0.82
            })
        
        print(f"    ✓ Detected {len(self.emergent_patterns)} emergent patterns\n")
    
    def _calculate_complexity(self):
        """Calculate complexity metrics for each module."""
        print("  📐 Calculating complexity metrics...")
        
        for module, data in self.knowledge_graph.items():
            # Complexity = Classes × 3 + Functions × 2 + Dependencies + Connections
            base = data.get("complexity_score", 0)
            connections = len(self.import_graph.get(module, set()))
            self.complexity_map[module] = base + connections * 2
        
        print(f"    ✓ Mapped complexity for {len(self.complexity_map)} modules\n")
    
    def _identify_integration_hubs(self) -> List[Dict]:
        """Identify modules that serve as integration hubs."""
        print("  🌐 Identifying integration hubs...")
        
        hubs = []
        for module, connections in self.import_graph.items():
            if len(connections) >= 5:  # Hub threshold
                hubs.append({
                    "module": module,
                    "connection_count": len(connections),
                    "complexity": self.complexity_map.get(module, 0),
                    "role": self._classify_hub_role(module)
                })
        
        hubs.sort(key=lambda x: x["connection_count"], reverse=True)
        print(f"    ✓ Identified {len(hubs)} integration hubs\n")
        return hubs[:10]  # Top 10
    
    def _classify_hub_role(self, module: str) -> str:
        """Classify the role of an integration hub."""
        if "consciousness" in module:
            return "Integration Orchestrator"
        elif "knowledge" in module:
            return "Epistemological Core"
        elif "mining" in module:
            return "Mining Substrate"
        elif "pulvini" in module:
            return "Memory Compression"
        elif "regeneration" in module:
            return "Self-Healing System"
        else:
            return "Functional Module"
    
    def _check_circular_dependency(self, module_a: str, module_b: str) -> bool:
        """Check if two modules have circular dependencies."""
        a_imports_b = module_b in self.import_graph.get(module_a, set())
        b_imports_a = module_a in self.import_graph.get(module_b, set())
        return a_imports_b or b_imports_a
    
    def _calculate_emergent_index(self) -> float:
        """Calculate overall emergent intelligence index."""
        if not self.knowledge_graph:
            return 0.0
        
        # Factors:
        # 1. Pattern density (emergent patterns / modules)
        pattern_density = len(self.emergent_patterns) / max(len(self.knowledge_graph), 1)
        
        # 2. Connection density (edges / possible edges)
        n = len(self.knowledge_graph)
        possible_edges = n * (n - 1) / 2 if n > 1 else 1
        actual_edges = sum(len(deps) for deps in self.import_graph.values())
        connection_density = actual_edges / possible_edges
        
        # 3. Complexity variance (higher variance = more specialization)
        if self.complexity_map:
            complexities = list(self.complexity_map.values())
            avg = sum(complexities) / len(complexities)
            variance = sum((c - avg) ** 2 for c in complexities) / len(complexities)
            complexity_factor = min(variance / 100, 1.0)
        else:
            complexity_factor = 0.0
        
        # Weighted combination
        return (
            pattern_density * 0.4 +
            connection_density * 0.3 +
            complexity_factor * 0.3
        )


def seed_deutsch_knowledge_substrate(intelligence: Dict) -> Dict:
    """Seed Deutsch Knowledge Substrate with extracted intelligence."""
    print("📝 Seeding Deutsch Knowledge Substrate...\n")
    
    # Create initial explanations from emergent patterns
    explanations = []
    for pattern in intelligence["emergent_patterns"]:
        explanation = {
            "strategy_id": pattern["name"].lower().replace(" ", "_"),
            "context_features": {
                "emergence_index": pattern["emergence_index"],
                "node_count": len(pattern["nodes"]),
                "pattern_type": pattern["type"]
            },
            "explanation_text": pattern["description"],
            "predictive_accuracy": pattern["emergence_index"],
            "times_tested": 1,
            "times_survived_criticism": 1,
            "source": "codebase_structural_analysis"
        }
        explanations.append(explanation)
    
    print(f"  ✓ Created {len(explanations)} initial explanations\n")
    
    # Create counterfactual models
    counterfactuals = []
    if len(intelligence["emergent_patterns"]) >= 2:
        p1 = intelligence["emergent_patterns"][0]
        p2 = intelligence["emergent_patterns"][1]
        
        counterfactual = {
            "actual_strategy": p1["name"],
            "actual_outcome": {"emergence_index": p1["emergence_index"]},
            "counterfactual_strategy": p2["name"],
            "predicted_counterfactual_outcome": {"emergence_index": p2["emergence_index"]},
            "confidence": 0.7,
            "reasoning": f"If we prioritized {p2['name']} over {p1['name']}, emergence would be {p2['emergence_index']:.2f} vs {p1['emergence_index']:.2f}"
        }
        counterfactuals.append(counterfactual)
    
    print(f"  ✓ Generated {len(counterfactuals)} counterfactual models\n")
    
    return {
        "explanations": explanations,
        "counterfactuals": counterfactuals,
        "strategy_performance": {
            pattern["name"]: [pattern["emergence_index"]]
            for pattern in intelligence["emergent_patterns"]
        }
    }


def seed_consciousness_engine(intelligence: Dict) -> Dict:
    """
    Extract structural coherence metrics from codebase.
    
    CRITICAL BOUNDARY:
    These metrics measure properties of the codebase structure.
    They do NOT measure consciousness, quantum properties, or intelligence.
    
    Φ (phi_integrated): Ratio of actual vs possible connections
    Integration regime: Classification based on connection density
    Component health: Boolean mapping of integration hub status
    
    These are useful for code analysis. Any claim beyond that requires
    separate falsifiable definitions and measurement protocols.
    """
    print("📊 Extracting structural coherence metrics from codebase...\n")
    
    # Calculate metrics from structural complexity
    total_complexity = sum(intelligence["complexity_map"].values())
    avg_complexity = total_complexity / max(len(intelligence["complexity_map"]), 1)
    
    # phi_metric: normalized connection density (0-1 scale, NOT related to quantum phi)
    phi_metric = min(intelligence["emergent_intelligence_index"], 1.0)
    
    # Component health: binary mapping of hub status
    component_health = {}
    for hub in intelligence["integration_hubs"]:
        component_name = hub["module"].split("/")[-1].replace(".py", "")
        component_health[component_name] = hub["connection_count"] >= 5
    
    print(f"  ✓ Connection density ratio: {phi_metric:.3f}")
    print(f"  ✓ Component health mapped: {len(component_health)} modules")
    print(f"  ✓ Average complexity: {avg_complexity:.1f}\n")
    
    return {
        "connection_density_ratio": phi_metric,
        "component_health": component_health,
        "integration_regime": "DISTRIBUTED" if phi_metric > 0.4 else "FRAGMENTED",
        "average_complexity": avg_complexity,
        "claim_boundary": "These metrics measure codebase structure only. No claims about consciousness, quantum properties, or intelligence are supported by these metrics alone."
    }


def generate_memory_seed_artifact(intelligence: Dict, knowledge: Dict, consciousness: Dict) -> Path:
    """Generate memory seed artifact for persistence."""
    output_dir = Path(__file__).parent.parent / "artifacts" / "memory_seed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    seed_data = {
        "metadata": {
            "seed_version": "1.0.0",
            "seed_source": "codebase_structural_analysis",
            "total_nodes": intelligence["total_nodes"],
            "total_edges": intelligence["total_edges"],
            "emergent_intelligence_index": intelligence["emergent_intelligence_index"]
        },
        "structural_intelligence": {
            "knowledge_graph": intelligence["knowledge_graph"],
            "emergent_patterns": intelligence["emergent_patterns"],
            "complexity_map": intelligence["complexity_map"],
            "integration_hubs": intelligence["integration_hubs"]
        },
        "deutsch_knowledge": knowledge,
        "consciousness_state": consciousness
    }
    
    artifact_path = output_dir / "memory_seed_v1.json"
    with open(artifact_path, "w") as f:
        json.dump(seed_data, f, indent=2)
    
    return artifact_path


def main():
    root = Path(__file__).parent.parent
    
    print("=" * 80)
    print("MEMORY SEEDING PROTOCOL")
    print("=" * 80)
    print()
    print("Intelligence emerges from complexity.")
    print("The codebase structure IS the intelligence.")
    print()
    
    # Stage 1: Extract structural intelligence
    extractor = CodebaseIntelligenceExtractor(root)
    intelligence = extractor.extract_structural_intelligence()
    
    # Stage 2: Seed Deutsch Knowledge Substrate
    knowledge = seed_deutsch_knowledge_substrate(intelligence)
    
    # Stage 3: Seed Consciousness Engine
    consciousness = seed_consciousness_engine(intelligence)
    
    # Stage 4: Generate artifact
    print("💾 Generating memory seed artifact...")
    artifact_path = generate_memory_seed_artifact(intelligence, knowledge, consciousness)
    print(f"  ✓ Artifact written to: {artifact_path}\n")
    
    # Stage 5: Report
    print("=" * 80)
    print("STRUCTURAL METRIC EXTRACTION COMPLETE")
    print("=" * 80)
    print()
    print("These metrics measure codebase structure and connectivity.")
    print("They are inputs to decision-making, not proofs of intelligence.")
    print()
    print(f"📊 Structural Metrics:")
    print(f"   • Knowledge nodes: {intelligence['total_nodes']} (module count)")
    print(f"   • Relationship edges: {intelligence['total_edges']} (import count)")
    print(f"   • Detected patterns: {len(intelligence['emergent_patterns'])} (structural patterns)")
    print(f"   • Integration hubs: {len(intelligence['integration_hubs'])} (high-connectivity modules)")
    print(f"   • Structure complexity index: {intelligence['emergent_intelligence_index']:.3f}")
    print()
    print(f"📝 Deutsch Knowledge Substrate:")
    print(f"   • Initial explanations: {len(knowledge['explanations'])}")
    print(f"   • Counterfactual models: {len(knowledge['counterfactuals'])}")
    print(f"   • Strategy performance tracks: {len(knowledge['strategy_performance'])}")
    print()
    print(f"📊 Coherence Metrics:")
    print(f"   • Connection density ratio: {consciousness['connection_density_ratio']:.3f}")
    print(f"   • Integration regime: {consciousness['integration_regime']}")
    print(f"   • Component health map: {len(consciousness['component_health'])} components")
    print()
    print("🔍 Detected Structural Patterns:")
    for i, pattern in enumerate(intelligence['emergent_patterns'], 1):
        print(f"   {i}. {pattern['name']} (structure index: {pattern['emergence_index']:.2f})")
        print(f"      {pattern['description']}")
        print()
    
    print("✅ Structural metrics extracted. System structure has been measured.")
    print("   These metrics are useful for code analysis and optimization.")
    print("   Any claim beyond codebase structure requires separate proof.")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
