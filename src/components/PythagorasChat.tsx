import React, { useState, useRef, useEffect } from "react";
import { MessageSquare, Send, Bot, User, Sparkles, Server } from "lucide-react";
import { ChatMessage } from "../types";

export const PythagorasChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "initial",
      role: "model",
      content: `### PYTHAGORAS-v2 Subspace Cryptography AI Online
\nI am initialized and ready to verify spatial mining optimizations. 
\nMy systems are designed to parse **dodecahedral Hilbert spaces**, rotate **eigenvector phases** with the Golden Ratio $\\Phi$, and optimize Grover iterations to mathematically annihilate classical ASIC hardware velocity. 
\nAsk me any question regarding the underlying mathematics, speedup theorems, or configuration parameters.`,
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [inputValue, setInputValue] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [activeEngine, setActiveEngine] = useState<string>("Detecting Active Engine...");

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const sendMessage = async (textToSend: string) => {
    if (!textToSend.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: "usr_" + Date.now(),
      role: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const historyPayload = messages.map(msg => ({
        role: msg.role === "model" ? "model" : "user",
        parts: [{ text: msg.content }]
      }));

      const response = await fetch("/api/ai/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: textToSend,
          history: historyPayload
        })
      });

      const data = await response.json();
      
      const aiMessage: ChatMessage = {
        id: "ai_" + Date.now(),
        role: "model",
        content: data.reply || "No reply generated.",
        timestamp: new Date().toLocaleTimeString()
      };

      if (data.model) {
        setActiveEngine(data.model + (data.fallback ? " (Local Fallback)" : " (Premium link)"));
      }

      setMessages(prev => [...prev, aiMessage]);
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        {
          id: "err_" + Date.now(),
          role: "model",
          content: `### Telemetry Interrupted
\nMy apologies, but my connection endpoint suffered a mathematical interruption: \`${err.message}\`. 
\nPlease ensure your local Express dev server is running on port 3000.`,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  const chips = [
    { label: "ASIC vs Quantum O(√I)", text: "How does the O(√I) structured search annihilate ASIC advantage?" },
    { label: "Phase Resonance (Φ^15)", text: "Explain how our golden ratio modulations Φ^15 prevent decoherence and stabilize state vectors." },
    { label: "Proof complexity", text: "Prove mathematically that Dodecahedral symmetry reduces quantum entropy." }
  ];

  return (
    <div className="bg-white border border-sand-dark rounded-xl h-[580px] flex flex-col shadow-sm">
      {/* HEADER */}
      <div className="p-4 border-b border-[#E2E4E9] flex items-center justify-between bg-sand rounded-t-xl shrink-0 font-sans">
        <div className="flex items-center gap-2">
          <Bot className="text-clicquot-orange w-4.5 h-4.5" />
          <div>
            <span className="text-xs font-mono font-bold text-oxford tracking-wider uppercase block">
              PYTHAGORAS-v2 Coprocessor
            </span>
            <span className="text-[9px] font-mono text-lux-slate block">
              Quantum Cryptography AI
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1 text-[9px] font-mono text-lux-slate bg-white px-2 py-1 rounded border border-[#E2E4E9]">
          <Server className="w-3 h-3 text-oxford shrink-0" />
          <span className="truncate max-w-[130px] text-oxford font-bold">{activeEngine === "Detecting Active Engine..." ? "PYTHAGORAS Engine ready" : activeEngine}</span>
        </div>
      </div>

      {/* MESSAGES SENSOR CONTAINER */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white">
        {messages.map((msg) => {
          const isAI = msg.role === "model";
          return (
            <div key={msg.id} className={`flex max-w-[85%] flex-col ${isAI ? "mr-auto" : "ml-auto"}`}>
              <div className="flex items-center gap-1.5 text-[9px] font-mono text-lux-slate mb-1 px-1">
                {isAI ? (
                  <>
                    <Sparkles className="w-2.5 h-2.5 text-clicquot-orange" />
                    <span className="font-bold text-oxford">PYTHAGORAS-v2</span>
                  </>
                ) : (
                  <>
                    <User className="w-2.5 h-2.5 text-lux-slate" />
                    <span className="font-bold text-clicquot-orange">OPERATOR</span>
                  </>
                )}
                <span>• {msg.timestamp}</span>
              </div>
              <div 
                className={`p-3 rounded-lg border text-xs leading-relaxed font-sans ${
                  isAI 
                    ? "bg-[#F8FAFC] border-[#E2E4E9] text-[#1A1A1E]" 
                    : "bg-[#F4F4F7] border-[#E2E4E9] text-[#1A1A1E]"
                }`}
              >
                {/* Manual simple markdown processing for code/subtitles */}
                {msg.content.split("\n").map((line, lIdx) => {
                  if (line.startsWith("### ")) {
                    return <h4 key={lIdx} className="font-mono text-xs font-bold text-black mt-2 mb-1 uppercase">{line.slice(4)}</h4>;
                  }
                  if (line.startsWith("**")) {
                    return <p key={lIdx} className="font-bold text-[#1A1A1E] my-1">{line}</p>;
                  }
                  if (line.includes("$$")) {
                    // Render simple formula center-aligned
                    const cleanFormula = line.replace(/\$\$/g, "");
                    return (
                      <div key={lIdx} className="bg-white border border-[#E2E4E9] p-2 my-2 text-center rounded font-mono text-black text-[11px] tracking-normal overflow-x-auto">
                        {cleanFormula}
                      </div>
                    );
                  }
                  if (line.trim().startsWith("- ")) {
                    return (
                      <ul key={lIdx} className="list-disc pl-4 space-y-0.5 my-1 text-[#334155]">
                        <li>{line.substring(2)}</li>
                      </ul>
                    );
                  }
                  return <p key={lIdx} className="my-1 text-[#334155] whitespace-pre-wrap leading-relaxed">{line}</p>;
                })}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex mr-auto flex-col max-w-[85%]">
            <div className="flex items-center gap-1.5 text-[9px] font-mono text-[#94A3B8] mb-1 px-1">
              <Bot className="w-2.5 h-2.5 text-black shrink-0" />
              <span className="font-bold text-[#1A1A1E]">PYTHAGORAS-v2</span>
              <span>• Computing...</span>
            </div>
            <div className="p-3 bg-[#F8FAFC] border border-[#E2E4E9] rounded-lg text-xs flex items-center gap-2">
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 bg-black rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-1.5 h-1.5 bg-black rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-1.5 h-1.5 bg-black rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
              <span className="text-[#64748B] font-mono text-[10px]">Tuning phase angles...</span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* QUICK CHIPS ACCESS */}
      <div className="px-4 py-2 border-t border-[#E2E4E9] bg-sand flex flex-wrap gap-1.5 shrink-0">
        {chips.map((chip, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => sendMessage(chip.text)}
            className="text-[9px] font-mono border border-sand-dark hover:border-clicquot-orange bg-white hover:bg-clicquot-orange/5 text-oxford px-2.5 py-1 rounded transition-colors active:scale-95 cursor-pointer"
          >
            {chip.label}
          </button>
        ))}
      </div>

      {/* INPUT ZONE */}
      <div className="p-3 border-t border-[#E2E4E9] bg-[#FAF9F6] rounded-b-xl shrink-0">
        <div className="flex items-center gap-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Interrogate PYTHAGORAS-v2..."
            rows={1}
            className="flex-1 max-h-16 resize-none bg-white border border-[#E2E4E9] hover:border-[#64748B] focus:border-clicquot-orange text-xs text-oxford rounded-md p-2.5 font-mono outline-none transition-colors focus:ring-1 focus:ring-clicquot-orange"
          />
          <button
            type="button"
            onClick={() => sendMessage(inputValue)}
            disabled={!inputValue.trim() || isLoading}
            className="bg-oxford text-white hover:bg-mckinsey-blue border border-clicquot-gold disabled:bg-[#E2E4E9] disabled:text-[#94A3B8] disabled:border-none p-2.5 rounded-md transition-colors active:scale-95 shrink-0 cursor-pointer"
          >
            <Send className="w-4 h-4 fill-current" />
          </button>
        </div>
      </div>
    </div>
  );
};
