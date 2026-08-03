"""CNN-LSTM PyTorch model for deep sequence demand forecasting.

Follows the same interface as other model wrappers:
    fit(X_train, y_train, X_valid, y_valid) -> self
    predict(X) -> np.ndarray
    save(path) / load(path)
    is_fitted property
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from src.utils.config import CNNLSTMConfig

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Early Stopping (mirrors LightGBM's early_stopping_rounds pattern)
# ═══════════════════════════════════════════════════════════════

class EarlyStopping:
    """Stop training when validation loss stops improving.

    Args:
        patience: Number of epochs to wait before stopping.
        min_delta: Minimum change in loss to qualify as improvement.
    """

    def __init__(self, patience: int = 20, min_delta: float = 1e-4):
        self.patience = patience
        self.min_delta = min_delta
        self.best_loss = float("inf")
        self.counter = 0
        self.best_state: dict | None = None

    def __call__(self, val_loss: float, model: nn.Module) -> bool:
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
            self.best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            self.counter += 1
        return self.counter >= self.patience

    def restore(self, model: nn.Module) -> None:
        """Restore model weights to the best checkpoint."""
        if self.best_state is not None:
            model.load_state_dict(self.best_state)


# ═══════════════════════════════════════════════════════════════
# CNN-LSTM Network
# ═══════════════════════════════════════════════════════════════

class CNNLSTMNetwork(nn.Module):
    """CNN-LSTM hybrid for time series regression.

    Architecture:
        Conv1D(filters[0], k) → ReLU → Conv1D(filters[1], k) → ReLU
        → LSTM(hidden, num_layers, dropout) → last hidden state
        → Linear(hidden, 1)
    """

    def __init__(
        self,
        n_features: int,
        conv_filters: list[int],
        conv_kernel_size: int,
        lstm_hidden: int,
        lstm_layers: int,
        dropout: float = 0.3,
    ):
        super().__init__()

        # CNN blocks
        self.conv1 = nn.Conv1d(
            in_channels=n_features,
            out_channels=conv_filters[0],
            kernel_size=conv_kernel_size,
            padding="same",
        )
        self.conv2 = nn.Conv1d(
            in_channels=conv_filters[0],
            out_channels=conv_filters[1],
            kernel_size=conv_kernel_size,
            padding="same",
        )

        # LSTM
        self.lstm = nn.LSTM(
            input_size=conv_filters[1],
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            dropout=dropout if lstm_layers > 1 else 0.0,
            batch_first=True,
        )

        # Output head
        self.fc = nn.Linear(lstm_hidden, 1)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: (batch_size, n_features, sequence_length) — Conv1D expects channels first.

        Returns:
            (batch_size, 1) — Single forecast value per sample.
        """
        # CNN expects (B, C, L) — channels first
        out = torch.relu(self.conv1(x))
        out = torch.relu(self.conv2(out))

        # LSTM expects (B, L, C) — batch_first
        out = out.permute(0, 2, 1)  # (B, seq_len, conv_filters[1])
        out, (h_n, _) = self.lstm(out)

        # Use last hidden state
        last_hidden = h_n[-1]  # (B, lstm_hidden)
        last_hidden = self.dropout(last_hidden)
        return self.fc(last_hidden)


# ═══════════════════════════════════════════════════════════════
# Model Wrapper
# ═══════════════════════════════════════════════════════════════

