import numpy as np

MORSE_CODE_DICT = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    ".": ".-.-.-",
    ",": "--..--",
    "?": "..--..",
    "'": ".----.",
    "!": "-.-.--",
    "/": "-..-.",
    "(": "-.--.",
    ")": "-.--.-",
    "&": ".-...",
    ":": "---...",
    ";": "-.-.-.",
    "=": "-...-",
    "+": ".-.-.",
    "-": "-....-",
    "_": "..--.-",
    '"': ".-..-.",
    "$": "...-..-",
    "@": ".--.-.",
}


def generate_tone(duration, frequency=700, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = 0.5 * np.sin(2 * np.pi * frequency * t)  # 0.5 cuz otherwise it's loud af
    return tone


def generate_silence(duration, sample_rate=44100):
    return np.zeros(int(sample_rate * duration))


def text_to_morse(text):
    morse_code = []
    for char in text.upper():
        if char in MORSE_CODE_DICT:
            morse_code.append(MORSE_CODE_DICT[char])
        elif char == " ":
            morse_code.append(" ")
    return " ".join(morse_code)


def morse_to_audio(morse_code, dot_duration=0.1, dash_duration=0.3, sample_rate=44100):
    audio = np.array([], dtype=np.float32)
    for symbol in morse_code:
        if symbol == ".":
            audio = np.concatenate(
                (audio, generate_tone(dot_duration, sample_rate=sample_rate))
            )
            audio = np.concatenate(
                (audio, generate_silence(dot_duration, sample_rate=sample_rate))
            )
        elif symbol == "-":
            audio = np.concatenate(
                (audio, generate_tone(dash_duration, sample_rate=sample_rate))
            )
            audio = np.concatenate(
                (audio, generate_silence(dot_duration, sample_rate=sample_rate))
            )
        elif symbol == " ":
            audio = np.concatenate(
                (audio, generate_silence(dot_duration * 3, sample_rate=sample_rate))
            )
    return audio
