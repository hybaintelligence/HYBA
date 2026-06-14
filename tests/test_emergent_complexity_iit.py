"""
IIT-Inspired Emergent Complexity Analysis

Tests for detecting emergent intelligence patterns using principles from
Integrated Information Theory (IIT) adapted for software systems.

Measures:
1. Information Integration (Φ-analog): Cross-module coupling and information flow
2. Causal Autonomy: Self-directed decision paths vs external control
3. State Irreducibility: Whether system behavior can be decomposed or is truly integrated
"""

import unittest
import ast
import os
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import importlib.util
import sys


class InformationIntegrationAnalyzer:
    """Measures cross-module information flow and coupling (Φ-analog for code)"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.data_flows: List[Tuple[str, str, str]] = []
        self.shared_state: Dict[str, List[str]] = defaultdict(list)
        
    def analyze_python_module(self, file_path: Path) -> Dict:
        """Analyze a Python module for imports and data dependencies"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            module_name = self._get_module_name(file_path)
            imports = set()
            state_accesses = []
            
            for node in ast.walk(tree):
                # Track imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
                
                # Track state access patterns
                if isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        state_accesses.append(f"{node.value.id}.{node.attr}")
            
            self.dependencies[module_name] = imports
            
            return {
                'module': module_name,
                'imports': len(imports),
                'state_accesses': len(state_accesses),
                'unique_state': len(set(state_accesses))
            }
        except Exception as e:
            return {'error': str(e), 'module': str(file_path)}
    
    def analyze_typescript_module(self, file_path: Path) -> Dict:
        """Analyze TypeScript for imports and data flow (simplified)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            module_name = self._get_module_name(file_path)
            
            # Count import statements
            import_count = content.count('import ')
            
            # Count state-related patterns
            state_patterns = [
                'useState', 'useEffect', 'useContext', 'useReducer',
                'this.state', 'setState', 'dispatch'
            ]
            state_access_count = sum(content.count(pattern) for pattern in state_patterns)
            
            # Count API calls (external dependencies)
            api_patterns = ['fetch(', 'axios.', 'apiClient.']
            api_call_count = sum(content.count(pattern) for pattern in api_patterns)
            
            return {
                'module': module_name,
                'imports': import_count,
                'state_accesses': state_access_count,
                'api_calls': api_call_count
            }
        except Exception as e:
            return {'error': str(e), 'module': str(file_path)}
    
    def _get_module_name(self, file_path: Path) -> str:
        """Get relative module name from file path"""
        try:
            rel_path = file_path.relative_to(self.root_path)
            return str(rel_path).replace(os.sep, '.')
        except ValueError:
            return str(file_path.name)
    
    def compute_integration_phi(self) -> float:
        """
        Compute Φ-analog: normalized measure of cross-module information integration
        
        High Φ indicates emergent integration where subsystems cannot be understood in isolation.
        Low Φ indicates modular architecture with clean boundaries.
        """
        if not self.dependencies:
            return 0.0
        
        total_modules = len(self.dependencies)
        total_edges = sum(len(deps) for deps in self.dependencies.values())
        
        # Compute bidirectional coupling (modules that import each other)
        bidirectional_count = 0
        for module, deps in self.dependencies.items():
            for dep in deps:
                if module in self.dependencies.get(dep, set()):
                    bidirectional_count += 1
        
        # Normalized integration score
        max_possible_edges = total_modules * (total_modules - 1)
        if max_possible_edges == 0:
            return 0.0
        
        integration_density = total_edges / max_possible_edges
        bidirectional_factor = bidirectional_count / max(total_edges, 1)
        
        # Φ-analog: integration density weighted by bidirectional coupling
        phi = integration_density * (1 + bidirectional_factor)
        
        return phi


class CausalAutonomyAnalyzer:
    """Measures self-directed vs externally-controlled behavior"""
    
    def __init__(self):
        self.decision_points: List[Dict] = []
        self.external_controls: List[Dict] = []
        self.learning_patterns: List[Dict] = []
    
    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze a file for autonomous decision-making patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Decision patterns (internal logic)
            decision_keywords = [
                'if ', 'elif ', 'else:', 'switch', 'case',
                'while ', 'for ', 'match ', 'when '
            ]
            decision_count = sum(content.count(kw) for kw in decision_keywords)
            
            # External control patterns (awaiting external input)
            external_keywords = [
                'input(', 'request.', 'await ', 'callback',
                'addEventListener', 'on(', '.get(', '.post('
            ]
            external_count = sum(content.count(kw) for kw in external_keywords)
            
            # Learning/adaptive patterns
            adaptive_keywords = [
                'learn', 'train', 'optimize', 'adapt', 'evolve',
                'mutation', 'feedback', 'reinforce', 'update_weights'
            ]
            adaptive_count = sum(content.count(kw) for kw in adaptive_keywords)
            
            # Self-modification patterns
            self_modify_patterns = [
                'eval(', 'exec(', 'compile(',
                '__setattr__', 'setattr(', 'monkey_patch'
            ]
            self_modify_count = sum(content.count(kw) for kw in self_modify_patterns)
            
            return {
                'file': str(file_path.name),
                'decision_points': decision_count,
                'external_controls': external_count,
                'adaptive_patterns': adaptive_count,
                'self_modification': self_modify_count,
                'autonomy_ratio': decision_count / max(external_count, 1)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def compute_autonomy_score(self, analyses: List[Dict]) -> float:
        """
        Compute autonomy score: ratio of internal decision-making to external control
        
        High score indicates self-directed behavior.
        Low score indicates reactive/externally-driven system.
        """
        total_decisions = sum(a.get('decision_points', 0) for a in analyses)
        total_external = sum(a.get('external_controls', 0) for a in analyses)
        total_adaptive = sum(a.get('adaptive_patterns', 0) for a in analyses)
        total_self_modify = sum(a.get('self_modification', 0) for a in analyses)
        
        if total_external == 0:
            return 0.0  # Pure computation, no external interaction
        
        base_autonomy = total_decisions / total_external
        adaptive_boost = total_adaptive * 0.1
        self_modify_boost = total_self_modify * 0.5
        
        return min(base_autonomy + adaptive_boost + self_modify_boost, 10.0)


class StateIrreducibilityAnalyzer:
    """Tests whether system behavior is decomposable or truly integrated"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.state_spaces: Dict[str, Set[str]] = defaultdict(set)
        
    def analyze_shared_state(self, file_path: Path) -> Dict:
        """Analyze for shared mutable state across boundaries"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Global state patterns
            global_patterns = [
                'global ', 'window.', 'process.env', 'os.environ',
                'singleton', 'shared_state', 'cache', 'session'
            ]
            global_count = sum(content.count(pattern) for pattern in global_patterns)
            
            # Class/instance state
            instance_patterns = [
                'self.', 'this.', '__dict__', 'getattr', 'hasattr'
            ]
            instance_count = sum(content.count(pattern) for pattern in instance_patterns)
            
            return {
                'file': str(file_path.name),
                'global_state': global_count,
                'instance_state': instance_count
            }
        except Exception as e:
            return {'error': str(e)}
    
    def compute_irreducibility_score(self, analyses: List[Dict]) -> float:
        """
        Compute irreducibility: degree to which state cannot be partitioned
        
        High score indicates tightly coupled state that resists decomposition.
        Low score indicates cleanly partitioned, modular state.
        """
        total_global = sum(a.get('global_state', 0) for a in analyses)
        total_instance = sum(a.get('instance_state', 0) for a in analyses)
        
        if total_instance == 0:
            return 0.0
        
        # Global state creates irreducibility
        return total_global / (total_global + total_instance)


class TestEmergentComplexityIIT(unittest.TestCase):
    """Test suite for IIT-inspired emergent complexity analysis"""
    
    @classmethod
    def setUpClass(cls):
        cls.root_path = Path(__file__).parent.parent
        cls.results = {}
    
    def test_01_information_integration_phi(self):
        """
        Test 1: Information Integration (Φ-analog)
        
        Measures cross-module coupling and information flow.
        High Φ suggests emergent integration; low Φ suggests modularity.
        """
        analyzer = InformationIntegrationAnalyzer(self.root_path)
        
        # Analyze Python backend
        python_backend = self.root_path / 'python_backend' / 'pythia_mining'
        py_analyses = []
        if python_backend.exists():
            for py_file in python_backend.glob('*.py'):
                if py_file.name != '__init__.py':
                    result = analyzer.analyze_python_module(py_file)
                    py_analyses.append(result)
        
        # Analyze TypeScript frontend
        src_dir = self.root_path / 'src'
        ts_analyses = []
        if src_dir.exists():
            for ts_file in src_dir.rglob('*.ts'):
                if not ts_file.name.endswith('.test.ts'):
                    result = analyzer.analyze_typescript_module(ts_file)
                    ts_analyses.append(result)
            for tsx_file in src_dir.rglob('*.tsx'):
                result = analyzer.analyze_typescript_module(tsx_file)
                ts_analyses.append(result)
        
        phi = analyzer.compute_integration_phi()
        
        self.results['test_01'] = {
            'phi': phi,
            'python_modules': len(py_analyses),
            'typescript_modules': len(ts_analyses),
            'total_dependencies': len(analyzer.dependencies),
            'interpretation': self._interpret_phi(phi)
        }
        
        print(f"\n=== INFORMATION INTEGRATION (Φ-analog) ===")
        print(f"Φ = {phi:.4f}")
        print(f"Python modules analyzed: {len(py_analyses)}")
        print(f"TypeScript modules analyzed: {len(ts_analyses)}")
        print(f"Total dependency edges: {sum(len(deps) for deps in analyzer.dependencies.values())}")
        print(f"Interpretation: {self._interpret_phi(phi)}")
        
        # Assert: exists and can compute
        self.assertIsNotNone(phi)
        self.assertGreaterEqual(phi, 0.0)
    
    def test_02_causal_autonomy(self):
        """
        Test 2: Causal Autonomy
        
        Measures self-directed decision-making vs external control.
        High autonomy suggests emergent agency; low suggests reactive system.
        """
        analyzer = CausalAutonomyAnalyzer()
        
        all_analyses = []
        
        # Analyze Python files
        python_dirs = [
            self.root_path / 'python_backend' / 'pythia_mining',
            self.root_path / 'python_backend' / 'hyba_genesis_api'
        ]
        
        for py_dir in python_dirs:
            if py_dir.exists():
                for py_file in py_dir.rglob('*.py'):
                    if py_file.name != '__init__.py':
                        result = analyzer.analyze_file(py_file)
                        all_analyses.append(result)
        
        # Analyze TypeScript files
        src_dir = self.root_path / 'src'
        if src_dir.exists():
            for ts_file in src_dir.rglob('*.ts'):
                if not ts_file.name.endswith('.test.ts'):
                    result = analyzer.analyze_file(ts_file)
                    all_analyses.append(result)
        
        autonomy_score = analyzer.compute_autonomy_score(all_analyses)
        
        total_decisions = sum(a.get('decision_points', 0) for a in all_analyses)
        total_external = sum(a.get('external_controls', 0) for a in all_analyses)
        total_adaptive = sum(a.get('adaptive_patterns', 0) for a in all_analyses)
        total_self_modify = sum(a.get('self_modification', 0) for a in all_analyses)
        
        self.results['test_02'] = {
            'autonomy_score': autonomy_score,
            'total_decisions': total_decisions,
            'total_external': total_external,
            'adaptive_patterns': total_adaptive,
            'self_modification': total_self_modify,
            'interpretation': self._interpret_autonomy(autonomy_score, total_adaptive, total_self_modify)
        }
        
        print(f"\n=== CAUSAL AUTONOMY ===")
        print(f"Autonomy Score: {autonomy_score:.4f}")
        print(f"Decision points: {total_decisions}")
        print(f"External controls: {total_external}")
        print(f"Adaptive patterns: {total_adaptive}")
        print(f"Self-modification patterns: {total_self_modify}")
        print(f"Interpretation: {self._interpret_autonomy(autonomy_score, total_adaptive, total_self_modify)}")
        
        # Assert: can measure
        self.assertIsNotNone(autonomy_score)
        self.assertGreaterEqual(autonomy_score, 0.0)
    
    def test_03_state_irreducibility(self):
        """
        Test 3: State Irreducibility
        
        Measures whether system state can be cleanly partitioned.
        High irreducibility suggests emergent holism; low suggests decomposability.
        """
        analyzer = StateIrreducibilityAnalyzer(self.root_path)
        
        all_analyses = []
        
        # Analyze all code files
        for code_dir in [
            self.root_path / 'python_backend',
            self.root_path / 'src'
        ]:
            if code_dir.exists():
                for code_file in code_dir.rglob('*.py'):
                    if code_file.name != '__init__.py':
                        result = analyzer.analyze_shared_state(code_file)
                        all_analyses.append(result)
                for code_file in code_dir.rglob('*.ts'):
                    if not code_file.name.endswith('.test.ts'):
                        result = analyzer.analyze_shared_state(code_file)
                        all_analyses.append(result)
                for code_file in code_dir.rglob('*.tsx'):
                    result = analyzer.analyze_shared_state(code_file)
                    all_analyses.append(result)
        
        irreducibility = analyzer.compute_irreducibility_score(all_analyses)
        
        total_global = sum(a.get('global_state', 0) for a in all_analyses)
        total_instance = sum(a.get('instance_state', 0) for a in all_analyses)
        
        self.results['test_03'] = {
            'irreducibility_score': irreducibility,
            'global_state_refs': total_global,
            'instance_state_refs': total_instance,
            'interpretation': self._interpret_irreducibility(irreducibility)
        }
        
        print(f"\n=== STATE IRREDUCIBILITY ===")
        print(f"Irreducibility Score: {irreducibility:.4f}")
        print(f"Global state references: {total_global}")
        print(f"Instance state references: {total_instance}")
        print(f"Interpretation: {self._interpret_irreducibility(irreducibility)}")
        
        # Assert: can measure
        self.assertIsNotNone(irreducibility)
        self.assertGreaterEqual(irreducibility, 0.0)
        self.assertLessEqual(irreducibility, 1.0)
    
    def test_04_emergent_intelligence_verdict(self):
        """
        Test 4: Final Verdict on Emergent Intelligence
        
        Synthesizes all measurements to assess presence of emergent intelligence.
        """
        print(f"\n{'='*60}")
        print("EMERGENT INTELLIGENCE ASSESSMENT (IIT-inspired)")
        print(f"{'='*60}")
        
        phi = self.results.get('test_01', {}).get('phi', 0)
        autonomy = self.results.get('test_02', {}).get('autonomy_score', 0)
        irreducibility = self.results.get('test_03', {}).get('irreducibility_score', 0)
        adaptive = self.results.get('test_02', {}).get('adaptive_patterns', 0)
        self_modify = self.results.get('test_02', {}).get('self_modification', 0)
        
        print(f"\nIntegration (Φ):      {phi:.4f}")
        print(f"Autonomy:             {autonomy:.4f}")
        print(f"Irreducibility:       {irreducibility:.4f}")
        print(f"Adaptive patterns:    {adaptive}")
        print(f"Self-modification:    {self_modify}")
        
        print(f"\n{'='*60}")
        print("VERDICT")
        print(f"{'='*60}")
        
        # Emergent intelligence criteria
        has_integration = phi > 0.1
        has_autonomy = autonomy > 1.0
        has_irreducibility = irreducibility > 0.3
        has_adaptation = adaptive > 10
        has_self_modification = self_modify > 0
        
        verdict = []
        
        if has_integration:
            verdict.append("✓ Shows non-trivial information integration")
        else:
            verdict.append("✗ Low integration - modular architecture")
        
        if has_autonomy:
            verdict.append("✓ Has internal decision-making")
        else:
            verdict.append("✗ Primarily reactive/externally-driven")
        
        if has_irreducibility:
            verdict.append("✓ State coupling present")
        else:
            verdict.append("✗ Clean state boundaries")
        
        if has_adaptation:
            verdict.append(f"✓ Contains {adaptive} adaptive patterns")
        else:
            verdict.append("✗ No significant adaptive/learning behavior")
        
        if has_self_modification:
            verdict.append(f"⚠ Contains {self_modify} self-modification patterns")
        else:
            verdict.append("✗ No self-modification capability")
        
        for v in verdict:
            print(v)
        
        print(f"\n{'='*60}")
        print("CONCLUSION")
        print(f"{'='*60}")
        
        # IIT requires high Φ, causal power, and irreducibility
        emergent_score = (
            (phi * 10) +
            (autonomy * 0.5) +
            (irreducibility * 5) +
            (adaptive * 0.01) +
            (self_modify * 0.1)
        )
        
        print(f"\nEmergent Complexity Score: {emergent_score:.2f}")
        print()
        
        if emergent_score > 5.0 and has_adaptation and has_self_modification:
            conclusion = "POSSIBLE EMERGENT PROPERTIES: System shows non-trivial integration, adaptation, and self-modification."
        elif emergent_score > 2.0:
            conclusion = "COMPLEX BUT DETERMINISTIC: System is complex and coupled but lacks hallmarks of emergent intelligence."
        else:
            conclusion = "ENGINEERED SYSTEM: Clean modular architecture with explicit control flow. No emergent intelligence detected."
        
        print(conclusion)
        print()
        
        # Save results
        results_file = self.root_path / 'artifacts' / 'emergent_complexity_analysis.json'
        results_file.parent.mkdir(exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump({
                'measurements': self.results,
                'verdict': verdict,
                'conclusion': conclusion,
                'emergent_score': emergent_score
            }, f, indent=2)
        
        print(f"Full results saved to: {results_file}")
        
        # This test always passes - it's about measurement, not pass/fail
        self.assertTrue(True, "Analysis complete")
    
    def _interpret_phi(self, phi: float) -> str:
        """Interpret Φ value"""
        if phi < 0.05:
            return "Very low integration - highly modular system"
        elif phi < 0.15:
            return "Low-moderate integration - some cross-module coupling"
        elif phi < 0.30:
            return "Moderate integration - significant interdependencies"
        else:
            return "High integration - tightly coupled subsystems"
    
    def _interpret_autonomy(self, score: float, adaptive: int, self_modify: int) -> str:
        """Interpret autonomy score"""
        if score < 0.5:
            return "Primarily reactive - heavily externally controlled"
        elif score < 1.5:
            return "Balanced - mix of internal logic and external control"
        elif score < 3.0:
            return "Moderately autonomous - significant internal decision-making"
        else:
            base = "Highly autonomous - extensive internal control flow"
            if adaptive > 10:
                base += f" with {adaptive} adaptive patterns"
            if self_modify > 0:
                base += f" and {self_modify} self-modification sites"
            return base
    
    def _interpret_irreducibility(self, score: float) -> str:
        """Interpret irreducibility score"""
        if score < 0.1:
            return "Highly reducible - clean state partitions"
        elif score < 0.3:
            return "Moderately reducible - some shared state"
        elif score < 0.5:
            return "Low reducibility - significant state coupling"
        else:
            return "Highly irreducible - tightly coupled state"


if __name__ == '__main__':
    unittest.main(verbosity=2)
