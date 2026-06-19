import React, { useMemo, useState } from "react";
import { motion } from "motion/react";
import { Lock, X, Check, ShieldAlert } from "lucide-react";
import type { ConfigurePoolRequest, PoolInfo } from "../apiClient";

interface PoolSecretsConfigProps {
  pool: PoolInfo;
  onClose: () => void;
  onSave: (payload: ConfigurePoolRequest, connectAfterSave: boolean) => Promise<void> | void;
}

function poolInstructions(poolId?: string): string {
  switch (poolId) {
    case "viabtc":
      return "ViaBTC requires only your pool username/worker and password.";
    case "braiins":
      return "Braiins requires only your pool username and password.";
    case "ckpool":
      return "CKPool requires only a BTC address. The backend uses a non-secret Stratum password placeholder.";
    case "nicehash":
      return "NiceHash requires worker and NH pool id. The backend resolves them into the Stratum username.";
    default:
      return "Configure the required pool fields. Secrets are redacted when read back from the API.";
  }
}

export const PoolSecretsConfig: React.FC<PoolSecretsConfigProps> = ({ pool, onClose, onSave }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [btcAddress, setBtcAddress] = useState("");
  const [worker, setWorker] = useState("");
  const [nicehashPoolId, setNicehashPoolId] = useState("");
  const [url, setUrl] = useState(pool.url || "");
  const [connectAfterSave, setConnectAfterSave] = useState(true);
  const [isSaved, setIsSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const poolId = pool.pool_id || "";
  const credentialMode = pool.credential_mode;
  const title = pool.name || poolId || "Mining Pool";

  const requiredFields = useMemo(() => new Set(pool.required_fields || []), [pool.required_fields]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const payload: ConfigurePoolRequest = {
      pool_id: poolId,
      url,
      enabled: true,
    };
    if (credentialMode === "username_password") {
      payload.username = username;
      payload.password = password;
    } else if (credentialMode === "btc_address") {
      payload.btc_address = btcAddress;
    } else if (credentialMode === "nicehash_worker_pool_id") {
      payload.worker = worker;
      payload.nicehash_pool_id = nicehashPoolId;
      if (password) payload.password = password;
    }
    try {
      await onSave(payload, connectAfterSave);
      setIsSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pool configuration failed");
    }
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
        className="bg-white border border-[#E2E4E9] rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden"
      >
        <div className="bg-black p-4 flex items-center justify-between text-white">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-clicquot-gold" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-widest">
              Pool Config: {title}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="hover:text-clicquot-gold transition-colors"
            aria-label="Close pool configuration"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          <div className="mb-5 flex items-start gap-3 bg-blue-50 border border-blue-100 p-3 rounded-lg">
            <ShieldAlert className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="text-[10px] font-mono text-blue-800 leading-normal">
              <strong>OPERATOR NOTICE:</strong> {poolInstructions(poolId)} Values are sent to the
              authenticated backend and are never echoed back in clear text.
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label
                htmlFor="pool-config-url"
                className="text-[10px] font-mono text-[#64748B] uppercase font-bold"
              >
                Pool URL
              </label>
              <input
                id="pool-config-url"
                type="text"
                required
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full bg-[#F8FAFC] border border-[#E2E4E9] rounded-lg p-2.5 font-mono text-xs text-[#1A1A1E] focus:bg-white focus:border-black outline-none transition-colors"
              />
            </div>

            {credentialMode === "username_password" && (
              <>
                <TextInput
                  label="Username"
                  value={username}
                  setValue={setUsername}
                  required={requiredFields.has("username")}
                  placeholder="pool-account.worker"
                />
                <TextInput
                  label="Password"
                  value={password}
                  setValue={setPassword}
                  required={requiredFields.has("password")}
                  placeholder="pool password"
                  type="password"
                />
              </>
            )}

            {credentialMode === "btc_address" && (
              <TextInput
                label="BTC Address"
                value={btcAddress}
                setValue={setBtcAddress}
                required={requiredFields.has("btc_address")}
                placeholder="bc1q..."
              />
            )}

            {credentialMode === "nicehash_worker_pool_id" && (
              <>
                <TextInput
                  label="Worker"
                  value={worker}
                  setValue={setWorker}
                  required={requiredFields.has("worker")}
                  placeholder="worker-name"
                />
                <TextInput
                  label="NH Pool ID"
                  value={nicehashPoolId}
                  setValue={setNicehashPoolId}
                  required={requiredFields.has("nicehash_pool_id")}
                  placeholder="nicehash pool id"
                />
                <TextInput
                  label="Optional Password"
                  value={password}
                  setValue={setPassword}
                  required={false}
                  placeholder="defaults to x when empty"
                  type="password"
                />
              </>
            )}

            <label className="flex items-center gap-2 text-[10px] font-mono text-[#64748B]">
              <input
                type="checkbox"
                checked={connectAfterSave}
                onChange={(event) => setConnectAfterSave(event.target.checked)}
              />
              Configure and switch/connect immediately
            </label>

            {error && (
              <div className="text-[10px] font-mono text-red-700 bg-red-50 border border-red-100 p-2 rounded">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isSaved}
              className={`w-full font-mono text-xs font-bold py-3 rounded-xl transition-all flex items-center justify-center gap-2 ${isSaved ? "bg-green-600 text-white" : "bg-black text-white hover:bg-black/80"}`}
            >
              {isSaved ? (
                <>
                  <Check className="w-4 h-4" /> CONFIGURED
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4" /> SAVE POOL CONFIG
                </>
              )}
            </button>
          </form>
        </div>
      </motion.div>
    </motion.div>
  );
};

function TextInput({
  label,
  value,
  setValue,
  placeholder,
  required,
  type = "text",
}: {
  label: string;
  value: string;
  setValue: (value: string) => void;
  placeholder: string;
  required: boolean;
  type?: string;
}) {
  const inputId = `pool-${label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
  return (
    <div className="space-y-1.5">
      <label htmlFor={inputId} className="text-[10px] font-mono text-[#64748B] uppercase font-bold">
        {label}
      </label>
      <input
        id={inputId}
        type={type}
        required={required}
        placeholder={placeholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="w-full bg-[#F8FAFC] border border-[#E2E4E9] rounded-lg p-2.5 font-mono text-xs text-[#1A1A1E] focus:bg-white focus:border-black outline-none transition-colors"
      />
    </div>
  );
}
