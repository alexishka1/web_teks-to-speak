export interface SynthesizePayload {
  text: string;
  voice_id: string;
  speed: number;
  pitch: number;
  pause_scale?: number;
  audio_effect?: string;
  emotion?: string;
  emotion_intensity?: number;
  sentence_emotions?: string[];
  is_cloned_voice?: boolean;
  voice_clone_consent?: boolean;
}

export interface SynthesizeResponse {
  job_id: string;
  status: string;
  audio_url: string;
  duration_sec: number;
  engine_used: string;
  created_at: string;
  message?: string;
}

export interface JobStatusResponse {
  id: string;
  status: string;
  audio_url: string | null;
  duration_sec: number;
  error_message: string | null;
  created_at: string;
}

export interface EmotionPresetDTO {
  id: string;
  name: string;
  category: string;
  speed: number;
  pitch: number;
  pause_scale: number;
  effect: string;
  color: string;
  description: string;
}

export async function fetchHealth() {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error("Gagal memeriksa status health");
  return res.json();
}

export async function fetchVoices() {
  const res = await fetch("/voices");
  if (!res.ok) {
    const fallbackRes = await fetch("/api/voices");
    if (!fallbackRes.ok) throw new Error("Gagal mengambil daftar suara");
    return fallbackRes.json();
  }
  return res.json();
}

export async function fetchEmotions(): Promise<EmotionPresetDTO[]> {
  const res = await fetch("/emotions");
  if (!res.ok) {
    const fallback = await fetch("/api/emotions");
    if (!fallback.ok) return [];
    return fallback.json();
  }
  return res.json();
}

export async function analyzeScriptEmotionsApi(text: string): Promise<any> {
  const res = await fetch("/emotions/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error("Gagal menganalisis emosi naskah");
  return res.json();
}

export async function synthesizeTTS(payload: SynthesizePayload): Promise<SynthesizeResponse> {
  const res = await fetch("/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Gagal melakukan sintesis (HTTP ${res.status})`);
  }

  return res.json();
}

export async function fetchJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Job status gagal diambil (${res.status})`);
  return res.json();
}

export function getAudioDownloadUrl(jobIdOrUrl: string): string {
  if (jobIdOrUrl.startsWith("http") || jobIdOrUrl.startsWith("/")) {
    return jobIdOrUrl;
  }
  return `/api/audio/${jobIdOrUrl}`;
}

export interface VoiceCloneLogDTO {
  id: string;
  voice_name: string;
  speaker_name: string;
  consent_checkbox: boolean;
  consent_text: string;
  sample_duration_sec: number;
  created_at: string;
}

export async function uploadVoiceCloneApi(formData: FormData) {
  const res = await fetch("/api/voice-clone/upload", {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Upload sampel gagal (${res.status})`);
  }
  return res.json();
}

export async function fetchVoiceCloneLogsApi(): Promise<VoiceCloneLogDTO[]> {
  const res = await fetch("/api/voice-clone/logs");
  if (!res.ok) return [];
  return res.json();
}

export interface VoiceCompareABResponseDTO {
  text: string;
  sample_a: {
    voice_id: string;
    name: string;
    audio_url: string;
    duration: number;
    engine_used: string;
    label: string;
  };
  sample_b: {
    voice_id: string;
    name: string;
    audio_url: string;
    duration: number;
    engine_used: string;
    label: string;
  };
}

