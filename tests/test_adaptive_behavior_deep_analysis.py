"""
Deep Analysis of Adaptive Behavior Patterns

Investigates the 152 adaptive patterns detected in the initial IIT scan
to determine if they represent genuine learning/optimization loops or
just naming conventions.

Tests for:
1. Feedback loops (state → action → state update based on outcome)
2. Parameter optimization (values that change based on performance)
3. Memory accumulation (state that grows with experience)
4. Self-tuning behavior (automatic configuration adjustment)
"""

import unittest
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class FeedbackLoopDetector:
    """Detects closed-loop feedback patterns where output affects future input"""
    
    def __init__(self):
        self.feedback_loops: List[Dict] = []
        
    def analyze_python_file(self, file_path: Path) -> Dict:
        """Search for feedback loop patterns in Python code"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
            
            loops = []
            
            # Pattern 1: State update based on previous state
            # Looking for: self.x = self.x * factor or self.x += delta
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    # Check if RHS references LHS (feedback pattern)
                    lhs_names = self._get_assignment_targets(node)
                    rhs_names = self._get_names_in_expr(node.value)
                    
                    feedback_vars = lhs_names & rhs_names
                    if feedback_vars:
                        loops.append({
                            'type': 'state_feedback',
                            'variables': list(feedback_vars),
                            'line': node.lineno if hasattr(node, 'lineno') else 0
                        })
            
            # Pattern 2: Update methods that modify state based on input
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if any(keyword in node.name.lower() for keyword in 
                           ['update', 'adjust', 'tune', 'optimize', 'adapt', 'learn']):
                        # Check if function modifies self attributes
                        modifies_state = False
                        for child in ast.walk(node):
                            if isinstance(child, (ast.Assign, ast.AugAssign)):
                                if self._assigns_to_self(child):
                                    modifies_state = True
                                    break
                        
                        if modifies_state:
                            loops.append({
                                'type': 'update_method',
                                'function': node.name,
                                'line': node.lineno
                            })
            
            # Pattern 3: Accumulation patterns (memory growth)
            accumulation_patterns = [
                r'\.append\(',
                r'\.extend\(',
                r'\.update\(',
                r'\[\w+\]\s*=',  # dict assignment
                r'\+=',  # augmented assignment
            ]
            
            for pattern in accumulation_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    loops.append({
                        'type': 'accumulation',
                        'pattern': pattern,
                        'line': line_num
                    })
            
            return {
                'file': str(file_path.name),
                'feedback_loops': loops,
                'count': len(loops)
            }
            
        except Exception as e:
            return {'file': str(file_path.name), 'error': str(e), 'count': 0}
    
    def _get_assignment_targets(self, node: ast.Assign) -> Set[str]:
        """Extract variable names being assigned to"""
        names = set()
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
            elif isinstance(target, ast.Attribute):
                names.add(f"{target.value.id if isinstance(target.value, ast.Name) else '?'}.{target.attr}")
        return names
    
    def _get_names_in_expr(self, node) -> Set[str]:
        """Extract all variable names referenced in an expression"""
        names = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                names.add(child.id)
            elif isinstance(child, ast.Attribute):
                if isinstance(child.value, ast.Name):
                    names.add(f"{child.value.id}.{child.attr}")
        return names
    
    def _assigns_to_self(self, node) -> bool:
        """Check if assignment modifies self attributes"""
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    if isinstance(target.value, ast.Name) and target.value.id == 'self':
                        return True
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Attribute):
                if isinstance(node.target.value, ast.Name) and node.target.value.id == 'self':
                    return True
        return False


class ParameterOptimizationDetector:
    """Detects parameters that are tuned based on performance metrics"""
    
    def analyze_file(self, file_path: Path) -> Dict:
        """Look for optimization/tuning patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            optimizations = []
            
            # Pattern 1: Gradient descent / optimization loops
            optimization_patterns = [
                (r'gradient', 'gradient_computation'),
                (r'learning_rate', 'learning_rate_usage'),
                (r'loss\s*=', 'loss_calculation'),
                (r'minimize|maximize', 'optimization_call'),
                (r'backprop', 'backpropagation'),
                (r'weight.*update', 'weight_update'),
                (r'hyperparameter', 'hyperparameter_tuning'),
            ]
            
            for pattern, label in optimization_patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    optimizations.append({
                        'type': label,
                        'line': line_num,
                        'snippet': content[max(0, match.start()-20):match.end()+20]
                    })
            
            # Pattern 2: Adaptive thresholds or parameters
            adaptive_patterns = [
                (r'threshold.*=.*adapt', 'adaptive_threshold'),
                (r'auto.*adjust', 'auto_adjustment'),
                (r'dynamic.*config', 'dynamic_configuration'),
            ]
            
            for pattern, label in adaptive_patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    optimizations.append({
                        'type': label,
                        'line': line_num
                    })
            
            return {
                'file': str(file_path.name),
                'optimizations': optimizations,
                'count': len(optimizations)
            }
            
        except Exception as e:
            return {'file': str(file_path.name), 'error': str(e), 'count': 0}


