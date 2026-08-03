"""Tests for CNN-LSTM model."""

import numpy as np
import pytest

from src.models.cnn_lstm_model import CNNLSTMModel
from src.utils.config import CNNLSTMConfig


@pytest.fixture
def cnn_config() -> CNNLSTMConfig:
    return CNNLSTMConfig(
        epochs=10,
        batch_size=16,
        sequence_length=30,
        early_stopping_patience=5,
        conv_filters=[32, 64],
        lstm_hidden=64,
        lstm_layers=1,
        dropout=0.2,
    )


@pytest.fixture
def sample_2d_data():
    """Generate synthetic data for CNN-LSTM: (n, features)."""
    rng = np.random.default_rng(42)
    n_samples = 200
    n_features = 5
    X = rng.normal(0, 1, (n_samples, n_features))
    y = X[:, 0] * 0.5 + X[:, 1] * 0.3 + rng.normal(0, 0.1, n_samples)
    return X.astype(np.float32), y.astype(np.float32)


class TestCNNLSTMModel:
    def test_fit_predict(self, cnn_config, sample_2d_data):
        X, y = sample_2d_data
        n_train = 150
        X_train, y_train = X[:n_train], y[:n_train]
        X_test, y_test = X[n_train:], y[n_train:]

        model = CNNLSTMModel(cnn_config)
        model.fit(X_train, y_train)
        assert model.is_fitted

        preds = model.predict(X_test)
        assert len(preds) == len(X_test)
        assert preds.dtype == np.float32 or preds.dtype == np.float64

    def test_fit_with_validation(self, cnn_config, sample_2d_data):
        X, y = sample_2d_data
        X_train, y_train = X[:120], y[:120]
        X_val, y_val = X[120:160], y[120:160]

        model = CNNLSTMModel(cnn_config)
        model.fit(X_train, y_train, X_val, y_val)
        assert model.is_fitted

    def test_save_load(self, cnn_config, sample_2d_data, tmp_path):
        X, y = sample_2d_data
        model = CNNLSTMModel(cnn_config)
        model.fit(X[:100], y[:100])

        path = tmp_path / "cnn_lstm.pt"
        model.save(path)
        assert path.exists()

        model2 = CNNLSTMModel()
        model2.load(path)
        assert model2.is_fitted

        preds = model2.predict(X[:10])
        assert len(preds) == 10

    def test_not_fitted_raises(self, cnn_config, sample_2d_data):
        X, _ = sample_2d_data
        model = CNNLSTMModel(cnn_config)
        with pytest.raises(RuntimeError):
            model.predict(X[:10])

    def test_3d_input(self, cnn_config):
        """Model should handle 3D input (n, features, seq_len)."""
        rng = np.random.default_rng(42)
        X = rng.normal(0, 1, (100, 8, 10)).astype(np.float32)
        y = X[:, 0, -1] * 0.5 + rng.normal(0, 0.1, 100).astype(np.float32)

        model = CNNLSTMModel(cnn_config)
        model.fit(X[:70], y[:70])
        preds = model.predict(X[70:])
        assert len(preds) == 30
