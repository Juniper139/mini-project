import librosa
import numpy as np

def audio_to_cnn_input(filepath, sr=16000, n_mels=64, n_fft=1024, hop_length=512):
    # 1) Load audio (mono + resample)
    y, _ = librosa.load(filepath, sr=sr, mono=True)

    # 2) Mel spectrogram
    mel = librosa.feature.melspectrogram(
        y=y, sr=sr, n_mels=n_mels, n_fft=n_fft, hop_length=hop_length
    )

    # 3) Log scale
    mel_db = librosa.power_to_db(mel, ref=np.max)

    # 4) Normalize to 0-1
    mel_db = mel_db.astype(np.float32)
    mel_norm = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-8)

    # 5) Add channel dimension -> (H, W, 1)
    mel_norm = np.expand_dims(mel_norm, axis=-1)

    return mel_norm

import os

def build_dataset(folder):
    X = []
    for f in os.listdir(folder):
        if f.endswith(".wav"):
            X.append(audio_to_cnn_input(os.path.join(folder, f)))
    return np.array(X)

X_train = build_dataset("clips")
print(X_train.shape)  # (num_clips, 64, time_frames, 1)

print(X_train.dtype, X_train.min(), X_train.max())


            