"use client";

import React, { useState, useMemo } from "react";
import {
  Terminal,
  Play,
  Copy,
  Check,
  Code2,
  Clock,
  Layers,
  FileJson,
  Volume2,
  Loader2,
} from "lucide-react";
import { useTTSStore } from "@/store/ttsStore";

type SnippetTab = "curl" | "python" | "javascript";

export function ApiPlayground() {
  const { voices, emotionsCatalog } = useTTSStore();

  // Form State
  const [selectedEndpoint, setSelectedEndpoint] = useState<string>("/api/tts");
  const [promptText, setPromptText] = useState(
    "Stop scroll dulu! Tahu nggak kenapa 90 persen kreator gagal monetisasi di bulan pertama? Ini dia rahasianya!"
  );
  const [voiceId, setVoiceId] = useState("piper_id_gadis_fast");
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(0.0);
  const [emotion, setEmotion] = useState("antusias");
  const [engine, setEngine] = useState("piper");

  // Code Tab
  const [activeSnippetTab, setActiveSnippetTab] = useState<SnippetTab>("curl");
  const [copied, setCopied] = useState(false);

  // Execution State
  const [isRunning, setIsRunning] = useState(false);
  const [responseStatus, setResponseStatus] = useState<number | null>(null);
  const [responseHeaders, setResponseHeaders] = useState<Record<string, string>>({});
  const [responseBody, setResponseBody] = useState<any>(null);
  const [executionTimeMs, setExecutionTimeMs] = useState<number | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // Generate code snippets dynamically
  const codeSnippets = useMemo(() => {
    const payloadObj: any = {
      text: promptText,
      voice_id: voiceId,
      speed: speed,
      pitch: pitch,
      emotion: emotion,
      engine: engine,
    };
    const jsonStr = JSON.stringify(payloadObj, null, 2);

    const curl = `curl -X POST "http://127.0.0.1:8000/api/tts" \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify(payloadObj)}'`;

    const python = `import requests

url = "http://127.0.0.1:8000/api/tts"
payload = ${JSON.stringify(payloadObj, null, 4)}

response = requests.post(url, json=payload)
data = response.json()
print("Audio URL:", data.get("audio_url"))`;

    const javascript = `// Panggil endpoint sintesis TaSTP
const response = await fetch("http://127.0.0.1:8000/api/tts", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify(${jsonStr}),
});

const result = await response.json();
console.log("Status:", result.status, "Audio:", result.audio_url);`;

    return { curl, python, javascript };
  }, [promptText, voiceId, speed, pitch, emotion, engine]);

  const handleCopyCode = () => {
    const textToCopy = codeSnippets[activeSnippetTab];
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunRequest = async () => {
    setIsRunning(true);
    setResponseStatus(null);
    setResponseBody(null);
    setAudioUrl(null);
    const startT = performance.now();

    try {
      if (selectedEndpoint === "/api/voices") {
        const res = await fetch("/api/voices");
        const json = await res.json();
        setResponseStatus(res.status);
        setExecutionTimeMs(Math.round(performance.now() - startT));
        setResponseBody(json);
        const headersMap: Record<string, string> = {};
        res.headers.forEach((v, k) => (headersMap[k] = v));
        setResponseHeaders(headersMap);
      } else if (selectedEndpoint === "/api/health") {
        const res = await fetch("/api/health");
        const json = await res.json();
        setResponseStatus(res.status);
        setExecutionTimeMs(Math.round(performance.now() - startT));
        setResponseBody(json);
        const headersMap: Record<string, string> = {};
        res.headers.forEach((v, k) => (headersMap[k] = v));
        setResponseHeaders(headersMap);
      } else if (selectedEndpoint === "/api/emotions/analyze") {
        const res = await fetch("/api/emotions/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: promptText }),
        });
        const json = await res.json();
        setResponseStatus(res.status);
        setExecutionTimeMs(Math.round(performance.now() - startT));
        setResponseBody(json);
        const headersMap: Record<string, string> = {};
        res.headers.forEach((v, k) => (headersMap[k] = v));
        setResponseHeaders(headersMap);
      } else {
        // Default: POST /api/tts
        const res = await fetch("/api/tts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: promptText,
            voice_id: voiceId,
            speed,
            pitch,
            emotion,
            engine,
          }),
        });
        const json = await res.json();
        setResponseStatus(res.status);
        setExecutionTimeMs(Math.round(performance.now() - startT));
        setResponseBody(json);
        if (json.audio_url) setAudioUrl(json.audio_url);
        const headersMap: Record<string, string> = {};
        res.headers.forEach((v, k) => (headersMap[k] = v));
        setResponseHeaders(headersMap);
      }
    } catch (err: any) {
      setResponseStatus(500);
      setExecutionTimeMs(Math.round(performance.now() - startT));
      setResponseBody({ error: err.message || "Gagal menghubungi server" });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="flex-1 h-screen overflow-y-auto p-6 md:p-8 bg-background max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="border-b border-border pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Terminal className="w-5 h-5 text-fg" strokeWidth={1.5} />
            <h1 className="text-lg font-semibold text-fg">API Playground</h1>
            <span className="text-[10px] px-2 py-0.5 rounded bg-panel border border-border text-muted font-mono uppercase">
              REST CLIENT
            </span>
          </div>
          <p className="text-xs text-muted">
            Uji coba langsung endpoint REST API mandiri TaSTP, inspect payload respons, dan salin kode integrasi.
          </p>
        </div>

        {/* Endpoint Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted">Endpoint:</span>
          <select
            value={selectedEndpoint}
            onChange={(e) => setSelectedEndpoint(e.target.value)}
            className="input-base text-xs py-1.5 bg-surface font-mono w-auto"
          >
            <option value="/api/tts">POST /api/tts (Sintesis Suara)</option>
            <option value="/api/voices">GET /api/voices (Katalog Suara)</option>
            <option value="/api/health">GET /api/health (Status Hardware)</option>
            <option value="/api/emotions/analyze">POST /api/emotions/analyze (Deteksi Emosi)</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Kolom Kiri: Parameter Request & Code Generator */}
        <div className="space-y-4">
          <div className="card-panel space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-2.5">
              <h2 className="text-xs font-semibold text-fg flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-fg" strokeWidth={1.5} /> Parameter Permintaan
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-panel border border-border text-muted">
                {selectedEndpoint.startsWith("/api/voices") || selectedEndpoint.startsWith("/api/health")
                  ? "GET"
                  : "POST"}{" "}
                JSON
              </span>
            </div>

            {/* Input Naskah Teks */}
            <div>
              <label className="text-xs font-medium text-fg block mb-1">Naskah Teks (text)</label>
              <textarea
                rows={3}
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                className="input-base text-xs resize-none font-sans"
              />
              {/* Preset Buttons */}
              <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                <button
                  type="button"
                  onClick={() =>
                    setPromptText("Stop scroll dulu! Ini rahasia algoritma konten yang jarang dibongkar kreator!")
                  }
                  className="text-[10px] px-2 py-0.5 rounded bg-surface border border-border text-muted hover:text-fg hover:border-fg transition-colors"
                >
                  Promosi Video
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setPromptText("Tahukah Anda, paus biru adalah hewan terbesar yang pernah hidup di bumi?")
                  }
                  className="text-[10px] px-2 py-0.5 rounded bg-surface border border-border text-muted hover:text-fg hover:border-fg transition-colors"
                >
                  Fakta Unik
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setPromptText("Halo semua, selamat datang di obrolan santai kita malam hari ini.")
                  }
                  className="text-[10px] px-2 py-0.5 rounded bg-surface border border-border text-muted hover:text-fg hover:border-fg transition-colors"
                >
                  Podcast Santai
                </button>
              </div>
            </div>

            {/* Parameter Baris */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-muted block mb-1">Voice ID</label>
                <select
                  value={voiceId}
                  onChange={(e) => setVoiceId(e.target.value)}
                  className="input-base text-xs bg-surface"
                >
                  {voices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-muted block mb-1">Preset Emosi</label>
                <select
                  value={emotion}
                  onChange={(e) => setEmotion(e.target.value)}
                  className="input-base text-xs bg-surface"
                >
                  {emotionsCatalog.map((emo) => (
                    <option key={emo.id} value={emo.id}>
                      {emo.name} ({emo.category})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-muted block mb-1">Kecepatan ({speed}x)</label>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.05"
                  value={speed}
                  onChange={(e) => setSpeed(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-panel border border-border rounded-full appearance-none accent-black dark:accent-white cursor-pointer"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted block mb-1">Engine</label>
                <select
                  value={engine}
                  onChange={(e) => setEngine(e.target.value)}
                  className="input-base text-xs bg-surface"
                >
                  <option value="piper">Piper (CPU Intel)</option>
                  <option value="remote">Remote (Colab GPU)</option>
                </select>
              </div>
            </div>

            {/* Tombol Run */}
            <button
              type="button"
              disabled={isRunning}
              onClick={handleRunRequest}
              className="btn-primary w-full py-2.5 text-xs font-semibold"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" strokeWidth={1.5} />
                  <span>Menjalankan Request...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" strokeWidth={1.5} />
                  <span>Kirim Permintaan (Run)</span>
                </>
              )}
            </button>
          </div>

          {/* Code Generator Snippets */}
          <div className="card-panel space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <div className="flex items-center gap-2">
                <Code2 className="w-4 h-4 text-fg" strokeWidth={1.5} />
                <div className="flex items-center bg-panel rounded-md p-0.5 border border-border">
                  {(["curl", "python", "javascript"] as SnippetTab[]).map((tab) => (
                    <button
                      key={tab}
                      type="button"
                      onClick={() => setActiveSnippetTab(tab)}
                      className={`text-xs px-2.5 py-1 rounded transition-colors duration-150 ${
                        activeSnippetTab === tab
                          ? "bg-primary text-primary-fg font-semibold"
                          : "text-muted hover:text-fg"
                      }`}
                    >
                      {tab === "curl" ? "cURL" : tab === "python" ? "Python" : "JavaScript"}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                onClick={handleCopyCode}
                className="btn-secondary h-7 px-2 text-xs"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5" strokeWidth={2} /> Tersalin!
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" strokeWidth={1.5} /> Salin
                  </>
                )}
              </button>
            </div>

            <pre className="p-3.5 rounded-md bg-panel border border-border text-xs font-mono text-fg overflow-x-auto max-h-44 leading-relaxed">
              {codeSnippets[activeSnippetTab]}
            </pre>
          </div>
        </div>

        {/* Kolom Kanan: Response Inspector */}
        <div className="card-panel space-y-4 flex flex-col h-full">
          <div className="flex items-center justify-between border-b border-border pb-2.5">
            <h2 className="text-xs font-semibold text-fg flex items-center gap-1.5">
              <FileJson className="w-4 h-4 text-fg" strokeWidth={1.5} /> Respons Server
            </h2>

            <div className="flex items-center gap-2">
              {responseStatus !== null && (
                <span
                  className="text-[10px] font-semibold px-2 py-0.5 rounded border border-border bg-panel text-fg font-mono"
                >
                  HTTP {responseStatus} {responseStatus === 200 ? "OK" : ""}
                </span>
              )}
              {executionTimeMs !== null && (
                <span className="text-xs text-muted flex items-center gap-1 font-mono">
                  <Clock className="w-3 h-3 text-muted" strokeWidth={1.5} /> {executionTimeMs} ms
                </span>
              )}
            </div>
          </div>

          {/* Audio Player jika respons memiliki audio */}
          {audioUrl && (
            <div className="p-3 rounded-md bg-panel border border-border flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs text-fg font-semibold">
                <Volume2 className="w-4 h-4 text-fg" strokeWidth={1.5} />
                <span>Audio Output Siap Putar</span>
              </div>
              <audio controls src={audioUrl} className="h-8 max-w-xs" />
            </div>
          )}

          {/* Response Headers */}
          {Object.keys(responseHeaders).length > 0 && (
            <div>
              <span className="text-[10px] uppercase font-semibold text-muted block mb-1">Headers</span>
              <div className="p-2.5 rounded-md bg-panel border border-border text-xs font-mono text-muted space-y-0.5 max-h-28 overflow-y-auto">
                {Object.entries(responseHeaders).map(([k, v]) => (
                  <div key={k} className="truncate">
                    <span className="text-fg font-semibold">{k}:</span> {v}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Response Body JSON */}
          <div className="flex-1 flex flex-col min-h-60">
            <span className="text-[10px] uppercase font-semibold text-muted block mb-1">Body JSON</span>
            <pre className="flex-1 p-3.5 rounded-md bg-panel border border-border text-xs font-mono text-fg overflow-auto leading-relaxed select-text">
              {responseBody
                ? JSON.stringify(responseBody, null, 2)
                : '// Klik tombol "Kirim Permintaan (Run)" untuk melihat respons server.'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
