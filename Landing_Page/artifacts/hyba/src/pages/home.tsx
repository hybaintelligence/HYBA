import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ArrowRight, Building2, Globe, FlaskConical, Sun, Moon } from "lucide-react";
import HilbertCanvas from "@/components/HilbertCanvas";
import { useTheme } from "@/App";
import QuantumTunneling from "@/components/quantum/QuantumTunneling";
import QuantumAnnealing from "@/components/quantum/QuantumAnnealing";
import QuantumSwarming from "@/components/quantum/QuantumSwarming";
import QuantumSuperposition from "@/components/quantum/QuantumSuperposition";

function StatCounter({ target, label, suffix = "", prefix = "" }: { target: number, label: string, suffix?: string, prefix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  useEffect(() => {
    if (isInView) {
      let start = 0;
      const duration = 2000;
      const startTime = performance.now();
      
      const updateCount = (currentTime: number) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing out cubic
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const currentCount = start + (target - start) * easeOut;
        
        setCount(currentCount);
        
        if (progress < 1) {
          requestAnimationFrame(updateCount);
        } else {
          setCount(target);
        }
      };
      
      requestAnimationFrame(updateCount);
    }
  }, [isInView, target]);

  // Format based on whether it's an integer or float
  const isFloat = target % 1 !== 0;
  const displayValue = isFloat ? count.toFixed(2) : Math.floor(count).toString();

  return (
    <div ref={ref} className="flex flex-col items-center justify-center p-8 gap-2">
      <div className="text-5xl font-serif text-hyba-gold">
        {prefix}{displayValue}{suffix}
      </div>
      <div className="text-xs font-mono text-foreground/40 uppercase tracking-wider text-center">
        {label}
      </div>
    </div>
  );
}

