"""
Mining Knowledge Base — Domain Knowledge for AI Decision-Making
Success criteria, pitfalls, rules, and expectations for mining operations

ELEVATED PURPOSE: This module provides comprehensive domain knowledge
to seed the AI with what success looks like, mining pitfalls to avoid,
rules of the game, and operational expectations. This ensures AI decisions
are grounded in mining domain expertise rather than generic optimization.

KNOWLEDGE BASE STRUCTURE:
- Success Criteria: What optimal mining operations look like
- Mining Pitfalls: Common failure patterns and how to avoid them
- Rules of the Game: Protocol constraints and mining rules
- Operational Expectations: Performance thresholds and targets
- Failure Patterns: Known failure modes and recovery strategies

AI INTEGRATION:
The AI orchestration layer references this knowledge base to:
- Make informed decisions based on success criteria
- Avoid known pitfalls and failure patterns
- Respect mining rules and protocol constraints
- Meet operational expectations and thresholds
- Apply appropriate recovery strategies

CLAIM BOUNDARY:
This provides domain knowledge for AI decision-making.
It does NOT claim to guarantee mining success or profitability.
This is knowledge-based guidance, not a guarantee of outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Tuple, Optional, Any
import numpy as np

PHI = (1.0 + 5.0 ** 0.5) / 2.0


# =============================================================================
# 1. SUCCESS CRITERIA — What Optimal Mining Looks Like
# =============================================================================

class SuccessMetric(Enum):
    """Key success metrics for mining operations."""
    
    HASHRATE = "hashrate"
    EFFICIENCY = "efficiency"
    UPTIME = "uptime"
    SHARE_ACCEPTANCE_RATE = "share_acceptance_rate"
    TEMPERATURE_STABILITY = "temperature_stability"
    POWER_EFFICIENCY = "power_efficiency"
    POOL_CONNECTION_STABILITY = "pool_connection_stability"
    ERROR_RATE = "error_rate"


@dataclass
class SuccessCriteria:
    """Definition of what success looks like in mining operations."""
    
    # Hashrate targets (H/s)
    target_hashrate_min: float = 50.0
    target_hashrate_optimal: float = 100.0
    target_hashrate_max: float = 200.0
    
    # Efficiency targets (shares per joule)
    target_efficiency_min: float = 0.5
    target_efficiency_optimal: float = 0.8
    target_efficiency_max: float = 1.0
    
    # Uptime targets (percentage)
    target_uptime_min: float = 95.0
    target_uptime_optimal: float = 99.0
    target_uptime_max: float = 100.0
    
    # Share acceptance rate (percentage)
    target_acceptance_rate_min: float = 95.0
    target_acceptance_rate_optimal: float = 98.0
    target_acceptance_rate_max: float = 100.0
    
    # Temperature stability (Celsius)
    target_temperature_min: float = 30.0
    target_temperature_optimal: float = 50.0
    target_temperature_max: float = 70.0
    
    # Error rate (percentage)
    target_error_rate_max: float = 1.0
    target_error_rate_optimal: float = 0.1
    target_error_rate_min: float = 0.0
    
    # Power efficiency (H/s per watt)
    target_power_efficiency_min: float = 0.5
    target_power_efficiency_optimal: float = 1.0
    target_power_efficiency_max: float = 2.0
    
    def evaluate_success(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate current metrics against success criteria."""
        evaluation = {
            "overall_score": 0.0,
            "metric_scores": {},
            "recommendations": []
        }
        
        # Hashrate evaluation
        hashrate = metrics.get("hashrate", 0.0)
        if hashrate >= self.target_hashrate_optimal:
            hashrate_score = 1.0
        elif hashrate >= self.target_hashrate_min:
            hashrate_score = (hashrate - self.target_hashrate_min) / (self.target_hashrate_optimal - self.target_hashrate_min)
        else:
            hashrate_score = 0.0
            evaluation["recommendations"].append("Hashrate below minimum target - consider optimization")
        
        evaluation["metric_scores"]["hashrate"] = hashrate_score
        
        # Efficiency evaluation
        efficiency = metrics.get("efficiency", 0.0)
        if efficiency >= self.target_efficiency_optimal:
            efficiency_score = 1.0
        elif efficiency >= self.target_efficiency_min:
            efficiency_score = (efficiency - self.target_efficiency_min) / (self.target_efficiency_optimal - self.target_efficiency_min)
        else:
            efficiency_score = 0.0
            evaluation["recommendations"].append("Efficiency below minimum target - check configuration")
        
        evaluation["metric_scores"]["efficiency"] = efficiency_score
        
        # Temperature evaluation
        temperature = metrics.get("temperature", 50.0)
        if self.target_temperature_min <= temperature <= self.target_temperature_optimal:
            temperature_score = 1.0
        elif temperature <= self.target_temperature_max:
            temperature_score = 1.0 - (temperature - self.target_temperature_optimal) / (self.target_temperature_max - self.target_temperature_optimal)
        else:
            temperature_score = 0.0
            evaluation["recommendations"].append("Temperature above maximum - immediate cooling required")
        
        evaluation["metric_scores"]["temperature"] = temperature_score
        
        # Error rate evaluation
        error_rate = metrics.get("error_rate", 0.0)
        if error_rate <= self.target_error_rate_optimal:
            error_rate_score = 1.0
        elif error_rate <= self.target_error_rate_max:
            error_rate_score = 1.0 - (error_rate - self.target_error_rate_optimal) / (self.target_error_rate_max - self.target_error_rate_optimal)
        else:
            error_rate_score = 0.0
            evaluation["recommendations"].append("Error rate above maximum - investigate immediately")
        
        evaluation["metric_scores"]["error_rate"] = error_rate_score
        
        # Calculate overall score (phi-harmonized)
        metric_values = list(evaluation["metric_scores"].values())
        evaluation["overall_score"] = np.mean(metric_values) * PHI
        
        return evaluation


