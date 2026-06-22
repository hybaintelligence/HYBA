"""Demo Data Acquisition Module.

This module provides functions to acquire free data sources for HYBA POST-QUANTUM
demonstrations across all target audiences (JPMorgan, FAB, Aramco, DIFC).
"""

import sys
import os
import requests
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import io

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine
from pythia_mining.phi_malloc import PhiMalloc
from pythia_mining.salamander_frontier import SalamanderOrchestrator


def acquire_jpmorgan_data(
    symbol: str = "AAPL",
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """
    Acquire financial data from Alpha Vantage for JPMorgan demo.
    
    Args:
        symbol: Stock symbol (default: AAPL)
        api_key: Alpha Vantage API key (required)
    
    Returns:
        DataFrame with daily financial data
    
    Note:
        Get free API key at https://www.alphavantage.co/support/#api-key
    """
    if api_key is None:
        raise ValueError("Alpha Vantage API key is required")
    
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if 'Time Series (Daily)' not in data:
        raise ValueError(f"Error fetching data: {data.get('Error Message', 'Unknown error')}")
    
    df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.astype(float)
    
    return df


def acquire_fab_data_rabobank(
    gt_network_path: Optional[str] = None,
    gn_network_path: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Acquire banking data from RaboBank dataset for FAB demo.
    
    Args:
        gt_network_path: Path to GT Network CSV file
        gn_network_path: Path to GN Network CSV file
    
    Returns:
        Tuple of (GT Network DataFrame, GN Network DataFrame)
    
    Note:
        Download from: https://drive.google.com/drive/folders/1D2nHBcCLiuNwN7c-BA6FjbHIHs5b28mH
    """
    if gt_network_path is None or gn_network_path is None:
        # Generate synthetic banking data for demo
        print("Warning: No RaboBank data paths provided, generating synthetic data")
        n_accounts = 1000
        n_transactions = 5000
        
        # GT Network (total money transferred)
        gt_network = pd.DataFrame({
            'from_account': np.random.randint(0, n_accounts, n_transactions),
            'to_account': np.random.randint(0, n_accounts, n_transactions),
            'total_amount': np.random.exponential(1000, n_transactions),
        })
        
        # GN Network (transaction count)
        gn_network = pd.DataFrame({
            'from_account': np.random.randint(0, n_accounts, n_transactions),
            'to_account': np.random.randint(0, n_accounts, n_transactions),
            'transaction_count': np.random.randint(1, 10, n_transactions),
        })
        
        return gt_network, gn_network
    
    gt_network = pd.read_csv(gt_network_path)
    gn_network = pd.read_csv(gn_network_path)
    
    return gt_network, gn_network


def acquire_aramco_seismic_data(
    file_path: Optional[str] = None,
    shape: tuple = (1000, 1000),
) -> np.ndarray:
    """
    Acquire seismic data for Aramco demo.
    
    Args:
        file_path: Path to seismic data file (SEG-Y or numpy format)
        shape: Shape of synthetic data if no file provided
    
    Returns:
        NumPy array with seismic data
    
    Note:
        Real seismic data available from:
        - SEG Wiki: https://wiki.seg.org/wiki/Open_data
        - BOEM: https://www.boem.gov/oil-gas-energy/resource-evaluation/geological-geophysical-gg-data
    """
    if file_path is None:
        # Generate synthetic seismic data for demo
        print("Warning: No seismic data file provided, generating synthetic data")
        data = np.random.randn(*shape).astype(np.float32)
        return data
    
    # Load from file (assuming numpy format for simplicity)
    data = np.load(file_path)
    
    return data


def acquire_difc_regulatory_data(
    limit: int = 100,
) -> pd.DataFrame:
    """
    Acquire regulatory data from indep-rules API for DIFC demo.
    
    Args:
        limit: Number of rules to fetch
    
    Returns:
        DataFrame with regulatory rules
    
    Note:
        API: https://api.ai-analytics.org/api/v1/indep/rules/recent
    """
    url = "https://api.ai-analytics.org/api/v1/indep/rules/recent"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise ValueError(f"Error fetching regulatory data: {response.status_code}")
    
    data = response.json()
    df = pd.DataFrame(data[:limit])
    
    return df


def acquire_all_demo_data(
    alpha_vantage_api_key: Optional[str] = None,
    rabobank_gt_path: Optional[str] = None,
    rabobank_gn_path: Optional[str] = None,
    seismic_data_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Acquire all demo data for all audiences.
    
    Args:
        alpha_vantage_api_key: Alpha Vantage API key for JPMorgan demo
        rabobank_gt_path: Path to RaboBank GT Network file
        rabobank_gn_path: Path to RaboBank GN Network file
        seismic_data_path: Path to seismic data file
    
    Returns:
        Dictionary with all demo data
    """
    data = {}
    
    # JPMorgan data
    try:
        if alpha_vantage_api_key:
            data['jpmorgan'] = acquire_jpmorgan_data(api_key=alpha_vantage_api_key)
            print(f"✓ Acquired JPMorgan data: {len(data['jpmorgan'])} days")
        else:
            print("⊘ Skipping JPMorgan data (no API key provided)")
    except Exception as e:
        print(f"✗ Error acquiring JPMorgan data: {e}")
    
    # FAB data
    try:
        data['fab_gt'], data['fab_gn'] = acquire_fab_data_rabobank(
            gt_network_path=rabobank_gt_path,
            gn_network_path=rabobank_gn_path,
        )
        print(f"✓ Acquired FAB data: {len(data['fab_gt'])} transactions")
    except Exception as e:
        print(f"✗ Error acquiring FAB data: {e}")
    
    # Aramco data
    try:
        data['aramco'] = acquire_aramco_seismic_data(file_path=seismic_data_path)
        print(f"✓ Acquired Aramco data: shape {data['aramco'].shape}")
    except Exception as e:
        print(f"✗ Error acquiring Aramco data: {e}")
    
    # DIFC data
    try:
        data['difc'] = acquire_difc_regulatory_data(limit=100)
        print(f"✓ Acquired DIFC data: {len(data['difc'])} rules")
    except Exception as e:
        print(f"✗ Error acquiring DIFC data: {e}")
    
    return data


if __name__ == "__main__":
    # Test data acquisition
    print("=== HYBA Demo Data Acquisition ===")
    
    data = acquire_all_demo_data()
    
    print("\n=== Summary ===")
    for key, value in data.items():
        if isinstance(value, pd.DataFrame):
            print(f"{key}: {len(value)} rows")
        elif isinstance(value, np.ndarray):
            print(f"{key}: shape {value.shape}")
        elif isinstance(value, tuple):
            print(f"{key}: {len(value[0])} rows (GT), {len(value[1])} rows (GN)")
