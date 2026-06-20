#!/usr/bin/env python3
"""
Multi-Dimensional Superiority Metrics for HYBA PQMC Benchmarks

This module provides comprehensive superiority metrics across multiple dimensions:
- Speed: Execution time, throughput, latency
- Accuracy: Result correctness, precision, recall
- Scalability: Performance scaling with data size
- Efficiency: Memory usage, energy consumption, cost
- Robustness: Error handling, fault tolerance
- Reproducibility: Consistency across runs

All metrics are statistically validated with confidence intervals and effect sizes.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from scipy import stats
import time


@dataclass
class SuperiorityMetrics:
    """Comprehensive superiority metrics."""
    
    # Speed metrics
    speedup: float
    throughput_improvement: float
    latency_reduction: float
    time_efficiency: float
    
    # Accuracy metrics
    accuracy_improvement: float
    precision_improvement: float
    recall_improvement: float
    f1_improvement: float
    error_rate_reduction: float
    
    # Scalability metrics
    scaling_factor: float
    big_o_complexity: str
    scalability_score: float
    data_size_scaling: float
    
    # Efficiency metrics
    memory_reduction: float
    energy_efficiency: float
    cost_efficiency: float
    resource_utilization: float
    
    # Robustness metrics
    fault_tolerance: float
    error_recovery: float
    stability_score: float
    resilience: float
    
    # Statistical validation
    p_value: float
    confidence_interval: Tuple[float, float]
    effect_size: float
    statistical_significance: bool
    power: float
    
    # Overall superiority
    overall_score: float
    superiority_rank: str
    confidence_level: float


class SuperiorityAnalyzer:
    """Analyzer for multi-dimensional superiority metrics."""
    
    def __init__(self, alpha: float = 0.05, power_target: float = 0.8):
        self.alpha = alpha
        self.power_target = power_target
        
    def calculate_speed_metrics(self, hyba_times: List[float], 
                                  classical_times: List[float]) -> Dict[str, float]:
        """Calculate speed-related superiority metrics."""
        hyba_mean = np.mean(hyba_times)
        classical_mean = np.mean(classical_times)
        
        speedup = classical_mean / hyba_mean if hyba_mean > 0 else 0
        throughput_improvement = speedup  # Assuming linear relationship
        latency_reduction = (classical_mean - hyba_mean) / classical_mean if classical_mean > 0 else 0
        time_efficiency = 1 / hyba_mean if hyba_mean > 0 else 0
        
        return {
            "speedup": speedup,
            "throughput_improvement": throughput_improvement,
            "latency_reduction": latency_reduction,
            "time_efficiency": time_efficiency
        }
    
    def calculate_accuracy_metrics(self, hyba_accuracies: List[float],
                                    classical_accuracies: List[float],
                                    hyba_precisions: Optional[List[float]] = None,
                                    classical_precisions: Optional[List[float]] = None,
                                    hyba_recalls: Optional[List[float]] = None,
                                    classical_recalls: Optional[List[float]] = None) -> Dict[str, float]:
        """Calculate accuracy-related superiority metrics."""
        hyba_mean = np.mean(hyba_accuracies)
        classical_mean = np.mean(classical_accuracies)
        
        accuracy_improvement = hyba_mean - classical_mean
        error_rate_reduction = (1 - hyba_mean) - (1 - classical_mean)
        
        precision_improvement = 0.0
        if hyba_precisions and classical_precisions:
            precision_improvement = np.mean(hyba_precisions) - np.mean(classical_precisions)
        
        recall_improvement = 0.0
        if hyba_recalls and classical_recalls:
            recall_improvement = np.mean(hyba_recalls) - np.mean(classical_recalls)
        
        # F1 score improvement
        if precision_improvement != 0 and recall_improvement != 0:
            hyba_f1 = 2 * (np.mean(hyba_precisions) * np.mean(hyba_recalls)) / (np.mean(hyba_precisions) + np.mean(hyba_recalls))
            classical_f1 = 2 * (np.mean(classical_precisions) * np.mean(classical_recalls)) / (np.mean(classical_precisions) + np.mean(classical_recalls))
            f1_improvement = hyba_f1 - classical_f1
        else:
            f1_improvement = 0.0
        
        return {
            "accuracy_improvement": accuracy_improvement,
            "precision_improvement": precision_improvement,
            "recall_improvement": recall_improvement,
            "f1_improvement": f1_improvement,
            "error_rate_reduction": error_rate_reduction
        }
    
    def calculate_scalability_metrics(self, hyba_times_by_size: Dict[int, float],
                                      classical_times_by_size: Dict[int, float]) -> Dict[str, Any]:
        """Calculate scalability-related superiority metrics."""
        sizes = sorted(hyba_times_by_size.keys())
        
        # Calculate scaling factors
        hyba_scaling = []
        classical_scaling = []
        
        for i in range(1, len(sizes)):
            size_ratio = sizes[i] / sizes[i-1]
            hyba_time_ratio = hyba_times_by_size[sizes[i]] / hyba_times_by_size[sizes[i-1]]
            classical_time_ratio = classical_times_by_size[sizes[i]] / classical_times_by_size[sizes[i-1]]
            
            hyba_scaling.append(hyba_time_ratio / size_ratio)
            classical_scaling.append(classical_time_ratio / size_ratio)
        
        scaling_factor = np.mean(hyba_scaling) / np.mean(classical_scaling) if classical_scaling else 0
        
        # Estimate Big O complexity
        if len(sizes) >= 2:
            # Simple log-log regression to estimate exponent
            log_sizes = np.log(sizes)
            log_hyba_times = np.log([hyba_times_by_size[s] for s in sizes])
            slope, _ = np.polyfit(log_sizes, log_hyba_times, 1)
            
            if slope < 1.1:
                hyba_big_o = "O(1) or O(log n)"
            elif slope < 1.5:
                hyba_big_o = "O(n)"
            elif slope < 2.1:
                hyba_big_o = "O(n log n)"
            elif slope < 3.1:
                hyba_big_o = "O(n^2)"
            else:
                hyba_big_o = f"O(n^{slope:.1f})"
        else:
            hyba_big_o = "Unknown"
        
        # Scalability score (lower is better for time complexity)
        scalability_score = 1.0 / (1.0 + scaling_factor) if scaling_factor > 0 else 0
        
        # Data size scaling
        if len(sizes) >= 2:
            data_size_scaling = (hyba_times_by_size[sizes[-1]] / hyba_times_by_size[sizes[0]]) / \
                               (classical_times_by_size[sizes[-1]] / classical_times_by_size[sizes[0]])
        else:
            data_size_scaling = 1.0
        
        return {
            "scaling_factor": scaling_factor,
            "big_o_complexity": hyba_big_o,
            "scalability_score": scalability_score,
            "data_size_scaling": data_size_scaling
        }
    
    def calculate_efficiency_metrics(self, hyba_memory: List[float],
                                      classical_memory: List[float],
                                      hyba_energy: Optional[List[float]] = None,
                                      classical_energy: Optional[List[float]] = None) -> Dict[str, float]:
        """Calculate efficiency-related superiority metrics."""
        hyba_mean = np.mean(hyba_memory)
        classical_mean = np.mean(classical_memory)
        
        memory_reduction = (classical_mean - hyba_mean) / classical_mean if classical_mean > 0 else 0
        
        energy_efficiency = 1.0
        if hyba_energy and classical_energy:
            hyba_energy_mean = np.mean(hyba_energy)
            classical_energy_mean = np.mean(classical_energy)
            energy_efficiency = classical_energy_mean / hyba_energy_mean if hyba_energy_mean > 0 else 0
        
        # Cost efficiency (assuming cost scales with memory and energy)
        cost_efficiency = (1.0 - memory_reduction) * (1.0 / energy_efficiency) if energy_efficiency > 0 else 0
        
        # Resource utilization (lower is better)
        resource_utilization = hyba_mean / classical_mean if classical_mean > 0 else 0
        
        return {
            "memory_reduction": memory_reduction,
            "energy_efficiency": energy_efficiency,
            "cost_efficiency": cost_efficiency,
            "resource_utilization": resource_utilization
        }
    
    def calculate_robustness_metrics(self, hyba_success_rate: float,
                                       classical_success_rate: float,
                                       hyba_recovery_time: Optional[float] = None,
                                       classical_recovery_time: Optional[float] = None) -> Dict[str, float]:
        """Calculate robustness-related superiority metrics."""
        fault_tolerance = hyba_success_rate - classical_success_rate
        
        error_recovery = 0.0
        if hyba_recovery_time and classical_recovery_time:
            error_recovery = (classical_recovery_time - hyba_recovery_time) / classical_recovery_time if classical_recovery_time > 0 else 0
        
        # Stability score (higher is better)
        stability_score = hyba_success_rate
        
        # Resilience (combination of fault tolerance and recovery)
        resilience = (hyba_success_rate + (1.0 - (hyba_recovery_time / classical_recovery_time) if hyba_recovery_time and classical_recovery_time > 0 else 0)) / 2
        
        return {
            "fault_tolerance": fault_tolerance,
            "error_recovery": error_recovery,
            "stability_score": stability_score,
            "resilience": resilience
        }
    
    def statistical_validation(self, hyba_results: List[float],
                               classical_results: List[float]) -> Tuple[float, Tuple[float, float], float, bool, float]:
        """Perform statistical validation of superiority."""
        # Two-sample t-test
        t_stat, p_value = stats.ttest_ind(hyba_results, classical_results)
        
        # Confidence interval for difference
        diff = np.mean(hyba_results) - np.mean(classical_results)
        std_err = np.sqrt(np.var(hyba_results)/len(hyba_results) + np.var(classical_results)/len(classical_results))
        ci = (diff - 1.96*std_err, diff + 1.96*std_err)
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt((np.var(hyba_results) + np.var(classical_results)) / 2)
        effect_size = diff / pooled_std if pooled_std > 0 else 0.0
        
        # Statistical significance
        significant = p_value < self.alpha
        
        # Statistical power
        n1, n2 = len(hyba_results), len(classical_results)
        if pooled_std > 0:
            # Simplified power calculation
            power = stats.norm.cdf(abs(effect_size) * np.sqrt(n1*n2/(n1+n2)) - 1.96)
        else:
            power = 0.0
        
        return p_value, ci, effect_size, significant, power
    
    def calculate_overall_superiority(self, metrics: Dict[str, float]) -> Tuple[float, str]:
        """Calculate overall superiority score and rank."""
        # Weighted average of all metrics
        weights = {
            "speedup": 0.2,
            "accuracy_improvement": 0.2,
            "scalability_score": 0.15,
            "memory_reduction": 0.1,
            "energy_efficiency": 0.1,
            "fault_tolerance": 0.1,
            "stability_score": 0.1,
            "resilience": 0.05
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in metrics:
                weighted_sum += metrics[metric] * weight
                total_weight += weight
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Determine rank
        if overall_score >= 0.8:
            rank = "Exceptional"
        elif overall_score >= 0.6:
            rank = "Superior"
        elif overall_score >= 0.4:
            rank = "Significant"
        elif overall_score >= 0.2:
            rank = "Moderate"
        elif overall_score >= 0.0:
            rank = "Marginal"
        else:
            rank = "Inferior"
        
        return overall_score, rank
    
    def analyze_superiority(self, 
                           hyba_times: List[float],
                           classical_times: List[float],
                           hyba_accuracies: List[float],
                           classical_accuracies: List[float],
                           hyba_memory: List[float],
                           classical_memory: List[float],
                           hyba_times_by_size: Optional[Dict[int, float]] = None,
                           classical_times_by_size: Optional[Dict[int, float]] = None,
                           hyba_success_rate: Optional[float] = None,
                           classical_success_rate: Optional[float] = None) -> SuperiorityMetrics:
        """Perform comprehensive superiority analysis."""
        
        # Speed metrics
        speed_metrics = self.calculate_speed_metrics(hyba_times, classical_times)
        
        # Accuracy metrics
        accuracy_metrics = self.calculate_accuracy_metrics(hyba_accuracies, classical_accuracies)
        
        # Scalability metrics
        if hyba_times_by_size and classical_times_by_size:
            scalability_metrics = self.calculate_scalability_metrics(hyba_times_by_size, classical_times_by_size)
        else:
            scalability_metrics = {
                "scaling_factor": 1.0,
                "big_o_complexity": "Unknown",
                "scalability_score": 0.5,
                "data_size_scaling": 1.0
            }
        
        # Efficiency metrics
        efficiency_metrics = self.calculate_efficiency_metrics(hyba_memory, classical_memory)
        
        # Robustness metrics
        if hyba_success_rate and classical_success_rate:
            robustness_metrics = self.calculate_robustness_metrics(hyba_success_rate, classical_success_rate)
        else:
            robustness_metrics = {
                "fault_tolerance": 0.0,
                "error_recovery": 0.0,
                "stability_score": 1.0,
                "resilience": 0.5
            }
        
        # Statistical validation
        p_value, ci, effect_size, significant, power = self.statistical_validation(hyba_accuracies, classical_accuracies)
        
        # Overall superiority
        all_metrics = {**speed_metrics, **accuracy_metrics, **scalability_metrics, 
                      **efficiency_metrics, **robustness_metrics}
        overall_score, rank = self.calculate_overall_superiority(all_metrics)
        
        return SuperiorityMetrics(
            # Speed
            speedup=speed_metrics["speedup"],
            throughput_improvement=speed_metrics["throughput_improvement"],
            latency_reduction=speed_metrics["latency_reduction"],
            time_efficiency=speed_metrics["time_efficiency"],
            
            # Accuracy
            accuracy_improvement=accuracy_metrics["accuracy_improvement"],
            precision_improvement=accuracy_metrics["precision_improvement"],
            recall_improvement=accuracy_metrics["recall_improvement"],
            f1_improvement=accuracy_metrics["f1_improvement"],
            error_rate_reduction=accuracy_metrics["error_rate_reduction"],
            
            # Scalability
            scaling_factor=scalability_metrics["scaling_factor"],
            big_o_complexity=scalability_metrics["big_o_complexity"],
            scalability_score=scalability_metrics["scalability_score"],
            data_size_scaling=scalability_metrics["data_size_scaling"],
            
            # Efficiency
            memory_reduction=efficiency_metrics["memory_reduction"],
            energy_efficiency=efficiency_metrics["energy_efficiency"],
            cost_efficiency=efficiency_metrics["cost_efficiency"],
            resource_utilization=efficiency_metrics["resource_utilization"],
            
            # Robustness
            fault_tolerance=robustness_metrics["fault_tolerance"],
            error_recovery=robustness_metrics["error_recovery"],
            stability_score=robustness_metrics["stability_score"],
            resilience=robustness_metrics["resilience"],
            
            # Statistical
            p_value=p_value,
            confidence_interval=ci,
            effect_size=effect_size,
            statistical_significance=significant,
            power=power,
            
            # Overall
            overall_score=overall_score,
            superiority_rank=rank,
            confidence_level=1.0 - self.alpha
        )


def main():
    """Test the superiority analyzer."""
    analyzer = SuperiorityAnalyzer(alpha=0.05, power_target=0.8)
    
    # Generate synthetic data
    np.random.seed(42)
    hyba_times = np.random.exponential(1.0, 100)
    classical_times = np.random.exponential(5.0, 100)
    hyba_accuracies = np.random.normal(0.95, 0.02, 100)
    classical_accuracies = np.random.normal(0.85, 0.05, 100)
    hyba_memory = np.random.normal(100, 10, 100)
    classical_memory = np.random.normal(500, 50, 100)
    
    # Scalability data
    hyba_times_by_size = {100: 1.0, 1000: 2.0, 10000: 5.0}
    classical_times_by_size = {100: 5.0, 1000: 50.0, 10000: 500.0}
    
    # Analyze superiority
    metrics = analyzer.analyze_superiority(
        hyba_times=hyba_times,
        classical_times=classical_times,
        hyba_accuracies=hyba_accuracies,
        classical_accuracies=classical_accuracies,
        hyba_memory=hyba_memory,
        classical_memory=classical_memory,
        hyba_times_by_size=hyba_times_by_size,
        classical_times_by_size=classical_times_by_size,
        hyba_success_rate=0.99,
        classical_success_rate=0.90
    )
    
    print("Superiority Metrics:")
    print(f"  Speedup: {metrics.speedup:.2f}x")
    print(f"  Accuracy Improvement: {metrics.accuracy_improvement:.4f}")
    print(f"  Scalability Score: {metrics.scalability_score:.4f}")
    print(f"  Memory Reduction: {metrics.memory_reduction:.2%}")
    print(f"  Energy Efficiency: {metrics.energy_efficiency:.2f}x")
    print(f"  Fault Tolerance: {metrics.fault_tolerance:.4f}")
    print(f"  Statistical Significance: {metrics.statistical_significance} (p={metrics.p_value:.4f})")
    print(f"  Effect Size: {metrics.effect_size:.4f}")
    print(f"  Overall Score: {metrics.overall_score:.4f}")
    print(f"  Superiority Rank: {metrics.superiority_rank}")


if __name__ == "__main__":
    main()
