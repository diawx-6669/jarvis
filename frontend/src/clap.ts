/**
 * Clap detector — listens to the microphone continuously (independent of
 * speech recognition) and fires a callback when it hears two sharp claps
 * close together, MCU-style ("Jarvis?" *clap clap*).
 *
 * Requiring TWO claps in a short window avoids false triggers from doors
 * slamming, coughs, keyboard clacks, etc.
 */

export interface ClapDetectorOptions {
  /** Amplitude (0-1) a transient must exceed to count as a clap. */
  threshold?: number;
  /** Minimum silence (ms) between the peak and being able to detect the next one. */
  refractoryMs?: number;
  /** Max gap (ms) between clap #1 and clap #2 to count as a pair. */
  maxGapMs?: number;
}

export function startClapDetector(
  onClap: () => void,
  opts: ClapDetectorOptions = {}
): { stop(): void } {
  const threshold = opts.threshold ?? 0.35;
  const refractoryMs = opts.refractoryMs ?? 250;
  const maxGapMs = opts.maxGapMs ?? 700;

  let stopped = false;
  let audioCtx: AudioContext | null = null;
  let stream: MediaStream | null = null;
  let lastClapTime = 0;
  let pendingFirstClap = 0;
  let rafId = 0;

  navigator.mediaDevices
    .getUserMedia({ audio: true })
    .then((s) => {
      if (stopped) {
        s.getTracks().forEach((t) => t.stop());
        return;
      }
      stream = s;
      audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0; // we want raw transients, not smoothed volume
      source.connect(analyser);

      const data = new Uint8Array(analyser.fftSize);

      const tick = () => {
        if (stopped) return;
        analyser.getByteTimeDomainData(data);

        // Peak amplitude this frame, normalized 0-1
        let peak = 0;
        for (let i = 0; i < data.length; i++) {
          const v = Math.abs(data[i] - 128) / 128;
          if (v > peak) peak = v;
        }

        const now = performance.now();
        if (peak > threshold && now - lastClapTime > refractoryMs) {
          lastClapTime = now;
          if (pendingFirstClap && now - pendingFirstClap <= maxGapMs) {
            pendingFirstClap = 0;
            onClap();
          } else {
            pendingFirstClap = now;
          }
        }

        // Expire a stale first clap
        if (pendingFirstClap && now - pendingFirstClap > maxGapMs) {
          pendingFirstClap = 0;
        }

        rafId = requestAnimationFrame(tick);
      };
      rafId = requestAnimationFrame(tick);
    })
    .catch((err) => {
      console.warn("[clap] microphone unavailable for clap detection:", err);
    });

  return {
    stop() {
      stopped = true;
      if (rafId) cancelAnimationFrame(rafId);
      if (stream) stream.getTracks().forEach((t) => t.stop());
      if (audioCtx) audioCtx.close().catch(() => {});
    },
  };
}