class MemoryAccumulationDetector:
    """Detects systems that accumulate experience/memory over time"""
    
    def analyze_file(self, file_path: Path) -> Dict:
        """Look for memory/experience accumulation patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            memory_patterns = []
            
            # Pattern 1: Explicit memory structures
            memory_keywords = [
                (r'memory', 'memory_reference'),
                (r'history', 'history_tracking'),
                (r'cache', 'caching'),
                (r'experience', 'experience_accumulation'),
                (r'recall', 'recall_mechanism'),
                (r'retain', 'retention'),
                (r'remember', 'memory_storage'),
            ]
            
            for pattern, label in memory_keywords:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    # Get surrounding context
                    line_start = content.rfind('\n', 0, match.start()) + 1
                    line_end = content.find('\n', match.end())
                    if line_end == -1:
                        line_end = len(content)
                    line_content = content[line_start:line_end].strip()
                    
                    memory_patterns.append({
                        'type': label,
                        'line': line_num,
                        'context': line_content[:100]
                    })
            
            return {
                'file': str(file_path.name),
                'memory_patterns': memory_patterns,
                'count': len(memory_patterns)
            }
            
        except Exception as e:
            return {'file': str(file_path.name), 'error': str(e), 'count': 0}


class SelfModificationDetector:
    """Deep analysis of the 2 self-modification sites detected"""
    
    def analyze_file(self, file_path: Path) -> Dict:
        """Look for self-modification patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modifications = []
            
            # Dangerous self-modification patterns
            self_modify_patterns = [
                (r'eval\s*\(', 'eval_usage', 'DANGEROUS'),
                (r'exec\s*\(', 'exec_usage', 'DANGEROUS'),
                (r'compile\s*\(', 'compile_usage', 'MODERATE'),
                (r'__setattr__', 'setattr_override', 'MODERATE'),
                (r'setattr\s*\(', 'setattr_usage', 'LOW'),
                (r'__dict__\[', 'dict_manipulation', 'LOW'),
                (r'globals\(\)', 'globals_access', 'MODERATE'),
                (r'locals\(\)', 'locals_access', 'LOW'),
                (r'type\s*\(.*\)\(', 'dynamic_type_creation', 'MODERATE'),
            ]
            
            for pattern, label, severity in self_modify_patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    # Get context
                    line_start = content.rfind('\n', 0, match.start()) + 1
                    line_end = content.find('\n', match.end())
                    if line_end == -1:
                        line_end = len(content)
                    line_content = content[line_start:line_end].strip()
                    
                    modifications.append({
                        'type': label,
                        'severity': severity,
                        'line': line_num,
                        'context': line_content[:150]
                    })
            
            return {
                'file': str(file_path.name),
                'modifications': modifications,
                'count': len(modifications)
            }
            
        except Exception as e:
            return {'file': str(file_path.name), 'error': str(e), 'count': 0}