# =============================================================================
# 2. MINING PITFALLS — Common Failure Patterns to Avoid
# =============================================================================

class PitfallCategory(Enum):
    """Categories of mining pitfalls."""
    
    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    POOL = "pool"
    CONFIGURATION = "configuration"
    ENVIRONMENTAL = "environmental"
    SECURITY = "security"


@dataclass
class MiningPitfall:
    """Definition of a mining pitfall and how to avoid it."""
    
    name: str
    category: PitfallCategory
    description: str
    symptoms: List[str]
    causes: List[str]
    prevention_strategies: List[str]
    recovery_actions: List[str]
    severity: str  # "low", "medium", "high", "critical"
    frequency: str  # "rare", "occasional", "common", "frequent"


class MiningPitfallsKnowledge:
    """Knowledge base of common mining pitfalls."""
    
    def __init__(self):
        self.pitfalls: List[MiningPitfall] = self._initialize_pitfalls()
    
    def _initialize_pitfalls(self) -> List[MiningPitfall]:
        """Initialize common mining pitfalls."""
        return [
            MiningPitfall(
                name="thermal_throttling",
                category=PitfallCategory.HARDWARE,
                description="GPU/CPU thermal throttling reducing performance",
                symptoms=["Sudden hashrate drop", "High temperature readings", "Fan noise increase"],
                causes=["Insufficient cooling", "Dust buildup", "Overclocking", "High ambient temperature"],
                prevention_strategies=[
                    "Monitor temperature continuously",
                    "Maintain proper airflow",
                    "Clean dust regularly",
                    "Avoid aggressive overclocking",
                    "Use thermal paste properly"
                ],
                recovery_actions=[
                    "Reduce intensity immediately",
                    "Improve cooling",
                    "Clean hardware",
                    "Reset overclocking settings"
                ],
                severity="high",
                frequency="common"
            ),
            MiningPitfall(
                name="pool_connection_timeout",
                category=PitfallCategory.NETWORK,
                description="Stratum pool connection timeouts and disconnections",
                symptoms=["Frequent disconnections", "Share submission failures", "Connection timeout errors"],
                causes=["Network instability", "Pool server issues", "Firewall blocking", "DNS resolution problems"],
                prevention_strategies=[
                    "Use multiple backup pools",
                    "Configure proper timeouts",
                    "Monitor network latency",
                    "Use reliable DNS servers",
                    "Configure firewall rules"
                ],
                recovery_actions=[
                    "Switch to backup pool",
                    "Increase timeout values",
                    "Check network connectivity",
                    "Restart network interface"
                ],
                severity="medium",
                frequency="common"
            ),
            MiningPitfall(
                name="stale_shares",
                category=PitfallCategory.POOL,
                description="High rate of stale shares being rejected by pool",
                symptoms=["High stale share rate", "Low acceptance rate", "Share rejection messages"],
                causes=["Network latency", "Pool difficulty too high", "Slow hardware", "Clock drift"],
                prevention_strategies=[
                    "Monitor network latency",
                    "Choose appropriate pool",
                    "Synchronize system clock",
                    "Optimize hardware performance",
                    "Use local stratum proxy"
                ],
                recovery_actions=[
                    "Switch to lower difficulty pool",
                    "Improve network connection",
                    "Synchronize clock",
                    "Reduce nonce range"
                ],
                severity="medium",
                frequency="occasional"
            ),
            MiningPitfall(
                name="memory_exhaustion",
                category=PitfallCategory.HARDWARE,
                description="System memory exhaustion causing crashes",
                symptoms=["System slowdown", "Process crashes", "High memory usage", "Swap activity"],
                causes=["Memory leak", "Insufficient RAM", "Large dataset processing", "Too many threads"],
                prevention_strategies=[
                    "Monitor memory usage",
                    "Limit thread count",
                    "Use memory-efficient algorithms",
                    "Add more RAM",
                    "Implement memory limits"
                ],
                recovery_actions=[
                    "Reduce thread count",
                    "Restart mining process",
                    "Clear cache",
                    "Kill memory-intensive processes"
                ],
                severity="high",
                frequency="occasional"
            ),
            MiningPitfall(
                name="configuration_drift",
                category=PitfallCategory.CONFIGURATION,
                description="Configuration parameters drifting from optimal values",
                symptoms=["Gradual performance decline", "Unexpected parameter changes", "Suboptimal settings"],
                causes=["Manual changes", "AI over-optimization", "Software updates", "Configuration corruption"],
                prevention_strategies=[
                    "Version control configuration",
                    "Monitor parameter changes",
                    "Validate configuration regularly",
                    "Use configuration management",
                    "Document all changes"
                ],
                recovery_actions=[
                    "Restore known good configuration",
                    "Reset to defaults",
                    "Review change history",
                    "Re-optimize parameters"
                ],
                severity="medium",
                frequency="common"
            ),
            MiningPitfall(
                name="pool_fee_changes",
                category=PitfallCategory.POOL,
                description="Unexpected pool fee changes affecting profitability",
                symptoms=["Reduced payouts", "Fee structure changes", "Profitability decline"],
                causes=["Pool policy changes", "Hidden fees", "Variable fee structures", "Promotional period end"],
                prevention_strategies=[
                    "Monitor pool announcements",
                    "Review fee structures regularly",
                    "Use multiple pools",
                    "Calculate expected payouts",
                    "Track payout history"
                ],
                recovery_actions=[
                    "Switch to different pool",
                    "Negotiate with pool operator",
                    "Adjust profitability expectations",
                    "Review pool terms"
                ],
                severity="low",
                frequency="occasional"
            ),
            MiningPitfall(
                name="hardware_degradation",
                category=PitfallCategory.HARDWARE,
                description="Gradual hardware performance degradation over time",
                symptoms=["Slow hashrate decline", "Increasing error rates", "Higher temperatures", "Fan noise increase"],
                causes=["Component aging", "Dust accumulation", "Thermal paste degradation", "Voltage fluctuations"],
                prevention_strategies=[
                    "Regular maintenance",
                    "Monitor performance trends",
                    "Control temperature",
                    "Use quality power supply",
                    "Replace components proactively"
                ],
                recovery_actions=[
                    "Clean hardware",
                    "Replace thermal paste",
                    "Underclock components",
                    "Replace degraded components",
                    "Upgrade hardware"
                ],
                severity="medium",
                frequency="common"
            ),
            MiningPitfall(
                name="share_submission_race_condition",
                category=PitfallCategory.SOFTWARE,
                description="Race conditions in share submission causing duplicates or misses",
                symptoms=["Duplicate shares", "Missed shares", "Submission timing issues", "Inconsistent results"],
                causes=["Concurrent submission", "Lack of synchronization", "Timing bugs", "Network delays"],
                prevention_strategies=[
                    "Implement proper synchronization",
                    "Use submission queue",
                    "Add duplicate detection",
                    "Test under load",
                    "Monitor submission timing"
                ],
                recovery_actions=[
                    "Restart submission process",
                    "Clear duplicate queue",
                    "Implement locking",
                    "Review submission logic"
                ],
                severity="medium",
                frequency="rare"
            )
        ]
    
    def get_pitfalls_by_category(self, category: PitfallCategory) -> List[MiningPitfall]:
        """Get pitfalls filtered by category."""
        return [p for p in self.pitfalls if p.category == category]
    
    def get_pitfalls_by_severity(self, severity: str) -> List[MiningPitfall]:
        """Get pitfalls filtered by severity."""
        return [p for p in self.pitfalls if p.severity == severity]
    
    def check_for_pitfall_indicators(self, metrics: Dict[str, float]) -> List[MiningPitfall]:
        """Check current metrics for pitfall indicators."""
        indicators = []
        
        # Check for thermal throttling
        temperature = metrics.get("temperature", 50.0)
        if temperature > 75:
            indicators.extend(self.get_pitfalls_by_category(PitfallCategory.HARDWARE))
        
        # Check for high error rates
        error_rate = metrics.get("error_rate", 0.0)
        if error_rate > 0.05:
            indicators.extend(self.get_pitfalls_by_category(PitfallCategory.NETWORK))
            indicators.extend(self.get_pitfalls_by_category(PitfallCategory.POOL))
        
        # Check for low hashrate
        hashrate = metrics.get("hashrate", 100.0)
        if hashrate < 30:
            indicators.extend(self.get_pitfalls_by_category(PitfallCategory.HARDWARE))
            indicators.extend(self.get_pitfalls_by_category(PitfallCategory.CONFIGURATION))
        
        return indicators


