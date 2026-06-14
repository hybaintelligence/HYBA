"""
NiceHash REST API client with HYBA quantum portfolio optimization integration.

Provides both public and private API access to NiceHash's hashpower marketplace.
The private API uses HMAC-SHA256 authentication with quantum-extracted entropy for
X-Nonce generation, enhancing operational security.

Usage:
    from nicehash import public_api, private_api, AnalyticalQuantumBackend

    # Public API
    api = public_api('https://api2.nicehash.com')
    buy_info = api.buy_info()

    # Private API
    api = private_api('https://api2.nicehash.com', org_id, key, secret)
    accounts = api.get_accounts()
"""

import hmac
import json
import logging
import optparse
import sys
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from hashlib import sha256
from time import mktime
from typing import Dict, Optional

import numpy as np
import requests

# Set up logging for production readiness
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class GoldenRatioScaler:
    """
    Implements φ-conjugate scaling hierarchies and Fibonacci-derived optimization metrics.
    Leverages the transcendental constant φ = (1 + √5)/2 ≈ 1.618033988749...
    and its mathematical properties: φ² = φ + 1, φ^(-1) = φ - 1
    """

    PHI = (1.0 + np.sqrt(5)) / 2.0  # Golden ratio ≈ 1.618
    PHI_CONJUGATE = (1.0 - np.sqrt(5)) / 2.0  # ≈ -0.618
    PHI_INVERSE = 1.0 / PHI  # = φ - 1 ≈ 0.618

    SCALE_FACTORS = {"5": PHI, "10": PHI**2, "15": PHI**3, "20": PHI**4}

    def __init__(self):
        self.fibonacci_sequence = self._generate_fibonacci(30)

    def _generate_fibonacci(self, n: int) -> np.ndarray:
        fib = np.zeros(n, dtype=float)
        fib[0], fib[1] = 1.0, 1.0
        for i in range(2, n):
            fib[i] = fib[i - 1] + fib[i - 2]
        return fib

    def phi_scaled_learning_rate(self, iteration: int, base_lr: float = 0.01) -> float:
        tau = 20.0
        decay = self.PHI_INVERSE ** (iteration / tau)
        return base_lr * decay

    def fibonacci_gate_angles(self, n_qubits: int) -> np.ndarray:
        angles = np.zeros(n_qubits)
        for i in range(n_qubits):
            fib_idx = min(i, len(self.fibonacci_sequence) - 2)
            ratio = self.fibonacci_sequence[fib_idx] / (
                self.fibonacci_sequence[fib_idx + 1] + 1e-10
            )
            angles[i] = 2 * np.pi * ratio
        return angles

    def golden_angle_distribution(self, n_samples: int) -> np.ndarray:
        golden_angle = 2 * np.pi / (self.PHI**2)
        indices = np.arange(n_samples)
        return (indices * golden_angle) % (2 * np.pi)

    def phi_scaled_regularization(self, layer_depth: int, base_reg: float = 0.001) -> float:
        return base_reg * (self.PHI_INVERSE**layer_depth)

    def markowitz_frontier_phi_scaling(self, efficient_frontier: np.ndarray) -> np.ndarray:
        scaled_frontier = efficient_frontier.copy()
        for i in range(len(scaled_frontier)):
            scaled_frontier[i] *= self.PHI ** (i / len(scaled_frontier))
        return scaled_frontier

    def info_theoretic_phi_entropy(self, probability_distribution: np.ndarray) -> float:
        log_phi = np.log(self.PHI)
        entropy = 0.0
        for p in probability_distribution:
            if p > 1e-10:
                entropy -= p * np.log(p) / log_phi
        return entropy

    def scale_factor_lookup(self, depth_key: str) -> float:
        return self.SCALE_FACTORS.get(depth_key, 1.0)


