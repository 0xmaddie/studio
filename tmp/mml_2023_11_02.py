# i forgot the prompt but i asked GPT to implement mml and this is what it came
# up with.

import numpy as np
import subprocess
import os

class MML:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.buffer = np.array([], dtype=np.float32)
        self.tempo = 120  # Beats per minute
        self.default_length = 4  # Default to quarter note
        self.octave = 4  # Starting octave
        self.volume = 1.0  # Volume level

        # Mapping notes to their frequencies
        self.note_frequencies = {
            'c': 261.63, 'c#': 277.18, 'd': 293.66, 'd#': 311.13,
            'e': 329.63, 'f': 349.23, 'f#': 369.99, 'g': 392.00,
            'g#': 415.30, 'a': 440.00, 'a#': 466.16, 'b': 493.88
        }

    def _note_to_frequency(self, note):
        """Convert a note to its frequency taking into account the current octave."""
        base_freq = self.note_frequencies[note.lower()]
        return base_freq * (2 ** (self.octave - 4))

    def _add_wave(self, frequency, duration):
        """Add a wave of the given frequency and duration to the buffer."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = 0.5 * self.volume * np.sin(2 * np.pi * frequency * t)
        self.buffer = np.concatenate((self.buffer, wave))

    def note(self, note, length=None):
        """Add a note to the buffer."""
        length = length or self.default_length
        duration = (60.0 / self.tempo) * (4.0 / length)
        freq = self._note_to_frequency(note)
        self._add_wave(freq, duration)

    def rest(self, length=None):
        """Add a rest to the buffer."""
        length = length or self.default_length
        duration = (60.0 / self.tempo) * (4.0 / length)
        rest = np.zeros(int(self.sample_rate * duration))
        self.buffer = np.concatenate((self.buffer, rest))

    def set_tempo(self, tempo):
        """Set the tempo in beats per minute."""
        self.tempo = tempo

    def set_default_length(self, length):
        """Set the default length for notes and rests."""
        self.default_length = length

    def set_octave(self, octave):
        """Set the current octave."""
        self.octave = octave

    def change_octave(self, change):
        """Change the current octave up or down."""
        self.octave += change

    def set_volume(self, volume):
        """Set the volume level."""
        self.volume = volume

    def save_to_file(self, filename):
        """Save the buffer to a file using sox."""
        temp_filename = filename + '.raw'
        with open(temp_filename, 'wb') as f:
            f.write(self.buffer.astype(np.float32).tobytes())

        # Use sox to convert raw audio to a more common format
        subprocess.call(['sox', '-r', str(self.sample_rate), '-e', 'floating-point', '-b', '32', '-c', '1', temp_filename, filename])
        os.remove(temp_filename)

# Test the class by creating a simple melody
mml = MML()
mml.set_tempo(120)
mml.set_default_length(4)
mml.note('e')
mml.note('d')
mml.note('c')
mml.note('d')
mml.note('e')
mml.note('e')
mml.note('e', 2)
mml.rest()
mml.note('d')
mml.note('d')
mml.note('d', 2)
mml.rest()
mml.note('e')
mml.note('g')
mml.note('g', 2)
mml.rest()
mml.note('e')
mml.note('d')
mml.note('c')
mml.note('d')
mml.note('e')
mml.note('e')
mml.note('e')
mml.note('e')
mml.note('d')
mml.note('d')
mml.note('e')
mml.note('d')
mml.note('c')

# Save to file
audio_filename = 'mary_had_a_little_lamb.wav'
mml.save_to_file(audio_filename)

audio_filename
