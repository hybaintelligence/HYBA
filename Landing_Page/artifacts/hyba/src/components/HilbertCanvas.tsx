import { useRef, useEffect } from 'react';

const PHI = (1 + Math.sqrt(5)) / 2;
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

interface Particle {
  x: number; y: number; z: number;
  baseTheta: number; basePhi: number;
  lane: number; isGold: boolean; size: number;
}

function project(
  x: number, y: number, z: number,
  cx: number, cy: number, fov: number
): [number, number, number] {
  const dz = z + 7;
  if (dz <= 0) return [-9999, -9999, 0];
  const scale = fov / dz;
  return [cx + x * scale, cy - y * scale, scale];
}

function buildIcosahedron(radius: number): [number, number, number][] {
  const t = PHI;
  const raw: [number, number, number][] = [
    [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
    [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
    [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1],
  ];
  return raw.map(([x, y, z]) => {
    const len = Math.sqrt(x * x + y * y + z * z);
    return [x / len * radius, y / len * radius, z / len * radius];
  });
}

const ICO_FACES = [
  [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
  [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
  [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
  [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
];

function rotateY(x: number, y: number, z: number, a: number): [number, number, number] {
  return [x * Math.cos(a) + z * Math.sin(a), y, -x * Math.sin(a) + z * Math.cos(a)];
}
function rotateX(x: number, y: number, z: number, a: number): [number, number, number] {
  return [x, y * Math.cos(a) - z * Math.sin(a), y * Math.sin(a) + z * Math.cos(a)];
}

export default function HilbertCanvas({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const LANES = 32;
    const PER_LANE = 48;
    const TOTAL = LANES * PER_LANE;
    const SPHERE_R = 2.5;

    const particles: Particle[] = [];
    for (let i = 0; i < TOTAL; i++) {
      const lane = Math.floor(i / PER_LANE);
      const isGold = lane % 8 < 3;
      const theta = i * GOLDEN_ANGLE;
      const phi = Math.acos(1 - 2 * (i + 0.5) / TOTAL);
      particles.push({
        x: SPHERE_R * Math.sin(phi) * Math.cos(theta),
        y: SPHERE_R * Math.sin(phi) * Math.sin(theta),
        z: SPHERE_R * Math.cos(phi),
        baseTheta: theta,
        basePhi: phi,
        lane, isGold, size: isGold ? 2.2 : 1.5,
      });
    }

    const icoVerts = buildIcosahedron(2.8);
    const icoVertsInner = buildIcosahedron(1.9);

    let rafId: number;
    let startTime = performance.now();

    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    function resize() {
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
    }
    resize();

    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    function draw() {
      const t = (performance.now() - startTime) * 0.001;
      const W = canvas.width;
      const H = canvas.height;
      const cx = W / 2;
      const cy = H / 2;
      const fov = Math.min(W, H) * 0.55;

      ctx.clearRect(0, 0, W, H);

      const rotY = t * 0.08;
      const rotX = t * 0.03;

      function applyRot(px: number, py: number, pz: number): [number, number, number] {
        let [rx, ry, rz] = rotateY(px, py, pz, rotY);
        [rx, ry, rz] = rotateX(rx, ry, rz, rotX);
        return [rx, ry, rz];
      }
      function applyRotReverse(px: number, py: number, pz: number): [number, number, number] {
        let [rx, ry, rz] = rotateY(px, py, pz, -rotY * 1.3);
        [rx, ry, rz] = rotateX(rx, ry, rz, -rotX * 1.3);
        return [rx, ry, rz];
      }

      const pulseR = 1 + 0.04 * Math.sin(t * Math.PI * 2 / 8);

      const glowR = Math.min(W, H) * 0.55 * pulseR;
      const grd = ctx.createRadialGradient(cx, cy, 0, cx, cy, glowR);
      grd.addColorStop(0, 'rgba(0,47,108,0.18)');
      grd.addColorStop(0.5, 'rgba(0,47,108,0.06)');
      grd.addColorStop(1, 'rgba(0,47,108,0)');
      ctx.fillStyle = grd;
      ctx.fillRect(0, 0, W, H);

      ctx.lineWidth = 0.6 / dpr;
      for (const face of ICO_FACES) {
        const verts = face.map(vi => {
          const [vx, vy, vz] = icoVerts[vi];
          const [rx, ry, rz] = applyRot(vx, vy, vz);
          return project(rx, ry, rz, cx, cy, fov);
        });
        if (verts.some(([, , s]) => s <= 0)) continue;
        ctx.beginPath();
        ctx.moveTo(verts[0][0], verts[0][1]);
        ctx.lineTo(verts[1][0], verts[1][1]);
        ctx.lineTo(verts[2][0], verts[2][1]);
        ctx.closePath();
        ctx.strokeStyle = 'rgba(31,130,192,0.13)';
        ctx.stroke();
      }

      for (const face of ICO_FACES) {
        const verts = face.map(vi => {
          const [vx, vy, vz] = icoVertsInner[vi];
          const [rx, ry, rz] = applyRotReverse(vx, vy, vz);
          return project(rx, ry, rz, cx, cy, fov);
        });
        if (verts.some(([, , s]) => s <= 0)) continue;
        ctx.beginPath();
        ctx.moveTo(verts[0][0], verts[0][1]);
        ctx.lineTo(verts[1][0], verts[1][1]);
        ctx.lineTo(verts[2][0], verts[2][1]);
        ctx.closePath();
        ctx.strokeStyle = 'rgba(242,169,0,0.07)';
        ctx.stroke();
      }

      const projected: [number, number, number][] = [];
      for (let i = 0; i < TOTAL; i++) {
        const p = particles[i];
        const drift = t * 0.04 * ((p.lane % 5) + 1);
        const theta = p.baseTheta + drift;
        const phi = p.basePhi + Math.sin(t * 0.12 + p.lane * 0.4) * 0.08;
        const px = SPHERE_R * Math.sin(phi) * Math.cos(theta);
        const py = SPHERE_R * Math.sin(phi) * Math.sin(theta);
        const pz = SPHERE_R * Math.cos(phi);
        const [rx, ry, rz] = applyRot(px, py, pz);
        projected.push(project(rx, ry, rz, cx, cy, fov));
      }

      const stride = 8;
      ctx.lineWidth = 0.5 / dpr;
      for (let i = 0; i < TOTAL; i += stride) {
        const j = (i + Math.floor(TOTAL / 16)) % TOTAL;
        const [ax, ay, as_] = projected[i];
        const [bx, by, bs_] = projected[j];
        if (as_ <= 0 || bs_ <= 0) continue;
        const dx = bx - ax; const dy = by - ay;
        if (dx * dx + dy * dy > (fov * 0.5) ** 2) continue;
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(bx, by);
        ctx.strokeStyle = 'rgba(0,91,153,0.18)';
        ctx.stroke();
      }

      for (let i = 0; i < TOTAL; i++) {
        const p = particles[i];
        const [px, py, ps_] = projected[i];
        if (ps_ <= 0) continue;
        const r = p.size * Math.min(ps_ * 0.012, 1.8);
        ctx.beginPath();
        ctx.arc(px, py, r, 0, Math.PI * 2);
        const alpha = 0.3 + Math.min(ps_ * 0.07, 0.65);
        ctx.fillStyle = p.isGold
          ? `rgba(242,169,0,${alpha})`
          : `rgba(31,130,192,${alpha})`;
        ctx.fill();
      }

      rafId = requestAnimationFrame(draw);
    }

    draw();

    return () => {
      cancelAnimationFrame(rafId);
      ro.disconnect();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{ width: '100%', height: '100%', display: 'block' }}
    />
  );
}