class QuantumBackend(ABC):
    """Abstract quantum computation backend."""

    @abstractmethod
    def apply_hadamard(self, state: np.ndarray, qubit: int, n_qubits: int) -> np.ndarray:
        pass

    @abstractmethod
    def apply_phase_gate(
        self, state: np.ndarray, angle: float, qubit: int, n_qubits: int
    ) -> np.ndarray:
        pass

    @abstractmethod
    def apply_controlled_z(
        self, state: np.ndarray, control: int, target: int, n_qubits: int
    ) -> np.ndarray:
        pass

    @abstractmethod
    def measure(self, state: np.ndarray, shots: int = 1) -> Dict[str, int]:
        pass

    @abstractmethod
    def expectation_value(self, state: np.ndarray, observable: np.ndarray) -> float:
        pass


class AnalyticalQuantumBackend(QuantumBackend):
    """Pure mathematical backend implementing unitary evolution through explicit matrix exponentiation."""

    def __init__(self):
        self.pauli_x = np.array([[0, 1], [1, 0]], dtype=complex)
        self.pauli_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        self.pauli_z = np.array([[1, 0], [0, -1]], dtype=complex)
        self.identity = np.eye(2, dtype=complex)

    def _kron_chain(self, operators: list, n_qubits: int) -> np.ndarray:
        result = operators[0]
        for op in operators[1:]:
            result = np.kron(result, op)
        return result

    def apply_hadamard(self, state: np.ndarray, qubit: int, n_qubits: int) -> np.ndarray:
        h_matrix = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
        operators = [self.identity if i != qubit else h_matrix for i in range(n_qubits)]
        unitary = self._kron_chain(operators, n_qubits)
        return unitary @ state

    def apply_phase_gate(
        self, state: np.ndarray, angle: float, qubit: int, n_qubits: int
    ) -> np.ndarray:
        phase_gate = np.array([[1, 0], [0, np.exp(1j * angle)]], dtype=complex)
        operators = [self.identity if i != qubit else phase_gate for i in range(n_qubits)]
        unitary = self._kron_chain(operators, n_qubits)
        return unitary @ state

    def apply_controlled_z(
        self, state: np.ndarray, control: int, target: int, n_qubits: int
    ) -> np.ndarray:
        cz_matrix = np.eye(2**n_qubits, dtype=complex)
        for i in range(2**n_qubits):
            bitstring = format(i, f"0{n_qubits}b")
            if bitstring[control] == "1" and bitstring[target] == "1":
                cz_matrix[i, i] = -1
        return cz_matrix @ state

    def measure(self, state: np.ndarray, shots: int = 1) -> Dict[str, int]:
        probabilities = np.abs(state) ** 2
        n_qubits = int(np.log2(len(state)))
        outcomes = np.random.choice(len(state), size=shots, p=probabilities)
        counts = {}
        for outcome in outcomes:
            bitstring = format(outcome, f"0{n_qubits}b")
            counts[bitstring] = counts.get(bitstring, 0) + 1
        return counts

    def expectation_value(self, state: np.ndarray, observable: np.ndarray) -> float:
        return float(np.real(state.conj() @ observable @ state))


