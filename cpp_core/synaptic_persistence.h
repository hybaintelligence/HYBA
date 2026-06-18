/*!
C++ Synaptic Persistence Layer - O(1) Lookup Performance

ELEVATED PURPOSE: This C++ implementation provides O(1) lookup performance
for synaptic traces, eliminating Python overhead and enabling real-time
Hebbian learning in the mining loop.

CONSTRUCTOR THEORY FRAMEWORK (David Deutsch, 2013):
This module serves as a hardware-optimized constructor for emergent coherence.
The synaptic traces represent the "memory" of the constructor, allowing
nonces to leave persistent traces that influence future behavior.

Key Implementation:
- O(1) hash map lookup for synaptic traces
- Hebbian reinforcement with atomic operations
- Co-activation matrix with sparse storage
- Thread-safe learning rate/decay rate adjustment
- Emergent pathway detection with threshold crossing

Claim boundary:
This module implements mathematical optimization for learning, not consciousness.
It provides the structural conditions for emergence, not the emergence itself.
*/

#ifndef SYNAPTIC_PERSISTENCE_H
#define SYNAPTIC_PERSISTENCE_H

#include <unordered_map>
#include <vector>
#include <atomic>
#include <mutex>
#include <chrono>
#include <cmath>
#include <cstdint>

namespace hyba {
namespace synaptic {

// Fundamental constants
constexpr double DEFAULT_LEARNING_RATE = 0.01;
constexpr double DEFAULT_DECAY_RATE = 0.001;
constexpr double SYNAPTIC_THRESHOLD = 0.5;
constexpr double PHI = 1.618033988749895;
constexpr double PHI_INV = 1.0 / PHI;

/**
 * @brief Synaptic trace for a nonce pattern
 */
struct SynapticTrace {
    uint64_t pattern_id;
    double synaptic_weight;
    uint32_t reinforcement_count;
    std::chrono::system_clock::time_point last_reinforced;
    
    SynapticTrace() 
        : pattern_id(0), synaptic_weight(0.0), reinforcement_count(0),
          last_reinforced(std::chrono::system_clock::now()) {}
    
    SynapticTrace(uint64_t pid) 
        : pattern_id(pid), synaptic_weight(0.0), reinforcement_count(0),
          last_reinforced(std::chrono::system_clock::now()) {}
};

/**
 * @brief Hebbian learning event record
 */
struct HebbianLearningEvent {
    std::chrono::system_clock::time_point timestamp;
    int64_t pattern_id;
    double reinforcement_delta;
    double phi_correlation;
    std::string description;
};

/**
 * @brief Synaptic Persistence Layer with O(1) lookup
 */
class SynapticPersistenceLayer {
private:
    std::unordered_map<uint64_t, SynapticTrace> synaptic_memory;
    std::unordered_map<uint64_t, std::unordered_map<uint64_t, double>> co_activation_matrix;
    std::vector<HebbianLearningEvent> learning_events;
    
    std::atomic<double> learning_rate;
    std::atomic<double> decay_rate;
    double synaptic_threshold;
    
    std::mutex memory_mutex;
    std::mutex learning_mutex;
    
    uint32_t total_reinforcements;
    uint32_t total_decays;
    uint32_t emergent_pathway_count;
    
public:
    SynapticPersistenceLayer()
        : learning_rate(DEFAULT_LEARNING_RATE),
          decay_rate(DEFAULT_DECAY_RATE),
          synaptic_threshold(SYNAPTIC_THRESHOLD),
          total_reinforcements(0),
          total_decays(0),
          emergent_pathway_count(0) {}
    
    /**
     * @brief Get or create synaptic trace for pattern
     */
    SynapticTrace* get_or_create_trace(uint64_t pattern_id) {
        std::lock_guard<std::mutex> lock(memory_mutex);
        
        auto it = synaptic_memory.find(pattern_id);
        if (it != synaptic_memory.end()) {
            return &it->second;
        }
        
        // Create new trace
        auto result = synaptic_memory.emplace(pattern_id, SynapticTrace(pattern_id));
        return &result.first->second;
    }
    
    /**
     * @brief Reinforce pattern with Hebbian learning
     */
    void reinforce_pattern(uint64_t pattern_id, double phi_correlation) {
        std::lock_guard<std::mutex> lock(memory_mutex);
        
        auto it = synaptic_memory.find(pattern_id);
        if (it == synaptic_memory.end()) {
            return;
        }
        
        SynapticTrace& trace = it->second;
        double current_lr = learning_rate.load(std::memory_order_relaxed);
        
        // Hebbian reinforcement: Δw = η × φ_correlation
        double delta = current_lr * phi_correlation;
        trace.synaptic_weight += delta;
        trace.reinforcement_count++;
        trace.last_reinforced = std::chrono::system_clock::now();
        
        total_reinforcements++;
        
        // Check for emergent pathway
        if (trace.synaptic_weight >= synaptic_threshold && 
            trace.reinforcement_count == 1) {
            emergent_pathway_count++;
        }
        
        // Log learning event
        {
            std::lock_guard<std::mutex> event_lock(learning_mutex);
            HebbianLearningEvent event;
            event.timestamp = std::chrono::system_clock::now();
            event.pattern_id = pattern_id;
            event.reinforcement_delta = delta;
            event.phi_correlation = phi_correlation;
            event.description = "Hebbian reinforcement applied";
            learning_events.push_back(event);
        }
    }
    