export default function Home() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isHovered, setIsHovered] = useState(false);
  const { theme, toggle } = useTheme();
  
  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (email && password) {
      setLocation("/dashboard");
    }
  };

  return (
    <div className="min-h-screen w-full bg-background text-foreground relative overflow-hidden flex flex-col">
      {/* Background Canvas */}
      <HilbertCanvas className="fixed inset-0 z-0 pointer-events-none dark:opacity-100 opacity-30" />
      
      {/* Overlay Gradient — top/bottom fade */}
      <div className="fixed inset-0 z-1 pointer-events-none bg-gradient-to-b from-background/90 via-transparent to-background/80" />
      {/* Overlay Gradient — left column darkening */}
      <div className="fixed inset-0 z-1 pointer-events-none bg-gradient-to-r from-background/85 via-transparent to-transparent" />
      {/* Overlay Gradient — right column darkening */}
      <div className="fixed inset-0 z-1 pointer-events-none bg-gradient-to-l from-background/70 via-transparent to-transparent" />
      
      {/* Header */}
      <header className="relative z-10 w-full px-8 py-6 flex items-center justify-between border-b border-border bg-transparent">
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="flex items-center gap-4"
        >
          <h1 className="text-2xl font-serif font-bold tracking-widest text-foreground">HYBA</h1>
          <div className="h-4 w-px bg-border"></div>
          <span className="text-xs uppercase tracking-widest text-hyba-gold font-mono">Analytics</span>
        </motion.div>
        
        <div className="flex items-center gap-6">
          <button onClick={toggle} className="p-2 rounded-sm border border-border hover:border-hyba-gold/40 text-foreground/50 hover:text-hyba-gold transition-all duration-300">
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
            className="flex items-center gap-3"
          >
            <div className="w-2 h-2 rounded-full bg-hyba-gold animate-pulse"></div>
            <span className="text-xs font-mono dark:text-hyba-gold/80 text-hyba-blue-dark/70 tracking-wider">CLASSIFIED INTERNAL ACCESS ONLY</span>
          </motion.div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 flex-1 flex flex-col w-full h-full overflow-y-auto">
        
        {/* Hero Section */}
        <section className="min-h-[100vh] flex flex-col lg:flex-row items-center justify-center pt-32 pb-24 px-8 lg:px-16 gap-16 max-w-[1400px] mx-auto w-full">
          {/* Left Column: Mission & Status */}
          <div className="flex-1 flex flex-col gap-8 max-w-xl z-20">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, ease: "easeOut", delay: 0.4 }}
              className="flex flex-col gap-6"
            >
              <div className="text-[10px] tracking-[0.3em] text-hyba-blue-light/70 font-mono uppercase">
                Sovereign Treasury Substrate
              </div>
              <h2 className="text-7xl lg:text-8xl font-serif font-light leading-tight tracking-tight text-foreground">
                Where<br/>
                Mathematics<br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-hyba-gold to-hyba-orange">Meets Treasury</span>
              </h2>
              
              <div className="h-px w-16 bg-hyba-gold/40 my-2"></div>
              
              <p className="text-base text-foreground/50 font-sans leading-relaxed max-w-sm">
                A privately commissioned computational substrate powering the HYBA treasury. 
                Funding research, foundation, and enterprise for the long term.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1, delay: 0.8 }}
              className="inline-flex items-center gap-3 px-4 py-2 border border-hyba-blue-light/30 bg-hyba-blue-dark/20 rounded-full w-fit mt-4 backdrop-blur-sm"
            >
              <span className="w-2 h-2 rounded-full bg-hyba-blue-light animate-pulse"></span>
              <span className="text-xs font-mono text-hyba-blue-light tracking-widest uppercase">V4-Prime · Commissioned June 2026</span>
            </motion.div>
          </div>

          {/* Right Column: Login Portal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, ease: "easeOut", delay: 0.5 }}
            className="w-full max-w-md z-20"
          >
            <div className="dark:bg-card/30 bg-white/90 backdrop-blur-xl border border-border p-12 rounded-sm shadow-2xl relative overflow-hidden min-h-[460px] flex flex-col justify-center">
              <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-hyba-gold to-hyba-orange"></div>
              
              {/* Subtle grid pattern background */}
              <div 
                className="absolute inset-0 opacity-10 pointer-events-none" 
                style={{ backgroundImage: 'radial-gradient(circle at center, rgba(255,255,255,0.8) 1px, transparent 1px)', backgroundSize: '24px 24px' }}
              />
              
              <div className="mb-10 relative z-10">
                <h3 className="text-2xl font-serif text-foreground mb-3">System Authentication</h3>
                <p className="text-sm text-foreground/50 font-sans">Enter your credentials to access the sovereign portal.</p>
              </div>

              <form onSubmit={handleLogin} className="space-y-6 relative z-10">
                <div className="space-y-3">
                  <Label htmlFor="email" className="text-xs uppercase tracking-widest text-foreground/70 font-mono">Identity</Label>
                  <Input 
                    id="email" 
                    type="email" 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="operator@hyba.io"
                    className="bg-transparent border-border text-foreground placeholder:text-foreground/20 focus-visible:ring-hyba-gold rounded-none h-12 px-4"
                    required
                  />
                </div>
                
                <div className="space-y-3">
                  <Label htmlFor="password" className="text-xs uppercase tracking-widest text-foreground/70 font-mono">Passphrase</Label>
                  <Input 
                    id="password" 
                    type="password" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="bg-transparent border-border text-foreground placeholder:text-foreground/20 focus-visible:ring-hyba-gold rounded-none h-12 px-4"
                    required
                  />
                  <p className="text-[10px] text-foreground/30 font-sans mt-2">Security protocols apply. Contact admin for access.</p>
                </div>

                <div className="pt-4">
                  <Button 
                    type="submit" 
                    onMouseEnter={() => setIsHovered(true)}
                    onMouseLeave={() => setIsHovered(false)}
                    className="w-full h-12 bg-hyba-gold hover:bg-hyba-orange text-black font-semibold tracking-widest uppercase transition-all duration-300 rounded-none group relative overflow-hidden"
                  >
                    <span className="relative z-10 flex items-center justify-center gap-2">
                      Sign In
                      <ArrowRight className={`w-4 h-4 transition-all duration-300 ${isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'}`} />
                    </span>
                  </Button>
                  <div className="mt-6 text-center">
                    <span className="text-[9px] text-foreground/20 font-mono tracking-wider">ENCRYPTED CHANNEL · TLS 1.3 · FIPS 140-2</span>
                  </div>
                </div>
              </form>
            </div>
          </motion.div>
        </section>

        {/* Stats Bar Section */}
        <section className="w-full bg-background border-y border-border relative z-20">
          <div className="max-w-[1400px] mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-border">
            <StatCounter target={7.58} label="Statistical Confidence" suffix="σ" />
            <div className="flex flex-col items-center justify-center p-8 gap-2">
              <div className="text-5xl font-serif text-hyba-gold">107/107</div>
              <div className="text-xs font-mono text-foreground/40 uppercase tracking-wider text-center">Canonical Baseline</div>
            </div>
            <StatCounter target={32} label="Manifold Capacity" />
            <StatCounter target={9} label="vs. 475 Baseline" />
          </div>
        </section>

        {/* Quantum Arsenal Section */}
        <section className="w-full py-24 px-8 lg:px-16 relative z-20">
          <div className="max-w-[1400px] mx-auto">
            {/* Section header */}
            <div className="mb-16 flex items-end justify-between">
              <div>
                <div className="text-[10px] tracking-[0.3em] text-hyba-blue-light/70 font-mono uppercase mb-3">
                  Computational Foundations
                </div>
                <h3 className="text-4xl font-serif font-light text-foreground">
                  The Quantum Arsenal
                </h3>
              </div>
              <div className="text-xs font-mono text-foreground/30 text-right hidden lg:block">
                Four sovereign mechanisms<br/>powering substrate intelligence
              </div>
            </div>

            {/* 2×2 grid of quantum visualization cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 30 }} viewport={{ once: true }} transition={{ duration: 0.8, delay: 0 }}>
                <div className="border border-border dark:bg-card/60 bg-white/80 backdrop-blur-sm p-0 overflow-hidden group hover:border-hyba-gold/30 transition-all duration-500">
                  <div className="h-[220px] relative">
                    <QuantumTunneling className="absolute inset-0" colorMode={theme} />
                  </div>
                  <div className="px-6 py-5 border-t border-border">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-serif text-base text-foreground mb-1">Quantum Tunneling</h4>
                        <p className="text-xs text-foreground/50 font-sans leading-relaxed max-w-xs">
                          Wave packets penetrating classically forbidden barriers via probability amplitude decay.
                        </p>
                      </div>
                      <div className="text-[9px] font-mono text-hyba-gold/60 tracking-widest uppercase mt-1 whitespace-nowrap ml-4">
                        Tunneling Protocol
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>

              <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 30 }} viewport={{ once: true }} transition={{ duration: 0.8, delay: 0.15 }}>
                <div className="border border-border dark:bg-card/60 bg-white/80 backdrop-blur-sm p-0 overflow-hidden group hover:border-hyba-gold/30 transition-all duration-500">
                  <div className="h-[220px] relative">
                    <QuantumAnnealing className="absolute inset-0" colorMode={theme} />
                  </div>
                  <div className="px-6 py-5 border-t border-border">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-serif text-base text-foreground mb-1">Quantum Annealing</h4>
                        <p className="text-xs text-foreground/50 font-sans leading-relaxed max-w-xs">
                          Golden-ratio guided energy minimization via temperature-scheduled quantum fluctuations.
                        </p>
                      </div>
                      <div className="text-[9px] font-mono text-hyba-gold/60 tracking-widest uppercase mt-1 whitespace-nowrap ml-4">
                        Φ-Annealing
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>

              <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 30 }} viewport={{ once: true }} transition={{ duration: 0.8, delay: 0.3 }}>
                <div className="border border-border dark:bg-card/60 bg-white/80 backdrop-blur-sm p-0 overflow-hidden group hover:border-hyba-gold/30 transition-all duration-500">
                  <div className="h-[220px] relative">
                    <QuantumSwarming className="absolute inset-0" colorMode={theme} />
                  </div>
                  <div className="px-6 py-5 border-t border-border">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-serif text-base text-foreground mb-1">Quantum Swarming</h4>
                        <p className="text-xs text-foreground/50 font-sans leading-relaxed max-w-xs">
                          Coherent multi-agent lane intelligence exhibiting collective phase synchronisation.
                        </p>
                      </div>
                      <div className="text-[9px] font-mono text-hyba-gold/60 tracking-widest uppercase mt-1 whitespace-nowrap ml-4">
                        Swarm Coherence
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>

              <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 30 }} viewport={{ once: true }} transition={{ duration: 0.8, delay: 0.45 }}>
                <div className="border border-border dark:bg-card/60 bg-white/80 backdrop-blur-sm p-0 overflow-hidden group hover:border-hyba-gold/30 transition-all duration-500">
                  <div className="h-[220px] relative">
                    <QuantumSuperposition className="absolute inset-0" colorMode={theme} />
                  </div>
                  <div className="px-6 py-5 border-t border-border">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-serif text-base text-foreground mb-1">Superposition</h4>
                        <p className="text-xs text-foreground/50 font-sans leading-relaxed max-w-xs">
                          Simultaneous multi-state wave function evolution collapsing at measurement boundary.
                        </p>
                      </div>
                      <div className="text-[9px] font-mono text-hyba-gold/60 tracking-widest uppercase mt-1 whitespace-nowrap ml-4">
                        Ψ Superposition
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>

            </div>
          </div>
        </section>

        {/* Pillars Section */}
        <section className="w-full py-32 px-8 lg:px-16 relative z-20">
          <div className="max-w-[1200px] mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Pillar 1 */}
              <motion.div 
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="group flex flex-col justify-between bg-card border border-white/5 p-8 min-h-[240px] hover:border-hyba-gold/30 hover:shadow-[0_0_20px_rgba(242,169,0,0.1)] transition-all duration-500 relative overflow-hidden"
              >
                <div>
                  <div className="w-10 h-10 flex items-center justify-center bg-hyba-blue-dark/40 border border-hyba-blue-mid/20 rounded-sm mb-6">
                    <Building2 className="w-5 h-5 text-white" />
                  </div>
                  <h4 className="font-serif text-xl text-foreground mb-3">HYBA Company</h4>
                  <p className="font-sans text-sm text-foreground/50 leading-relaxed">
                    Sovereign enterprise operations. The operational core of the HYBA group.
                  </p>
                </div>
                <div className="h-[2px] w-full bg-hyba-gold/50 mt-8 group-hover:bg-hyba-gold transition-colors duration-500"></div>
              </motion.div>

              {/* Pillar 2 */}
              <motion.div 
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
                className="group flex flex-col justify-between bg-card border border-white/5 p-8 min-h-[240px] hover:border-hyba-gold/30 hover:shadow-[0_0_20px_rgba(242,169,0,0.1)] transition-all duration-500 relative overflow-hidden"
              >
                <div>
                  <div className="w-10 h-10 flex items-center justify-center bg-hyba-blue-dark/40 border border-hyba-blue-mid/20 rounded-sm mb-6">
                    <Globe className="w-5 h-5 text-white" />
                  </div>
                  <h4 className="font-serif text-xl text-foreground mb-3">HYBA Foundation</h4>
                  <p className="font-sans text-sm text-foreground/50 leading-relaxed">
                    Philanthropic capital deployment. Advancing science, education, and public good.
                  </p>
                </div>
                <div className="h-[2px] w-full bg-hyba-blue-mid/50 mt-8 group-hover:bg-hyba-blue-mid transition-colors duration-500"></div>
              </motion.div>

              {/* Pillar 3 */}
              <motion.div 
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, ease: "easeOut", delay: 0.4 }}
                className="group flex flex-col justify-between bg-card border border-white/5 p-8 min-h-[240px] hover:border-hyba-gold/30 hover:shadow-[0_0_20px_rgba(242,169,0,0.1)] transition-all duration-500 relative overflow-hidden"
              >
                <div>
                  <div className="w-10 h-10 flex items-center justify-center bg-hyba-blue-dark/40 border border-hyba-blue-mid/20 rounded-sm mb-6">
                    <FlaskConical className="w-5 h-5 text-white" />
                  </div>
                  <h4 className="font-serif text-xl text-foreground mb-3">HYBA Research</h4>
                  <p className="font-sans text-sm text-foreground/50 leading-relaxed">
                    Computational discovery at the frontier. Where mathematical theory meets applied intelligence.
                  </p>
                </div>
                <div className="h-[2px] w-full bg-hyba-blue-light/50 mt-8 group-hover:bg-hyba-blue-light transition-colors duration-500"></div>
              </motion.div>
            </div>
          </div>
        </section>
      </main>
      
      {/* Footer */}
      <footer className="relative z-10 w-full px-8 py-6 flex justify-between items-center text-xs font-mono text-foreground/30 border-t border-border mt-auto bg-transparent">
        <span>&copy; 2026 HYBA Analytics Ltd. London.</span>
        <span>Secured Substrate</span>
      </footer>
    </div>
  );
}
