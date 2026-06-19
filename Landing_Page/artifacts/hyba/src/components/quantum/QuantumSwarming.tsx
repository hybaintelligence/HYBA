import { useRef, useEffect } from "react";

interface QuantumCanvasProps {
  className?: string;
  colorMode?: "dark" | "light";
}

interface SwarmParticle {
  x: number; y: number;
  vx: number; vy: number;
  lane: number;
  coherence: number;
}

export default function QuantumSwarming({ className, colorMode = "dark" }: QuantumCanvasProps) {
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

    const particles: SwarmParticle[] = [];
    for (let i = 0; i < 80; i++) {
      particles.push({
        x: Math.random() * (canvas.offsetWidth || 800),
        y: Math.random() * (canvas.offsetHeight || 220),
        vx: 0,
        vy: 0,
        lane: i % 4,
        coherence: Math.random(),
      });
    }

    function draw() {
      const W = canvas!.offsetWidth;
      const H = canvas!.offsetHeight;
      const cx = W / 2;
      const cy = H / 2;

      const bg = colorMode === "dark" ? "rgba(2,13,26,1)" : "rgba(248,246,241,0)";
      const waveColor = colorMode === "dark" ? "rgba(31,130,192,0.9)" : "rgba(0,71,153,0.9)";
      const goldColor = colorMode === "dark" ? "rgba(242,169,0,0.9)" : "rgba(200,130,0,0.95)";
      const textColor = colorMode === "dark" ? "rgba(255,255,255,0.4)" : "rgba(0,47,108,0.5)";

      ctx!.clearRect(0, 0, W, H);
      if (colorMode === "dark") {
        ctx!.fillStyle = bg;
        ctx!.fillRect(0, 0, W, H);
      }

      // Hubs
      const hubs = Array.from({ length: 4 }, (_, i) => ({
        x: cx + Math.cos(t * 0.01 + i * Math.PI / 2) * (W * 0.25),
        y: cy + Math.sin(t * 0.01 + i * Math.PI / 2) * (H * 0.3),
      }));

      // Draw hubs
      hubs.forEach(h => {
        ctx!.beginPath();
        ctx!.arc(h.x, h.y, 8 + 4 * Math.sin(t * 0.05), 0, Math.PI * 2);
        ctx!.fillStyle = colorMode === "dark" ? "rgba(242,169,0,0.3)" : "rgba(200,130,0,0.2)";
        ctx!.fill();
      });

      let totalCoherence = 0;

      // Update and draw particles
      particles.forEach(p => {
        const hub = hubs[p.lane];
        const dxHub = hub.x - p.x;
        const dyHub = hub.y - p.y;
        const distHub = Math.sqrt(dxHub * dxHub + dyHub * dyHub);

        if (distHub < 30) {
          p.coherence = Math.min(p.coherence + 0.01, 1);
        } else {
          p.coherence = Math.max(p.coherence - 0.005, 0);
        }

        totalCoherence += p.coherence;

        const fluctX = (Math.random() - 0.5) * (1 - p.coherence) * 2;
        const fluctY = (Math.random() - 0.5) * (1 - p.coherence) * 2;

        p.vx += dxHub * 0.002 + fluctX;
        p.vy += dyHub * 0.002 + fluctY;

        const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
        if (speed > 2) {
          p.vx = (p.vx / speed) * 2;
          p.vy = (p.vy / speed) * 2;
        }

        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x += W;
        if (p.x > W) p.x -= W;
        if (p.y < 0) p.y += H;
        if (p.y > H) p.y -= H;
      });

      // Draw connections
      ctx!.lineWidth = 1;
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const pi = particles[i];
          const pj = particles[j];
          const dx = pi.x - pj.x;
          const dy = pi.y - pj.y;
          if (dx * dx + dy * dy < 1600) {
            const avgCoh = (pi.coherence + pj.coherence) / 2;
            ctx!.beginPath();
            ctx!.moveTo(pi.x, pi.y);
            ctx!.lineTo(pj.x, pj.y);
            ctx!.strokeStyle = colorMode === "dark" 
              ? `rgba(31,130,192,${avgCoh * 0.15})`
              : `rgba(0,71,153,${avgCoh * 0.25})`;
            ctx!.stroke();
          }
        }
      }

      // Draw dots
      particles.forEach(p => {
        if (p.coherence > 0.7) {
          ctx!.beginPath();
          ctx!.arc(p.x, p.y, 7, 0, Math.PI * 2);
          ctx!.fillStyle = colorMode === "dark" ? "rgba(242,169,0,0.2)" : "rgba(200,130,0,0.15)";
          ctx!.fill();
          
          ctx!.beginPath();
          ctx!.arc(p.x, p.y, 3, 0, Math.PI * 2);
          ctx!.fillStyle = goldColor;
          ctx!.fill();
        } else if (p.coherence < 0.3) {
          ctx!.beginPath();
          ctx!.arc(p.x, p.y, 2, 0, Math.PI * 2);
          ctx!.fillStyle = colorMode === "dark" ? "rgba(31,130,192,0.5)" : "rgba(0,71,153,0.4)";
          ctx!.fill();
        } else {
          // Interpolate
          ctx!.beginPath();
          ctx!.arc(p.x, p.y, 2.5, 0, Math.PI * 2);
          ctx!.fillStyle = colorMode === "dark" ? "rgba(100,150,150,0.7)" : "rgba(100,100,150,0.7)";
          ctx!.fill();
        }
      });

      // Draw readout
      const avg = (totalCoherence / particles.length) * 100;
      ctx!.fillStyle = textColor;
      ctx!.font = "9px Menlo, monospace";
      ctx!.fillText(`COHERENCE: ${avg.toFixed(1)}%`, 10, H - 10);

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