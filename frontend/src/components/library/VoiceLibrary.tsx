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
  Mic,
  Sparkles,
  Trash2,
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
    deleteVoice,
  } = useTTSStore();

  const [searchQuery, setSearchQuery] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    fetchVoicesList();
  }, [fetchVoicesList]);

  // Audio preview playback handler
  useEffect(() => {
    if (!audioRef.current) return;
    if (isPlayingPreview && previewAudioUrl) {
      if (audioRef.current.src !== previewAudioUrl && !audioRef.current.src.endsWith(previewAudioUrl)) {
        audioRef.current.src = previewAudioUrl;
      }
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch((err) => {
        console.error("Audio playback error:", err);
        stopVoicePreview();
      });
    } else {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  }, [isPlayingPreview, previewAudioUrl, stopVoicePreview]);

  // Hanya tampilkan suara hasil rekaman/kloning
  const myVoices = voices.filter((v) => {
    const matchesSearch =
      v.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const handleSelectVoice = (voice: typeof voices[0]) => {
    setSelectedVoiceId(voice.id);
    if (voice.engine) {
      useTTSStore.getState().setSelectedEngine(voice.engine);
    }
    stopVoicePreview();
    setActiveTab("tts");
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-y-auto bg-background p-6">
      {/* Hidden Audio Player for Previews */}
      <audio
        ref={audioRef}
        onEnded={() => stopVoicePreview()}
        onError={() => stopVoicePreview()}
      />

      <div className="max-w-5xl mx-auto w-full space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
          <div>
            <h1 className="text-lg font-semibold text-fg flex items-center gap-2">
              <Mic className="w-5 h-5 text-fg" strokeWidth={1.5} />
              Suara Saya
            </h1>
            <p className="text-xs text-muted mt-0.5">
              Koleksi suara dari rekaman & kloning suara Anda sendiri. Tidak ada suara preset bawaan.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-1 rounded-md border border-border bg-surface text-fg font-semibold">
              {myVoices.length} SUARA TERSEDIA
            </span>
            <button
              type="button"
              onClick={() => setActiveTab("clone")}
              className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-fg font-semibold flex items-center gap-1.5 hover:opacity-90 transition-opacity"
            >
              <Sparkles className="w-3.5 h-3.5" strokeWidth={1.5} />
              Rekam Suara Baru
            </button>
          </div>
        </div>

        {/* Search */}
        {myVoices.length > 0 && (
          <div className="relative w-full max-w-md">
            <Search className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" strokeWidth={1.5} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Cari suara Anda..."
              className="input-base pl-9 text-xs"
            />
          </div>
        )}

        {/* Voice Cards Grid */}
        {myVoices.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {myVoices.map((voice) => {
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
                    {/* Top Bar */}
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

                      <span className="text-[10px] px-2 py-0.5 rounded border border-primary/30 bg-primary/10 text-primary uppercase font-semibold">
                        {voice.is_cloned ? "Suara Klon" : "Rekaman"}
                      </span>
                    </div>

                    <p className="text-xs text-muted leading-relaxed mb-4 line-clamp-2">
                      {voice.description ||
                        "Suara hasil rekaman/kloning pribadi Anda."}
                    </p>

                    <div className="flex items-center gap-2 text-[10px] text-muted font-mono mb-4">
                      <span className="px-1.5 py-0.5 rounded bg-panel border border-border">
                        {voice.sample_rate} Hz
                      </span>
                      <span className="px-1.5 py-0.5 rounded bg-panel border border-border uppercase">
                        {voice.engine || "chatterbox"}
                      </span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 pt-3 border-t border-border">
                    {/* Preview Button */}
                    <button
                      type="button"
                      onClick={() => playVoicePreview(voice.id)}
                      className={`btn-secondary flex-1 h-8 text-xs ${
                        isPreviewing
                          ? "bg-primary text-primary-fg border-primary font-semibold"
                          : ""
                      }`}
                      title="Dengarkan rekaman/sampel suara asli"
                    >
                      {isPreviewing ? (
                        <>
                          <Pause className="w-3.5 h-3.5 fill-current" strokeWidth={1.5} />
                          <span>Berhenti</span>
                        </>
                      ) : (
                        <>
                          <Play className="w-3.5 h-3.5 fill-current ml-0.5" strokeWidth={1.5} />
                          <span>Dengar Suara</span>
                        </>
                      )}
                    </button>

                    {/* Use this voice button */}
                    <button
                      type="button"
                      onClick={() => handleSelectVoice(voice)}
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

                    {/* Delete button */}
                    <button
                      type="button"
                      onClick={() => {
                        if (confirm(`Yakin ingin menghapus suara "${voice.name}"?`)) {
                          deleteVoice(voice.id);
                        }
                      }}
                      className="h-8 w-8 rounded-md border border-border bg-surface hover:bg-red-500/10 hover:border-red-500/40 text-muted hover:text-red-500 flex items-center justify-center transition-colors shrink-0"
                      title="Hapus profil suara ini"
                    >
                      <Trash2 className="w-3.5 h-3.5" strokeWidth={1.5} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Empty State — No Voices Yet */
          <div className="text-center py-20 bg-surface border border-border rounded-lg space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-panel border border-border flex items-center justify-center">
              <Mic className="w-8 h-8 text-muted" strokeWidth={1} />
            </div>
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-fg">
                Belum Ada Suara
              </h3>
              <p className="text-xs text-muted max-w-md mx-auto leading-relaxed">
                Kamu belum merekam atau mengunggah suara apapun.
                Buka menu <strong>Voice Clone</strong> untuk merekam suaramu sendiri
                dan jadikan profil suara yang bisa digunakan untuk menghasilkan narasi.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setActiveTab("clone")}
              className="mt-2 px-4 py-2 rounded-md bg-primary text-primary-fg text-xs font-semibold inline-flex items-center gap-2 hover:opacity-90 transition-opacity"
            >
              <Sparkles className="w-4 h-4" strokeWidth={1.5} />
              Mulai Rekam Suara
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
