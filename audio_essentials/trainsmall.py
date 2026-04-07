import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, TensorDataset

from audio_essentials.dataset.anomaly_clips.preprocess import build_dataset
from modelsmall import ConvAutoencoderSmall

# ---- Data ----
X_train = build_dataset("clips")  # (N, 64, 157, 1)
X_torch = torch.from_numpy(X_train).permute(0, 3, 1, 2).float()  # (N, 1, 64, 157)

print(X_torch.shape)
print(X_torch.dtype, X_torch.min().item(), X_torch.max().item())

device = "cuda" if torch.cuda.is_available() else "cpu"

dataset = TensorDataset(X_torch, X_torch)   # input == target
loader = DataLoader(dataset, batch_size=32, shuffle=True)

# ---- Model ----
model = ConvAutoencoderSmall().to(device)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)

# ---- Training ----
for epoch in range(26):
    model.train()
    total_loss = 0.0

    for x, y in loader:
        x, y = x.to(device), y.to(device)

        optimizer.zero_grad()
        y_hat = model(x)
        loss = criterion(y_hat, y)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * x.size(0)

    print(f"Epoch {epoch+1:02d} | Loss: {total_loss / len(dataset):.6f}")

# ---- Save model ----
torch.save(model.state_dict(), "autoencoder_small.pth")

# ---- Compute threshold (95th percentile of normal reconstruction errors) ----
model.eval()
X_dev = X_torch.to(device)

with torch.no_grad():
    recon = model(X_dev)

    min_w = min(X_dev.shape[-1], recon.shape[-1])
    errors = ((X_dev[..., :min_w] - recon[..., :min_w]) ** 2).mean(dim=(1, 2, 3)).cpu().numpy()

threshold = float(np.percentile(errors, 95))
torch.save(torch.tensor(threshold), "threshold_small.pt")

print("Saved threshold:", threshold)