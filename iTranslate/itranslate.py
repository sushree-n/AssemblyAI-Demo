import os
import queue
import sys
import threading

import deepl
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    TerminationEvent,
    TurnEvent,
)

load_dotenv()

SAMPLE_RATE = 16000
FRAME_MS = 50
BLOCK_SIZE = SAMPLE_RATE * FRAME_MS // 1000

LANG_A = os.getenv("LANG_A", "en")
LANG_B = os.getenv("LANG_B", "hi")

KEYTERMS_PROMPT = [t.strip() for t in os.getenv("KEYTERMS_PROMPT", "").split(",") if t.strip()]

CLEAR_LINE = "\x1b[2K\r"

# AssemblyAI language_code -> DeepL source/target codes.
# DeepL requires a region variant (EN-US/EN-GB) as a *target*, but accepts
# bare EN as a *source*. Extend these if you add more languages to the pair.
DEEPL_SOURCE = {"en": "EN", "hi": "HI"}
DEEPL_TARGET = {"en": "EN-US", "hi": "HI"}

deepl_client = deepl.Translator(os.environ["DEEPL_API_KEY"])

ELEVEN_MODEL = "eleven_flash_v2_5"
TTS_SAMPLE_RATE = 24000
ELEVENLABS_VOICE_ID = {
    LANG_A: os.environ["ELEVENLABS_VOICE_ID_A"],
    LANG_B: os.environ["ELEVENLABS_VOICE_ID_B"],
}

elevenlabs_client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

audio_queue: "queue.Queue[bytes]" = queue.Queue()

# Set before TTS playback starts, cleared after. mic_callback checks this so
# the device doesn't transcribe its own translated speech back into the pipeline.
is_playing = threading.Event()

DEVANAGARI_RANGE = ("ऀ", "ॿ")


def detect_script(text: str) -> str:
    """Route en/hi by script instead of AssemblyAI's language_code field.

    language_detection reports a separate classifier pass and can misfire on
    short or mid-conversation code-switches even when the transcript itself
    is correct. En/hi use disjoint scripts (Latin vs Devanagari), so checking
    for Devanagari characters is a more reliable routing signal for this pair.
    This trick doesn't generalize to language pairs that share a script
    (e.g. en/es) — those would need to trust language_code/language_confidence.
    """
    if any(DEVANAGARI_RANGE[0] <= ch <= DEVANAGARI_RANGE[1] for ch in text):
        return "hi"
    return "en"


def translate(text: str, source_lang: str, target_lang: str) -> str:
    result = deepl_client.translate_text(
        text,
        source_lang=DEEPL_SOURCE[source_lang],
        target_lang=DEEPL_TARGET[target_lang],
    )
    return result.text


def synthesize(text: str, voice_id: str) -> bytes:
    chunks = elevenlabs_client.text_to_speech.convert(
        voice_id,
        text=text,
        model_id=ELEVEN_MODEL,
        output_format=f"pcm_{TTS_SAMPLE_RATE}",
    )
    return b"".join(chunks)


def play(pcm_bytes: bytes) -> None:
    audio = np.frombuffer(pcm_bytes, dtype=np.int16)
    sd.play(audio, samplerate=TTS_SAMPLE_RATE)
    sd.wait()


def speak(text: str, target_lang: str) -> None:
    print(f"[SPEAKING {target_lang.upper()}]...")
    try:
        audio = synthesize(text, ELEVENLABS_VOICE_ID[target_lang])
    except Exception as exc:
        print(f"[ERROR] TTS failed: {exc}", file=sys.stderr)
        return

    is_playing.set()
    try:
        play(audio)
    except Exception as exc:
        print(f"[ERROR] playback failed: {exc}", file=sys.stderr)
    finally:
        is_playing.clear()


def mic_callback(indata, frames, time_info, status):
    if status:
        print(f"Mic status: {status}", file=sys.stderr)
    if is_playing.is_set():
        return
    audio_queue.put(bytes(indata))


def on_begin(client: StreamingClient, event: BeginEvent):
    print(f"Session started: {event.id}")
    print(f"LISTENING [{LANG_A} <-> {LANG_B}]  (Ctrl+C to stop)")


def on_turn(client: StreamingClient, event: TurnEvent):
    if not event.transcript:
        return
    if not event.end_of_turn:
        print(f"{CLEAR_LINE}[partial] {event.transcript}", end="", flush=True)
        return

    detected = detect_script(event.transcript)
    if detected == LANG_A:
        target = LANG_B
    elif detected == LANG_B:
        target = LANG_A
    else:
        print(f"{CLEAR_LINE}[WARN] unrecognized language '{detected}', skipping: {event.transcript}")
        return

    print(f"{CLEAR_LINE}[{detected.upper()}] {event.transcript}")
    print("[TRANSLATING...]")
    try:
        translated = translate(event.transcript, detected, target)
    except Exception as exc:
        print(f"[ERROR] translation failed: {exc}", file=sys.stderr)
        return

    print(f"[{target.upper()}] {translated}")
    threading.Thread(target=speak, args=(translated, target), daemon=True).start()


def on_terminated(client: StreamingClient, event: TerminationEvent):
    print(f"\nSession terminated: {event.audio_duration_seconds}s of audio processed")


def on_error(client: StreamingClient, error: StreamingError):
    print(f"Error: {error}", file=sys.stderr)


def main():
    client = StreamingClient(
        StreamingClientOptions(
            api_key=os.environ["ASSEMBLYAI_API_KEY"],
            terminate_timeout=30.0,
        )
    )

    client.on(StreamingEvents.Begin, on_begin)
    client.on(StreamingEvents.Turn, on_turn)
    client.on(StreamingEvents.Termination, on_terminated)
    client.on(StreamingEvents.Error, on_error)

    params = dict(
        sample_rate=SAMPLE_RATE,
        speech_model="universal-3-5-pro",
        language_detection=True,
        language_codes=[LANG_A, LANG_B],
        voice_focus="near-field",
        mode="max_accuracy",
    )
    if KEYTERMS_PROMPT:
        params["keyterms_prompt"] = KEYTERMS_PROMPT

    client.connect(StreamingParameters(**params))

    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="int16",
        channels=1,
        callback=mic_callback,
    )

    try:
        with stream:
            while True:
                chunk = audio_queue.get()
                client.stream(chunk)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect(terminate=True)


if __name__ == "__main__":
    main()
