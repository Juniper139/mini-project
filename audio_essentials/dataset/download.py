import os
import yt_dlp
import librosa
import soundfile as sf

def download_audio(youtube_url, output_path="downloaded_audio.wav"):
    ydl_opts = {
        # More forgiving format selection than bestaudio/best
        "format": '140',

        "outtmpl": "temp_audio.%(ext)s",

        

        # Helps mimic a regular browser a bit
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        },

        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
        }],

        # Set False while debugging so you can see what's happening
        "quiet": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    # Rename the extracted wav to your target name
    for file in os.listdir():
        if file.startswith("temp_audio") and file.endswith(".wav"):
            os.replace(file, output_path)
            break

    print("Audio downloaded successfully:", output_path)


def convert_and_crop(
    input_file,
    start_time_sec,
    num_clips,
    clip_duration=5,
    output_folder="anomaly_clips",
    target_sr=16000
):
    os.makedirs(output_folder, exist_ok=True)

    # Load, convert to mono, resample
    y, sr = librosa.load(input_file, sr=target_sr, mono=True)

    total_clip_samples = clip_duration * target_sr
    start_sample = start_time_sec * target_sr

    for i in range(num_clips):
        begin = start_sample + i * total_clip_samples
        end = begin + total_clip_samples

        if end > len(y):
            print("Reached end of file.")
            break

        clip = y[begin:end]
        output_path = os.path.join(output_folder, f"clip13_{i:03d}.wav")
        sf.write(output_path, clip, target_sr)

    print(f"Saved {i+1} clips to {output_folder}")


if __name__ == "__main__":
    url = input("Enter YouTube URL: ")
    start_time = int(input("Enter start time (in seconds): "))
    number_of_clips = int(input("Enter number of 5-second clips: "))
    #folder_name = input("Enter output folder name: ")

    download_audio(url)

    convert_and_crop(
        input_file="downloaded_audio.wav",
        start_time_sec=start_time,
        num_clips=number_of_clips,
        clip_duration=5,
        #output_folder=folder_name,
        target_sr=16000
    )