class CNNLSTMModel:
    """CNN-LSTM wrapper following the same interface as LightGBMModel.

    Usage:
        model = CNNLSTMModel(config)
        model.fit(X_train, y_train, X_valid, y_valid)
        predictions = model.predict(X_test)
        model.save("models/cnn_lstm.pt")
    """

    def __init__(self, config: CNNLSTMConfig | None = None):
        self.config = config or CNNLSTMConfig()
        self._model: CNNLSTMNetwork | None = None
        self._is_fitted: bool = False
        self._n_features: int = 0
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @property
    def model(self) -> CNNLSTMNetwork:
        if self._model is None:
            raise RuntimeError("Model not fitted. Call fit() first.")
        return self._model

    def _build_network(self, n_features: int) -> CNNLSTMNetwork:
        return CNNLSTMNetwork(
            n_features=n_features,
            conv_filters=self.config.conv_filters,
            conv_kernel_size=self.config.conv_kernel_size,
            lstm_hidden=self.config.lstm_hidden,
            lstm_layers=self.config.lstm_layers,
            dropout=self.config.dropout,
        ).to(self._device)

    def _to_tensor(self, data: np.ndarray | torch.Tensor) -> torch.Tensor:
        if isinstance(data, np.ndarray):
            data = torch.from_numpy(data).float()
        return data.to(self._device)

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_valid: np.ndarray | None = None,
        y_valid: np.ndarray | None = None,
    ) -> "CNNLSTMModel":
        """Train the CNN-LSTM model.

        Args:
            X_train: Shape (n_samples, n_features, sequence_length) or (n_samples, n_features).
            y_train: Shape (n_samples,).
            X_valid: Optional validation data for early stopping.
            y_valid: Optional validation targets.

        Returns:
            self for chaining.
        """
        c = self.config

        # Handle 2D input (n_samples, n_features) → add sequence dim
        if X_train.ndim == 2:
            X_train = X_train[:, :, np.newaxis]
        if X_valid is not None and X_valid.ndim == 2:
            X_valid = X_valid[:, :, np.newaxis]

        self._n_features = X_train.shape[1]
        self._model = self._build_network(self._n_features)

        # DataLoaders
        train_ds = TensorDataset(
            self._to_tensor(X_train),
            self._to_tensor(y_train).reshape(-1, 1),
        )
        train_loader = DataLoader(train_ds, batch_size=c.batch_size, shuffle=True)

        val_loader = None
        if X_valid is not None and y_valid is not None and len(X_valid) > 0:
            val_ds = TensorDataset(
                self._to_tensor(X_valid),
                self._to_tensor(y_valid).reshape(-1, 1),
            )
            val_loader = DataLoader(val_ds, batch_size=c.batch_size, shuffle=False)

        # Optimizer + scheduler + loss
        optimizer = torch.optim.Adam(self._model.parameters(), lr=c.learning_rate)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5, patience=10
        )
        criterion = nn.MSELoss()
        early_stopper = EarlyStopping(patience=c.early_stopping_patience)

        # Training loop
        for epoch in range(c.epochs):
            self._model.train()
            train_loss = 0.0
            for xb, yb in train_loader:
                xb, yb = xb.to(self._device), yb.to(self._device)
                optimizer.zero_grad()
                loss = criterion(self._model(xb), yb)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()

            train_loss /= max(len(train_loader), 1)

            # Validation
            if val_loader is not None:
                self._model.eval()
                val_loss = 0.0
                with torch.no_grad():
                    for xb, yb in val_loader:
                        xb, yb = xb.to(self._device), yb.to(self._device)
                        val_loss += criterion(self._model(xb), yb).item()
                val_loss /= max(len(val_loader), 1)
                scheduler.step(val_loss)

                if early_stopper(val_loss, self._model):
                    log.info("CNN-LSTM early stopping at epoch %d (val_loss=%.6f)", epoch + 1, val_loss)
                    break
            else:
                scheduler.step(train_loss)

        # Restore best weights
        early_stopper.restore(self._model)
        self._is_fitted = True
        log.info("CNN-LSTM fitted: %d features, %d train samples, device=%s",
                 self._n_features, len(X_train), self._device)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions.

        Args:
            X: Shape (n_samples, n_features) or (n_samples, n_features, sequence_length).

        Returns:
            Array of predictions, shape (n_samples,).
        """
        if not self._is_fitted:
            raise RuntimeError("Model not fitted.")

        if X.ndim == 2:
            X = X[:, :, np.newaxis]

        self._model.eval()
        with torch.no_grad():
            x_tensor = self._to_tensor(X)
            preds = self._model(x_tensor).cpu().numpy()
        return preds.ravel()

    def save(self, path: str | Path) -> None:
        """Save model state dict and metadata to disk."""
        if not self._is_fitted:
            raise RuntimeError("Cannot save unfitted model.")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": self._model.state_dict(),
                "n_features": self._n_features,
                "config": self.config,
            },
            path,
        )
        log.info("CNN-LSTM model saved to %s", path)

    def load(self, path: str | Path) -> "CNNLSTMModel":
        """Load model from disk."""
        path = Path(path)
        checkpoint = torch.load(path, map_location=self._device, weights_only=False)

        self._n_features = checkpoint["n_features"]
        self.config = checkpoint.get("config", self.config)
        self._model = self._build_network(self._n_features)
        self._model.load_state_dict(checkpoint["state_dict"])
        self._model.eval()
        self._is_fitted = True
        log.info("CNN-LSTM model loaded from %s (%d features)", path, self._n_features)
        return self
