# SDR Plot Examples

These examples cover sdrrat-style drawing only: FFT spectrum, waterfall
spectrogram output, center/span passband overlays, VFO cursors, and peak
markers. glyph-arts does not connect to SDR hardware or demodulate signals.

```bash
glyph-arts spectrum --file examples/sdr/spectrum.json --width 76 --height 16 --title RF-Spectrum
glyph-arts waterfall --file examples/sdr/waterfall.json --width 76 --height 16 --title RF-Waterfall
glyph-arts spectrum --format csv < examples/sdr/spectrum.csv
```