export async function compareVoiceCloneABApi(payload: {
  voice_id: string;
  baseline_voice_id?: string;
  text: string;
}): Promise<VoiceCompareABResponseDTO> {
  const res = await fetch("/api/voice-clone/compare-ab", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Komparasi A/B gagal (${res.status})`);
  }
  return res.json();
}


export interface ProjectBlockItem {
  id: string;
  project_id: string;
  sequence: number;
  speaker_name: string;
  voice_id: string;
  emotion: string;
  text: string;
  speed: number;
  pitch: number;
  duration_sec: number;
  audio_path?: string | null;
}

export interface ProjectItem {
  id: string;
  title: string;
  description?: string;
  total_duration_sec: number;
  final_audio_url?: string | null;
  created_at: string;
  blocks: ProjectBlockItem[];
}

export async function fetchProjectsApi(): Promise<ProjectItem[]> {
  const res = await fetch("/api/projects");
  if (!res.ok) return [];
  return res.json();
}

export async function createProjectApi(title: string, description?: string): Promise<ProjectItem> {
  const res = await fetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, description }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal membuat proyek");
  }
  return res.json();
}

export async function fetchProjectDetailsApi(projectId: string): Promise<ProjectItem> {
  const res = await fetch(`/api/projects/${projectId}`);
  if (!res.ok) throw new Error("Gagal mengambil proyek");
  return res.json();
}

export async function addProjectBlockApi(
  projectId: string,
  blockData: {
    speaker_name: string;
    voice_id: string;
    emotion: string;
    text: string;
    speed: number;
    pitch: number;
  }
): Promise<ProjectBlockItem> {
  const res = await fetch(`/api/projects/${projectId}/blocks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(blockData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal menambahkan blok dialog");
  }
  return res.json();
}

export async function deleteProjectBlockApi(projectId: string, blockId: string) {
  const res = await fetch(`/api/projects/${projectId}/blocks/${blockId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Gagal menghapus blok dialog");
  return res.json();
}

export async function renderProjectDialogueApi(projectId: string): Promise<ProjectItem> {
  const res = await fetch(`/api/projects/${projectId}/render`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal merender dialog gabungan");
  }
  return res.json();
}

export interface HistoryItemDTO {
  id: string;
  job_id: string;
  project_id?: string | null;
  title: string;
  preview_text: string;
  audio_url: string;
  duration_sec: number;
  voice_name: string;
  created_at: string;
}

export async function fetchHistoryApi(limit: number = 50, offset: number = 0): Promise<HistoryItemDTO[]> {
  const res = await fetch(`/api/history?limit=${limit}&offset=${offset}`);
  if (!res.ok) return [];
  return res.json();
}

export async function deleteHistoryApi(historyId: string) {
  const res = await fetch(`/api/history/${historyId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal menghapus riwayat");
  }
  return res.json();
}

// ==========================================
// TAHAP 11: STUDIO MANAGER APIS
// ==========================================

export interface VoiceDTO {
  id: string;
  name: string;
  gender: string;
  language: string;
  category: string;
  description: string;
  engine: string;
  sample_rate: number;
  is_cloned: boolean;
  is_active: boolean;
  preview_url?: string | null;
}

export interface StylePresetDTO {
  id: string;
  name: string;
  category: string;
  voice_id?: string | null;
  speed: number;
  pitch: number;
  pause_scale: number;
  audio_effect: string;
  emotion: string;
  emotion_intensity: number;
  description: string;
  is_active: boolean;
  created_at: string;
}

export interface EmotionItemDTO {
  id: string;
  name: string;
  category: string;
  speed: number;
  pitch: number;
  pause_scale: number;
  effect: string;
  color: string;
  description: string;
  is_active: boolean;
  created_at?: string;
}

export interface LexiconItemDTO {
  id: string;
  word: string;
  replacement: string;
  voice_id?: string | null;
  is_regex: boolean;
  is_active: boolean;
  created_at: string;
}

export async function fetchPresetsApi(): Promise<StylePresetDTO[]> {
  const res = await fetch("/api/presets");
  if (!res.ok) return [];
  return res.json();
}

// 1. Studio Voices
export async function fetchStudioVoicesApi(): Promise<VoiceDTO[]> {
  const res = await fetch("/api/studio/voices");
  if (!res.ok) throw new Error("Gagal mengambil daftar suara studio");
  return res.json();
}

export async function createStudioVoiceApi(data: Partial<VoiceDTO>): Promise<VoiceDTO> {
  const res = await fetch("/api/studio/voices", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal menambahkan suara baru");
  }
  return res.json();
}

export async function updateStudioVoiceApi(id: string, data: Partial<VoiceDTO>): Promise<VoiceDTO> {
  const res = await fetch(`/api/studio/voices/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal memperbarui suara");
  }
  return res.json();
}

export async function deleteStudioVoiceApi(id: string) {
  const res = await fetch(`/api/studio/voices/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal menghapus suara");
  }
  return res.json();
}

export async function uploadStudioVoiceModelApi(formData: FormData): Promise<VoiceDTO> {
  const res = await fetch("/api/studio/voices/upload", {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload suara gagal (${res.status})`);
  }
  return res.json();
}

// 2. Studio Presets
export async function fetchStudioPresetsApi(): Promise<StylePresetDTO[]> {
  const res = await fetch("/api/studio/presets");
  if (!res.ok) throw new Error("Gagal mengambil daftar preset");
  return res.json();
}

export async function createStudioPresetApi(data: Partial<StylePresetDTO>): Promise<StylePresetDTO> {
  const res = await fetch("/api/studio/presets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal menambahkan preset baru");
  }
  return res.json();
}

export async function updateStudioPresetApi(id: string, data: Partial<StylePresetDTO>): Promise<StylePresetDTO> {
  const res = await fetch(`/api/studio/presets/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal memperbarui preset");
  }
  return res.json();
}

export async function deleteStudioPresetApi(id: string) {
  const res = await fetch(`/api/studio/presets/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal menghapus preset");
  }
  return res.json();
}

// 3. Studio Emotions
export async function fetchStudioEmotionsApi(): Promise<EmotionItemDTO[]> {
  const res = await fetch("/api/studio/emotions");
  if (!res.ok) throw new Error("Gagal mengambil katalog emosi");
  return res.json();
}

export async function createStudioEmotionApi(data: Partial<EmotionItemDTO>): Promise<EmotionItemDTO> {
  const res = await fetch("/api/studio/emotions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal menambahkan emosi");
  }
  return res.json();
}

export async function updateStudioEmotionApi(id: string, data: Partial<EmotionItemDTO>): Promise<EmotionItemDTO> {
  const res = await fetch(`/api/studio/emotions/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal memperbarui emosi");
  }
  return res.json();
}

export async function deleteStudioEmotionApi(id: string) {
  const res = await fetch(`/api/studio/emotions/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal menghapus emosi");
  }
  return res.json();
}

// 4. Studio Lexicon
export async function fetchStudioLexiconApi(): Promise<LexiconItemDTO[]> {
  const res = await fetch("/api/studio/lexicon");
  if (!res.ok) throw new Error("Gagal mengambil kamus pelafalan");
  return res.json();
}

export async function createStudioLexiconApi(data: Partial<LexiconItemDTO>): Promise<LexiconItemDTO> {
  const res = await fetch("/api/studio/lexicon", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal menambahkan kata ke kamus");
  }
  return res.json();
}

export async function updateStudioLexiconApi(id: string, data: Partial<LexiconItemDTO>): Promise<LexiconItemDTO> {
  const res = await fetch(`/api/studio/lexicon/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal memperbarui entri kamus");
  }
  return res.json();
}

export async function deleteStudioLexiconApi(id: string) {
  const res = await fetch(`/api/studio/lexicon/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Gagal menghapus entri kamus");
  }
  return res.json();
}

