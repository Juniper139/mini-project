import time
import numpy as np
import torch
import sounddevice as sd
from scipy.io.wavfile import write

from audio_essentials.dataset.anomaly_clips.preprocess import audio_to_cnn_input
from modelsmall import ConvAutoencoderSmall

# ---------------- CONFIG ----------------
device = "cuda" if torch.cuda.is_available() else "cpu"

SAMPLE_RATE = 16000      # same kind of rate usually used in preprocessing
DURATION = 5             # seconds per recording
TEMP_WAV = "temp_input.wav"
threshold = 0.008

# ---------------- LOAD MODEL ----------------
model = ConvAutoencoderSmall().to(device)
model.load_state_dict(torch.load("autoencoder_small.pth", map_location=device))
model.eval()

print("Mic anomaly detection started. Press Ctrl+C to stop.\n")

try:
    while True:
        print(f"Recording {DURATION} seconds...")

        # Record audio from laptop mic
        audio = sd.rec(
            int(SAMPLE_RATE * DURATION),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32"
        )
        sd.wait()

        # Convert float32 [-1,1] to int16 for wav saving
        audio_int16 = (audio * 32767).astype(np.int16)

        # Save temporary wav file
        write(TEMP_WAV, SAMPLE_RATE, audio_int16)

        # Preprocess -> (64, 157, 1)
        mel = audio_to_cnn_input(TEMP_WAV)

        # To torch -> (1, 1, 64, 157)
        x = torch.from_numpy(mel).permute(2, 0, 1).unsqueeze(0).float().to(device)

        with torch.no_grad():
            recon = model(x)

            min_w = min(x.shape[-1], recon.shape[-1])
            err = ((x[..., :min_w] - recon[..., :min_w]) ** 2).mean().item()

        verdict = "ANOMALY" if err > threshold else "normal"
        print(f"error={err:.6f} -> {verdict}\n")

        # small pause before next chunk
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopped by user.")