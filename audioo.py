from pydub import AudioSegment
import os, sys

src = "test_audio.mp3"
dst = "test_audio.wav"

try:
    print("Loading", src)
    seg = AudioSegment.from_file(src)
    print("Loaded: channels=", seg.channels, "frame_rate=", seg.frame_rate, "sample_width=", seg.sample_width)
    seg = seg.set_frame_rate(16000).set_channels(1)
    seg.export(dst, format="wav", codec="pcm_s16le")
    print("Exported", dst, "size=", os.path.getsize(dst), "bytes")
except Exception as e:
    print("Error:", e)
    sys.exit(1)