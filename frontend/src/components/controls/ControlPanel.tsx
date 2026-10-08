"use client";

import React, { useEffect } from "react";
import { useTTSStore } from "@/store/ttsStore";
import {
  Sliders,
  Play,
  RotateCcw,
  Zap,
  Radio,
  ShieldAlert,
  Loader2,
  Clock,
  Sparkles,
  SlidersHorizontal,
  AlertCircle,
} from "lucide-react";

const EFFECTS = [
  { id: "none", label: "Studio Murni (-16 LUFS)" },
  { id: "reverb", label: "Gema Aula / Reverb" },
  { id: "radio", label: "Transmisi Radio / HT" },
  { id: "telephone", label: "Panggilan Telepon" },
  { id: "whisper", label: "Bisikan Lembut (Whisper)" },
  { id: "podcast_eq", label: "Podcast Warm EQ" },
];

export function ControlPanel() {
  const {
    selectedEngine,
    setSelectedEngine,
    selectedVoiceId,
    setSelectedVoiceId,
    speed,
    setSpeed,
    pitch,
    setPitch,
    pauseScale,
    setPauseScale,
    audioEffect,
    setAudioEffect,
    selectedEmotion,
    setSelectedEmotion,
    emotionIntensity,
    setEmotionIntensity,
    emotionsCatalog,
    fetchEmotionsList,
    isClonedVoice,
    setIsClonedVoice,
    cloneConsentGiven,
    setCloneConsentGiven,
    voices,
    presetsCatalog,
    selectedPresetId,
    fetchPresetsList,
    applyPreset,
    isGenerating,
    generationProgress,
    generationStep,
    generationMessage,
    generationError,
    generateSpeech,
  } = useTTSStore();

  useEffect(() => {
    fetchEmotionsList();
    fetchPresetsList();
  }, [fetchEmotionsList, fetchPresetsList]);

  const handleResetSliders = () => {
    setSpeed(1.0);
    setPitch(0.0);
    setPauseScale(1.0);
    setEmotionIntensity(100);
    setSelectedEmotion("neutral");
  };

  const displayVoices =
    voices.length > 0
      ? voices
      : [
          {
            id: "id_ID-news_tts-medium",
            name: "Ida - Berita & Narasi Resmi",
            category: "news",
            gender: "female",
            description: "Artikulasi jernih dan akurat untuk berita & edukasi.",
            engine: "piper",
            sample_rate: 22050,
          },
          {
            id: "piper_id_gadis_fast",
            name: "Gadis - Kreator Energik",
            category: "creator",
            gender: "female",
            description: "Suara wanita ceria pas untuk TikTok & Reels.",
            engine: "piper",
            sample_rate: 22050,
          },
          {
            id: "piper_id_bima_narrator",
            name: "Bima - Narator Hangat",
            category: "narrator",
            gender: "male",
            description: "Vokal pria berwibawa untuk narasi YouTube.",
            engine: "piper",
            sample_rate: 22050,
          },
        ];

  return (
    <aside className="w-80 border-l border-border bg-surface flex flex-col justify-between shrink-0 h-full overflow-y-auto">
      <div className="p-4 space-y-5">
        {/* Panel Title */}
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-fg" strokeWidth={1.5} />
            <h2 className="font-semibold text-sm text-fg">Pengaturan Suara</h2>
          </div>
          <button
            type="button"
            onClick={handleResetSliders}
            className="text-xs text-muted hover:text-fg flex items-center gap-1 transition-colors duration-150"
            title="Reset ke pengaturan awal"
          >
            <RotateCcw className="w-3.5 h-3.5" strokeWidth={1.5} />
            <span>Reset</span>
          </button>
        </div>

        {/* 1. Engine Selector */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-muted flex items-center justify-between">
            <span>TTS Engine</span>
            <span className="text-[10px] font-semibold text-fg px-1.5 py-0.2 rounded border border-border bg-panel">
              INTEL IRIS READY
            </span>
          </label>
          <div className="grid grid-cols-2 gap-1.5 bg-panel p-1 rounded-md border border-border">
            <button
              type="button"
              onClick={() => setSelectedEngine("piper")}
              className={`py-1.5 px-2 rounded text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors duration-150 ${
                selectedEngine === "piper"
                  ? "bg-primary text-primary-fg shadow-sm"
                  : "text-muted hover:text-fg font-normal"
              }`}
            >
              <Zap className="w-3.5 h-3.5" strokeWidth={1.5} /> Piper ONNX
            </button>
            <button
              type="button"
              onClick={() => setSelectedEngine("remote")}
              className={`py-1.5 px-2 rounded text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors duration-150 ${
                selectedEngine === "remote"
                  ? "bg-primary text-primary-fg shadow-sm"
                  : "text-muted hover:text-fg font-normal"
              }`}
              title="Remote GPU (Colab/Kaggle) dengan fallback otomatis ke Piper"
            >
              <Radio className="w-3.5 h-3.5" strokeWidth={1.5} /> Remote GPU
            </button>
          </div>
        </div>

        {/* 2. Voice Selection */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-muted flex items-center justify-between">
            <span>Karakter Suara ({displayVoices.length})</span>
            <span className="text-[10px] text-muted font-mono">Bahasa Indonesia</span>
          </label>
          <div id="voice-selection-list" className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
            {displayVoices.map((v) => {
              const isSelected = selectedVoiceId === v.id;
              return (
                <button
                  key={v.id}
                  id={`btn-voice-${v.id}`}
                  type="button"
                  onClick={() => setSelectedVoiceId(v.id)}
                  className={`w-full text-left p-2.5 rounded-md border text-xs transition-colors duration-150 ${
                    isSelected
                      ? "bg-panel border-2 border-primary text-fg font-semibold shadow-sm"
                      : "bg-surface border-border text-muted hover:text-fg hover:border-fg/30"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-fg flex items-center gap-1.5 truncate">
                      <span>{v.name.split("-")[0].trim()}</span>
                      <span className="text-[10px] font-normal text-muted">
                        ({v.gender === "female" || v.gender === "Wanita" ? "Wanita" : "Pria"})
                      </span>
                    </span>
                    <div className="flex items-center gap-1 shrink-0">
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-panel border border-border text-muted font-normal">
                        {v.backed_by === "dedicated_model" || v.id === "id_ID-news_tts-medium"
                          ? "Model Mandiri"
                          : "Profil Vokal"}
                      </span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-panel border border-border text-fg uppercase font-semibold">
                        {v.category}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* 3. Preset Gaya */}
        <div className="space-y-1.5 p-3 rounded-md border border-border bg-panel">
          <label className="text-xs font-semibold text-fg flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <SlidersHorizontal className="w-3.5 h-3.5 text-fg" strokeWidth={1.5} /> Preset Gaya
            </span>
            <span className="text-[10px] text-muted font-mono">
              {presetsCatalog.length} Tersedia
            </span>
          </label>
          <select
            id="select-style-preset"
            value={selectedPresetId || ""}
            onChange={(e) => {
              if (e.target.value) applyPreset(e.target.value);
            }}
            className="input-base text-xs bg-surface border-border text-fg"
          >
            <option value="">-- Pilih Preset Siap Pakai --</option>
            {presetsCatalog.map((preset) => (
              <option key={preset.id} value={preset.id}>
                {preset.name} ({preset.category})
              </option>
            ))}
          </select>
        </div>

        {/* 4. Global Emotion Selector */}
        <div className="space-y-2 p-3 rounded-md border border-border bg-panel">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-fg flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-fg" strokeWidth={1.5} /> Preset Emosi
            </label>
            <span
              className="text-[10px] px-2 py-0.5 rounded border border-border bg-surface text-fg font-semibold cursor-help"
              title="Emosi dihasilkan secara adaptif via kontrol prosodi laju kata, pitch fundamental, jeda, dan filter akustik."
            >
              Emosi Didekati
            </span>
          </div>

          <select
            value={selectedEmotion}
            onChange={(e) => setSelectedEmotion(e.target.value)}
            className="input-base text-xs bg-surface border-border"
          >
            <option value="neutral">Netral (Baku / Standard)</option>
            <option value="auto">Auto Emotion (Deteksi per Kalimat)</option>
            {emotionsCatalog.map((emo) => (
              <option key={emo.id} value={emo.id}>
                {emo.name} ({emo.category})
              </option>
            ))}
          </select>

          {selectedEmotion !== "neutral" && selectedEmotion !== "auto" && (
            <div className="space-y-1 pt-2 border-t border-border">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted text-[11px]">Intensitas Emosi</span>
                <span className="font-mono text-fg font-semibold text-xs">{emotionIntensity}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={emotionIntensity}
                onChange={(e) => setEmotionIntensity(parseInt(e.target.value, 10))}
                className="w-full h-1.5 bg-surface border border-border rounded-full appearance-none accent-black dark:accent-white cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-muted">
                <span>0% Netral</span>
                <span>50% Halus</span>
                <span>100% Penuh</span>
              </div>
            </div>
          )}
        </div>

        {/* 5. Speed Slider */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted">Kecepatan Bicara (Tempo)</span>
            <span className="font-mono text-fg font-semibold">{speed.toFixed(2)}x</span>
          </div>
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.05"
            value={speed}
            onChange={(e) => setSpeed(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-panel border border-border rounded-full appearance-none accent-black dark:accent-white cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-muted">
            <span>0.5x Santai</span>
            <span>1.0x Normal</span>
            <span>2.0x Cepat</span>
          </div>
        </div>

        {/* 6. Pitch Slider */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted">Tinggi Nada (Pitch)</span>
            <span className="font-mono text-fg font-semibold">
              {pitch > 0 ? `+${pitch.toFixed(1)}` : pitch.toFixed(1)}
            </span>
          </div>
          <input
            type="range"
            min="-5"
            max="5"
            step="0.5"
            value={pitch}
            onChange={(e) => setPitch(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-panel border border-border rounded-full appearance-none accent-black dark:accent-white cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-muted">
            <span>Berat (-5)</span>
            <span>Netral (0)</span>
            <span>Tinggi (+5)</span>
          </div>
        </div>

        {/* 7. Pause Slider */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-muted" strokeWidth={1.5} /> Durasi Jeda
            </span>
            <span className="font-mono text-fg font-semibold">{pauseScale.toFixed(2)}x</span>
          </div>
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={pauseScale}
            onChange={(e) => setPauseScale(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-panel border border-border rounded-full appearance-none accent-black dark:accent-white cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-muted">
            <span>Singkat</span>
            <span>Alami (450ms)</span>
            <span>Panjang</span>
          </div>
        </div>

        {/* 8. Server Audio Effects (FFmpeg) */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-muted">Efek Audio Mastering (FFmpeg)</label>
          <select
            value={audioEffect}
            onChange={(e) => setAudioEffect(e.target.value)}
            className="input-base text-xs bg-panel border-border"
          >
            {EFFECTS.map((ef) => (
              <option key={ef.id} value={ef.id}>
                {ef.label}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-muted leading-relaxed">
            Termasuk normalisasi -16 LUFS standar siaran dan de-esser 5-9 kHz.
          </p>
        </div>

        {/* 9. Voice Clone Ethics Checkbox */}
        <div className="p-3 rounded-md border border-border bg-panel space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-fg flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-fg" strokeWidth={1.5} /> Mode Voice Clone
            </span>
            <input
              type="checkbox"
              checked={isClonedVoice}
              onChange={(e) => setIsClonedVoice(e.target.checked)}
              className="w-4 h-4 rounded border-border accent-black dark:accent-white cursor-pointer"
            />
          </div>
          {isClonedVoice && (
            <div className="pt-2 border-t border-border space-y-1.5">
              <label className="flex items-start gap-2 text-xs text-muted cursor-pointer leading-relaxed">
                <input
                  type="checkbox"
                  checked={cloneConsentGiven}
                  onChange={(e) => setCloneConsentGiven(e.target.checked)}
                  className="mt-0.5 w-3.5 h-3.5 rounded border-border accent-black dark:accent-white"
                />
                <span>
                  Saya memiliki izin eksplisit dari pemilik suara asli untuk sintesis suara ini.
                </span>
              </label>
            </div>
          )}
        </div>

        {/* Error Notification (Icon + weight + border style, no color) */}
        {generationError && (
          <div className="status-error">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" strokeWidth={2} />
            <div className="leading-relaxed">{generationError}</div>
          </div>
        )}
      </div>

      {/* Bottom Sticky Generate Section with Real-Time Progress */}
      <div className="p-4 border-t border-border bg-surface shrink-0 space-y-2.5">
        {isGenerating && (
          <div className="space-y-1.5 bg-panel p-2.5 rounded-md border border-border">
            <div className="flex items-center justify-between text-xs">
              <span className="text-fg flex items-center gap-1.5 font-medium">
                <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.5} />
                {generationMessage || "Memproses..."}
              </span>
              <span className="font-mono text-fg font-semibold">
                {generationProgress}%
              </span>
            </div>
            <div className="w-full bg-surface h-1.5 rounded-full overflow-hidden border border-border">
              <div
                className="bg-primary h-full transition-all duration-300 rounded-full"
                style={{ width: `${generationProgress}%` }}
              />
            </div>
            <div className="text-[10px] text-muted text-right">
              Tahap: {generationStep}
            </div>
          </div>
        )}

        <button
          id="generate-button"
          type="button"
          onClick={generateSpeech}
          disabled={isGenerating}
          className="btn-primary w-full py-2.5 text-sm font-semibold tracking-wide"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" strokeWidth={1.5} />
              <span>Menyintesis Suara...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" strokeWidth={1.5} />
              <span>Generate Suara</span>
            </>
          )}
        </button>
        <div className="text-center text-[11px] text-muted">
          Output: WAV 16-bit • Equal-Power Crossfade 40ms
        </div>
      </div>
    </aside>
  );
}
