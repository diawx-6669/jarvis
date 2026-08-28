/**
 * Clap detector — listens to the microphone continuously (independent of
 * speech recognition) and fires a callback when it hears one sharp clap.
 */

export interface ClapDetectorOptions {
  /** Amplitude (0-1) a transient must exceed to count as a clap. */
  threshold?: number;
  /** Minimum silence (ms) between the peak and being able to detect the next one. */
  refractoryMs?: number;
}

export function startClapDetector(
  onClap: () => void,
  opts: ClapDetectorOptions = {}
): { stop(): void } {
  const threshold = opts.threshold ?? 0.30;
  const refractoryMs = opts.refractoryMs ?? 800;

  let stopped = false;
  let audioCtx: AudioContext | null = null;
  let stream: MediaStream | null = null;
  let lastClapTime = 0;
  let rafId = 0;

  navigator.mediaDevices
    .getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } })
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
          onClap();
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
