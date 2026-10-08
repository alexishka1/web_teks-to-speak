"use client";

import React, { useState } from "react";
import { useTTSStore } from "@/store/ttsStore";
import { EmotionPicker } from "./EmotionPicker";
import {
  Clipboard,
  Trash2,
  Sparkles,
  FileText,
  Volume2,
  Clock,
  Eye,
  Edit3,
  PlayCircle,
  Wand2,
  Tag,
} from "lucide-react";

const SAMPLES = [
  {
    label: "Hook TikTok",
    text: "Stop scroll dulu! Tahu nggak kenapa 90 persen kreator gagal monetisasi di bulan pertama? Ini dia 3 rahasia algoritma yang jarang dibocorin!",
  },
  {
    label: "YouTube Narasi",
    text: "Di era digital saat ini, kecerdasan buatan telah merevolusi cara kita memproduksi konten audio. Tidak perlu lagi mikrofon studio bernilai puluhan juta rupiah untuk menghasilkan suara narator yang jernih dan berwibawa.",
  },
  {
    label: "Podcast Intro",
    text: "Halo sahabat setia pendengar siniar. Kembali lagi bersama saya di episode spesial minggu ini. Kita akan berbincang hangat mengenai perjalanan membangun karya dari nol.",
  },
];

export function EditorSection() {
  const {
    text,
    setText,
    sentences,
    activeSentenceIndex,
    isPlaying,
    seekToSentence,
    emotionsCatalog,
    sentenceEmotions,
    setSentenceEmotion,
    runAutoEmotionAnalysis,
    isAutoEmotionMode,
  } = useTTSStore();

  const [viewMode, setViewMode] = useState<"edit" | "highlight">("edit");
  const [pickerSentenceIndex, setPickerSentenceIndex] = useState<number | null>(null);

  const charCount = text.length;
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const estimatedSeconds = Math.max(1, Math.round((wordCount / 140) * 60));

  const handlePaste = async () => {
    try {
      const clipText = await navigator.clipboard.readText();
      setText(clipText);
    } catch {
      // Fallback
    }
  };

  const handleClear = () => {
    setText("");
  };

  const handleAutoEmotionClick = async () => {
    setViewMode("highlight");
    await runAutoEmotionAnalysis();
  };

  const activePickerSentence =
    pickerSentenceIndex !== null && pickerSentenceIndex < sentences.length
      ? sentences[pickerSentenceIndex]
      : null;

  return (
    <div className="flex-1 flex flex-col h-full min-w-0 bg-background overflow-hidden">
      {/* Emotion Picker Modal */}
      {pickerSentenceIndex !== null && activePickerSentence && (
        <EmotionPicker
          isOpen={true}
          onClose={() => setPickerSentenceIndex(null)}
          sentenceIndex={pickerSentenceIndex}
          sentenceText={activePickerSentence.text}
          currentEmotion={sentenceEmotions[pickerSentenceIndex] || "neutral"}
          emotionsCatalog={emotionsCatalog}
          onSelectEmotion={setSentenceEmotion}
        />
      )}

      {/* Top Header of Editor */}
      <div className="p-4 border-b border-border bg-surface flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-fg" strokeWidth={1.5} />
          <h1 className="font-semibold text-sm text-fg">Editor Naskah Narasi</h1>
          <span className="text-xs text-muted hidden sm:inline">• Studio Mandiri</span>
        </div>

        {/* View Mode Toggle, Auto Emotion & Toolbar */}
        <div className="flex items-center gap-2">
          {/* Tombol Auto Emotion Analysis */}
          <button
            type="button"
            onClick={handleAutoEmotionClick}
            className="btn-secondary h-8 px-2.5 text-xs font-semibold"
            title="Analisis dan tentukan emosi tiap kalimat secara otomatis (offline)"
          >
            <Wand2 className="w-3.5 h-3.5" strokeWidth={1.5} />
            <span>Auto Emotion</span>
          </button>

          {/* Toggle View */}
          <div className="flex items-center bg-panel rounded-md p-0.5 border border-border">
            <button
              type="button"
              onClick={() => setViewMode("edit")}
              className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-colors duration-150 ${
                viewMode === "edit"
                  ? "bg-primary text-primary-fg"
                  : "text-muted hover:text-fg"
              }`}
              title="Edit teks naskah langsung"
            >
              <Edit3 className="w-3.5 h-3.5" strokeWidth={1.5} />
              <span>Teks</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("highlight")}
              className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-colors duration-150 ${
                viewMode === "highlight"
                  ? "bg-primary text-primary-fg"
                  : "text-muted hover:text-fg"
              }`}
              title="Mode per kalimat dengan penanda emosi dan highlight"
            >
              <Eye className="w-3.5 h-3.5" strokeWidth={1.5} />
              <span>Emosi & Karaoke</span>
            </button>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={handlePaste}
              className="btn-ghost h-8"
              title="Tempel dari Clipboard"
            >
              <Clipboard className="w-3.5 h-3.5" strokeWidth={1.5} />
              <span className="hidden sm:inline">Paste</span>
            </button>
            <button
              type="button"
              onClick={handleClear}
              className="btn-ghost h-8 text-muted hover:text-fg"
              title="Kosongkan Teks"
            >
              <Trash2 className="w-3.5 h-3.5" strokeWidth={1.5} />
              <span className="hidden sm:inline">Clear</span>
            </button>
          </div>
        </div>
      </div>

      {/* Preset Script Prompts */}
      <div className="px-4 py-2 border-b border-border bg-panel flex items-center gap-2 overflow-x-auto text-xs shrink-0">
        <span className="text-muted flex items-center gap-1 shrink-0 text-xs font-medium">
          <Sparkles className="w-3.5 h-3.5 text-fg" strokeWidth={1.5} /> Contoh:
        </span>
        {SAMPLES.map((s, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setText(s.text)}
            className="px-2.5 py-1 rounded-md bg-surface hover:bg-hover text-muted hover:text-fg border border-border text-xs whitespace-nowrap transition-colors duration-150 font-normal"
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-4 flex flex-col min-h-0 overflow-y-auto">
        {viewMode === "highlight" && sentences.length > 0 ? (
          <div className="flex-1 bg-surface border border-border rounded-lg p-4 overflow-y-auto space-y-3">
            <div className="text-xs text-muted pb-3 border-b border-border flex flex-wrap items-center justify-between gap-2">
              <span className="flex items-center gap-1.5">
                <Tag className="w-3.5 h-3.5 text-fg" strokeWidth={1.5} />
                <span>Pilih badge untuk mengubah emosi per kalimat:</span>
              </span>
              <span className="text-xs text-fg font-semibold flex items-center gap-2">
                {isAutoEmotionMode && (
                  <span className="px-2 py-0.5 rounded border border-border bg-panel text-[11px] font-semibold">
                    AUTO EMOTION AKTIF
                  </span>
                )}
                <span>
                  {activeSentenceIndex >= 0
                    ? `Memutar #${activeSentenceIndex + 1}`
                    : `${sentences.length} Kalimat`}
                </span>
              </span>
            </div>

            <div className="space-y-2">
              {sentences.map((sent, idx) => {
                const isActive = activeSentenceIndex === idx;
                const emoId = sentenceEmotions[idx] || "neutral";
                const emoPreset = emotionsCatalog.find((e) => e.id === emoId);

                return (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border text-sm transition-colors duration-150 flex items-start gap-3 ${
                      isActive
                        ? "bg-panel border-2 border-primary text-fg font-semibold shadow-sm"
                        : "bg-surface border-border text-muted hover:text-fg hover:border-fg/30"
                    }`}
                  >
                    {/* Sentence Index Indicator */}
                    <button
                      type="button"
                      onClick={() => seekToSentence(idx)}
                      className={`text-xs font-mono px-2 py-0.5 rounded shrink-0 mt-0.5 cursor-pointer border ${
                        isActive
                          ? "bg-primary text-primary-fg border-primary font-semibold"
                          : "bg-panel text-muted border-border hover:text-fg hover:border-fg"
                      }`}
                      title="Klik untuk putar kalimat ini"
                    >
                      #{idx + 1}
                    </button>

                    {/* Sentence Text with Seeking */}
                    <span
                      onClick={() => seekToSentence(idx)}
                      className="flex-1 leading-relaxed cursor-pointer"
                    >
                      {sent.text}
                    </span>

                    {/* Emotion Tag Picker Trigger */}
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setPickerSentenceIndex(idx);
                        }}
                        className="px-2 py-1 rounded-md text-xs font-semibold flex items-center gap-1.5 border border-border bg-panel hover:bg-hover hover:border-fg text-fg transition-colors duration-150"
                        title="Klik untuk memilih emosi kalimat ini"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-fg shrink-0" />
                        <span>{emoPreset?.name || emoId}</span>
                      </button>

                      {isActive && isPlaying && (
                        <PlayCircle className="w-4 h-4 text-fg animate-pulse shrink-0" strokeWidth={1.5} />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <textarea
            id="tts-textarea"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Tuliskan naskah Anda di sini... (mendukung format angka rupiah, tanggal, singkatan, dan tanda baca otomatis)"
            className="w-full flex-1 bg-surface border border-border rounded-lg p-4 text-sm text-fg placeholder:text-muted/60 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary resize-none font-sans leading-relaxed tracking-normal transition-colors duration-150"
            maxLength={5000}
          />
        )}
      </div>

      {/* Editor Stats Footer */}
      <div className="px-4 py-2.5 border-t border-border bg-surface flex items-center justify-between text-xs text-muted shrink-0">
        <div className="flex items-center gap-4">
          <span>
            Karakter: <strong className="text-fg font-semibold">{charCount}</strong>/5.000
          </span>
          <span>
            Kata: <strong className="text-fg font-semibold">{wordCount}</strong>
          </span>
          <span className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-muted" strokeWidth={1.5} />
            Estimasi: ~<strong className="text-fg font-semibold">{estimatedSeconds}s</strong>
          </span>
        </div>

        <div className="text-xs text-muted hidden sm:flex items-center gap-1.5">
          <Volume2 className="w-3.5 h-3.5 text-fg" strokeWidth={1.5} />
          <span>Mastering -16 LUFS & De-esser otomatis</span>
        </div>
      </div>
    </div>
  );
}
