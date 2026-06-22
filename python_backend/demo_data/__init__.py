"""HYBA Demo Data Package.

This package provides data acquisition, POST-QUANTUM processing, and demo execution
for HYBA POST-QUANTUM demonstrations across all target audiences (JPMorgan, FAB, Aramco, DIFC).
"""

from demo_data.data_acquisition import (
    acquire_jpmorgan_data,
    acquire_fab_data_rabobank,
    acquire_aramco_seismic_data,
    acquire_difc_regulatory_data,
    acquire_all_demo_data,
)

from demo_data.post_quantum_processing import (
    process_with_pulvini,
    allocate_with_phimalloc,
    process_with_salamander,
    process_with_post_quantum,
    demonstrate_post_quantum_advantages,
)

from demo_data.demo_execution import (
    run_jpmorgan_demo,
    run_fab_demo,
    run_aramco_demo,
    run_difc_demo,
    run_all_demos,
)

__all__ = [
    # Data acquisition
    'acquire_jpmorgan_data',
    'acquire_fab_data_rabobank',
    'acquire_aramco_seismic_data',
    'acquire_difc_regulatory_data',
    'acquire_all_demo_data',
    # POST-QUANTUM processing
    'process_with_pulvini',
    'allocate_with_phimalloc',
    'process_with_salamander',
    'process_with_post_quantum',
    'demonstrate_post_quantum_advantages',
    # Demo execution
    'run_jpmorgan_demo',
    'run_fab_demo',
    'run_aramco_demo',
    'run_difc_demo',
    'run_all_demos',
]

__version__ = '1.0.0'