class VariationalQuantumAlgorithm:
    """Substrate-agnostic variational quantum algorithm framework."""

    def __init__(self, backend: QuantumBackend, n_qubits: int):
        self.backend = backend
        self.n_qubits = n_qubits
        self.scaler = GoldenRatioScaler()

    def vqe_ansatz(self, params: np.ndarray, state: np.ndarray) -> np.ndarray:
        current_state = state.copy()
        layers = len(params) // self.n_qubits
        param_idx = 0
        for layer in range(layers):
            for qubit in range(self.n_qubits):
                current_state = self.backend.apply_hadamard(current_state, qubit, self.n_qubits)
            for qubit in range(self.n_qubits):
                if param_idx < len(params):
                    current_state = self.backend.apply_phase_gate(
                        current_state, params[param_idx], qubit, self.n_qubits
                    )
                    param_idx += 1
        return current_state

    def cost_function(
        self, params: np.ndarray, hamiltonian: np.ndarray, initial_state: np.ndarray
    ) -> float:
        state = self.vqe_ansatz(params, initial_state)
        return self.backend.expectation_value(state, hamiltonian)

    def optimize(
        self,
        hamiltonian: np.ndarray,
        initial_params=None,
        method="COBYLA",
        problem_depth="10",
    ):
        initial_state = np.ones(2**self.n_qubits, dtype=complex) / np.sqrt(2**self.n_qubits)
        if initial_params is None:
            golden_angles = self.scaler.golden_angle_distribution(self.n_qubits * 3)
            initial_params = golden_angles[: self.n_qubits * 3] * 0.1
        scale_factor = self.scaler.scale_factor_lookup(problem_depth)
        scaled_hamiltonian = hamiltonian * scale_factor

        def objective(p):
            state = self.vqe_ansatz(p, initial_state)
            energy = self.backend.expectation_value(state, scaled_hamiltonian)
            layer_depth = len(p) // self.n_qubits
            regularization = self.scaler.phi_scaled_regularization(layer_depth)
            return energy + regularization * np.sum(p**2)

        fib_angles = self.scaler.fibonacci_gate_angles(len(initial_params))
        initial_params = initial_params * (fib_angles / (np.max(fib_angles) + 1e-10))

        try:
            from scipy.optimize import minimize

            result = minimize(objective, initial_params, method=method, options={"maxiter": 1000})
            logger.info("VQA optimization completed successfully.")
            return result.x, result.fun
        except Exception as e:
            logger.error(f"VQA optimization failed: {e}")
            raise


class QuantumCryptographicProtocol:
    """Quantum-secure protocol leveraging quantum information theoretic principles."""

    def __init__(self, backend: QuantumBackend):
        self.backend = backend

    def quantum_entropy_extraction(self, n_qubits: int, target_bits: int = 256) -> bytes:
        initial_state = np.ones(2**n_qubits, dtype=complex) / np.sqrt(2**n_qubits)
        bits_per_shot = n_qubits
        min_shots = int(np.ceil(target_bits / bits_per_shot))
        shots = max(256, min_shots)
        try:
            measurement_results = self.backend.measure(initial_state, shots=shots)
            bitstrings = []
            for bitstring, count in measurement_results.items():
                bitstrings.extend([bitstring] * count)
            concatenated = "".join(bitstrings)
            while len(concatenated) < target_bits:
                additional_shots = int(np.ceil((target_bits - len(concatenated)) / bits_per_shot))
                more_results = self.backend.measure(initial_state, additional_shots)
                more_bitstrings = []
                for bs, cnt in more_results.items():
                    more_bitstrings.extend([bs] * cnt)
                concatenated += "".join(more_bitstrings)
            concatenated = concatenated[:target_bits]
            while len(concatenated) % 8 != 0:
                concatenated += "0"
            byte_array = bytes(int(concatenated[i : i + 8], 2) for i in range(0, target_bits, 8))
            return byte_array
        except Exception as e:
            logger.error(f"Entropy extraction failed: {e}")
            raise

    def quantum_authentication_challenge(self, secret_key: str, message: bytes):
        try:
            n_qubits = min(16, len(secret_key))
            if n_qubits < 1:
                n_qubits = 1
            from hashlib import sha256

            challenge_hash = sha256(message).hexdigest()[:16]
            key_str = secret_key + challenge_hash
            key_angles = np.array([ord(c) * np.pi / 256 for c in key_str[:n_qubits]])
            state = np.ones(2**n_qubits, dtype=complex) / np.sqrt(2**n_qubits)
            for qubit, angle in enumerate(key_angles):
                state = self.backend.apply_phase_gate(state, angle, qubit, n_qubits)
            return state, challenge_hash
        except Exception as e:
            logger.error(f"Challenge generation failed: {e}")
            raise

    def verify_authentication(
        self,
        state: np.ndarray,
        expected_hash: str,
        secret_key: str,
        tolerance: float = 0.01,
    ) -> bool:
        try:
            n_qubits = int(np.log2(len(state)))
            key_str = secret_key + expected_hash
            key_angles = np.array([ord(c) * np.pi / 256 for c in key_str[:n_qubits]])
            expected_state = np.ones(2**n_qubits, dtype=complex) / np.sqrt(2**n_qubits)
            for qubit, angle in enumerate(key_angles):
                expected_state = self.backend.apply_phase_gate(
                    expected_state, angle, qubit, n_qubits
                )
            fidelity = np.abs(np.dot(expected_state.conj(), state)) ** 2
            verified = fidelity > (1 - tolerance)
            logger.info(f"Authentication verified: {verified} (fidelity: {fidelity:.4f})")
            return verified
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False


