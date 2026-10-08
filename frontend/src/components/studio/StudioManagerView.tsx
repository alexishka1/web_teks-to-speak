"use client";

import React, { useState, useEffect } from "react";
import {
  Sliders,
  Mic,
  SlidersHorizontal,
  Smile,
  BookOpen,
  Plus,
  Upload,
  Trash2,
  Edit2,
  Check,
  X,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Volume2,
  Info,
  ShieldCheck,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import {
  fetchStudioVoicesApi,
  createStudioVoiceApi,
  updateStudioVoiceApi,
  deleteStudioVoiceApi,
  uploadStudioVoiceModelApi,
  fetchStudioPresetsApi,
  createStudioPresetApi,
  updateStudioPresetApi,
  deleteStudioPresetApi,
  fetchStudioEmotionsApi,
  createStudioEmotionApi,
  updateStudioEmotionApi,
  deleteStudioEmotionApi,
  fetchStudioLexiconApi,
  createStudioLexiconApi,
  updateStudioLexiconApi,
  deleteStudioLexiconApi,
  VoiceDTO,
  StylePresetDTO,
  EmotionItemDTO,
  LexiconItemDTO,
} from "@/lib/api";
import { useTTSStore } from "@/store/ttsStore";

type StudioTab = "voices" | "presets" | "emotions" | "lexicon";

export function StudioManagerView() {
  const [activeTab, setActiveTab] = useState<StudioTab>("voices");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Store refresh actions for hot reload
  const { fetchVoicesList, fetchPresetsList, fetchEmotionsList } = useTTSStore();

  // Tab Data States
  const [voices, setVoices] = useState<VoiceDTO[]>([]);
  const [presets, setPresets] = useState<StylePresetDTO[]>([]);
  const [emotions, setEmotions] = useState<EmotionItemDTO[]>([]);
  const [lexicon, setLexicon] = useState<LexiconItemDTO[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Modals & Forms
  const [showVoiceUploadModal, setShowVoiceUploadModal] = useState(false);
  const [showVoiceCloneModal, setShowVoiceCloneModal] = useState(false);
  const [showPresetModal, setShowPresetModal] = useState(false);
  const [showEmotionModal, setShowEmotionModal] = useState(false);
  const [showLexiconModal, setShowLexiconModal] = useState(false);

  // Edit targets (null means create new)
  const [editingPreset, setEditingPreset] = useState<StylePresetDTO | null>(null);
  const [editingEmotion, setEditingEmotion] = useState<EmotionItemDTO | null>(null);
  const [editingLexicon, setEditingLexicon] = useState<LexiconItemDTO | null>(null);

  // Audio Preview State
  const [previewAudioUrl, setPreviewAudioUrl] = useState<string | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Load active tab data on change
  useEffect(() => {
    loadCurrentTabData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const showNotification = (type: "success" | "error", text: string) => {
    setFeedback({ type, text });
    setTimeout(() => setFeedback(null), 4500);
  };

  const loadCurrentTabData = async () => {
    setIsLoading(true);
    try {
      if (activeTab === "voices") {
        const data = await fetchStudioVoicesApi();
        setVoices(data);
      } else if (activeTab === "presets") {
        const data = await fetchStudioPresetsApi();
        setPresets(data);
      } else if (activeTab === "emotions") {
        const data = await fetchStudioEmotionsApi();
        setEmotions(data);
      } else if (activeTab === "lexicon") {
        const data = await fetchStudioLexiconApi();
        setLexicon(data);
      }
    } catch (err: any) {
      showNotification("error", err.message || "Gagal memuat data studio.");
    } finally {
      setIsLoading(false);
    }
  };

  // =========================================================================
  // 1. VOICES ACTIONS
  // =========================================================================

  const handleToggleVoiceActive = async (voice: VoiceDTO) => {
    try {
      const updated = await updateStudioVoiceApi(voice.id, { is_active: !voice.is_active });
      setVoices((prev) => prev.map((v) => (v.id === voice.id ? updated : v)));
      // Hot reload global voice list
      await fetchVoicesList();
      showNotification(
        "success",
        `Suara '${voice.name}' ${updated.is_active ? "diaktifkan" : "dinonaktifkan"}. Perubahan langsung aktif di Text to Speech!`
      );
    } catch (err: any) {
      showNotification("error", err.message || "Gagal mengubah status suara.");
    }
  };

  const handleDeleteVoice = async (voiceId: string, voiceName: string) => {
    if (!confirm(`Hapus suara '${voiceName}' dari Studio Manager?`)) return;
    try {
      await deleteStudioVoiceApi(voiceId);
      setVoices((prev) => prev.filter((v) => v.id !== voiceId));
      await fetchVoicesList();
      showNotification("success", `Suara '${voiceName}' berhasil dihapus.`);
    } catch (err: any) {
      showNotification("error", err.message || "Gagal menghapus suara.");
    }
  };

  // Upload Voice Model Form State
  const [uploadModelFile, setUploadModelFile] = useState<File | null>(null);
  const [uploadConfigFile, setUploadConfigFile] = useState<File | null>(null);
  const [voiceFormName, setVoiceFormName] = useState("");
  const [voiceFormGender, setVoiceFormGender] = useState("female");
  const [voiceFormLang, setVoiceFormLang] = useState("id-ID");
  const [voiceFormCategory, setVoiceFormCategory] = useState("creator");
  const [voiceFormDesc, setVoiceFormDesc] = useState("");
  const [isSubmittingVoice, setIsSubmittingVoice] = useState(false);

  const handleUploadVoiceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadModelFile || !uploadConfigFile || !voiceFormName.trim()) {
      showNotification("error", "Harap pilih file .onnx, file .json, dan isi nama suara.");
      return;
    }

    if (!uploadModelFile.name.toLowerCase().endsWith(".onnx")) {
      showNotification("error", "File model harus memiliki ekstensi .onnx!");
      return;
    }
    if (!uploadConfigFile.name.toLowerCase().endsWith(".json")) {
      showNotification("error", "File konfigurasi harus memiliki ekstensi .json!");
      return;
    }

    setIsSubmittingVoice(true);
    try {
      const formData = new FormData();
      formData.append("model_file", uploadModelFile);
      formData.append("config_file", uploadConfigFile);
      formData.append("name", voiceFormName.trim());
      formData.append("gender", voiceFormGender);
      formData.append("language", voiceFormLang);
      formData.append("category", voiceFormCategory);
      formData.append("description", voiceFormDesc.trim());

      const created = await uploadStudioVoiceModelApi(formData);
      setVoices((prev) => [created, ...prev]);
      await fetchVoicesList();
      setShowVoiceUploadModal(false);
      setUploadModelFile(null);
      setUploadConfigFile(null);
      setVoiceFormName("");
      setVoiceFormDesc("");
      showNotification(
        "success",
        `Model suara '${created.name}' lolos uji sintesis dan langsung tersedia di Text to Speech!`
      );
    } catch (err: any) {
      showNotification("error", err.message || "Validasi atau sintesis model suara gagal.");
    } finally {
      setIsSubmittingVoice(false);
    }
  };

  // Voice Clone Form State
  const [cloneSampleFile, setCloneSampleFile] = useState<File | null>(null);
  const [cloneVoiceName, setCloneVoiceName] = useState("");
  const [cloneSpeakerName, setCloneSpeakerName] = useState("");
  const [cloneConsent, setCloneConsent] = useState(false);
  const [isSubmittingClone, setIsSubmittingClone] = useState(false);

  const handleVoiceCloneSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cloneSampleFile || !cloneVoiceName.trim() || !cloneSpeakerName.trim()) {
      showNotification("error", "Harap lengkapi semua kolom dan pilih file sampel audio (10-30 detik).");
      return;
    }
    if (!cloneConsent) {
      showNotification("error", "WAJIB mencentang persetujuan pemilik suara demi kepatuhan etika AI!");
      return;
    }

    setIsSubmittingClone(true);
    try {
      const formData = new FormData();
      formData.append("file", cloneSampleFile);
      formData.append("voice_name", cloneVoiceName.trim());
      formData.append("speaker_name", cloneSpeakerName.trim());
      formData.append("consent_checkbox", "true");

      const res = await fetch("/api/voice-clone/upload", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Gagal mengklon suara.");
      }

      setShowVoiceCloneModal(false);
      setCloneSampleFile(null);
      setCloneVoiceName("");
      setCloneSpeakerName("");
      setCloneConsent(false);
      await loadCurrentTabData();
      await fetchVoicesList();
      showNotification("success", "Klon suara berhasil diproses dan dicatat dalam audit consent!");
    } catch (err: any) {
      showNotification("error", err.message || "Gagal memproses kloning suara.");
    } finally {
      setIsSubmittingClone(false);
    }
  };

  // =========================================================================
  // 2. PRESETS ACTIONS
  // =========================================================================

  const [presetForm, setPresetForm] = useState({
    id: "",
    name: "",
    category: "content_creator",
    voice_id: "",
    speed: 1.0,
    pitch: 0.0,
    pause_scale: 1.0,
    audio_effect: "none",
    emotion: "neutral",
    emotion_intensity: 100,
    description: "",
    is_active: true,
  });

  const handleOpenPresetModal = (presetToEdit?: StylePresetDTO) => {
    if (presetToEdit) {
      setEditingPreset(presetToEdit);
      setPresetForm({
        id: presetToEdit.id,
        name: presetToEdit.name,
        category: presetToEdit.category,
        voice_id: presetToEdit.voice_id || "",
        speed: presetToEdit.speed,
        pitch: presetToEdit.pitch,
        pause_scale: presetToEdit.pause_scale,
        audio_effect: presetToEdit.audio_effect,
        emotion: presetToEdit.emotion,
        emotion_intensity: presetToEdit.emotion_intensity,
        description: presetToEdit.description,
        is_active: presetToEdit.is_active,
      });
    } else {
      setEditingPreset(null);
      setPresetForm({
        id: "",
        name: "",
        category: "content_creator",
        voice_id: voices[0]?.id || "",
        speed: 1.0,
        pitch: 0.0,
        pause_scale: 1.0,
        audio_effect: "none",
        emotion: "neutral",
        emotion_intensity: 100,
        description: "",
        is_active: true,
      });
    }
    setShowPresetModal(true);
  };

  const handleSavePreset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!presetForm.name.trim()) {
      showNotification("error", "Nama preset wajib diisi!");
      return;
    }

    try {
      if (editingPreset) {
        const updated = await updateStudioPresetApi(editingPreset.id, presetForm);
        setPresets((prev) => prev.map((p) => (p.id === editingPreset.id ? updated : p)));
        showNotification("success", `Preset '${updated.name}' berhasil diperbarui!`);
      } else {
        const created = await createStudioPresetApi(presetForm);
        setPresets((prev) => [created, ...prev]);
        showNotification("success", `Preset baru '${created.name}' langsung tersedia di Text to Speech!`);
      }
      await fetchPresetsList();
      setShowPresetModal(false);
    } catch (err: any) {
      showNotification("error", err.message || "Gagal menyimpan preset.");
    }
  };

  const handleTogglePresetActive = async (preset: StylePresetDTO) => {
    try {
      const updated = await updateStudioPresetApi(preset.id, { is_active: !preset.is_active });
      setPresets((prev) => prev.map((p) => (p.id === preset.id ? updated : p)));
      await fetchPresetsList();
      showNotification(
        "success",
        `Preset '${preset.name}' ${updated.is_active ? "diaktifkan" : "dinonaktifkan"} secara instan.`
      );
    } catch (err: any) {
      showNotification("error", err.message || "Gagal mengubah status preset.");
    }
  };

  const handleDeletePreset = async (presetId: string, presetName: string) => {
    if (!confirm(`Hapus preset '${presetName}'?`)) return;
    try {
      await deleteStudioPresetApi(presetId);
      setPresets((prev) => prev.filter((p) => p.id !== presetId));
      await fetchPresetsList();
      showNotification("success", `Preset '${presetName}' dihapus.`);
    } catch (err: any) {
      showNotification("error", err.message || "Gagal menghapus preset.");
    }
  };

  // =========================================================================
  // 3. EMOTIONS ACTIONS
  // =========================================================================

  const [emotionForm, setEmotionForm] = useState({
    id: "",
    name: "",
    category: "dasar",
    speed: 1.0,
    pitch: 0.0,
    pause_scale: 1.0,
    effect: "none",
    color: "#94a3b8",
    description: "",
    is_active: true,
  });

  const handleOpenEmotionModal = (emoToEdit?: EmotionItemDTO) => {
    if (emoToEdit) {
      setEditingEmotion(emoToEdit);
      setEmotionForm({
        id: emoToEdit.id,
        name: emoToEdit.name,
        category: emoToEdit.category,
        speed: emoToEdit.speed,
        pitch: emoToEdit.pitch,
        pause_scale: emoToEdit.pause_scale,
        effect: emoToEdit.effect,
        color: emoToEdit.color,
        description: emoToEdit.description,
        is_active: emoToEdit.is_active,
      });
    } else {
      setEditingEmotion(null);
      setEmotionForm({
        id: "",
        name: "",
        category: "dasar",
        speed: 1.0,
        pitch: 0.0,
        pause_scale: 1.0,
        effect: "none",
        color: "#60a5fa",
        description: "",
        is_active: true,
      });
    }
    setShowEmotionModal(true);
  };

  const handleSaveEmotion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emotionForm.name.trim() || (!editingEmotion && !emotionForm.id.trim())) {
      showNotification("error", "ID dan Nama emosi wajib diisi.");
      return;
    }

    try {
      if (editingEmotion) {
        const updated = await updateStudioEmotionApi(editingEmotion.id, emotionForm);
        setEmotions((prev) => prev.map((e) => (e.id === editingEmotion.id ? updated : e)));
        showNotification("success", `Emosi '${updated.name}' berhasil diperbarui!`);
      } else {
        const created = await createStudioEmotionApi(emotionForm);
        setEmotions((prev) => [...prev, created]);
        showNotification("success", `Emosi baru '${created.name}' langsung aktif di Text to Speech!`);
      }
      await fetchEmotionsList();
      setShowEmotionModal(false);
    } catch (err: any) {
      showNotification("error", err.message || "Gagal menyimpan emosi.");
    }
  };

  const handleToggleEmotionActive = async (emo: EmotionItemDTO) => {
    try {
      const updated = await updateStudioEmotionApi(emo.id, { is_active: !emo.is_active });
      setEmotions((prev) => prev.map((e) => (e.id === emo.id ? updated : e)));
      await fetchEmotionsList();
      showNotification(
        "success",
        `Emosi '${emo.name}' ${updated.is_active ? "diaktifkan" : "dinonaktifkan"}.`
      );
    } catch (err: any) {
      showNotification("error", err.message || "Gagal mengubah status emosi.");
    }
  };

  const handleDeleteEmotion = async (emoId: string, emoName: string) => {
    if (emoId === "neutral") {
      showNotification("error", "Emosi netral adalah standar sistem dan tidak boleh dihapus.");
      return;
    }
    if (!confirm(`Hapus emosi '${emoName}'?`)) return;
    try {
      await deleteStudioEmotionApi(emoId);
      setEmotions((prev) => prev.filter((e) => e.id !== emoId));
      await fetchEmotionsList();
      showNotification("success", `Emosi '${emoName}' dihapus.`);
    } catch (err: any) {
      showNotification("error", err.message || "Gagal menghapus emosi.");
    }
  };

  // =========================================================================
  // 4. LEXICON ACTIONS
  // =========================================================================

  const [lexiconForm, setLexiconForm] = useState({
    word: "",
    replacement: "",
    voice_id: "",
    is_regex: false,
    is_active: true,
  });

  const handleOpenLexiconModal = (entryToEdit?: LexiconItemDTO) => {
    if (entryToEdit) {
      setEditingLexicon(entryToEdit);
      setLexiconForm({
        word: entryToEdit.word,
        replacement: entryToEdit.replacement,
        voice_id: entryToEdit.voice_id || "",
        is_regex: entryToEdit.is_regex,
        is_active: entryToEdit.is_active,
      });
    } else {
      setEditingLexicon(null);
      setLexiconForm({
        word: "",
        replacement: "",
        voice_id: "",
        is_regex: false,
        is_active: true,
      });
    }
    setShowLexiconModal(true);
  };

  const handleSaveLexicon = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lexiconForm.word.trim() || !lexiconForm.replacement.trim()) {
      showNotification("error", "Kata asli dan pelafalan pengganti wajib diisi.");
      return;
    }

    try {
      const payload = {
        ...lexiconForm,
        voice_id: lexiconForm.voice_id || null,
      };

      if (editingLexicon) {
        const updated = await updateStudioLexiconApi(editingLexicon.id, payload);
        setLexicon((prev) => prev.map((l) => (l.id === editingLexicon.id ? updated : l)));
        showNotification("success", `Entri kamus '${updated.word}' diperbarui!`);
      } else {
        const created = await createStudioLexiconApi(payload);
        setLexicon((prev) => [created, ...prev]);
        showNotification("success", `Entri kata '${created.word}' langsung aktif di pipeline pelafalan!`);
      }
      setShowLexiconModal(false);
    } catch (err: any) {
      showNotification("error", err.message || "Gagal menyimpan entri kamus.");
    }
  };

  const handleToggleLexiconActive = async (entry: LexiconItemDTO) => {
    try {
      const updated = await updateStudioLexiconApi(entry.id, { is_active: !entry.is_active });
      setLexicon((prev) => prev.map((l) => (l.id === entry.id ? updated : l)));
      showNotification(
        "success",
        `Kamus '${entry.word}' ${updated.is_active ? "diaktifkan" : "dinonaktifkan"}.`
      );
    } catch (err: any) {
      showNotification("error", err.message || "Gagal mengubah status kamus.");
    }
  };

  const handleDeleteLexicon = async (entryId: string, word: string) => {
    if (!confirm(`Hapus kata '${word}' dari kamus?`)) return;
    try {
      await deleteStudioLexiconApi(entryId);
      setLexicon((prev) => prev.filter((l) => l.id !== entryId));
      showNotification("success", `Kata '${word}' dihapus dari kamus.`);
    } catch (err: any) {
      showNotification("error", err.message || "Gagal menghapus entri kamus.");
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-background text-fg overflow-y-auto">
      {/* Top Banner & Title */}
      <div className="p-6 border-b border-border bg-surface backdrop-blur flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-panel border border-border text-fg">
              <Sliders className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-fg flex items-center gap-2">
                Studio Manager
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-panel border border-border text-fg font-semibold border border-border">
                  Demo Dynamic
                </span>
              </h1>
              <p className="text-xs text-muted mt-0.5">
                Kelola Suara, Preset, Emosi, dan Kamus Pelafalan secara dinamis tanpa coding (Hot-Reload otomatis).
              </p>
            </div>
          </div>
        </div>

        {/* Global Tab Buttons */}
        <div className="flex items-center gap-1.5 p-1 bg-surface border border-border rounded-xl self-stretch sm:self-auto overflow-x-auto">
          <button
            id="tab-btn-voices"
            onClick={() => setActiveTab("voices")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "voices"
                ? "bg-primary text-primary-fg text-fg shadow-sm"
                : "text-muted hover:text-fg hover:bg-panel"
            }`}
          >
            <Mic className="w-3.5 h-3.5" />
            Suara ({voices.length})
          </button>
          <button
            id="tab-btn-presets"
            onClick={() => setActiveTab("presets")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "presets"
                ? "bg-primary text-primary-fg text-fg shadow-sm"
                : "text-muted hover:text-fg hover:bg-panel"
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            Preset ({presets.length})
          </button>
          <button
            id="tab-btn-emotions"
            onClick={() => setActiveTab("emotions")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "emotions"
                ? "bg-primary text-primary-fg text-fg shadow-sm"
                : "text-muted hover:text-fg hover:bg-panel"
            }`}
          >
            <Smile className="w-3.5 h-3.5" />
            Emosi ({emotions.length})
          </button>
          <button
            id="tab-btn-lexicon"
            onClick={() => setActiveTab("lexicon")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "lexicon"
                ? "bg-primary text-primary-fg text-fg shadow-sm"
                : "text-muted hover:text-fg hover:bg-panel"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            Kamus ({lexicon.length})
          </button>
        </div>
      </div>

      {/* Floating Notification */}
      {feedback && (
        <div
          className={`mx-6 mt-4 p-3.5 rounded-xl border flex items-center gap-3 text-xs font-medium transition-all ${
            feedback.type === "success"
              ? "bg-panel border border-border border-border text-fg font-semibold"
              : "bg-surface border-2 border-dashed border-fg border-fg text-fg font-semibold"
          }`}
        >
          {feedback.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 shrink-0 text-fg font-semibold" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0 text-fg font-semibold" />
          )}
          <span>{feedback.text}</span>
          <button
            onClick={() => setFeedback(null)}
            className="ml-auto text-muted hover:text-fg"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <div className="p-6 space-y-6">
        {/* ================================================================= */}
        {/* TAB 1: SUARA (VOICES)                                            */}
        {/* ================================================================= */}
        {activeTab === "voices" && (
          <div className="space-y-5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold text-fg">Daftar Suara Kreator & Model</h2>
                <p className="text-xs text-muted">
                  Suara aktif langsung tersedia di dropdown Text to Speech. Nonaktifkan untuk menyembunyikan tanpa menghapus.
                </p>
              </div>
              <div className="flex items-center gap-2.5">
                <button
                  onClick={() => setShowVoiceCloneModal(true)}
                  className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-panel hover:bg-hover border border-border text-xs font-medium text-fg transition-all"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-fg" />
                  Klon Suara (Sampel)
                </button>
                <button
                  id="btn-upload-voice"
                  onClick={() => setShowVoiceUploadModal(true)}
                  className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-primary text-primary-fg hover:bg-primary-hover text-fg text-xs font-medium shadow-sm transition-all"
                >
                  <Upload className="w-3.5 h-3.5" />
                  Upload Model (.onnx + .json)
                </button>
              </div>
            </div>

            {/* Voices Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {voices.map((voice) => (
                <div
                  key={voice.id}
                  className={`p-4 rounded-xl border transition-all ${
                    voice.is_active
                      ? "bg-surface border-border hover:border-border"
                      : "bg-surface border-border opacity-60"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-fg truncate">{voice.name}</h3>
                        {voice.is_cloned && (
                          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-panel text-fg font-mono border border-border">
                            Klon
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5 mt-1 text-[11px] text-muted">
                        <span className="capitalize">{voice.gender}</span>
                        <span>•</span>
                        <span>{voice.language}</span>
                        <span>•</span>
                        <span className="px-1.5 py-0.2 rounded bg-panel text-[10px] text-fg">
                          {voice.engine}
                        </span>
                      </div>
                    </div>

                    {/* Active Toggle Switch */}
                    <button
                      onClick={() => handleToggleVoiceActive(voice)}
                      title={voice.is_active ? "Klik untuk nonaktifkan" : "Klik untuk aktifkan"}
                      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        voice.is_active ? "bg-primary text-primary-fg" : "bg-panel"
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                          voice.is_active ? "translate-x-4" : "translate-x-0"
                        }`}
                      />
                    </button>
                  </div>

                  <p className="text-xs text-muted mt-2.5 line-clamp-2 min-h-[32px]">
                    {voice.description || "Tidak ada deskripsi tambahan."}
                  </p>

                  <div className="mt-3.5 pt-3 border-t border-border flex items-center justify-between text-xs">
                    <span className="text-[11px] text-muted font-mono truncate max-w-[150px]">
                      {voice.id}
                    </span>
                    <div className="flex items-center gap-1">
                      {voice.preview_url && (
                        <button
                          onClick={() => {
                            const audio = new Audio(voice.preview_url || "");
                            audio.play().catch(() => {});
                          }}
                          className="p-1.5 rounded-lg text-muted hover:text-fg hover:bg-hover transition-colors"
                          title="Putar Sampel"
                        >
                          <Volume2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteVoice(voice.id, voice.name)}
                        className="p-1.5 rounded-lg text-muted hover:text-fg font-semibold hover:bg-surface border-2 border-dashed border-fg transition-colors"
                        title="Hapus Suara"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 2: PRESET GAYA (PRESETS)                                     */}
        {/* ================================================================= */}
        {activeTab === "presets" && (
          <div className="space-y-5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold text-fg">Preset Gaya Vokal TaSTP</h2>
                <p className="text-xs text-muted">
                  Simpan kombinasi kecepatan, pitch, jeda, emosi, dan efek audio favorit untuk dipakai dalam 1-klik di editor.
                </p>
              </div>
              <button
                id="btn-add-preset"
                onClick={() => handleOpenPresetModal()}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-primary text-primary-fg hover:bg-primary-hover text-fg text-xs font-medium shadow-sm transition-all"
              >
                <Plus className="w-3.5 h-3.5" />
                Tambah Preset Baru
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {presets.map((p) => (
                <div
                  key={p.id}
                  className={`p-4 rounded-xl border transition-all ${
                    p.is_active
                      ? "bg-surface border-border hover:border-border"
                      : "bg-surface border-border opacity-60"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold text-fg truncate">{p.name}</h3>
                      <div className="flex items-center gap-1.5 mt-1 text-[11px] text-muted">
                        <span className="capitalize px-1.5 py-0.2 rounded bg-indigo-500/10 text-fg">
                          {p.category}
                        </span>
                        <span>•</span>
                        <span className="capitalize">{p.emotion} ({p.emotion_intensity}%)</span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleTogglePresetActive(p)}
                      title={p.is_active ? "Nonaktifkan preset" : "Aktifkan preset"}
                      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        p.is_active ? "bg-primary text-primary-fg" : "bg-panel"
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                          p.is_active ? "translate-x-4" : "translate-x-0"
                        }`}
                      />
                    </button>
                  </div>

                  <p className="text-xs text-muted mt-2 line-clamp-2 min-h-[32px]">
                    {p.description || "Tidak ada deskripsi."}
                  </p>

                  {/* Parameter Tags */}
                  <div className="mt-3 flex flex-wrap gap-1.5 text-[11px]">
                    <span className="px-2 py-0.5 rounded bg-panel text-fg">
                      Kecepatan: {p.speed}x
                    </span>
                    <span className="px-2 py-0.5 rounded bg-panel text-fg">
                      Pitch: {p.pitch >= 0 ? `+${p.pitch}` : p.pitch}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-panel text-fg">
                      Jeda: {p.pause_scale}x
                    </span>
                    {p.audio_effect !== "none" && (
                      <span className="px-2 py-0.5 rounded bg-panel text-purple-300 border border-border">
                        Efek: {p.audio_effect}
                      </span>
                    )}
                  </div>

                  <div className="mt-3.5 pt-3 border-t border-border flex items-center justify-between text-xs">
                    <span className="text-[11px] text-muted font-mono truncate max-w-[130px]">
                      {p.id}
                    </span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleOpenPresetModal(p)}
                        className="p-1.5 rounded-lg text-muted hover:text-fg hover:bg-hover transition-colors"
                        title="Edit Preset"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeletePreset(p.id, p.name)}
                        className="p-1.5 rounded-lg text-muted hover:text-fg font-semibold hover:bg-surface border-2 border-dashed border-fg transition-colors"
                        title="Hapus Preset"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 3: KATALOG EMOSI (EMOTIONS)                                  */}
        {/* ================================================================= */}
        {activeTab === "emotions" && (
          <div className="space-y-5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold text-fg">Katalog Modulasi Emosi Vokal</h2>
                <p className="text-xs text-muted">
                  Konfigurasi parameter prosodi per emosi untuk modulasi vokal berfrekuensi natural.
                </p>
              </div>
              <button
                id="btn-add-emotion"
                onClick={() => handleOpenEmotionModal()}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-primary text-primary-fg hover:bg-primary-hover text-fg text-xs font-medium shadow-sm transition-all"
              >
                <Plus className="w-3.5 h-3.5" />
                Tambah Emosi Baru
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {emotions.map((emo) => (
                <div
                  key={emo.id}
                  className={`p-4 rounded-xl border relative overflow-hidden transition-all ${
                    emo.is_active
                      ? "bg-surface border-border hover:border-border"
                      : "bg-surface border-border opacity-60"
                  }`}
                >
                  {/* Top Color Accent Strip */}
                  <div
                    className="absolute top-0 left-0 right-0 h-1"
                    style={{ backgroundColor: emo.color || "#94a3b8" }}
                  />

                  <div className="flex items-start justify-between gap-2 mt-1">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-3 h-3 rounded-full shrink-0 shadow-sm"
                          style={{ backgroundColor: emo.color }}
                        />
                        <h3 className="text-sm font-semibold text-fg truncate">{emo.name}</h3>
                      </div>
                      <div className="flex items-center gap-1.5 mt-1 text-[11px] text-muted">
                        <span className="capitalize">{emo.category}</span>
                        <span>•</span>
                        <span className="font-mono text-muted">{emo.id}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleToggleEmotionActive(emo)}
                      title={emo.is_active ? "Nonaktifkan emosi" : "Aktifkan emosi"}
                      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        emo.is_active ? "bg-primary text-primary-fg" : "bg-panel"
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                          emo.is_active ? "translate-x-4" : "translate-x-0"
                        }`}
                      />
                    </button>
                  </div>

                  <p className="text-xs text-muted mt-2 line-clamp-2 min-h-[32px]">
                    {emo.description || "Tanpa deskripsi."}
                  </p>

                  <div className="mt-3 flex flex-wrap gap-1.5 text-[11px]">
                    <span className="px-2 py-0.5 rounded bg-panel text-fg">
                      Speed: {emo.speed}x
                    </span>
                    <span className="px-2 py-0.5 rounded bg-panel text-fg">
                      Pitch: {emo.pitch >= 0 ? `+${emo.pitch}` : emo.pitch}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-panel text-fg">
                      Jeda: {emo.pause_scale}x
                    </span>
                    {emo.effect !== "none" && (
                      <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-fg border border-indigo-500/20">
                        Efek: {emo.effect}
                      </span>
                    )}
                  </div>

                  <div className="mt-3.5 pt-3 border-t border-border flex items-center justify-end gap-1 text-xs">
                    <button
                      onClick={() => handleOpenEmotionModal(emo)}
                      className="p-1.5 rounded-lg text-muted hover:text-fg hover:bg-hover transition-colors"
                      title="Edit Emosi"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    {emo.id !== "neutral" && (
                      <button
                        onClick={() => handleDeleteEmotion(emo.id, emo.name)}
                        className="p-1.5 rounded-lg text-muted hover:text-fg font-semibold hover:bg-surface border-2 border-dashed border-fg transition-colors"
                        title="Hapus Emosi"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 4: KAMUS PELAFALAN (LEXICON)                                 */}
        {/* ================================================================= */}
        {activeTab === "lexicon" && (
          <div className="space-y-5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold text-fg">Kamus Pelafalan Kustom (Lexicon)</h2>
                <p className="text-xs text-muted">
                  Koreksi fonetik istilah asing, akronim, atau nama brand kreator agar dibaca natural oleh engine vokal.
                </p>
              </div>
              <button
                id="btn-add-lexicon"
                onClick={() => handleOpenLexiconModal()}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-primary text-primary-fg hover:bg-primary-hover text-fg text-xs font-medium shadow-sm transition-all"
              >
                <Plus className="w-3.5 h-3.5" />
                Tambah Kata Baru
              </button>
            </div>

            <div className="bg-surface border border-border rounded-xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-surface text-muted uppercase font-medium border-b border-border">
                    <tr>
                      <th className="py-3 px-4">Kata Asli</th>
                      <th className="py-3 px-4">Pelafalan Pengganti</th>
                      <th className="py-3 px-4">Mode</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1E293B]">
                    {lexicon.map((entry) => (
                      <tr
                        key={entry.id}
                        className={`hover:bg-[#18233C]/60 transition-colors ${
                          !entry.is_active ? "opacity-50" : ""
                        }`}
                      >
                        <td className="py-3.5 px-4 font-semibold text-fg">
                          {entry.word}
                        </td>
                        <td className="py-3.5 px-4 font-mono text-fg font-semibold">
                          {entry.replacement}
                        </td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                              entry.is_regex
                                ? "bg-panel border border-border text-fg font-semibold border border-amber-500/20"
                                : "bg-panel text-fg"
                            }`}
                          >
                            {entry.is_regex ? "Regex" : "Batas Kata (\\b)"}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <button
                            onClick={() => handleToggleLexiconActive(entry)}
                            className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                              entry.is_active ? "bg-primary text-primary-fg" : "bg-panel"
                            }`}
                          >
                            <span
                              className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                                entry.is_active ? "translate-x-4" : "translate-x-0"
                              }`}
                            />
                          </button>
                        </td>
                        <td className="py-3.5 px-4 text-right space-x-1">
                          <button
                            onClick={() => handleOpenLexiconModal(entry)}
                            className="p-1.5 rounded-lg text-muted hover:text-fg hover:bg-hover transition-colors"
                            title="Edit"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDeleteLexicon(entry.id, entry.word)}
                            className="p-1.5 rounded-lg text-muted hover:text-fg font-semibold hover:bg-surface border-2 border-dashed border-fg transition-colors"
                            title="Hapus"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ===================================================================== */}
      {/* MODAL 1: UPLOAD SUARA BARU (.onnx + .json)                            */}
      {/* ===================================================================== */}
      {showVoiceUploadModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-indigo-500/20 text-fg">
                  <Upload className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-fg">Upload Suara Baru</h3>
                  <p className="text-xs text-muted">Piper TTS (.onnx + .json)</p>
                </div>
              </div>
              <button
                onClick={() => setShowVoiceUploadModal(false)}
                className="text-muted hover:text-fg p-1 rounded-lg hover:bg-panel"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUploadVoiceSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-medium text-fg mb-1">
                  File Model ONNX (.onnx) <span className="text-fg font-semibold">*</span>
                </label>
                <input
                  id="input-file-onnx"
                  type="file"
                  accept=".onnx"
                  onChange={(e) => setUploadModelFile(e.target.files?.[0] || null)}
                  required
                  className="w-full p-2 bg-surface border border-border rounded-lg text-fg file:mr-3 file:py-1 file:px-2.5 file:rounded-md file:border-0 file:text-xs file:bg-primary text-primary-fg file:text-fg hover:file:bg-indigo-500 cursor-pointer"
                />
              </div>

              <div>
                <label className="block font-medium text-fg mb-1">
                  File Konfigurasi JSON (.json) <span className="text-fg font-semibold">*</span>
                </label>
                <input
                  id="input-file-json"
                  type="file"
                  accept=".json"
                  onChange={(e) => setUploadConfigFile(e.target.files?.[0] || null)}
                  required
                  className="w-full p-2 bg-surface border border-border rounded-lg text-fg file:mr-3 file:py-1 file:px-2.5 file:rounded-md file:border-0 file:text-xs file:bg-primary text-primary-fg file:text-fg hover:file:bg-indigo-500 cursor-pointer"
                />
              </div>

              <div>
                <label className="block font-medium text-fg mb-1">
                  Nama Suara <span className="text-fg font-semibold">*</span>
                </label>
                <input
                  id="input-voice-name"
                  type="text"
                  value={voiceFormName}
                  onChange={(e) => setVoiceFormName(e.target.value)}
                  placeholder="Misal: Gadis Studio Ekspresif"
                  required
                  className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-fg mb-1">Gender</label>
                  <select
                    value={voiceFormGender}
                    onChange={(e) => setVoiceFormGender(e.target.value)}
                    className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg focus:outline-none focus:border-indigo-500"
                  >
                    <option value="female">Wanita</option>
                    <option value="male">Pria</option>
                    <option value="neutral">Netral</option>
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-fg mb-1">Kategori</label>
                  <select
                    value={voiceFormCategory}
                    onChange={(e) => setVoiceFormCategory(e.target.value)}
                    className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg focus:outline-none focus:border-indigo-500"
                  >
                    <option value="creator">Kreator Konten</option>
                    <option value="narrator">Narator Cerita</option>
                    <option value="podcast">Podcast</option>
                    <option value="news">Berita Formal</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-medium text-fg mb-1">Deskripsi Suara</label>
                <textarea
                  value={voiceFormDesc}
                  onChange={(e) => setVoiceFormDesc(e.target.value)}
                  placeholder="Karakter suara, nada, dan kecocokan naskah..."
                  rows={2}
                  className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              <div className="p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-[11px] text-fg flex items-start gap-2">
                <Info className="w-4 h-4 shrink-0 text-fg mt-0.5" />
                <span>
                  Sistem akan menguji sintesis satu kalimat secara otomatis. Bila file korup atau tidak cocok, proses akan ditolak dengan pesan error yang jelas.
                </span>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowVoiceUploadModal(false)}
                  className="px-4 py-2 rounded-lg bg-panel hover:bg-panel text-fg text-xs font-medium"
                >
                  Batal
                </button>
                <button
                  id="btn-submit-upload-voice"
                  type="submit"
                  disabled={isSubmittingVoice}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-fg hover:bg-primary-hover text-fg text-xs font-medium shadow-md transition-all disabled:opacity-50"
                >
                  {isSubmittingVoice ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Menguji Sintesis...
                    </>
                  ) : (
                    "Uji & Simpan Suara"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL 2: VOICE CLONE WITH ETHICAL CONSENT                             */}
      {/* ===================================================================== */}
      {showVoiceCloneModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-purple-500/20 text-fg font-mono">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-fg">Klon Suara (Voice Clone)</h3>
                  <p className="text-xs text-muted">Kepatuhan Etika & Hak Cipta AI</p>
                </div>
              </div>
              <button
                onClick={() => setShowVoiceCloneModal(false)}
                className="text-muted hover:text-fg p-1 rounded-lg hover:bg-panel"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleVoiceCloneSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-medium text-fg mb-1">
                  Sampel Audio Suara (WAV/MP3, 10–30 Detik) <span className="text-fg font-semibold">*</span>
                </label>
                <input
                  type="file"
                  accept="audio/*"
                  onChange={(e) => setCloneSampleFile(e.target.files?.[0] || null)}
                  required
                  className="w-full p-2 bg-surface border border-border rounded-lg text-fg file:mr-3 file:py-1 file:px-2.5 file:rounded-md file:border-0 file:text-xs file:bg-purple-600 file:text-fg cursor-pointer"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-fg mb-1">
                    Nama Profil Suara <span className="text-fg font-semibold">*</span>
                  </label>
                  <input
                    type="text"
                    value={cloneVoiceName}
                    onChange={(e) => setCloneVoiceName(e.target.value)}
                    placeholder="Misal: Suara Budi V2"
                    required
                    className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg"
                  />
                </div>
                <div>
                  <label className="block font-medium text-fg mb-1">
                    Nama Pemilik Suara <span className="text-fg font-semibold">*</span>
                  </label>
                  <input
                    type="text"
                    value={cloneSpeakerName}
                    onChange={(e) => setCloneSpeakerName(e.target.value)}
                    placeholder="Misal: Budi Santoso"
                    required
                    className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg"
                  />
                </div>
              </div>

              {/* Mandatory Ethics Consent Checkbox */}
              <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/30 text-purple-200 space-y-2">
                <label className="flex items-start gap-2.5 cursor-pointer">
                  <input
                    id="checkbox-clone-consent"
                    type="checkbox"
                    checked={cloneConsent}
                    onChange={(e) => setCloneConsent(e.target.checked)}
                    required
                    className="mt-0.5 rounded border-purple-400 text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-[11px] leading-relaxed">
                    <strong>Pernyataan Izin Pemilik Suara:</strong> Saya secara sadar menyatakan bahwa saya memiliki izin tertulis dan hak legal atas sampel suara ini untuk digunakan dalam sistem kecerdasan buatan TaSTP, serta bertanggung jawab penuh atas segala penggunaannya.
                  </span>
                </label>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowVoiceCloneModal(false)}
                  className="px-4 py-2 rounded-lg bg-panel hover:bg-panel text-fg text-xs font-medium"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingClone || !cloneConsent}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-fg text-xs font-medium shadow-md transition-all disabled:opacity-50"
                >
                  {isSubmittingClone ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Memproses Kloning...
                    </>
                  ) : (
                    "Daftarkan Klon Suara"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL 3: TAMBAH / EDIT PRESET GAYA                                   */}
      {/* ===================================================================== */}
      {showPresetModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="text-base font-bold text-fg">
                {editingPreset ? "Edit Preset Gaya" : "Tambah Preset Gaya Baru"}
              </h3>
              <button
                onClick={() => setShowPresetModal(false)}
                className="text-muted hover:text-fg p-1 rounded-lg hover:bg-panel"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSavePreset} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-fg mb-1">
                    Nama Preset <span className="text-fg font-semibold">*</span>
                  </label>
                  <input
                    id="input-preset-name"
                    type="text"
                    value={presetForm.name}
                    onChange={(e) => setPresetForm({ ...presetForm, name: e.target.value })}
                    placeholder="Misal: Promo Kilat"
                    required
                    className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg"
                  />
                </div>
                <div>
                  <label className="block font-medium text-fg mb-1">Kategori</label>
                  <select
                    value={presetForm.category}
                    onChange={(e) => setPresetForm({ ...presetForm, category: e.target.value })}
                    className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg"
                  >
                    <option value="content_creator">Kreator Konten</option>
                    <option value="commercial">Iklan & Promo</option>
                    <option value="storytelling">Bercerita</option>
                    <option value="podcast">Podcast</option>
                  </select>
                </div>
              </div>

              {/* Sliders: Speed, Pitch, Pause */}
              <div className="space-y-2.5 p-3 rounded-xl bg-surface border border-border">
                <div>
                  <div className="flex justify-between text-fg mb-1">
                    <span>Kecepatan Bicara</span>
                    <span className="font-mono text-fg">{presetForm.speed}x</span>
                  </div>
                  <input
                    type="range"
                    min="0.5"
                    max="2.0"
                    step="0.05"
                    value={presetForm.speed}
                    onChange={(e) => setPresetForm({ ...presetForm, speed: parseFloat(e.target.value) })}
                    className="w-full accent-indigo-500"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-fg mb-1">
                    <span>Tinggi Rendah Pitch</span>
                    <span className="font-mono text-fg">
                      {presetForm.pitch >= 0 ? `+${presetForm.pitch}` : presetForm.pitch}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="-10"
                    max="10"
                    step="0.5"
                    value={presetForm.pitch}
                    onChange={(e) => setPresetForm({ ...presetForm, pitch: parseFloat(e.target.value) })}
                    className="w-full accent-indigo-500"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-fg mb-1">
                    <span>Durasi Jeda (Pause Scale)</span>
                    <span className="font-mono text-fg">{presetForm.pause_scale}x</span>
                  </div>
                  <input
                    type="range"
                    min="0.5"
                    max="2.0"
                    step="0.05"
                    value={presetForm.pause_scale}
                    onChange={(e) => setPresetForm({ ...presetForm, pause_scale: parseFloat(e.target.value) })}
                    className="w-full accent-indigo-500"
                  />
                </div>
              </div>

              {/* Audio Effect & Emotion */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-fg mb-1">Efek Audio Server</label>
                  <select
                    value={presetForm.audio_effect}
                    onChange={(e) => setPresetForm({ ...presetForm, audio_effect: e.target.value })}
                    className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg"
                  >
                    <option value="none">Tanpa Efek (Pure)</option>
                    <option value="podcast_eq">Podcast Warm EQ</option>
                    <option value="reverb">Reverb Hangat</option>
                    <option value="radio">Radio Retro</option>
                    <option value="telephone">Telepon Seluler</option>
                    <option value="whisper">Bisikan Lembut</option>
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-fg mb-1">Emosi Tertaut</label>
                  <select
                    value={presetForm.emotion}
                    onChange={(e) => setPresetForm({ ...presetForm, emotion: e.target.value })}
                    className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg"
                  >
                    <option value="neutral">Netral (Standar)</option>
                    <option value="happy">Gembira / Ceria</option>
                    <option value="enthusiastic">Antusias & Enerjik</option>
                    <option value="storytelling">Storytelling / Mendongeng</option>
                    <option value="confident">Percaya Diri</option>
                    <option value="calm">Tenang / Santai</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-medium text-fg mb-1">Deskripsi Singkat</label>
                <input
                  type="text"
                  value={presetForm.description}
                  onChange={(e) => setPresetForm({ ...presetForm, description: e.target.value })}
                  placeholder="Karakteristik preset ini..."
                  className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowPresetModal(false)}
                  className="px-4 py-2 rounded-lg bg-panel hover:bg-panel text-fg text-xs font-medium"
                >
                  Batal
                </button>
                <button
                  id="btn-submit-preset"
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-primary text-primary-fg hover:bg-primary-hover text-fg text-xs font-medium shadow-md transition-all"
                >
                  Simpan Preset
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL 4: TAMBAH / EDIT EMOSI                                         */}
      {/* ===================================================================== */}
      {showEmotionModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="text-base font-bold text-fg">
                {editingEmotion ? "Edit Emosi Vokal" : "Tambah Emosi Baru"}
              </h3>
              <button
                onClick={() => setShowEmotionModal(false)}
                className="text-muted hover:text-fg p-1 rounded-lg hover:bg-panel"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveEmotion} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-fg mb-1">
                    ID Emosi (Slug) <span className="text-fg font-semibold">*</span>
                  </label>
                  <input
                    type="text"
                    value={emotionForm.id}
                    onChange={(e) => setEmotionForm({ ...emotionForm, id: e.target.value })}
                    disabled={!!editingEmotion}
                    placeholder="misal: dramatic_trailer"
                    required
                    className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg disabled:opacity-50"
                  />
                </div>
                <div>
                  <label className="block font-medium text-fg mb-1">
                    Nama Emosi <span className="text-fg font-semibold">*</span>
                  </label>
                  <input
                    type="text"
                    value={emotionForm.name}
                    onChange={(e) => setEmotionForm({ ...emotionForm, name: e.target.value })}
                    placeholder="Misal: Dramatis Sinematik"
                    required
                    className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-fg mb-1">Kategori</label>
                  <select
                    value={emotionForm.category}
                    onChange={(e) => setEmotionForm({ ...emotionForm, category: e.target.value })}
                    className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg"
                  >
                    <option value="dasar">Emosi Dasar</option>
                    <option value="nuansa">Nuansa Emosi</option>
                    <option value="gaya_bicara">Gaya Bicara</option>
                    <option value="karakter">Karakter & Non-Verbal</option>
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-fg mb-1">Warna Label</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={emotionForm.color}
                      onChange={(e) => setEmotionForm({ ...emotionForm, color: e.target.value })}
                      className="w-9 h-9 p-0.5 bg-surface border border-border rounded-lg cursor-pointer"
                    />
                    <input
                      type="text"
                      value={emotionForm.color}
                      onChange={(e) => setEmotionForm({ ...emotionForm, color: e.target.value })}
                      className="flex-1 p-2 bg-surface border border-border rounded-lg text-fg font-mono"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2 p-3 rounded-xl bg-surface border border-border">
                <div className="flex justify-between text-fg">
                  <span>Speed: {emotionForm.speed}x</span>
                  <span>Pitch: {emotionForm.pitch}</span>
                  <span>Jeda: {emotionForm.pause_scale}x</span>
                </div>
              </div>

              <div>
                <label className="block font-medium text-fg mb-1">Deskripsi</label>
                <input
                  type="text"
                  value={emotionForm.description}
                  onChange={(e) => setEmotionForm({ ...emotionForm, description: e.target.value })}
                  placeholder="Karakter vokal dari emosi ini..."
                  className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowEmotionModal(false)}
                  className="px-4 py-2 rounded-lg bg-panel hover:bg-panel text-fg text-xs font-medium"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-primary text-primary-fg hover:bg-primary-hover text-fg text-xs font-medium shadow-md transition-all"
                >
                  Simpan Emosi
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODAL 5: TAMBAH / EDIT KAMUS PELAFALAN                                */}
      {/* ===================================================================== */}
      {showLexiconModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="text-base font-bold text-fg">
                {editingLexicon ? "Edit Kata Kamus" : "Tambah Entri Kamus Pelafalan"}
              </h3>
              <button
                onClick={() => setShowLexiconModal(false)}
                className="text-muted hover:text-fg p-1 rounded-lg hover:bg-panel"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveLexicon} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-medium text-fg mb-1">
                  Kata Asli Naskah <span className="text-fg font-semibold">*</span>
                </label>
                <input
                  type="text"
                  value={lexiconForm.word}
                  onChange={(e) => setLexiconForm({ ...lexiconForm, word: e.target.value })}
                  placeholder="Misal: ChatGPT"
                  required
                  className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg"
                />
              </div>

              <div>
                <label className="block font-medium text-fg mb-1">
                  Pelafalan Pengganti Fonetik <span className="text-fg font-semibold">*</span>
                </label>
                <input
                  type="text"
                  value={lexiconForm.replacement}
                  onChange={(e) => setLexiconForm({ ...lexiconForm, replacement: e.target.value })}
                  placeholder="Misal: cet-ji-pi-ti"
                  required
                  className="w-full p-2.5 bg-surface border border-border rounded-lg text-fg font-mono"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="chk-regex"
                  checked={lexiconForm.is_regex}
                  onChange={(e) => setLexiconForm({ ...lexiconForm, is_regex: e.target.checked })}
                  className="rounded border-border text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="chk-regex" className="text-fg cursor-pointer">
                  Gunakan ekspresi reguler (Regex)
                </label>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowLexiconModal(false)}
                  className="px-4 py-2 rounded-lg bg-panel hover:bg-panel text-fg text-xs font-medium"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-primary text-primary-fg hover:bg-primary-hover text-fg text-xs font-medium shadow-md transition-all"
                >
                  Simpan Kata
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
