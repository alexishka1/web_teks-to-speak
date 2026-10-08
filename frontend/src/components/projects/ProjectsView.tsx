"use client";

import React, { useState, useEffect } from "react";
import {
  FolderKanban,
  Plus,
  Trash2,
  Users,
  Sparkles,
  Download,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Mic2,
} from "lucide-react";
import {
  fetchProjectsApi,
  createProjectApi,
  fetchProjectDetailsApi,
  addProjectBlockApi,
  deleteProjectBlockApi,
  renderProjectDialogueApi,
  ProjectItem,
} from "@/lib/api";
import { useTTSStore } from "@/store/ttsStore";

export function ProjectsView() {
  const { voices, emotionsCatalog, fetchEmotionsList, fetchVoicesList } = useTTSStore();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [activeProject, setActiveProject] = useState<ProjectItem | null>(null);

  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [isRendering, setIsRendering] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // New Block Form state
  const [newSpeaker, setNewSpeaker] = useState("Host");
  const [newVoiceId, setNewVoiceId] = useState("piper_id_gadis_fast");
  const [newEmotion, setNewEmotion] = useState("antusias");
  const [newText, setNewText] = useState("");

  useEffect(() => {
    fetchVoicesList();
    fetchEmotionsList();
    loadProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadProjects = async () => {
    setIsLoading(true);
    try {
      const data = await fetchProjectsApi();
      setProjects(data);
      if (data.length > 0 && !selectedProjectId) {
        setSelectedProjectId(data[0].id);
        setActiveProject(data[0]);
      }
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectProject = async (id: string) => {
    setSelectedProjectId(id);
    setFeedback(null);
    try {
      const p = await fetchProjectDetailsApi(id);
      setActiveProject(p);
    } catch {
      // ignore
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      const created = await createProjectApi(newTitle, newDesc);
      setNewTitle("");
      setNewDesc("");
      setIsCreatingProject(false);
      await loadProjects();
      handleSelectProject(created.id);
      setFeedback({ type: "success", text: `Proyek '${created.title}' berhasil dibuat.` });
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Gagal membuat proyek" });
    }
  };

  const handleAddBlock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId || !newText.trim()) return;

    try {
      await addProjectBlockApi(selectedProjectId, {
        speaker_name: newSpeaker,
        voice_id: newVoiceId,
        emotion: newEmotion,
        text: newText,
        speed: 1.0,
        pitch: 0.0,
      });
      setNewText("");
      const updated = await fetchProjectDetailsApi(selectedProjectId);
      setActiveProject(updated);
      setFeedback({ type: "success", text: "Blok percakapan ditambahkan." });
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Gagal menambahkan blok" });
    }
  };

  const handleDeleteBlock = async (blockId: string) => {
    if (!selectedProjectId) return;
    try {
      await deleteProjectBlockApi(selectedProjectId, blockId);
      const updated = await fetchProjectDetailsApi(selectedProjectId);
      setActiveProject(updated);
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Gagal menghapus blok" });
    }
  };

  const handleRenderDialogue = async () => {
    if (!selectedProjectId) return;
    setIsRendering(true);
    setFeedback(null);
    try {
      const rendered = await renderProjectDialogueApi(selectedProjectId);
      setActiveProject(rendered);
      await loadProjects();
      setFeedback({
        type: "success",
        text: `Render gabungan selesai. Durasi dialog: ${rendered.total_duration_sec.toFixed(1)} detik.`,
      });
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Gagal merender dialog gabungan." });
    } finally {
      setIsRendering(false);
    }
  };

  return (
    <div className="flex-1 h-screen flex flex-col md:flex-row overflow-hidden bg-background">
      {/* Kolom Kiri: Daftar Proyek (Lebar 72) */}
      <div className="w-full md:w-72 border-r border-border bg-surface flex flex-col h-full shrink-0">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FolderKanban className="w-4 h-4 text-fg" strokeWidth={1.5} />
            <h2 className="text-xs font-semibold text-fg uppercase tracking-wider">Daftar Proyek</h2>
          </div>
          <button
            type="button"
            onClick={() => setIsCreatingProject(!isCreatingProject)}
            className="btn-secondary h-7 px-2 text-xs"
            title="Buat Proyek Baru"
          >
            <Plus className="w-3.5 h-3.5" strokeWidth={1.5} /> Baru
          </button>
        </div>

        {/* Modal/Form Buat Proyek */}
        {isCreatingProject && (
          <form onSubmit={handleCreateProject} className="p-3 bg-panel border-b border-border space-y-2">
            <input
              type="text"
              required
              placeholder="Judul Proyek..."
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              className="input-base text-xs py-1.5"
            />
            <input
              type="text"
              placeholder="Deskripsi singkat..."
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              className="input-base text-xs py-1.5"
            />
            <div className="flex justify-end gap-1.5">
              <button
                type="button"
                onClick={() => setIsCreatingProject(false)}
                className="btn-ghost text-xs py-1 px-2"
              >
                Batal
              </button>
              <button type="submit" className="btn-primary text-xs py-1 px-3">
                Simpan
              </button>
            </div>
          </form>
        )}

        {/* List Proyek */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {isLoading && projects.length === 0 ? (
            <div className="p-4 text-center text-xs text-muted flex items-center justify-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.5} /> Memuat proyek...
            </div>
          ) : projects.length === 0 ? (
            <div className="p-6 text-center text-xs text-muted">
              Belum ada proyek. Klik tombol &ldquo;+ Baru&rdquo; di atas untuk memulai dialog multi-speaker.
            </div>
          ) : (
            projects.map((p) => {
              const isSelected = selectedProjectId === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleSelectProject(p.id)}
                  className={`w-full text-left p-2.5 rounded-md border text-xs transition-colors duration-150 ${
                    isSelected
                      ? "bg-panel border-2 border-primary text-fg font-semibold shadow-sm"
                      : "bg-surface border-border text-muted hover:text-fg hover:border-fg/30"
                  }`}
                >
                  <div className="text-fg truncate">{p.title}</div>
                  <div className="flex items-center justify-between text-[11px] text-muted mt-1 font-mono">
                    <span>{p.blocks?.length || 0} Blok</span>
                    <span>{p.total_duration_sec > 0 ? `${p.total_duration_sec.toFixed(1)}s` : "Belum dirender"}</span>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Kolom Kanan: Detail Dialog Multi-Speaker & Render */}
      <div className="flex-1 h-full overflow-y-auto p-6 bg-background space-y-5">
        {activeProject ? (
          <>
            {/* Header Proyek */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-base font-semibold text-fg">{activeProject.title}</h1>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-panel border border-border text-muted font-mono">
                    MULTI-SPEAKER
                  </span>
                </div>
                {activeProject.description && (
                  <p className="text-xs text-muted mt-0.5">{activeProject.description}</p>
                )}
              </div>

              {/* Tombol Render Gabungan */}
              <button
                type="button"
                disabled={isRendering || !activeProject.blocks || activeProject.blocks.length === 0}
                onClick={handleRenderDialogue}
                className="btn-primary h-9 px-4 text-xs font-semibold"
              >
                {isRendering ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" strokeWidth={1.5} />
                    <span>Menyintesis & Menggabungkan Audio...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" strokeWidth={1.5} />
                    <span>Render Dialog Gabungan</span>
                  </>
                )}
              </button>
            </div>

            {/* Feedback Message */}
            {feedback && (
              <div className={feedback.type === "success" ? "status-success" : "status-error"}>
                {feedback.type === "success" ? (
                  <CheckCircle2 className="w-4 h-4 shrink-0" strokeWidth={2} />
                ) : (
                  <AlertCircle className="w-4 h-4 shrink-0" strokeWidth={2} />
                )}
                <span>{feedback.text}</span>
              </div>
            )}

            {/* Audio Player Hasil Render Gabungan */}
            {activeProject.final_audio_url && (
              <div className="p-4 rounded-lg bg-panel border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-xs font-semibold text-fg">
                    <span className="w-2 h-2 rounded-full bg-fg" />
                    Audio Gabungan Siap Putar
                  </div>
                  <p className="text-xs text-muted font-mono">
                    Label: &ldquo;Dibuat dengan AI&rdquo; • Durasi: {activeProject.total_duration_sec.toFixed(1)}s
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <audio controls src={activeProject.final_audio_url} className="h-8 max-w-xs" />
                  <a
                    href={activeProject.final_audio_url}
                    download={`tastp_${activeProject.id}.wav`}
                    className="btn-secondary h-8 px-2.5 text-xs"
                    title="Download Audio Dialog WAV"
                  >
                    <Download className="w-3.5 h-3.5" strokeWidth={1.5} />
                  </a>
                </div>
              </div>
            )}

            {/* List Blok Dialog Percakapan */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-fg flex items-center gap-2">
                <Users className="w-4 h-4 text-fg" strokeWidth={1.5} />
                Blok Percakapan ({activeProject.blocks?.length || 0})
              </h3>

              {(!activeProject.blocks || activeProject.blocks.length === 0) ? (
                <div className="p-6 rounded-lg border border-border bg-surface text-center text-xs text-muted">
                  Belum ada baris dialog. Masukkan baris percakapan pembicara di form bawah.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {activeProject.blocks.map((b, idx) => (
                    <div
                      key={b.id}
                      className="p-3.5 rounded-lg bg-surface border border-border flex flex-col md:flex-row md:items-start justify-between gap-3 hover:border-fg/40 transition-colors duration-150"
                    >
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2 text-xs">
                          <span className="font-semibold text-fg px-2 py-0.5 rounded bg-panel border border-border">
                            #{idx + 1} {b.speaker_name}
                          </span>
                          <span className="text-xs text-muted flex items-center gap-1">
                            <Mic2 className="w-3 h-3 text-muted" strokeWidth={1.5} />
                            {b.voice_id}
                          </span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-panel border border-border text-fg font-semibold uppercase">
                            {b.emotion}
                          </span>
                        </div>
                        <p className="text-xs text-fg leading-relaxed bg-panel p-2.5 rounded-md border border-border">
                          &ldquo;{b.text}&rdquo;
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={() => handleDeleteBlock(b.id)}
                        className="btn-ghost text-muted hover:text-fg self-end md:self-start h-8 px-2"
                        title="Hapus Baris Dialog"
                      >
                        <Trash2 className="w-3.5 h-3.5" strokeWidth={1.5} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Form Tambah Blok Percakapan Baru */}
            <form onSubmit={handleAddBlock} className="card-panel space-y-3">
              <h4 className="text-xs font-semibold text-fg flex items-center gap-1.5">
                <Plus className="w-3.5 h-3.5 text-fg" strokeWidth={1.5} /> Tambah Baris Percakapan
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* Nama Pembicara */}
                <div>
                  <label className="text-xs font-medium text-muted block mb-1">Nama Pembicara</label>
                  <input
                    type="text"
                    required
                    placeholder="Mis. Host / Bintang Tamu"
                    value={newSpeaker}
                    onChange={(e) => setNewSpeaker(e.target.value)}
                    className="input-base text-xs"
                  />
                </div>

                {/* Pemilih Suara */}
                <div>
                  <label className="text-xs font-medium text-muted block mb-1">Karakter Suara</label>
                  <select
                    value={newVoiceId}
                    onChange={(e) => setNewVoiceId(e.target.value)}
                    className="input-base text-xs"
                  >
                    {voices.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name} ({v.is_cloned ? "Klon" : v.category})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Pemilih Emosi */}
                <div>
                  <label className="text-xs font-medium text-muted block mb-1">Ekspresi Emosi</label>
                  <select
                    value={newEmotion}
                    onChange={(e) => setNewEmotion(e.target.value)}
                    className="input-base text-xs"
                  >
                    {emotionsCatalog.map((emo) => (
                      <option key={emo.id} value={emo.id}>
                        {emo.name} ({emo.category})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Teks Dialog */}
              <div>
                <label className="text-xs font-medium text-muted block mb-1">Teks Dialog</label>
                <textarea
                  rows={2}
                  required
                  placeholder="Masukkan kalimat dialog untuk pembicara ini..."
                  value={newText}
                  onChange={(e) => setNewText(e.target.value)}
                  className="input-base text-xs resize-none"
                />
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  className="btn-primary text-xs font-semibold flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" strokeWidth={1.5} />
                  <span>Tambahkan ke Dialog</span>
                </button>
              </div>
            </form>
          </>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 text-muted">
            <FolderKanban className="w-10 h-10 text-muted/60 mb-3" strokeWidth={1.5} />
            <h3 className="text-sm font-semibold text-fg">Pilih atau Buat Proyek</h3>
            <p className="text-xs text-muted max-w-sm mt-1">
              Pilih proyek di panel kiri untuk mulai menyusun dialog antar pembicara dan merender gabungan audio.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