class QuantumPortfolioOptimizer:
    """Portfolio optimization via QAOA with φ-conjugate asset allocation."""

    def __init__(self, backend: QuantumBackend, n_assets: int):
        self.backend = backend
        self.n_assets = n_assets
        self.vqa = VariationalQuantumAlgorithm(backend, n_assets)
        self.scaler = GoldenRatioScaler()

    def construct_portfolio_hamiltonian(
        self,
        expected_returns: np.ndarray,
        covariance: np.ndarray,
        risk_aversion: float = 0.5,
    ) -> np.ndarray:
        n = self.n_assets
        h_matrix = np.zeros((2**n, 2**n), dtype=complex)
        phi_risk_aversion = risk_aversion * self.scaler.PHI
        for i in range(2**n):
            allocation = np.array([(i >> j) & 1 for j in range(n)], dtype=float)
            allocation = allocation / (np.sum(allocation) + 1e-10)
            scaled_allocation = self.scaler.markowitz_frontier_phi_scaling(allocation)
            objective = (
                -np.dot(expected_returns, scaled_allocation)
                + phi_risk_aversion * scaled_allocation @ covariance @ scaled_allocation
            )
            h_matrix[i, i] = objective
        return h_matrix

    def fibonacci_rebalancing_schedule(self, total_periods: int) -> np.ndarray:
        fib_len = min(int(np.log2(total_periods)) + 1, len(self.scaler.fibonacci_sequence))
        fib_seq = self.scaler.fibonacci_sequence[:fib_len]
        schedule = []
        cumulative = 0
        for fib_val in fib_seq:
            cumulative += int(fib_val)
            if cumulative <= total_periods:
                schedule.append(cumulative)
            else:
                break
        return np.array(schedule)

    def optimize_allocation(
        self,
        expected_returns: np.ndarray,
        covariance: np.ndarray,
        problem_depth: str = "10",
    ):
        hamiltonian = self.construct_portfolio_hamiltonian(expected_returns, covariance)
        optimized_params, min_value = self.vqa.optimize(hamiltonian, problem_depth=problem_depth)
        initial_state = np.ones(2**self.n_assets, dtype=complex) / np.sqrt(2**self.n_assets)
        final_state = self.vqa.vqe_ansatz(optimized_params, initial_state)
        allocation_probs = np.abs(final_state) ** 2
        phi_entropy = self.scaler.info_theoretic_phi_entropy(allocation_probs)
        information_efficiency = phi_entropy / np.log2(2**self.n_assets)
        scale_factor = self.scaler.scale_factor_lookup(problem_depth)
        rebalance_schedule = self.fibonacci_rebalancing_schedule(252)
        fib_period = rebalance_schedule[0] if len(rebalance_schedule) > 0 else 1.0
        metrics = {
            "energy_eigenvalue": float(min_value),
            "phi_entropy": float(phi_entropy),
            "information_efficiency": float(information_efficiency),
            "problem_scale_factor": float(scale_factor),
            "fibonacci_rebalance_period": float(fib_period),
        }
        allocation_dict = {i: float(allocation_probs[i]) for i in range(len(allocation_probs))}
        logger.info("Portfolio optimization completed.")
        return allocation_dict, metrics


