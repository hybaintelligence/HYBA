import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Lock, X, Check, ShieldAlert } from 'lucide-react';

interface PoolSecretsConfigProps {
  poolName: string;
  onClose: () => void;
  onSave: (username: string, secret: string) => void;
  initialUsername?: string;
}

export const PoolSecretsConfig: React.FC<PoolSecretsConfigProps> = ({ poolName, onClose, onSave, initialUsername }) => {
  const [username, setUsername] = useState(initialUsername || '');
  const [password, setPassword] = useState('');
  const [isSaved, setIsSaved] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(username, password);
    setIsSaved(true);
    setTimeout(() => {
      onClose();
    }, 1500);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-md"
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        className="bg-white border border-[#E2E4E9] rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
      >
        <div className="bg-black p-4 flex items-center justify-between text-white">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-clicquot-gold" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-widest">
              Pool Secretbox: {poolName}
            </h3>
          </div>
          <button onClick={onClose} className="hover:text-clicquot-gold transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          <div className="mb-6 flex items-start gap-3 bg-blue-50 border border-blue-100 p-3 rounded-lg">
            <ShieldAlert className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="text-[10px] font-mono text-blue-800 leading-normal">
              <strong>OPERATOR NOTICE:</strong> Solock pool authentication requires a BTC Address as the primary identifier. In the Bitcoin protocol, privacy is derived from pseudonymity; system passwords are non-critical but mandatory for Stratum v1 handshake.
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-[10px] font-mono text-[#64748B] uppercase font-bold">
                Username (BTC address)
              </label>
              <input
                type="text"
                required
                placeholder="bc1q..."
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-[#F8FAFC] border border-[#E2E4E9] rounded-lg p-2.5 font-mono text-xs text-[#1A1A1E] focus:bg-white focus:border-black outline-none transition-colors"
                autoFocus
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] font-mono text-[#64748B] uppercase font-bold">
                Secret (Password)
              </label>
              <input
                type="password"
                placeholder="x"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#F8FAFC] border border-[#E2E4E9] rounded-lg p-2.5 font-mono text-xs text-[#1A1A1E] focus:bg-white focus:border-black outline-none transition-colors"
              />
              <p className="text-[9px] text-[#94A3B8] font-mono">
                Hint: "anything" is accepted. In Bitcoin there are no secrets.
              </p>
            </div>

            <button
              type="submit"
              disabled={isSaved}
              className={`w-full font-mono text-xs font-bold py-3 rounded-xl transition-all flex items-center justify-center gap-2 ${isSaved ? 'bg-green-600 text-white' : 'bg-black text-white hover:bg-black/80'}`}
            >
              {isSaved ? (
                <>
                  <Check className="w-4 h-4" />
                  CREDENTIALS BROADCASTED
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4" />
                  LOCK SECRETBOX
                </>
              )}
            </button>
          </form>
        </div>
      </motion.div>
    </motion.div>
  );
};
