import os
import librosa
import soundfile as sf

def slice_audio_to_clips(
    input_wav,
    output_folder,
    start_time_sec=0,
    num_clips=10,
    clip_duration_sec=5,
    sr=16000
):
    os.makedirs(output_folder, exist_ok=True)

    # Load full audio as mono at 16k
    y, _ = librosa.load(input_wav, sr=sr, mono=True)

    start_sample = int(start_time_sec * sr)
    clip_len = int(clip_duration_sec * sr)

    for i in range(num_clips):
        begin = start_sample + i * clip_len
        end = begin + clip_len

        if end > len(y):
            break

        clip = y[begin:end]
        out_path = os.path.join(output_folder, f"clip_{i:03d}.wav")
        sf.write(out_path, clip, sr)

    print(f"Saved {i+1} clips to: {output_folder}")
    
slice_audio_to_clips(
    input_wav=r"D:\miniproj-audiomodel\anomaly2.wav",
    output_folder="anomaly_clips",
    start_time_sec=0,
    num_clips=20,
    clip_duration_sec=5,
    sr=16000
)