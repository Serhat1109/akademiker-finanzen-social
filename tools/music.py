"""Erzeugt eine ruhige, selbst komponierte Hintergrundmusik (keine Lizenzrechte Dritter).

Akkordfolge C - G - Am - F, weiche Flächen plus leises Arpeggio, Ein- und Ausblendung.
Aufruf: python3 tools/music.py ausgabe.wav [sekunden]
"""
import sys, wave
import numpy as np

SR = 44100
dur = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
n = int(SR * dur)
t = np.arange(n) / SR

def hz(m):  # MIDI-Note -> Frequenz
    return 440.0 * 2 ** ((m - 69) / 12)

chords = [[48, 55, 60, 64], [43, 50, 59, 62], [45, 52, 57, 60], [41, 48, 57, 60]]  # C, G, Am, F
bar = 2.4  # Sekunden pro Akkord (ca. 100 BPM, 4/4)
out = np.zeros(n)

def tone(f, start, length, amp, attack, release, bright=0.25):
    i0, i1 = int(start * SR), min(n, int((start + length + release) * SR))
    if i0 >= n: return
    tt = np.arange(i1 - i0) / SR
    env = np.minimum(1, tt / attack) * np.where(tt < length, 1, np.exp(-(tt - length) / (release / 4)))
    w = np.sin(2 * np.pi * f * tt) + bright * np.sin(4 * np.pi * f * tt) + 0.08 * np.sin(6 * np.pi * f * tt)
    out[i0:i1] += amp * env * w

k = 0
s = 0.0
while s < dur:
    ch = chords[k % 4]
    for m in ch:                                   # weiche Fläche
        tone(hz(m), s, bar, 0.05, 0.6, 1.2, 0.15)
    tone(hz(ch[0] - 12), s, bar, 0.07, 0.05, 0.8, 0.1)  # Bass
    arp = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12]
    for j in range(8):                             # Achtel-Arpeggio, pianoartig
        st = s + j * bar / 8
        f = hz(arp[j % 4])
        i0 = int(st * SR); i1 = min(n, i0 + int(1.2 * SR))
        if i0 < n:
            tt = np.arange(i1 - i0) / SR
            env = np.minimum(1, tt / 0.005) * np.exp(-tt * 3.5)
            out[i0:i1] += 0.045 * env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt))
    s += bar; k += 1

# einfacher Hall (Verzögerungen) und Ein-/Ausblendung
for d, g in ((0.11, 0.35), (0.23, 0.25), (0.37, 0.15)):
    sh = int(d * SR); out[sh:] += g * out[:-sh]
fade = np.minimum(1, t / 1.0) * np.minimum(1, (dur - t) / 1.5)
out *= fade
out /= np.max(np.abs(out)) + 1e-9
out *= 0.5
right = np.roll(out, int(0.012 * SR))              # leichte Stereobreite
pcm = (np.stack([out, right], axis=1) * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(sys.argv[1], dur)