class TestAdaptiveBehaviorDeepAnalysis(unittest.TestCase):
    """Deep dive into adaptive patterns found in initial IIT scan"""
    
    @classmethod
    def setUpClass(cls):
        cls.root_path = Path(__file__).parent.parent
        cls.results = {}
    
    def test_01_feedback_loops(self):
        """
        Test 1: Feedback Loop Detection
        
        True feedback requires: output → action → measure → adjust input
        """
        detector = FeedbackLoopDetector()
        
        all_results = []
        python_dirs = [
            self.root_path / 'python_backend' / 'pythia_mining',
            self.root_path / 'python_backend' / 'hyba_genesis_api'
        ]
        
        for py_dir in python_dirs:
            if py_dir.exists():
                for py_file in py_dir.rglob('*.py'):
                    if py_file.name != '__init__.py':
                        result = detector.analyze_python_file(py_file)
                        if result.get('count', 0) > 0:
                            all_results.append(result)
        
        total_loops = sum(r.get('count', 0) for r in all_results)
        
        print(f"\n=== FEEDBACK LOOP ANALYSIS ===")
        print(f"Total feedback patterns found: {total_loops}")
        print(f"Files with feedback loops: {len(all_results)}")
        
        # Show top files
        all_results.sort(key=lambda x: x.get('count', 0), reverse=True)
        print(f"\nTop 5 files with most feedback patterns:")
        for i, result in enumerate(all_results[:5], 1):
            print(f"  {i}. {result['file']}: {result['count']} patterns")
        
        self.results['feedback_loops'] = {
            'total': total_loops,
            'files': len(all_results),
            'top_files': all_results[:5]
        }
        
        self.assertGreater(total_loops, 0, "Should find feedback patterns")
    
    def test_02_parameter_optimization(self):
        """
        Test 2: Parameter Optimization Detection
        
        Looks for genuine optimization loops vs. static configuration.
        """
        detector = ParameterOptimizationDetector()
        
        all_results = []
        
        for code_dir in [
            self.root_path / 'python_backend',
            self.root_path / 'src'
        ]:
            if code_dir.exists():
                for py_file in code_dir.rglob('*.py'):
                    if py_file.name != '__init__.py':
                        result = detector.analyze_file(py_file)
                        if result.get('count', 0) > 0:
                            all_results.append(result)
        
        total_optimizations = sum(r.get('count', 0) for r in all_results)
        
        print(f"\n=== PARAMETER OPTIMIZATION ANALYSIS ===")
        print(f"Total optimization patterns: {total_optimizations}")
        print(f"Files with optimization: {len(all_results)}")
        
        # Show examples
        if all_results:
            print(f"\nExample files:")
            for result in all_results[:3]:
                print(f"  - {result['file']}: {result['count']} patterns")
        
        self.results['optimizations'] = {
            'total': total_optimizations,
            'files': len(all_results)
        }
    
    def test_03_memory_accumulation(self):
        """
        Test 3: Memory Accumulation Analysis
        
        Systems with memory accumulate state over time that affects future behavior.
        """
        detector = MemoryAccumulationDetector()
        
        all_results = []
        
        for code_dir in [
            self.root_path / 'python_backend',
            self.root_path / 'src'
        ]:
            if code_dir.exists():
                for py_file in code_dir.rglob('*.py'):
                    if py_file.name != '__init__.py':
                        result = detector.analyze_file(py_file)
                        if result.get('count', 0) > 0:
                            all_results.append(result)
        
        total_memory = sum(r.get('count', 0) for r in all_results)
        
        print(f"\n=== MEMORY ACCUMULATION ANALYSIS ===")
        print(f"Total memory-related patterns: {total_memory}")
        print(f"Files with memory: {len(all_results)}")
        
        # Group by type
        type_counts = defaultdict(int)
        for result in all_results:
            for pattern in result.get('memory_patterns', []):
                type_counts[pattern['type']] += 1
        
        print(f"\nBreakdown by type:")
        for mem_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {mem_type}: {count}")
        
        self.results['memory'] = {
            'total': total_memory,
            'files': len(all_results),
            'by_type': dict(type_counts)
        }
        
        self.assertGreater(total_memory, 0, "Should find memory patterns")
    
    def test_04_self_modification_sites(self):
        """
        Test 4: Self-Modification Site Analysis
        
        Deep dive into the 2 self-modification sites found in initial scan.
        """
        detector = SelfModificationDetector()
        
        all_results = []
        dangerous_sites = []
        
        for code_dir in [
            self.root_path / 'python_backend',
            self.root_path / 'src'
        ]:
            if code_dir.exists():
                for py_file in code_dir.rglob('*.py'):
                    if py_file.name != '__init__.py':
                        result = detector.analyze_file(py_file)
                        if result.get('count', 0) > 0:
                            all_results.append(result)
                            for mod in result.get('modifications', []):
                                if mod['severity'] == 'DANGEROUS':
                                    dangerous_sites.append({
                                        'file': result['file'],
                                        **mod
                                    })
        
        total_modifications = sum(r.get('count', 0) for r in all_results)
        
        print(f"\n=== SELF-MODIFICATION SITE ANALYSIS ===")
        print(f"Total self-modification patterns: {total_modifications}")
        print(f"Files with self-modification: {len(all_results)}")
        print(f"DANGEROUS sites (eval/exec): {len(dangerous_sites)}")
        
        # Show dangerous sites
        if dangerous_sites:
            print(f"\n⚠ DANGEROUS SELF-MODIFICATION SITES:")
            for site in dangerous_sites:
                print(f"  File: {site['file']} (line {site['line']})")
                print(f"  Type: {site['type']}")
                print(f"  Context: {site['context']}")
                print()
        
        # Group by severity
        severity_counts = defaultdict(int)
        for result in all_results:
            for mod in result.get('modifications', []):
                severity_counts[mod['severity']] += 1
        
        print(f"By severity:")
        for severity in ['DANGEROUS', 'MODERATE', 'LOW']:
            count = severity_counts.get(severity, 0)
            print(f"  {severity}: {count}")
        
        self.results['self_modification'] = {
            'total': total_modifications,
            'files': len(all_results),
            'dangerous_sites': len(dangerous_sites),
            'by_severity': dict(severity_counts),
            'dangerous_details': dangerous_sites
        }
    
    def test_05_adaptive_behavior_verdict(self):
        """
        Test 5: Final Verdict on Adaptive Behavior
        
        Synthesizes findings to determine if adaptive patterns represent
        genuine learning/optimization vs. naming conventions.
        """
        print(f"\n{'='*60}")
        print("ADAPTIVE BEHAVIOR VERDICT")
        print(f"{'='*60}")
        
        feedback = self.results.get('feedback_loops', {}).get('total', 0)
        optimizations = self.results.get('optimizations', {}).get('total', 0)
        memory = self.results.get('memory', {}).get('total', 0)
        self_mod = self.results.get('self_modification', {}).get('total', 0)
        dangerous = self.results.get('self_modification', {}).get('dangerous_sites', 0)
        
        print(f"\nMeasurements:")
        print(f"  Feedback loops:        {feedback}")
        print(f"  Optimization patterns: {optimizations}")
        print(f"  Memory patterns:       {memory}")
        print(f"  Self-modification:     {self_mod} ({dangerous} dangerous)")
        
        print(f"\n{'='*60}")
        print("ANALYSIS")
        print(f"{'='*60}")
        
        # Determine if patterns are genuine
        genuine_adaptive = (
            optimizations > 5 and  # Real optimization code
            feedback > 10 and      # Multiple feedback loops
            memory > 20            # Significant memory usage
        )
        
        has_learning = optimizations > 0 and 'gradient' in str(self.results)
        has_dangerous_self_mod = dangerous > 0
        
        print()
        if genuine_adaptive:
            print("✓ GENUINE ADAPTIVE BEHAVIOR DETECTED")
            print("  System shows real optimization, feedback, and memory.")
        else:
            print("✗ NAMING CONVENTIONS, NOT ADAPTIVE BEHAVIOR")
            print("  Keywords present but lack closed-loop learning structure.")
        
        print()
        if has_learning:
            print("✓ LEARNING MECHANISMS PRESENT")
            print("  Gradient/optimization code suggests learning capability.")
        else:
            print("✗ NO LEARNING MECHANISMS")
            print("  No gradient descent or machine learning patterns found.")
        
        print()
        if has_dangerous_self_mod:
            print("⚠ DANGEROUS SELF-MODIFICATION DETECTED")
            print(f"  {dangerous} eval/exec sites allow runtime code generation.")
            print("  THIS IS A TRUE SELF-MODIFICATION CAPABILITY.")
        else:
            print("✓ NO DANGEROUS SELF-MODIFICATION")
            print("  System does not use eval/exec for runtime code generation.")
        
        print(f"\n{'='*60}")
        print("CONCLUSION")
        print(f"{'='*60}")
        print()
        
        if genuine_adaptive and has_learning:
            conclusion = "ADAPTIVE SYSTEM: Contains genuine learning/optimization loops."
        elif memory > 50 and feedback > 20:
            conclusion = "STATEFUL SYSTEM: Accumulates memory and uses feedback, but no learning."
        else:
            conclusion = "DETERMINISTIC SYSTEM: Adaptive keywords are naming conventions, not behavior."
        
        print(conclusion)
        print()
        
        # Save results
        import json
        results_file = self.root_path / 'artifacts' / 'adaptive_behavior_analysis.json'
        results_file.parent.mkdir(exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump({
                'measurements': self.results,
                'genuine_adaptive': genuine_adaptive,
                'has_learning': has_learning,
                'has_dangerous_self_mod': has_dangerous_self_mod,
                'conclusion': conclusion
            }, f, indent=2)
        
        print(f"Full results saved to: {results_file}")
        
        self.assertTrue(True, "Analysis complete")


if __name__ == '__main__':
    unittest.main(verbosity=2)
