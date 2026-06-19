import { useRef, useEffect } from "react";

interface QuantumCanvasProps {
  className?: string;
  colorMode?: "dark" | "light";
}

interface Particle {
  x: number;
  t: number;
}

export default function QuantumAnnealing({ className, colorMode = "dark" }: QuantumCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let rafId: number;
    let frame = 0;

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

    const particles: Particle[] = Array.from({ length: 5 }, () => ({
      x: Math.random() * (canvas.offsetWidth || 800),
      t: 1.0,
    }));

    function energy(x: number) {
      // Landscape function
      const sc = 0.05;
      return 0.3 * Math.sin(x * 0.08 * sc) + 
             0.15 * Math.sin(x * 0.19 * sc) + 
             0.08 * Math.cos(x * 0.35 * sc) + 
             0.05 * Math.sin(x * 0.6 * sc);
    }

    function draw() {
      const W = canvas!.offsetWidth;
      const H = canvas!.offsetHeight;

      const bg = colorMode === "dark" ? "rgba(2,13,26,1)" : "rgba(248,246,241,0)";
      const waveColor = colorMode === "dark" ? "rgba(31,130,192,0.6)" : "rgba(0,71,153,0.6)";
      const fillLight = colorMode === "dark" ? "rgba(0,47,108,0.3)" : "rgba(0,71,153,0.15)";
      const goldColor = colorMode === "dark" ? "rgba(242,169,0,0.9)" : "rgba(200,130,0,0.95)";
      const textColor = colorMode === "dark" ? "rgba(255,255,255,0.4)" : "rgba(0,47,108,0.5)";

      ctx!.clearRect(0, 0, W, H);
      if (colorMode === "dark") {
        ctx!.fillStyle = bg;
        ctx!.fillRect(0, 0, W, H);
      }

      // Draw landscape
      ctx!.beginPath();
      ctx!.moveTo(0, H);
      
      let minE = Infinity;
      let minX = 0;
      
      for (let x = 0; x <= W; x += 2) {
        const e = energy(x);
        // Map [-0.6, 0.6] to [0.1*H, 0.7*H] approx
        const y = H * 0.5 + e * H * 0.4;
        ctx!.lineTo(x, y);
        if (e < minE) {
          minE = e;
          minX = x;
        }
      }
      ctx!.lineTo(W, H);
      ctx!.closePath();
      
      ctx!.fillStyle = fillLight;
      ctx!.fill();
      ctx!.strokeStyle = waveColor;
      ctx!.lineWidth = 1.5;
      ctx!.stroke();

      // Draw global minimum label
      const minY = H * 0.5 + minE * H * 0.4;
      ctx!.fillStyle = textColor;
      ctx!.font = "8px Menlo, monospace";
      ctx!.textAlign = "center";
      ctx!.fillText("↓ GLOBAL Φ-MINIMUM", minX, minY - 15);

      // Update and draw particles
      particles.forEach(p => {
        // Temperature schedule
        p.t *= 0.9995;
        if (frame % 600 === 0) p.t = 1.0;

        // Propose new state
        const proposedX = p.x + (Math.random() - 0.5) * (p.t * 160); // +- 80*t
        if (proposedX >= 0 && proposedX <= W) {
          const currentE = energy(p.x);
          const proposedE = energy(proposedX);
          
          if (proposedE < currentE || Math.random() < Math.exp(-(proposedE - currentE) / Math.max(p.t, 0.01))) {
            p.x = proposedX;
          }
        }

        const py = H * 0.5 + energy(p.x) * H * 0.4;

        // Draw line down to curve
        ctx!.beginPath();
        ctx!.moveTo(p.x, py - 40 * p.t);
        ctx!.lineTo(p.x, py);
        ctx!.strokeStyle = colorMode === "dark" ? "rgba(242,169,0,0.3)" : "rgba(200,130,0,0.4)";
        ctx!.stroke();

        // Draw particle
        ctx!.beginPath();
        ctx!.arc(p.x, py, 5, 0, Math.PI * 2);
        ctx!.fillStyle = goldColor;
        ctx!.fill();

        // Glow
        ctx!.beginPath();
        ctx!.arc(p.x, py, 10, 0, Math.PI * 2);
        if (p.t > 0.2) {
          ctx!.fillStyle = colorMode === "dark" ? "rgba(31,130,192,0.4)" : "rgba(0,71,153,0.3)";
        } else {
          ctx!.fillStyle = colorMode === "dark" ? "rgba(242,169,0,0.5)" : "rgba(200,130,0,0.4)";
        }
        ctx!.fill();
      });

      // Draw T gauge
      const avgT = particles.reduce((sum, p) => sum + p.t, 0) / particles.length;
      const barW = 80;
      const barH = 4;
      const gaugeX = W - 100;
      const gaugeY = H - 20;
      
      ctx!.fillStyle = textColor;
      ctx!.textAlign = "left";
      ctx!.fillText("TEMPERATURE", gaugeX, gaugeY - 6);
      
      ctx!.fillStyle = colorMode === "dark" ? "rgba(255,255,255,0.1)" : "rgba(0,47,108,0.1)";
      ctx!.fillRect(gaugeX, gaugeY, barW, barH);
      
      const grad = ctx!.createLinearGradient(gaugeX, 0, gaugeX + barW, 0);
      grad.addColorStop(0, goldColor);
      grad.addColorStop(1, colorMode === "dark" ? "rgba(31,130,192,1)" : "rgba(0,71,153,1)");
      
      ctx!.fillStyle = grad;
      ctx!.fillRect(gaugeX, gaugeY, barW * avgT, barH);

      frame++;
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