# chirp — Interface

**Chirp** encodes morphons as geometry-native acoustic signals. A
chirp is a three-layer message:

1. **Primary digit** — a DTMF-style tone pair selected from a 9-channel
   grid keyed by the morphon's digital-root channel.
2. **Upper word** (8 bits) — derived from the morphon's E8 coordinates,
   written into harmonics above the carrier.
3. **Lower word** (8 bits) — derived from a superpermutation index over
   the morphon's leech-space encoding, written into subharmonics below.

A single chirp captures channel + 8-D position + a permutation index
that disambiguates among morphons of the same channel and E8 position.

This first build emits a *structured representation* of the chirp
(a dataclass with the three layers + the carrier frequencies) rather
than raw audio. The audio synthesizer is a future extension; the
structure here is what audio would render.

## What this package exposes

| Symbol | Purpose |
|---|---|
| `Chirp` | The provider class. Implements the `transport` port. |
| `ChirpFrame` | The encoded form — primary tones + upper word + lower word + metadata. |
| `encode_frame(morphon)` | Pure function: morphon → ChirpFrame. |
| `decode_frame(frame)` | Inverse: ChirpFrame → key identity (channel + first 4 E8 bits + 4 super bits). |
| `DTMF_CARRIERS` | Channel → (low_freq, high_freq) Hz map. |

## DTMF carriers

The 9 channels map to a 3×3 grid of tone pairs in the standard DTMF
range, extended:

| Channel | Triad | Low Hz | High Hz |
|---:|---|---:|---:|
| 1 | LOW (Initiation) | 697 | 1209 |
| 2 | LOW (Forge) | 697 | 1336 |
| 3 | LOW (Apex) | 697 | 1477 |
| 4 | MID (Movement) | 770 | 1209 |
| 5 | MID (Action) | 770 | 1336 |
| 6 | MID (Manifestation) | 770 | 1477 |
| 7 | HIGH (Archive) | 852 | 1209 |
| 8 | HIGH (Forge close) | 852 | 1336 |
| 9 | HIGH (Reset) | 852 | 1477 |

(This matches the standard DTMF row/column frequencies for the keypad
1-9, which lets the chirp transport ride over telephony-grade infra
for free.)

## Encoding algorithm

```
input: a morphon with at minimum a payload (the rest can be computed)

1. Project to channel:    ch = morphon.dr_channel  (compute if not cached)
2. Project to E8:          coords = morphon.e8_coordinates
3. Project to Leech:       leech = morphon.leech_point

4. Upper word (8 bits) — derive from E8 coordinates:
   for each of the 8 coords c_i:
     bit_i = 1 if c_i >= 0 else 0
   upper_word = bits concatenated

5. Lower word (8 bits) — derive from Leech-point hex:
   take the first 2 hex chars after the leech:: prefix
   lower_word = int(hex, 16)

6. Carrier tones:           (low_hz, high_hz) = DTMF_CARRIERS[ch]

7. Return ChirpFrame(channel=ch, low_hz=low_hz, high_hz=high_hz,
                      upper_word=upper_word, lower_word=lower_word,
                      morphon_id=morphon.id)
```

## Invariants

1. **Deterministic**: same morphon (same payload + state) → same frame.
2. **Pure**: doesn't mutate the morphon.
3. **Self-keying**: the chirp frame includes the morphon_id so the
   receiver can correlate back.
4. **Carrier ranges**: low ∈ {697, 770, 852}, high ∈ {1209, 1336, 1477}.

## What this package does NOT do

- Doesn't render audio (no WAV / MIDI yet). `ChirpFrame.to_audio()` is
  a future extension that would use `wave` or `mido`.
- Doesn't transmit. Network rendering is a future extension.
- Doesn't decode arbitrary recordings — only round-trips the frame
  representation it produces.
- Doesn't carry the full payload — by design. The chirp is a
  *content-address transmitter*; the payload itself lives in MMDB.

## How morphon talks to this

Through the `transport` port:

```python
from cmplx.morphon import MorphonController
from cmplx.transport.chirp import Chirp

MorphonController.get().register("transport", Chirp())

# encode any morphon as a chirp frame:
frame = MorphonController.get().get_provider("transport").encode(morphon)
```
