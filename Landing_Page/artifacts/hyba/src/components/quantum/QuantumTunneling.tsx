import { useRef, useEffect } from "react";

interface QuantumCanvasProps {
  className?: string;
  colorMode?: "dark" | "light";
}

export default function QuantumTunneling({ className, colorMode = "dark" }: QuantumCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let rafId: number;
    let t = 0;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    function resize() {
      const w = canvas!.offsetWidth;
      const h = canvas!.offsetHeight;
      canvas!.width = w * dpr;
      canvas!.height = h * dpr;
      ctx!.scale(dpr, dpr);
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    // Wave parameters
    const sigma = 55;
    const k = 0.06;
    const omega = 1.8;
    const A = 60;
    
    // Wave state
    let x0 = canvas.offsetWidth * 0.15;
    const speed = 0.4;
    let hasHitBarrier = false;
    let reflectionStartFrame = 0;

    function draw() {
      const W = canvas!.offsetWidth;
      const H = canvas!.offsetHeight;
      const centerY = H / 2;

      const bg = colorMode === "dark" ? "rgba(2,13,26,1)" : "rgba(248,246,241,0)";
      const waveColor = colorMode === "dark" ? "rgba(31,130,192,0.9)" : "rgba(0,71,153,0.9)";
      const goldColor = colorMode === "dark" ? "rgba(242,169,0,0.9)" : "rgba(200,130,0,0.95)";
      const textColor = colorMode === "dark" ? "rgba(255,255,255,0.4)" : "rgba(0,47,108,0.5)";

      ctx!.clearRect(0, 0, W, H);
      if (colorMode === "dark") {
        ctx!.fillStyle = bg;
        ctx!.fillRect(0, 0, W, H);
      }

      // Draw potential energy level
      ctx!.setLineDash([4, 4]);
      ctx!.strokeStyle = colorMode === "dark" ? "rgba(255,255,255,0.15)" : "rgba(0,47,108,0.15)";
      ctx!.beginPath();
      ctx!.moveTo(0, centerY);
      ctx!.lineTo(W, centerY);
      ctx!.stroke();
      ctx!.setLineDash([]);
      ctx!.font = "8px Menlo, monospace";
      ctx!.fillStyle = colorMode === "dark" ? "rgba(255,255,255,0.3)" : "rgba(0,47,108,0.3)";
      ctx!.fillText("POTENTIAL ENERGY LEVEL", 10, centerY - 5);

      // Draw barrier
      const barrierX = W * 0.55;
      const barrierW = 12;
      ctx!.fillStyle = "rgba(242,169,0,0.25)";
      ctx!.fillRect(barrierX, 0, barrierW, H);
      ctx!.fillStyle = textColor;
      ctx!.font = "9px Menlo, monospace";
      ctx!.fillText("BARRIER", barrierX - 15, 20);

      // Move wave
      x0 += speed;
      if (x0 > barrierX - sigma * 2 && !hasHitBarrier) {
        hasHitBarrier = true;
        reflectionStartFrame = t;
      }

      if (x0 > W + sigma * 3) {
        // Reset
        x0 = W * 0.15;
        hasHitBarrier = false;
      }

      // Draw main/reflected wave (left of barrier)
      ctx!.beginPath();
      ctx!.strokeStyle = waveColor;
      ctx!.lineWidth = 1.5;
      for (let x = 0; x <= barrierX; x++) {
        let psi = 0;
        if (!hasHitBarrier) {
          // Approaching
          psi = A * Math.exp(-((x - x0) ** 2) / (2 * sigma ** 2)) * Math.cos(k * (x - x0) - omega * t * 0.1);
        } else {
          // Reflected
          const framesSinceHit = t - reflectionStartFrame;
          const decay = Math.max(0.7 - framesSinceHit * 0.005, 0.2);
          const reflectX0 = barrierX - sigma * 2 - (x0 - (barrierX - sigma * 2));
          psi = (A * decay) * Math.exp(-((x - reflectX0) ** 2) / (2 * sigma ** 2)) * Math.cos(-k * (x - reflectX0) - omega * t * 0.1);
        }
        if (x === 0) ctx!.moveTo(x, centerY + psi);
        else ctx!.lineTo(x, centerY + psi);
      }
      ctx!.stroke();

      // Draw evanescent and transmitted waves if hit
      if (hasHitBarrier) {
        // Evanescent wave inside barrier
        ctx!.beginPath();
        ctx!.strokeStyle = goldColor;
        ctx!.lineWidth = 1.5;
        for (let x = barrierX; x <= barrierX + barrierW; x++) {
          const kappa = 0.15;
          const psiEv = Math.exp(-kappa * (x - barrierX)) * Math.sin(omega * t * 0.1) * 0.4 * A;
          if (x === barrierX) ctx!.moveTo(x, centerY + psiEv);
          else ctx!.lineTo(x, centerY + psiEv);
        }
        ctx!.stroke();

        // Transmitted wave (right of barrier)
        ctx!.beginPath();
        ctx!.strokeStyle = goldColor;
        ctx!.lineWidth = 1.5;
        for (let x = barrierX + barrierW; x <= W; x++) {
          const transX0 = barrierX + barrierW + (x0 - (barrierX - sigma * 2));
          const psiTrans = (A * 0.3) * Math.exp(-((x - transX0) ** 2) / (2 * sigma ** 2)) * Math.cos(k * (x - transX0) - omega * t * 0.1);
          if (x === barrierX + barrierW) ctx!.moveTo(x, centerY + psiTrans);
          else ctx!.lineTo(x, centerY + psiTrans);
        }
        ctx!.stroke();
      }

      t++;
      rafId = requestAnimationFrame(draw);
    }

    draw();

    return () => {
      cancelAnimationFrame(rafId);
      ro.disconnect();
    };
  }, [colorMode]);

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{ width: "100%", height: "100%", display: "block" }}
    />
  );
}