"""Tests for the /api/predict endpoint with optimizer integration."""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone


class PredictionEndpointTests(unittest.TestCase):
    """Test the /api/predict endpoint integration with AI optimizer."""

    def setUp(self):
        """Clear the singleton registry before each test."""
        from pythia_mining.genesis_ai_service import GenesisAIServiceRegistry
        GenesisAIServiceRegistry._instance = None
        GenesisAIServiceRegistry._genesis_ai = None

    def test_prediction_returns_503_when_optimizer_not_connected(self):
        """Prediction endpoint fails closed when optimizer is unavailable."""
        from hyba_genesis_api.api.misc import PredictRequest, predict_params
        from fastapi import HTTPException
        import asyncio

        request = PredictRequest(state={"networkDifficulty": 7234567890123})
        
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(predict_params(request))
        
        self.assertEqual(ctx.exception.status_code, 503)
        detail = ctx.exception.detail
        self.assertIsInstance(detail, dict)
        self.assertEqual(detail["error"], "optimizer_runtime_not_connected")
        self.assertIn("message", detail)
        self.assertIn("timestamp", detail)

    def test_prediction_returns_success_when_optimizer_connected(self):
        """Prediction endpoint returns predictions when optimizer is available."""
        from hyba_genesis_api.api.misc import PredictRequest, predict_params
        import asyncio

        # Mock the optimizer
        mock_optimizer = Mock()
        mock_optimizer.meta_learning_snapshot.return_value = {
            "strategy_probabilities": {
                "phi_scaled_compressed_solver_search": 0.7,
                "golden_ratio_baseline": 0.3,
            },
            "recent_performance": [
                {"accepted": True, "phi_resonance": 0.8},
                {"accepted": True, "phi_resonance": 0.75},
                {"accepted": False, "phi_resonance": 0.6},
                {"accepted": True, "phi_resonance": 0.82},
            ],
        }

        with patch(
            "hyba_genesis_api.api.misc.GenesisAIServiceRegistry"
        ) as mock_registry:
            mock_registry.get_ai_optimizer.return_value = mock_optimizer
            
            request = PredictRequest(state={"networkDifficulty": 7234567890123})
            result = asyncio.run(predict_params(request))
            
            self.assertTrue(result["success"])
            self.assertEqual(result["status"], "predicted")
            self.assertEqual(result["source"], "measured_optimizer_runtime")
            self.assertIn("recommendation", result)
            self.assertIn("optimizer_state", result)
            
            recommendation = result["recommendation"]
            self.assertIn("strategy", recommendation)
            self.assertIn("power_scale", recommendation)
            self.assertIn("confidence", recommendation)
            self.assertGreater(recommendation["confidence"], 0.0)
            self.assertLessEqual(recommendation["confidence"], 1.0)
            
            optimizer_state = result["optimizer_state"]
            self.assertIn("acceptance_rate", optimizer_state)
            self.assertIn("strategy_probabilities", optimizer_state)

    def test_prediction_adjusts_power_scale_based_on_acceptance_rate(self):
        """Prediction endpoint recommends higher power scale for low acceptance rates."""
        from hyba_genesis_api.api.misc import PredictRequest, predict_params
        import asyncio

        # Test low acceptance rate (should increase power)
        mock_optimizer = Mock()
        mock_optimizer.meta_learning_snapshot.return_value = {
            "strategy_probabilities": {"strategy_a": 1.0},
            "recent_performance": [
                {"accepted": False},
                {"accepted": False},
                {"accepted": False},
                {"accepted": False},
            ],
        }

        with patch(
            "hyba_genesis_api.api.misc.GenesisAIServiceRegistry"
        ) as mock_registry:
            mock_registry.get_ai_optimizer.return_value = mock_optimizer
            
            request = PredictRequest(state={"networkDifficulty": 100})
            result = asyncio.run(predict_params(request))
            
            self.assertGreaterEqual(result["recommendation"]["power_scale"], 1.2)
            self.assertEqual(result["optimizer_state"]["acceptance_rate"], 0.0)

    def test_prediction_rejects_invalid_difficulty(self):
        """Prediction endpoint validates network difficulty parameter."""
        from hyba_genesis_api.api.misc import PredictRequest
        from pydantic import ValidationError

        # Negative difficulty should fail validation
        with self.assertRaises(ValidationError):
            PredictRequest(state={"networkDifficulty": -1})

        # Zero difficulty should fail validation
        with self.assertRaises(ValidationError):
            PredictRequest(state={"networkDifficulty": 0})

        # Positive difficulty should validate
        request = PredictRequest(state={"networkDifficulty": 1000})
        self.assertIsNotNone(request)
        self.assertEqual(request.state.networkDifficulty, 1000)

    def test_prediction_handles_empty_strategy_probabilities(self):
        """Prediction endpoint handles optimizer with no strategy history."""
        from hyba_genesis_api.api.misc import PredictRequest, predict_params
        import asyncio

        mock_optimizer = Mock()
        mock_optimizer.meta_learning_snapshot.return_value = {
            "strategy_probabilities": {},
            "recent_performance": [],
        }

        with patch(
            "hyba_genesis_api.api.misc.GenesisAIServiceRegistry"
        ) as mock_registry:
            mock_registry.get_ai_optimizer.return_value = mock_optimizer
            
            request = PredictRequest(state={"networkDifficulty": 1000})
            result = asyncio.run(predict_params(request))
            
            self.assertTrue(result["success"])
            self.assertEqual(result["recommendation"]["confidence"], 0.0)
            self.assertEqual(result["recommendation"]["strategy"], "phi_scaled_compressed_solver_search")

    def test_prediction_response_includes_timestamp(self):
        """Prediction endpoint includes ISO timestamp in all responses."""
        from hyba_genesis_api.api.misc import PredictRequest, predict_params
        from fastapi import HTTPException
        import asyncio

        request = PredictRequest(state={"networkDifficulty": 1000})
        
        # Test 503 response
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(predict_params(request))
        
        self.assertIn("timestamp", ctx.exception.detail)
        timestamp = ctx.exception.detail["timestamp"]
        # Verify ISO format
        datetime.fromisoformat(timestamp)

        # Test success response
        mock_optimizer = Mock()
        mock_optimizer.meta_learning_snapshot.return_value = {
            "strategy_probabilities": {"s1": 1.0},
            "recent_performance": [{"accepted": True}],
        }

        with patch(
            "hyba_genesis_api.api.misc.GenesisAIServiceRegistry"
        ) as mock_registry:
            mock_registry.get_ai_optimizer.return_value = mock_optimizer
            result = asyncio.run(predict_params(request))
            
            self.assertIn("timestamp", result)
            datetime.fromisoformat(result["timestamp"])


if __name__ == "__main__":
    unittest.main()