# =============================================================================
# 3. RULES OF THE GAME — Protocol Constraints and Mining Rules
# =============================================================================

class MiningRule(Enum):
    """Mining protocol rules and constraints."""
    
    SHARE_VALIDATION = "share_validation"
    DIFFICULTY_ADJUSTMENT = "difficulty_adjustment"
    NONCE_UNIQUENESS = "nonce_uniqueness"
    BLOCK_REWARD_RULES = "block_reward_rules"
    POOL_PROTOCOL = "pool_protocol"
    STRATUM_COMPLIANCE = "stratum_compliance"
    SHARE_TIMING = "share_timing"
    AUTHENTICATION = "authentication"


@dataclass
class MiningRuleDefinition:
    """Definition of a mining rule and its constraints."""
    
    rule: MiningRule
    description: str
    constraints: List[str]
    validation_method: str
    penalty_for_violation: str
    compliance_level: str  # "mandatory", "recommended", "optional"


class MiningRulesKnowledge:
    """Knowledge base of mining rules and protocol constraints."""
    
    def __init__(self):
        self.rules: List[MiningRuleDefinition] = self._initialize_rules()
    
    def _initialize_rules(self) -> List[MiningRuleDefinition]:
        """Initialize mining rules."""
        return [
            MiningRuleDefinition(
                rule=MiningRule.SHARE_VALIDATION,
                description="Shares must meet pool difficulty requirements",
                constraints=[
                    "Share hash must be less than target difficulty",
                    "Share must be from valid nonce range",
                    "Share must be submitted within time window",
                    "Share must pass pool-specific validation"
                ],
                validation_method="hash_comparison",
                penalty_for_violation="share_rejection",
                compliance_level="mandatory"
            ),
            MiningRuleDefinition(
                rule=MiningRule.DIFFICULTY_ADJUSTMENT,
                description="Mining difficulty adjusts based on network conditions",
                constraints=[
                    "Difficulty adjusts every 2016 blocks (Bitcoin)",
                    "Difficulty targets 10-minute block time",
                    "Minimum difficulty adjustment is 0.25x",
                    "Maximum difficulty adjustment is 4x"
                ],
                validation_method="network_consensus",
                penalty_for_violation="orphaned_blocks",
                compliance_level="mandatory"
            ),
            MiningRuleDefinition(
                rule=MiningRule.NONCE_UNIQUENESS,
                description="Nonces must be unique within valid range",
                constraints=[
                    "Nonce must be in range [0, 2^32)",
                    "Same nonce cannot be used for same block header",
                    "Nonce exhaustion requires extra nonce",
                    "Nonce must be incremented properly"
                ],
                validation_method="uniqueness_check",
                penalty_for_violation="invalid_share",
                compliance_level="mandatory"
            ),
            MiningRuleDefinition(
                rule=MiningRule.POOL_PROTOCOL,
                description="Must follow pool communication protocol",
                constraints=[
                    "Use stratum protocol version 1 or 2",
                    "Authenticate with worker credentials",
                    "Subscribe to mining notifications",
                    "Submit shares in correct format",
                    "Handle pool messages appropriately"
                ],
                validation_method="protocol_compliance",
                penalty_for_violation="disconnection",
                compliance_level="mandatory"
            ),
            MiningRuleDefinition(
                rule=MiningRule.SHARE_TIMING,
                description="Shares must be submitted within reasonable time",
                constraints=[
                    "Submit shares within block time window",
                    "Avoid stale submissions",
                    "Respect pool's share submission rate limits",
                    "Handle network delays appropriately"
                ],
                validation_method="timestamp_validation",
                penalty_for_violation="stale_share",
                compliance_level="recommended"
            ),
            MiningRuleDefinition(
                rule=MiningRule.AUTHENTICATION,
                description="Must authenticate with pool using valid credentials",
                constraints=[
                    "Use valid worker name and password",
                    "Keep credentials secure",
                    "Re-authenticate on connection loss",
                    "Use TLS when available"
                ],
                validation_method="credential_check",
                penalty_for_violation="access_denied",
                compliance_level="mandatory"
            )
        ]
    
    def get_mandatory_rules(self) -> List[MiningRuleDefinition]:
        """Get mandatory compliance rules."""
        return [r for r in self.rules if r.compliance_level == "mandatory"]
    
    def validate_against_rules(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an operation against mining rules."""
        validation_result = {
            "compliant": True,
            "violations": [],
            "warnings": []
        }
        
        # Rule validation logic would go here
        # For now, return compliant as placeholder
        
        return validation_result


# =============================================================================
# 4. OPERATIONAL EXPECTATIONS — Performance Thresholds and Targets
# =============================================================================

class OperationalThreshold(Enum):
    """Operational performance thresholds."""
    
    HASHRATE_THRESHOLD = "hashrate_threshold"
    TEMPERATURE_THRESHOLD = "temperature_threshold"
    ERROR_RATE_THRESHOLD = "error_rate_threshold"
    UPTIME_THRESHOLD = "uptime_threshold"
    LATENCY_THRESHOLD = "latency_threshold"
    POWER_THRESHOLD = "power_threshold"


@dataclass
class OperationalExpectation:
    """Definition of operational expectations and thresholds."""
    
    threshold: OperationalThreshold
    min_value: float
    target_value: float
    max_value: float
    warning_threshold: float
    critical_threshold: float
    unit: str
    description: str
    higher_is_better: bool = False  # If True, higher values are better (e.g., hashrate, uptime)


class OperationalExpectationsKnowledge:
    """Knowledge base of operational expectations."""
    
    def __init__(self):
        self.expectations: List[OperationalExpectation] = self._initialize_expectations()
    
    def _initialize_expectations(self) -> List[OperationalExpectation]:
        """Initialize operational expectations."""
        return [
            OperationalExpectation(
                threshold=OperationalThreshold.HASHRATE_THRESHOLD,
                min_value=10.0,
                target_value=100.0,
                max_value=200.0,
                warning_threshold=50.0,
                critical_threshold=25.0,
                unit="H/s",
                description="Expected hashrate performance range",
                higher_is_better=True
            ),
            OperationalExpectation(
                threshold=OperationalThreshold.TEMPERATURE_THRESHOLD,
                min_value=20.0,
                target_value=50.0,
                max_value=80.0,
                warning_threshold=70.0,
                critical_threshold=85.0,
                unit="°C",
                description="Safe operating temperature range",
                higher_is_better=False
            ),
            OperationalExpectation(
                threshold=OperationalThreshold.ERROR_RATE_THRESHOLD,
                min_value=0.0,
                target_value=0.1,
                max_value=5.0,
                warning_threshold=1.0,
                critical_threshold=3.0,
                unit="%",
                description="Acceptable error rate threshold",
                higher_is_better=False
            ),
            OperationalExpectation(
                threshold=OperationalThreshold.UPTIME_THRESHOLD,
                min_value=90.0,
                target_value=99.9,
                max_value=100.0,
                warning_threshold=95.0,
                critical_threshold=90.0,
                unit="%",
                description="Expected system uptime percentage",
                higher_is_better=True
            ),
            OperationalExpectation(
                threshold=OperationalThreshold.LATENCY_THRESHOLD,
                min_value=0.0,
                target_value=50.0,
                max_value=500.0,
                warning_threshold=200.0,
                critical_threshold=400.0,
                unit="ms",
                description="Network latency to pool",
                higher_is_better=False
            ),
            OperationalExpectation(
                threshold=OperationalThreshold.POWER_THRESHOLD,
                min_value=50.0,
                target_value=200.0,
                max_value=500.0,
                warning_threshold=400.0,
                critical_threshold=450.0,
                unit="W",
                description="Power consumption range",
                higher_is_better=False
            )
        ]
    
    def check_thresholds(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Check current metrics against operational thresholds."""
        threshold_status = {
            "within_limits": True,
            "warnings": [],
            "critical_alerts": [],
            "threshold_violations": []
        }
        
        for expectation in self.expectations:
            # Skip if metric is not provided (not in dict)
            if expectation.threshold.value not in metrics:
                continue
            
            metric_value = metrics[expectation.threshold.value]
            
            if expectation.higher_is_better:
                # For metrics where higher is better (hashrate, uptime), check if too LOW
                if metric_value < expectation.critical_threshold:
                    threshold_status["critical_alerts"].append({
                        "threshold": expectation.threshold.value,
                        "value": metric_value,
                        "critical_threshold": expectation.critical_threshold,
                        "unit": expectation.unit
                    })
                    threshold_status["within_limits"] = False
                elif metric_value < expectation.warning_threshold:
                    threshold_status["warnings"].append({
                        "threshold": expectation.threshold.value,
                        "value": metric_value,
                        "warning_threshold": expectation.warning_threshold,
                        "unit": expectation.unit
                    })
            else:
                # For metrics where lower is better (temperature, error rate, latency, power), check if too HIGH
                if metric_value > expectation.critical_threshold:
                    threshold_status["critical_alerts"].append({
                        "threshold": expectation.threshold.value,
                        "value": metric_value,
                        "critical_threshold": expectation.critical_threshold,
                        "unit": expectation.unit
                    })
                    threshold_status["within_limits"] = False
                elif metric_value > expectation.warning_threshold:
                    threshold_status["warnings"].append({
                        "threshold": expectation.threshold.value,
                        "value": metric_value,
                        "warning_threshold": expectation.warning_threshold,
                        "unit": expectation.unit
                    })
            
            # Check min value violation (for all metrics)
            if metric_value < expectation.min_value:
                threshold_status["threshold_violations"].append({
                    "threshold": expectation.threshold.value,
                    "value": metric_value,
                    "min_value": expectation.min_value,
                    "unit": expectation.unit
                })
                threshold_status["within_limits"] = False
        
        return threshold_status


# =============================================================================
# 5. UNIFIED KNOWLEDGE BASE
# =============================================================================

class MiningKnowledgeBase:
    """
    Unified knowledge base for AI decision-making.
    
    This consolidates all domain knowledge into a single interface
    that the AI orchestration layer can reference for informed
    decision-making.
    """
    
    def __init__(self):
        self.success_criteria = SuccessCriteria()
        self.pitfalls = MiningPitfallsKnowledge()
        self.rules = MiningRulesKnowledge()
        self.expectations = OperationalExpectationsKnowledge()
    
    def evaluate_current_state(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate current state against all knowledge bases."""
        evaluation = {
            "success_evaluation": self.success_criteria.evaluate_success(metrics),
            "pitfall_indicators": self.pitfalls.check_for_pitfall_indicators(metrics),
            "threshold_status": self.expectations.check_thresholds(metrics),
            "overall_assessment": self._generate_overall_assessment(metrics)
        }
        return evaluation
    
    def _generate_overall_assessment(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Generate overall assessment from all knowledge bases."""
        success_eval = self.success_criteria.evaluate_success(metrics)
        threshold_status = self.expectations.check_thresholds(metrics)
        pitfall_indicators = self.pitfalls.check_for_pitfall_indicators(metrics)
        
        assessment = {
            "status": "healthy",
            "confidence": success_eval["overall_score"],
            "priority_actions": [],
            "risk_level": "low"
        }
        
        # Determine risk level based on critical alerts
        if threshold_status["critical_alerts"]:
            assessment["status"] = "critical"
            assessment["risk_level"] = "critical"
            assessment["priority_actions"].extend([
                f"CRITICAL: {alert['threshold']} at {alert['value']}{alert['unit']} exceeds critical threshold {alert['critical_threshold']}{alert['unit']}"
                for alert in threshold_status["critical_alerts"]
            ])
        elif threshold_status["warnings"]:
            assessment["status"] = "warning"
            assessment["risk_level"] = "medium"
            assessment["priority_actions"].extend([
                f"WARNING: {alert['threshold']} at {alert['value']}{alert['unit']} exceeds warning threshold {alert['warning_threshold']}{alert['unit']}"
                for alert in threshold_status["warnings"]
            ])
        
        # Add pitfall recommendations
        if pitfall_indicators:
            assessment["priority_actions"].extend([
                f"PITFALL RISK: {pitfall.name} - {pitfall.description}"
                for pitfall in pitfall_indicators
            ])
        
        # Add success criteria recommendations
        assessment["priority_actions"].extend(success_eval["recommendations"])
        
        return assessment
    
    def get_success_criteria(self) -> SuccessCriteria:
        """Get success criteria for reference."""
        return self.success_criteria
    
    def get_pitfalls(self) -> List[MiningPitfall]:
        """Get all known pitfalls for reference."""
        return self.pitfalls.pitfalls
    
    def get_rules(self) -> List[MiningRuleDefinition]:
        """Get all mining rules for reference."""
        return self.rules.rules
    
    def get_expectations(self) -> List[OperationalExpectation]:
        """Get all operational expectations for reference."""
        return self.expectations.expectations


__all__ = [
    "MiningKnowledgeBase",
    "SuccessCriteria",
    "MiningPitfallsKnowledge",
    "MiningRulesKnowledge",
    "OperationalExpectationsKnowledge",
    "SuccessMetric",
    "PitfallCategory",
    "MiningPitfall",
    "MiningRule",
    "MiningRuleDefinition",
    "OperationalThreshold",
    "OperationalExpectation",
]