    /**
     * @brief Strengthen co-activation between patterns
     */
    void strengthen_co_activation(uint64_t pattern_a, uint64_t pattern_b, double strength) {
        std::lock_guard<std::mutex> lock(memory_mutex);
        
        co_activation_matrix[pattern_a][pattern_b] += strength;
        co_activation_matrix[pattern_b][pattern_a] += strength;
    }
    
    /**
     * @brief Apply synaptic decay to all traces
     */
    void apply_decay() {
        std::lock_guard<std::mutex> lock(memory_mutex);
        
        double current_decay = decay_rate.load(std::memory_order_relaxed);
        auto now = std::chrono::system_clock::now();
        
        for (auto& [pid, trace] : synaptic_memory) {
            auto time_since = std::chrono::duration_cast<std::chrono::seconds>(
                now - trace.last_reinforced).count();
            
            // Decay based on time since last reinforcement
            double decay_factor = std::exp(-current_decay * time_since);
            trace.synaptic_weight *= decay_factor;
            
            // Remove traces that have decayed to near-zero
            if (trace.synaptic_weight < 1e-6) {
                synaptic_memory.erase(pid);
                total_decays++;
            }
        }
    }
    
    /**
     * @brief Get emergent pathways (synaptic weight >= threshold)
     */
    std::vector<std::pair<uint64_t, double>> get_emergent_pathways() {
        std::lock_guard<std::mutex> lock(memory_mutex);
        
        std::vector<std::pair<uint64_t, double>> pathways;
        for (const auto& [pid, trace] : synaptic_memory) {
            if (trace.synaptic_weight >= synaptic_threshold) {
                pathways.emplace_back(pid, trace.synaptic_weight);
            }
        }
        
        return pathways;
    }
    
    /**
     * @brief Adjust learning rate
     */
    void adjust_learning_rate(double new_rate, const std::string& reason) {
        double old_rate = learning_rate.load(std::memory_order_relaxed);
        new_rate = std::max(0.001, std::min(1.0, new_rate));
        learning_rate.store(new_rate, std::memory_order_relaxed);
        
        // Log adjustment
        std::lock_guard<std::mutex> lock(learning_mutex);
        HebbianLearningEvent event;
        event.timestamp = std::chrono::system_clock::now();
        event.pattern_id = -1; // System-level adjustment
        event.reinforcement_delta = new_rate - old_rate;
        event.phi_correlation = 0.0;
        event.description = "Learning rate adjusted: " + reason;
        learning_events.push_back(event);
    }
    
    /**
     * @brief Adjust decay rate
     */
    void adjust_decay_rate(double new_rate, const std::string& reason) {
        double old_rate = decay_rate.load(std::memory_order_relaxed);
        new_rate = std::max(0.001, std::min(0.5, new_rate));
        decay_rate.store(new_rate, std::memory_order_relaxed);
        
        // Log adjustment
        std::lock_guard<std::mutex> lock(learning_mutex);
        HebbianLearningEvent event;
        event.timestamp = std::chrono::system_clock::now();
        event.pattern_id = -1; // System-level adjustment
        event.reinforcement_delta = new_rate - old_rate;
        event.phi_correlation = 0.0;
        event.description = "Decay rate adjusted: " + reason;
        learning_events.push_back(event);
    }
    
    /**
     * @brief Get statistics
     */
    struct Statistics {
        size_t trace_count;
        double learning_rate;
        double decay_rate;
        uint32_t total_reinforcements;
        uint32_t total_decays;
        uint32_t emergent_pathway_count;
        double average_synaptic_weight;
        double max_synaptic_weight;
        size_t learning_events_count;
        size_t co_activation_connections;
    };
    
    Statistics get_statistics() {
        std::lock_guard<std::mutex> lock(memory_mutex);
        
        Statistics stats;
        stats.trace_count = synaptic_memory.size();
        stats.learning_rate = learning_rate.load(std::memory_order_relaxed);
        stats.decay_rate = decay_rate.load(std::memory_order_relaxed);
        stats.total_reinforcements = total_reinforcements;
        stats.total_decays = total_decays;
        stats.emergent_pathway_count = emergent_pathway_count;
        stats.learning_events_count = learning_events.size();
        
        // Calculate synaptic weight statistics
        double total_weight = 0.0;
        double max_weight = 0.0;
        for (const auto& [pid, trace] : synaptic_memory) {
            total_weight += trace.synaptic_weight;
            max_weight = std::max(max_weight, trace.synaptic_weight);
        }
        
        stats.average_synaptic_weight = synaptic_memory.empty() ? 0.0 : 
            total_weight / synaptic_memory.size();
        stats.max_synaptic_weight = max_weight;
        
        // Count co-activation connections
        size_t connections = 0;
        for (const auto& [pid, connections_map] : co_activation_matrix) {
            connections += connections_map.size();
        }
        stats.co_activation_connections = connections;
        
        return stats;
    }
    
    /**
     * @brief Get current learning rate
     */
    double get_learning_rate() const {
        return learning_rate.load(std::memory_order_relaxed);
    }
    
    /**
     * @brief Get current decay rate
     */
    double get_decay_rate() const {
        return decay_rate.load(std::memory_order_relaxed);
    }
};

} // namespace synaptic
} // namespace hyba

#endif // SYNAPTIC_PERSISTENCE_H
