import matplotlib.pyplot as plt
import librosa.display
import os
import numpy as np

def save_mel_image(filepath, save_path, sr=16000):
    y, _ = librosa.load(filepath, sr=sr)

    mel = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_mels=64,
        n_fft=1024,
        hop_length=512
    )

    mel_db = librosa.power_to_db(mel, ref=np.max)

    plt.figure(figsize=(6, 4))
    librosa.display.specshow(mel_db, sr=sr, hop_length=512, x_axis='time', y_axis='mel')
    plt.colorbar(format='%+2.0f dB')
    plt.title("Mel Spectrogram")
    plt.tight_layout()

    plt.savefig(save_path)
    plt.close()
    


# Create output folders
os.makedirs("mel_images/normal", exist_ok=True)
os.makedirs("mel_images/anomaly", exist_ok=True)

# Loop normal clips
normal_folder = "clips"

for fname in sorted(os.listdir(normal_folder)):
    if not fname.lower().endswith(".wav"):
        continue

    input_path = os.path.join(normal_folder, fname)
    output_path = os.path.join("mel_images/normal", fname.replace(".wav", ".png"))

    save_mel_image(input_path, output_path)


# Loop anomaly clips
anomaly_folder = "anomaly_clips"

for fname in sorted(os.listdir(anomaly_folder)):
    if not fname.lower().endswith(".wav"):
        continue

    input_path = os.path.join(anomaly_folder, fname)
    output_path = os.path.join("mel_images/anomaly", fname.replace(".wav", ".png"))

    save_mel_image(input_path, output_path)