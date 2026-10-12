import wave
import math
import struct
import os

SAMPLE_RATE = 44100

def create_wav(filename, samples):
    with wave.open(filename, 'w') as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(SAMPLE_RATE)
        data = bytearray()
        for s in samples:
            # Clamp between -1.0 and 1.0
            s = max(-1.0, min(1.0, s))
            val = int(s * 32767.0)
            data += struct.pack('<h', val)
        wav.writeframes(data)

def generate_tone(freq, duration, decay=True, wave_type='sine'):
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        if wave_type == 'sine':
            val = math.sin(2 * math.pi * freq * t)
        elif wave_type == 'square':
            val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        elif wave_type == 'triangle':
            val = 2.0 * abs(2.0 * (t * freq - math.floor(t * freq + 0.5))) - 1.0
        else:
            val = math.sin(2 * math.pi * freq * t)
        
        # Envelope
        if decay:
            envelope = math.exp(-t * (4.0 / duration))
        else:
            envelope = 1.0
        samples.append(val * envelope * 0.4)
    return samples

def generate_move_sound(path):
    samples = generate_tone(520, 0.05, decay=True, wave_type='square')
    create_wav(path, samples)

def generate_rotate_sound(path):
    num_samples = int(SAMPLE_RATE * 0.08)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        freq = 400 + 400 * (t / 0.08)
        val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        envelope = 1.0 - (t / 0.08)
        samples.append(val * envelope * 0.35)
    create_wav(path, samples)

def generate_drop_sound(path):
    num_samples = int(SAMPLE_RATE * 0.12)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        freq = 250 * math.exp(-t * 20) + 60
        val = math.sin(2 * math.pi * freq * t) + 0.3 * (1.0 if math.sin(2 * math.pi * freq * 0.5 * t) > 0 else -1.0)
        envelope = math.exp(-t * 25)
        samples.append(val * envelope * 0.5)
    create_wav(path, samples)

def generate_clear_sound(path):
    # Two-tone arpeggio
    s1 = generate_tone(523.25, 0.07, decay=True, wave_type='triangle') # C5
    s2 = generate_tone(659.25, 0.07, decay=True, wave_type='triangle') # E5
    s3 = generate_tone(783.99, 0.12, decay=True, wave_type='triangle') # G5
    create_wav(path, s1 + s2 + s3)

def generate_tetris_sound(path):
    # Grand fanfare: C5, E5, G5, C6
    s1 = generate_tone(523.25, 0.08, decay=True, wave_type='square')
    s2 = generate_tone(659.25, 0.08, decay=True, wave_type='square')
    s3 = generate_tone(783.99, 0.08, decay=True, wave_type='square')
    s4 = generate_tone(1046.50, 0.25, decay=True, wave_type='square')
    create_wav(path, s1 + s2 + s3 + s4)

def generate_levelup_sound(path):
    # Level up chime
    s1 = generate_tone(440.0, 0.07, decay=True, wave_type='sine')
    s2 = generate_tone(554.37, 0.07, decay=True, wave_type='sine')
    s3 = generate_tone(659.25, 0.07, decay=True, wave_type='sine')
    s4 = generate_tone(880.0, 0.18, decay=True, wave_type='sine')
    create_wav(path, s1 + s2 + s3 + s4)

def generate_gameover_sound(path):
    # Descending gloomy tones
    s1 = generate_tone(440, 0.12, decay=True, wave_type='triangle')
    s2 = generate_tone(370, 0.12, decay=True, wave_type='triangle')
    s3 = generate_tone(311, 0.14, decay=True, wave_type='triangle')
    s4 = generate_tone(220, 0.35, decay=True, wave_type='sawtooth' if False else 'sine')
    create_wav(path, s1 + s2 + s3 + s4)

def generate_all_sounds(target_dir):
    os.makedirs(target_dir, exist_ok=True)
    sounds = {
        'move.wav': generate_move_sound,
        'rotate.wav': generate_rotate_sound,
        'drop.wav': generate_drop_sound,
        'clear.wav': generate_clear_sound,
        'tetris.wav': generate_tetris_sound,
        'levelup.wav': generate_levelup_sound,
        'gameover.wav': generate_gameover_sound,
    }
    for filename, func in sounds.items():
        file_path = os.path.join(target_dir, filename)
        if not os.path.exists(file_path):
            func(file_path)
            print(f"Generated sound: {filename}")

if __name__ == '__main__':
    sound_dir = os.path.join(os.path.dirname(__file__), 'sounds')
    generate_all_sounds(sound_dir)
    print("All sounds generated successfully!")