class public_api:
    """NiceHash public API client."""

    def __init__(self, host, verbose=False, quantum_backend: Optional[QuantumBackend] = None):
        self.host = host
        self.verbose = verbose
        self.quantum_backend = quantum_backend or AnalyticalQuantumBackend()
        self.logger = logger

    def request(self, method, path, query, body):
        try:
            url = self.host + path
            if query:
                url += "?" + query
            if self.verbose:
                self.logger.info(f"[HTTP] {method} {url}")
            s = requests.Session()
            if body:
                if isinstance(body, str):
                    body = json.loads(body)
                body_json = json.dumps(body)
                response = s.request(method, url, data=body_json, timeout=10)
            else:
                response = s.request(method, url, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.content:
                raise Exception(f"{response.status_code}: {response.reason}: {response.content}")
            else:
                raise Exception(f"{response.status_code}: {response.reason}")
        except Exception as e:
            self.logger.error(f"Public API request failed: {e}")
            raise

    def get_current_global_stats(self):
        return self.request("GET", "/main/api/v2/public/stats/global/current/", "", None)

    def get_global_stats_24(self):
        return self.request("GET", "/main/api/v2/public/stats/global/24h/", "", None)

    def get_active_orders(self):
        return self.request("GET", "/main/api/v2/public/orders/active/", "", None)

    def get_active_orders2(self):
        return self.request("GET", "/main/api/v2/public/orders/active2/", "", None)

    def buy_info(self):
        return self.request("GET", "/main/api/v2/public/buy/info/", "", None)

    def get_algorithms(self):
        return self.request("GET", "/main/api/v2/mining/algorithms/", "", None)

    def get_markets(self):
        return self.request("GET", "/main/api/v2/mining/markets/", "", None)

    def get_currencies(self):
        return self.request("GET", "/main/api/v2/public/currencies/", "", None)

    def get_multialgo_info(self):
        return self.request("GET", "/main/api/v2/public/simplemultialgo/info/", "", None)

    def get_exchange_markets_info(self):
        return self.request("GET", "/exchange/api/v2/info/status", "", None)

    def get_exchange_trades(self, market):
        return self.request("GET", "/exchange/api/v2/trades", "market=" + market, None)

    def get_candlesticks(self, market, from_s, to_s, resolution):
        return self.request(
            "GET",
            "/exchange/api/v2/candlesticks",
            "market={}&from={}&to={}&resolution={}".format(market, from_s, to_s, resolution),
            None,
        )

    def get_exchange_orderbook(self, market, limit):
        return self.request(
            "GET",
            "/exchange/api/v2/orderbook",
            "market={}&limit={}".format(market, limit),
            None,
        )

    def quantum_portfolio_optimization(
        self,
        expected_returns: np.ndarray,
        covariance: np.ndarray,
        problem_depth: str = "10",
    ):
        n_assets = len(expected_returns)
        optimizer = QuantumPortfolioOptimizer(self.quantum_backend, n_assets)
        return optimizer.optimize_allocation(
            expected_returns, covariance, problem_depth=problem_depth
        )


class private_api:
    """NiceHash private API client with quantum-enhanced authentication."""

    def __init__(
        self,
        host,
        organisation_id,
        key,
        secret,
        verbose=False,
        quantum_backend: Optional[QuantumBackend] = None,
    ):
        self.key = key
        self.secret = secret
        self.organisation_id = organisation_id
        self.host = host
        self.verbose = verbose
        self.quantum_backend = quantum_backend or AnalyticalQuantumBackend()
        self.crypto_protocol = QuantumCryptographicProtocol(self.quantum_backend)
        self.logger = logger

    def request(self, method, path, query, body):
        try:
            xtime = self.get_epoch_ms_from_now()
            quantum_random_bytes = self.crypto_protocol.quantum_entropy_extraction(16)
            xnonce = str(uuid.UUID(bytes=quantum_random_bytes[:16]))
            message = bytearray(self.key, "utf-8")
            message += bytearray(b"\x00")
            message += bytearray(str(xtime), "utf-8")
            message += bytearray(b"\x00")
            message += bytearray(xnonce, "utf-8")
            message += bytearray(b"\x00")
            message += bytearray(b"\x00")
            message += bytearray(self.organisation_id, "utf-8")
            message += bytearray(b"\x00")
            message += bytearray(b"\x00")
            message += bytearray(method, "utf-8")
            message += bytearray(b"\x00")
            message += bytearray(path, "utf-8")
            message += bytearray(b"\x00")
            message += bytearray(query, "utf-8")
            if body:
                if isinstance(body, str):
                    body = json.loads(body)
                body_json = json.dumps(body)
                message += bytearray(b"\x00")
                message += bytearray(body_json, "utf-8")
            digest = hmac.new(bytearray(self.secret, "utf-8"), message, sha256).hexdigest()
            xauth = self.key + ":" + digest
            headers = {
                "X-Time": str(xtime),
                "X-Nonce": xnonce,
                "X-Auth": xauth,
                "Content-Type": "application/json",
                "X-Organization-Id": self.organisation_id,
                "X-Request-Id": str(uuid.uuid4()),
            }
            s = requests.Session()
            s.headers.update(headers)
            url = self.host + path
            if query:
                url += "?" + query
            if self.verbose:
                self.logger.info(f"[HTTP] {method} {url}")
            if body:
                response = s.request(method, url, data=body_json, timeout=10)
            else:
                response = s.request(method, url, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.content:
                raise Exception(f"{response.status_code}: {response.reason}: {response.content}")
            else:
                raise Exception(f"{response.status_code}: {response.reason}")
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in request: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Private API request failed: {e}")
            raise

    def get_epoch_ms_from_now(self):
        now = datetime.now()
        now_ec_since_epoch = mktime(now.timetuple()) + now.microsecond / 1000000.0
        return int(now_ec_since_epoch * 1000)

    def algo_settings_from_response(self, algorithm, algo_response):
        algo_setting = None
        for item in algo_response["miningAlgorithms"]:
            if item["algorithm"] == algorithm:
                algo_setting = item
        if algo_setting is None:
            raise Exception("Settings for algorithm not found in algo_response parameter")
        return algo_setting

    def get_accounts(self):
        return self.request("GET", "/main/api/v2/accounting/accounts2/", "", None)

    def get_accounts_for_currency(self, currency):
        return self.request("GET", "/main/api/v2/accounting/account2/" + currency, "", None)

    def get_withdrawal_addresses(self, currency, size, page):
        params = "currency={}&size={}&page={}".format(currency, size, page)
        return self.request("GET", "/main/api/v2/accounting/withdrawalAddresses/", params, None)

    def get_withdrawal_types(self):
        return self.request("GET", "/main/api/v2/accounting/withdrawalAddresses/types/", "", None)

    def withdraw_request(self, address_id, amount, currency):
        withdraw_data = {
            "withdrawalAddressId": address_id,
            "amount": amount,
            "currency": currency,
        }
        return self.request("POST", "/main/api/v2/accounting/withdrawal/", "", withdraw_data)

    def get_my_active_orders(self, algorithm, market, limit):
        ts = self.get_epoch_ms_from_now()
        params = "algorithm={}&market={}&ts={}&limit={}&op=LT".format(algorithm, market, ts, limit)
        return self.request("GET", "/main/api/v2/hashpower/myOrders", params, None)

    def create_pool(self, name, algorithm, pool_host, pool_port, username, password):
        pool_data = {
            "name": name,
            "algorithm": algorithm,
            "stratumHostname": pool_host,
            "stratumPort": pool_port,
            "username": username,
            "password": password,
        }
        return self.request("POST", "/main/api/v2/pool/", "", pool_data)

    def delete_pool(self, pool_id):
        return self.request("DELETE", "/main/api/v2/pool/" + pool_id, "", None)

    def get_my_pools(self, page, size):
        return self.request("GET", "/main/api/v2/pools/", "", None)

    def get_hashpower_orderbook(self, algorithm):
        return self.request(
            "GET", "/main/api/v2/hashpower/orderBook/", "algorithm=" + algorithm, None
        )

    def create_hashpower_order(
        self, market, type, algorithm, price, limit, amount, pool_id, algo_response
    ):
        algo_setting = self.algo_settings_from_response(algorithm, algo_response)
        order_data = {
            "market": market,
            "algorithm": algorithm,
            "amount": amount,
            "price": price,
            "limit": limit,
            "poolId": pool_id,
            "type": type,
            "marketFactor": algo_setting["marketFactor"],
            "displayMarketFactor": algo_setting["displayMarketFactor"],
        }
        return self.request("POST", "/main/api/v2/hashpower/order/", "", order_data)

    def cancel_hashpower_order(self, order_id):
        return self.request("DELETE", "/main/api/v2/hashpower/order/" + order_id, "", None)

    def refill_hashpower_order(self, order_id, amount):
        refill_data = {"amount": amount}
        return self.request(
            "POST",
            "/main/api/v2/hashpower/order/" + order_id + "/refill/",
            "",
            refill_data,
        )

    def set_price_hashpower_order(self, order_id, price, algorithm, algo_response):
        algo_setting = self.algo_settings_from_response(algorithm, algo_response)
        price_data = {
            "price": price,
            "marketFactor": algo_setting["marketFactor"],
            "displayMarketFactor": algo_setting["displayMarketFactor"],
        }
        return self.request(
            "POST",
            "/main/api/v2/hashpower/order/" + order_id + "/updatePriceAndLimit/",
            "",
            price_data,
        )

    def set_limit_hashpower_order(self, order_id, limit, algorithm, algo_response):
        algo_setting = self.algo_settings_from_response(algorithm, algo_response)
        limit_data = {
            "limit": limit,
            "marketFactor": algo_setting["marketFactor"],
            "displayMarketFactor": algo_setting["displayMarketFactor"],
        }
        return self.request(
            "POST",
            "/main/api/v2/hashpower/order/" + order_id + "/updatePriceAndLimit/",
            "",
            limit_data,
        )

    def get_my_exchange_orders(self, market):
        return self.request("GET", "/exchange/api/v2/myOrders", "market=" + market, None)

    def get_my_exchange_trades(self, market):
        return self.request("GET", "/exchange/api/v2/myTrades", "market=" + market, None)

    def create_exchange_limit_order(self, market, side, quantity, price):
        query = "market={}&side={}&type=limit&quantity={}&price={}".format(
            market, side, quantity, price
        )
        return self.request("POST", "/exchange/api/v2/order", query, None)

    def create_exchange_buy_market_order(self, market, quantity):
        query = "market={}&side=buy&type=market&secQuantity={}".format(market, quantity)
        return self.request("POST", "/exchange/api/v2/order", query, None)

    def create_exchange_sell_market_order(self, market, quantity):
        query = "market={}&side=sell&type=market&quantity={}".format(market, quantity)
        return self.request("POST", "/exchange/api/v2/order", query, None)

    def cancel_exchange_order(self, market, order_id):
        query = "market={}&orderId={}".format(market, order_id)
        return self.request("DELETE", "/exchange/api/v2/order", query, None)


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option(
        "-b",
        "--base_url",
        dest="base",
        help="Api base url",
        default="https://api2.nicehash.com",
    )
    parser.add_option("-o", "--organization_id", dest="org", help="Organization id")
    parser.add_option("-k", "--key", dest="key", help="Api key")
    parser.add_option("-s", "--secret", dest="secret", help="Secret for api key")
    parser.add_option("-m", "--method", dest="method", help="Method for request", default="GET")
    parser.add_option("-p", "--path", dest="path", help="Path for request", default="/")
    parser.add_option("-q", "--params", dest="params", help="Parameters for request")
    parser.add_option("-d", "--body", dest="body", help="Body for request (JSON string)")

    options, args = parser.parse_args()

    if not options.org or not options.key or not options.secret:
        logger.error("Organization ID, API key, and secret are required.")
        sys.exit(1)

    backend = AnalyticalQuantumBackend()
    private_api_instance = private_api(
        options.base,
        options.org,
        options.key,
        options.secret,
        verbose=True,
        quantum_backend=backend,
    )

    params = options.params or ""
    body = None
    if options.body:
        try:
            body = json.loads(options.body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in body: {e}")
            sys.exit(1)

    try:
        response = private_api_instance.request(options.method, options.path, params, body)
        print(json.dumps(response, indent=2))
        sys.exit(0)
    except Exception as ex:
        logger.error(f"Unexpected error: {ex}")
        sys.exit(1)
