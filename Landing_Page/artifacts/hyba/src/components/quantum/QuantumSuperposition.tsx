import { useRef, useEffect } from "react";

interface QuantumCanvasProps {
  className?: string;
  colorMode?: "dark" | "light";
}

export default function QuantumSuperposition({ className, colorMode = "dark" }: QuantumCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let rafId: number;
    let t = 0;
    
    // Measurement state
    let measurementFrame = 0;
    let isCollapsing = false;
    let collapseX = 0;

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

    const waves = [
      { A: 25, k: 0.025, speed: 1.2, colorD: "rgba(31,130,192,0.5)", colorL: "rgba(0,71,153,0.5)", label: "ψ₁" },
      { A: 20, k: 0.04, speed: 0.9, colorD: "rgba(242,169,0,0.5)", colorL: "rgba(200,130,0,0.5)", label: "ψ₂" },
      { A: 15, k: 0.06, speed: 1.5, colorD: "rgba(232,89,26,0.4)", colorL: "rgba(200,60,10,0.4)", label: "ψ₃" },
    ];

    function draw() {
      const W = canvas!.offsetWidth;
      const H = canvas!.offsetHeight;
      const centerY = H / 2;

      const bg = colorMode === "dark" ? "rgba(2,13,26,1)" : "rgba(248,246,241,0)";
      const supColor = colorMode === "dark" ? "rgba(255,255,255,0.9)" : "rgba(0,47,108,0.9)";
      const goldColor = colorMode === "dark" ? "rgba(242,169,0,0.9)" : "rgba(200,130,0,0.95)";
      const textColor = colorMode === "dark" ? "rgba(255,255,255,0.4)" : "rgba(0,47,108,0.5)";

      ctx!.clearRect(0, 0, W, H);
      if (colorMode === "dark") {
        ctx!.fillStyle = bg;
        ctx!.fillRect(0, 0, W, H);
      }

      if (t > 0 && t % 180 === 0 && !isCollapsing) {
        isCollapsing = true;
        measurementFrame = t;
        collapseX = W * 0.2 + Math.random() * (W * 0.6);
      }

      let waveOpacity = 1;
      let collapseProgress = 0;
      
      if (isCollapsing) {
        const framesSince = t - measurementFrame;
        if (framesSince < 15) {
          waveOpacity = 1 - framesSince / 15;
          collapseProgress = framesSince / 15;
        } else if (framesSince < 45) {
          waveOpacity = 0;
          collapseProgress = 1;
        } else if (framesSince < 75) {
          waveOpacity = (framesSince - 45) / 30;
          collapseProgress = 1 - waveOpacity;
        } else {
          isCollapsing = false;
        }
      }

      // Draw probability density and total wave
      ctx!.beginPath();
      ctx!.moveTo(0, centerY);
      const totalPoints = [];
      for (let x = 0; x <= W; x++) {
        let psiTotal = 0;
        
        if (collapseProgress < 1) {
          waves.forEach(w => {
            psiTotal += w.A * Math.sin(w.k * x + w.speed * t * 0.05);
          });
          psiTotal *= waveOpacity;
        }

        if (collapseProgress > 0) {
          // Gaussian at collapse point
          const A_collapse = 60 * collapseProgress;
          const sigma = 15;
          psiTotal += A_collapse * Math.exp(-((x - collapseX) ** 2) / (2 * sigma ** 2)) * Math.cos(0.1 * (x - collapseX));
        }

        totalPoints.push(psiTotal);
      }

      // Fill density
      ctx!.beginPath();
      ctx!.moveTo(0, centerY);
      for (let x = 0; x <= W; x++) {
        ctx!.lineTo(x, centerY + Math.abs(totalPoints[x]));
      }
      for (let x = W; x >= 0; x--) {
        ctx!.lineTo(x, centerY - Math.abs(totalPoints[x]));
      }
      ctx!.closePath();
      ctx!.fillStyle = colorMode === "dark" ? "rgba(242,169,0,0.06)" : "rgba(200,130,0,0.06)";
      ctx!.fill();

      // Draw individual waves
      if (waveOpacity > 0) {
        waves.forEach((w, i) => {
          ctx!.beginPath();
          for (let x = 0; x <= W; x++) {
            const y = centerY + w.A * Math.sin(w.k * x + w.speed * t * 0.05);
            if (x === 0) ctx!.moveTo(x, y);
            else ctx!.lineTo(x, y);
          }
          ctx!.globalAlpha = waveOpacity;
          ctx!.strokeStyle = colorMode === "dark" ? w.colorD : w.colorL;
          ctx!.lineWidth = 1;
          ctx!.stroke();
          ctx!.globalAlpha = 1;

          // Label
          ctx!.fillStyle = colorMode === "dark" ? w.colorD : w.colorL;
          ctx!.globalAlpha = waveOpacity;
          ctx!.font = "10px sans-serif";
          ctx!.fillText(w.label, 10, centerY - 30 + i * 15);
          ctx!.globalAlpha = 1;
        });
      }

      // Draw total superposition wave
      ctx!.beginPath();
      for (let x = 0; x <= W; x++) {
        const y = centerY + totalPoints[x];
        if (x === 0) ctx!.moveTo(x, y);
        else ctx!.lineTo(x, y);
      }
      ctx!.strokeStyle = supColor;
      ctx!.lineWidth = 2;
      ctx!.stroke();

      // Superposition label
      ctx!.fillStyle = supColor;
      ctx!.font = "10px sans-serif";
      ctx!.fillText("Ψ = ψ₁+ψ₂+ψ₃", 10, 20);

      // Draw measurement sweep
      if (isCollapsing && t - measurementFrame < 20) {
        const sweepX = collapseX + ((t - measurementFrame) / 20) * 100 - 50;
        ctx!.beginPath();
        ctx!.moveTo(sweepX, 0);
        ctx!.lineTo(sweepX, H);
        ctx!.strokeStyle = goldColor;
        ctx!.lineWidth = 2;
        ctx!.stroke();
      }

      // Label at bottom
      ctx!.fillStyle = textColor;
      if (isCollapsing && t % 10 < 5) {
        ctx!.fillStyle = goldColor;
      }
      ctx!.font = "8px Menlo, monospace";
      ctx!.fillText("MEASUREMENT → COLLAPSE", W / 2 - 60, H - 10);

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