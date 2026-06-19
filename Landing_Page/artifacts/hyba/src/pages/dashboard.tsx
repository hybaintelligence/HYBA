import { motion } from "framer-motion";
import { Link } from "wouter";

export default function Dashboard() {
  return (
    <div className="min-h-screen w-full bg-background text-foreground relative overflow-hidden flex flex-col items-center justify-center">
      {/* Background Images */}
      <div className="fixed inset-0 z-0 opacity-10 pointer-events-none mix-blend-screen">
        <img 
          src="/bg-circuit.png" 
          alt="Circuit" 
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background to-transparent" />
      </div>
      
      <div className="relative z-10 flex flex-col items-center text-center max-w-xl px-4">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          className="mb-8"
        >
          <div className="w-16 h-16 border border-hyba-gold rounded-full flex items-center justify-center relative">
            <div className="absolute inset-0 rounded-full border-t border-hyba-orange animate-spin" style={{ animationDuration: '3s' }}></div>
            <div className="w-2 h-2 bg-hyba-gold rounded-full animate-pulse"></div>
          </div>
        </motion.div>

        <motion.h1 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 1, delay: 0.5 }}
          className="text-4xl font-serif text-white mb-4"
        >
          Welcome to HYBA
        </motion.h1>
        
        <motion.p
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 1, delay: 0.8 }}
          className="text-white/50 font-mono uppercase tracking-widest text-sm mb-12"
        >
          Portal Loading... Secure Connection Established.
        </motion.p>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1.5 }}
        >
          <Link href="/" className="text-xs text-hyba-blue-light hover:text-hyba-gold transition-colors font-mono uppercase tracking-widest flex items-center gap-2">
            <span className="w-4 h-px bg-current"></span>
            Return to Gateway
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
