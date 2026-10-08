"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import {
  History,
  Play,
  Pause,
  Download,
  Trash2,
  Search,
  Clock,
  Mic2,
  Loader2,
  FileAudio,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { fetchHistoryApi, deleteHistoryApi, HistoryItemDTO } from "@/lib/api";

const ITEMS_PER_PAGE = 25;

export function HistoryView() {
  const [historyItems, setHistoryItems] = useState<HistoryItemDTO[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activePlayingId, setActivePlayingId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Audio player state
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Virtualized windowing state
  const [visibleCount, setVisibleCount] = useState(ITEMS_PER_PAGE);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const data = await fetchHistoryApi(100, 0);
      setHistoryItems(data);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return historyItems;
    const q = searchQuery.toLowerCase();
    return historyItems.filter(
      (item) =>
        item.preview_text.toLowerCase().includes(q) ||
        item.voice_name.toLowerCase().includes(q) ||
        item.title.toLowerCase().includes(q)
    );
  }, [historyItems, searchQuery]);

  // Windowed items (ringan & cepat dirender, tanpa DOM bloat)
  const windowedItems = useMemo(() => {
    return filteredItems.slice(0, visibleCount);
  }, [filteredItems, visibleCount]);

  const handlePlayAudio = (item: HistoryItemDTO) => {
    if (activePlayingId === item.id) {
      if (audioRef.current) {
        if (audioRef.current.paused) {
          audioRef.current.play();
        } else {
          audioRef.current.pause();
          setActivePlayingId(null);
        }
      }
      return;
    }

    setActivePlayingId(item.id);
    if (audioRef.current) {
      audioRef.current.src = item.audio_url;
      audioRef.current.play().catch(() => setActivePlayingId(null));
    }
  };

  const handleDelete = async (item: HistoryItemDTO) => {
    if (!confirm(`Hapus rekaman "${item.title}" dari riwayat?`)) return;

    try {
      await deleteHistoryApi(item.id);
      setHistoryItems((prev) => prev.filter((i) => i.id !== item.id));
      if (activePlayingId === item.id) {
        if (audioRef.current) audioRef.current.pause();
        setActivePlayingId(null);
      }
      setFeedback({ type: "success", text: "Riwayat berhasil dihapus." });
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Gagal menghapus riwayat." });
    }
  };

  const totalDuration = useMemo(() => {
    return historyItems.reduce((acc, curr) => acc + (curr.duration_sec || 0), 0);
  }, [historyItems]);

  return (
    <div className="flex-1 h-screen overflow-y-auto p-6 md:p-8 bg-background max-w-5xl mx-auto">
      {/* Hidden audio element for inline playback */}
      <audio
        ref={audioRef}
        onEnded={() => setActivePlayingId(null)}
        onError={() => setActivePlayingId(null)}
        className="hidden"
      />

      {/* Header */}
      <div className="border-b border-border pb-5 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <History className="w-5 h-5 text-fg" strokeWidth={1.5} />
            <h1 className="text-lg font-semibold text-fg">Riwayat Narasi Studio</h1>
            <span className="text-[10px] px-2 py-0.5 rounded bg-panel border border-border text-muted font-mono">
              SQLITE
            </span>
          </div>
          <p className="text-xs text-muted">
            Semua rekaman audio hasil sintesis tersimpan aman secara lokal di server.
          </p>
        </div>

        {/* Statistik Ringkas */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-md bg-surface border border-border text-xs min-w-24">
            <span className="text-muted block text-[11px]">Total File</span>
            <strong className="text-fg font-semibold font-mono text-sm">{historyItems.length}</strong>
          </div>
          <div className="p-2.5 rounded-md bg-surface border border-border text-xs min-w-24">
            <span className="text-muted block text-[11px]">Total Durasi</span>
            <strong className="text-fg font-semibold font-mono text-sm">{totalDuration.toFixed(1)}s</strong>
          </div>
        </div>
      </div>

      {/* Feedback Alert */}
      {feedback && (
        <div className={`mb-4 ${feedback.type === "success" ? "status-success" : "status-error"}`}>
          {feedback.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 shrink-0" strokeWidth={2} />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0" strokeWidth={2} />
          )}
          <span>{feedback.text}</span>
        </div>
      )}

      {/* Search Input Bar */}
      <div className="mb-5 relative">
        <Search className="w-4 h-4 text-muted absolute left-3.5 top-1/2 -translate-y-1/2" strokeWidth={1.5} />
        <input
          type="text"
          placeholder="Cari naskah atau karakter suara di riwayat..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="input-base text-xs pl-10 py-2.5 w-full"
        />
      </div>

      {/* List Riwayat (Tervirtualisasi / Windowed) */}
      {isLoading ? (
        <div className="py-12 text-center text-xs text-muted flex items-center justify-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-fg" strokeWidth={1.5} /> Memuat data riwayat...
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="p-12 text-center text-xs text-muted space-y-2 border border-border rounded-lg bg-surface">
          <FileAudio className="w-10 h-10 text-muted/50 mx-auto" strokeWidth={1.5} />
          <h3 className="font-semibold text-fg">Belum Ada Riwayat</h3>
          <p className="max-w-sm mx-auto text-muted">
            {searchQuery
              ? "Tidak ada audio yang cocok dengan pencarian."
              : "Buat narasi pertama Anda di tab Text to Speech Studio."}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {windowedItems.map((item) => {
            const isPlaying = activePlayingId === item.id;
            return (
              <div
                key={item.id}
                className={`p-4 rounded-lg border transition-colors duration-150 ${
                  isPlaying
                    ? "bg-panel border-2 border-primary shadow-sm"
                    : "bg-surface border-border hover:border-fg/40"
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  {/* Info Teks & Metadata */}
                  <div className="flex-1 space-y-1.5 min-w-0">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="font-semibold text-fg flex items-center gap-1.5 truncate">
                        <Mic2 className="w-3.5 h-3.5 text-muted shrink-0" strokeWidth={1.5} />
                        {item.voice_name}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-panel border border-border text-muted shrink-0 flex items-center gap-1 font-mono">
                        <Clock className="w-3 h-3" strokeWidth={1.5} />
                        {item.duration_sec.toFixed(1)}s
                      </span>
                      <span className="text-[11px] text-muted shrink-0 hidden sm:inline font-mono">
                        {new Date(item.created_at).toLocaleString("id-ID", {
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>

                    <p className="text-xs text-muted leading-relaxed line-clamp-2">
                      &ldquo;{item.preview_text}&rdquo;
                    </p>
                  </div>

                  {/* Tombol Aksi: Putar, Unduh, Hapus */}
                  <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                    {/* Tombol Putar Ulang */}
                    <button
                      type="button"
                      onClick={() => handlePlayAudio(item)}
                      className={`btn-secondary h-8 px-2.5 text-xs ${
                        isPlaying ? "bg-primary text-primary-fg border-primary font-semibold" : ""
                      }`}
                      title={isPlaying ? "Jeda Audio" : "Putar Ulang Audio"}
                    >
                      {isPlaying ? (
                        <>
                          <Pause className="w-3.5 h-3.5 fill-current" strokeWidth={1.5} />
                          <span>Jeda</span>
                        </>
                      ) : (
                        <>
                          <Play className="w-3.5 h-3.5 fill-current ml-0.5" strokeWidth={1.5} />
                          <span>Putar</span>
                        </>
                      )}
                    </button>

                    {/* Tombol Unduh */}
                    <a
                      href={item.audio_url}
                      download={`tastp_${item.id}.wav`}
                      className="btn-secondary h-8 px-2.5 text-xs"
                      title="Unduh File WAV Berlabel AI"
                    >
                      <Download className="w-3.5 h-3.5" strokeWidth={1.5} />
                      <span className="hidden sm:inline">WAV</span>
                    </a>

                    {/* Tombol Hapus */}
                    <button
                      type="button"
                      onClick={() => handleDelete(item)}
                      className="btn-ghost h-8 px-2 text-muted hover:text-fg"
                      title="Hapus Dari Riwayat"
                    >
                      <Trash2 className="w-3.5 h-3.5" strokeWidth={1.5} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Tombol Tampilkan Lebih Banyak (Pagination Ringan) */}
          {visibleCount < filteredItems.length && (
            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => setVisibleCount((prev) => prev + ITEMS_PER_PAGE)}
                className="btn-secondary w-full py-2 text-xs font-semibold"
              >
                Tampilkan Lebih Banyak ({filteredItems.length - visibleCount} tersisa)
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
