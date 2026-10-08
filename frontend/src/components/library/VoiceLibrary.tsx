"use client";

import React, { useState, useEffect, useRef } from "react";
import { useTTSStore } from "@/store/ttsStore";
import {
  Search,
  Play,
  Pause,
  Volume2,
  Check,
  User,
  ArrowRight,
} from "lucide-react";

export function VoiceLibrary() {
  const {
    voices,
    fetchVoicesList,
    selectedVoiceId,
    setSelectedVoiceId,
    setActiveTab,
    previewingVoiceId,
    previewAudioUrl,
    isPlayingPreview,
    playVoicePreview,
    stopVoicePreview,
  } = useTTSStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    fetchVoicesList();
  }, [fetchVoicesList]);

  // Audio preview playback handler
  useEffect(() => {
    if (audioRef.current && previewAudioUrl) {
      audioRef.current.src = previewAudioUrl;
      audioRef.current.play().catch(() => {});
    }
  }, [previewAudioUrl]);

  const categories = [
    { id: "all", label: "Semua Suara" },
    { id: "creator", label: "TikTok & Reels" },
    { id: "narrator", label: "Narator YouTube" },
    { id: "podcast", label: "Podcast / Siniar" },
    { id: "news", label: "Berita & Edukasi" },
  ];

  const filteredVoices = voices.filter((v) => {
    const matchesSearch =
      v.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.category?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      selectedCategory === "all" || v.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleSelectVoice = (voiceId: string) => {
    setSelectedVoiceId(voiceId);
    stopVoicePreview();
    setActiveTab("tts");
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-y-auto bg-background p-6">
      {/* Hidden Audio Player for 3-Second Previews */}
      <audio
        ref={audioRef}
        onEnded={() => stopVoicePreview()}
        onError={() => stopVoicePreview()}
      />

      {/* Header */}
      <div className="max-w-6xl mx-auto w-full space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
          <div>
            <h1 className="text-lg font-semibold text-fg flex items-center gap-2">
              <Volume2 className="w-5 h-5 text-fg" strokeWidth={1.5} />
              Voice Library Indonesia
            </h1>
            <p className="text-xs text-muted mt-0.5">
              Koleksi model vokal saraf lokal (Piper ONNX CPU) tanpa API pihak ketiga.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-1 rounded-md border border-border bg-surface text-fg font-semibold">
              {voices.length} SUARA TERSEDIA
            </span>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="flex flex-col sm:flex-row items-center gap-3">
          {/* Search Box */}
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" strokeWidth={1.5} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Cari nama suara, karakter, atau gaya konten..."
              className="input-base pl-9 text-xs"
            />
          </div>

          {/* Category Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
            {categories.map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-3 py-1.5 rounded-md text-xs transition-colors duration-150 whitespace-nowrap ${
                  selectedCategory === cat.id
                    ? "bg-primary text-primary-fg font-semibold"
                    : "bg-surface border border-border text-muted hover:text-fg hover:border-fg/40"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Grid of Voice Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredVoices.map((voice) => {
            const isSelected = selectedVoiceId === voice.id;
            const isPreviewing =
              previewingVoiceId === voice.id && isPlayingPreview;

            return (
              <div
                key={voice.id}
                className={`rounded-lg border p-4 flex flex-col justify-between transition-colors duration-150 ${
                  isSelected
                    ? "bg-panel border-2 border-primary shadow-sm"
                    : "bg-surface border-border hover:border-fg/40"
                }`}
              >
                <div>
                  {/* Top Bar of Card */}
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <h3 className="font-semibold text-sm text-fg">
                        {voice.name}
                      </h3>
                      <span className="text-xs text-muted flex items-center gap-1 mt-0.5">
                        <User className="w-3 h-3 text-muted" strokeWidth={1.5} />
                        {voice.gender === "female" || voice.gender === "Wanita"
                          ? "Wanita"
                          : "Pria"}{" "}
                        • {voice.language}
                      </span>
                    </div>

                    <span className="text-[10px] px-2 py-0.5 rounded border border-border bg-panel text-fg uppercase font-semibold">
                      {voice.category}
                    </span>
                  </div>

                  <p className="text-xs text-muted leading-relaxed mb-4 line-clamp-2">
                    {voice.description ||
                      "Model suara saraf berbahasa Indonesia dengan artikulasi natural."}
                  </p>

                  <div className="flex items-center gap-2 text-[10px] text-muted font-mono mb-4">
                    <span className="px-1.5 py-0.5 rounded bg-panel border border-border">
                      {voice.sample_rate} Hz
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-panel border border-border">
                      {voice.engine.toUpperCase()} ONNX
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-panel border border-border font-sans text-fg">
                      {voice.backed_by === "dedicated_model" || voice.id === "id_ID-news_tts-medium"
                        ? "Model Mandiri"
                        : "Profil Vokal"}
                    </span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2 pt-3 border-t border-border">
                  {/* Preview 3-Second Button */}
                  <button
                    type="button"
                    onClick={() => playVoicePreview(voice.id)}
                    className={`btn-secondary flex-1 h-8 text-xs ${
                      isPreviewing
                        ? "bg-primary text-primary-fg border-primary font-semibold"
                        : ""
                    }`}
                    title="Dengarkan sampel suara 3 detik"
                  >
                    {isPreviewing ? (
                      <>
                        <Pause className="w-3.5 h-3.5 fill-current" strokeWidth={1.5} />
                        <span>Memutar (3s)</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5 fill-current ml-0.5" strokeWidth={1.5} />
                        <span>Preview 3s</span>
                      </>
                    )}
                  </button>

                  {/* Use this voice button */}
                  <button
                    type="button"
                    onClick={() => handleSelectVoice(voice.id)}
                    className={`h-8 px-3 text-xs font-semibold rounded-md border transition-colors duration-150 flex items-center justify-center gap-1.5 ${
                      isSelected
                        ? "bg-primary text-primary-fg border-primary"
                        : "bg-surface border-border hover:bg-hover hover:border-fg text-fg"
                    }`}
                    title="Pilih suara ini dan gunakan di Text-to-Speech Studio"
                  >
                    {isSelected ? (
                      <>
                        <Check className="w-3.5 h-3.5" strokeWidth={2} />
                        <span>Aktif</span>
                      </>
                    ) : (
                      <>
                        <span>Pilih</span>
                        <ArrowRight className="w-3.5 h-3.5" strokeWidth={1.5} />
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {filteredVoices.length === 0 && (
          <div className="text-center py-16 bg-surface border border-border rounded-lg">
            <p className="text-sm text-muted">
              Tidak ada model suara yang cocok dengan filter pencarian.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
