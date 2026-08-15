import os
import wave
import contextlib

def get_wav_duration(filepath):
    try:
        with contextlib.closing(wave.open(filepath, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return duration * 1000.0 # to ms
    except Exception as e:
        return None

def main():
    folder = "out_wwise/wav_music"
    files = [f for f in os.listdir(folder) if f.endswith(".wav")][:10]
    print(f"Checking durations for {len(files)} files in {folder}:")
    for f in files:
        path = os.path.join(folder, f)
        dur = get_wav_duration(path)
        print(f"File: {f}, Duration: {dur} ms")

if __name__ == "__main__":
    main()
