import torch
import torch.nn as nn
import torch.nn.functional as F

class ConvAutoencoderSmall(nn.Module):
    def __init__(self):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1),   # (B,16,64,157)
            nn.ReLU(),
            nn.MaxPool2d(2, 2),               # (B,16,32,78)

            nn.Conv2d(16, 32, 3, padding=1),  # (B,32,32,78)
            nn.ReLU(),
            nn.Dropout2d(0.2),
            nn.MaxPool2d(2, 2),               # (B,32,16,39)
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(32, 16, 2, stride=2),  # (B,16,32,78)
            nn.ReLU(),
            nn.ConvTranspose2d(16, 1, 2, stride=2),   # (B,1,64,156)
            nn.Sigmoid()
        )

    def forward(self, x):
        z = self.encoder(x)
        out = self.decoder(z)
        if out.shape[-1] == 156:
            out = F.pad(out, (0, 1, 0, 0))
        return out