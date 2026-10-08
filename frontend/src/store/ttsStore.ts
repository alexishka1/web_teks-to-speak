import { create } from "zustand";
import {
  fetchVoices,
  fetchEmotions,
  fetchPresetsApi,
  analyzeScriptEmotionsApi,
  synthesizeTTS,
  SynthesizePayload,
  EmotionPresetDTO,
  StylePresetDTO,
} from "@/lib/api";

export interface Voice {
  id: string;
  name: string;
  gender: string;
  language: string;
  category: string;
  description: string;
  engine: string;
  sample_rate: number;
  is_cloned?: boolean;
  backed_by?: string;
}

export type ActiveTab = "tts" | "library" | "clone" | "projects" | "history" | "playground" | "studio";

export interface SentenceTiming {
  text: string;
  startTime: number;
  endTime: number;
  emotion?: string;
  color?: string;
}

export function splitSentencesClient(
  text: string,
  totalDuration: number = 0,
  sentenceEmotions: Record<number, string> = {},
  emotionsMap: Record<string, EmotionPresetDTO> = {}
): SentenceTiming[] {
  if (!text.trim()) return [];
  const raw = text.split(/(?<=[.!?])\s+|\n\n+/).map((s) => s.trim()).filter((s) => s.length > 0);
  if (raw.length === 0) return [];

  const wordCounts = raw.map((s) => Math.max(1, s.split(/\s+/).length));
  const totalWords = wordCounts.reduce((acc, curr) => acc + curr, 0);

  let currentStart = 0;
  return raw.map((sentText, idx) => {
    const fraction = wordCounts[idx] / totalWords;
    const sentenceDur = totalDuration > 0 ? totalDuration * fraction : wordCounts[idx] * 0.35;
    const start = currentStart;
    const end = currentStart + sentenceDur;
    currentStart = end;

    const emoId = sentenceEmotions[idx] || "neutral";
    const emoObj = emotionsMap[emoId];
    const color = emoObj?.color || "#737373";

    return {
      text: sentText,
      startTime: start,
      endTime: end,
      emotion: emoId,
      color,
    };
  });
}

interface TTSState {
  // Navigation
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;

  // Editor State
  text: string;
  setText: (text: string) => void;
  sentences: SentenceTiming[];
  activeSentenceIndex: number;
  setActiveSentenceIndex: (index: number) => void;

  // Synthesis Parameters
  selectedEngine: string;
  setSelectedEngine: (engine: string) => void;
  selectedVoiceId: string;
  setSelectedVoiceId: (voiceId: string) => void;
  speed: number;
  setSpeed: (speed: number) => void;
  pitch: number;
  setPitch: (pitch: number) => void;
  pauseScale: number;
  setPauseScale: (pauseScale: number) => void;
  audioEffect: string;
  setAudioEffect: (effect: string) => void;

  // Style Presets (Tahap 11)
  presetsCatalog: StylePresetDTO[];
  selectedPresetId: string | null;
  fetchPresetsList: () => Promise<void>;
  applyPreset: (presetId: string) => void;

  // Emotion System (Tahap 6)
  emotionsCatalog: EmotionPresetDTO[];
  fetchEmotionsList: () => Promise<void>;
  selectedEmotion: string;
  setSelectedEmotion: (emotion: string) => void;
  emotionIntensity: number; // 0 - 100
  setEmotionIntensity: (intensity: number) => void;
  sentenceEmotions: Record<number, string>;
  setSentenceEmotion: (sentenceIndex: number, emotionId: string) => void;
  isAutoEmotionMode: boolean;
  setIsAutoEmotionMode: (isAuto: boolean) => void;
  runAutoEmotionAnalysis: () => Promise<void>;

  // Voice Clone Ethics
  isClonedVoice: boolean;
  setIsClonedVoice: (isCloned: boolean) => void;
  cloneConsentGiven: boolean;
  setCloneConsentGiven: (consent: boolean) => void;

  // Available Voices
  voices: Voice[];
  isLoadingVoices: boolean;
  fetchVoicesList: () => Promise<void>;

  // Generation State & Progress
  isGenerating: boolean;
  generationProgress: number; // 0 - 100
  generationStep: string;
  generationMessage: string;
  generationError: string | null;
  currentJobId: string | null;
  generateSpeech: () => Promise<void>;

  // Playback State
  audioUrl: string | null;
  audioDuration: number;
  isPlaying: boolean;
  currentTime: number;
  playbackSpeed: number;
  setIsPlaying: (isPlaying: boolean) => void;
  setCurrentTime: (time: number) => void;
  setPlaybackSpeed: (speed: number) => void;
  setAudioResult: (url: string | null, duration?: number, jobId?: string) => void;
  seekToSentence: (sentenceIndex: number) => void;

  // 3-Second Voice Preview State
  previewingVoiceId: string | null;
  previewAudioUrl: string | null;
  isPlayingPreview: boolean;
  playVoicePreview: (voiceId: string) => Promise<void>;
  stopVoicePreview: () => void;
}

const DEFAULT_SAMPLE_TEXT = `Stop scroll dulu! Tahu nggak rahasia terbesar kreator konten dengan jutaan penonton?

Kuncinya ada pada modulasi emosi vokal di 3 detik pertama. Jangan pernah menyapa dengan suara datar dan membosankan. Gunakan intonasi antusias yang memicu rasa penasaran alami audiens!

Sshh... bisik-bisik, ini rahasia yang jarang dibocorkan: dengan mengatur tinggi nada, ritme jeda, dan efek reverb hangat, narasi video Anda terdengar seperti siaran studio profesional.`;

export const useTTSStore = create<TTSState>((set, get) => ({
  activeTab: "tts",
  setActiveTab: (tab) => set({ activeTab: tab }),

  text: DEFAULT_SAMPLE_TEXT,
  setText: (text) => {
    const { audioDuration, sentenceEmotions, emotionsCatalog } = get();
    const emotionsMap: Record<string, EmotionPresetDTO> = {};
    emotionsCatalog.forEach((e) => (emotionsMap[e.id] = e));
    const timings = splitSentencesClient(text, audioDuration, sentenceEmotions, emotionsMap);
    set({ text, sentences: timings });
  },
  sentences: splitSentencesClient(DEFAULT_SAMPLE_TEXT, 0),
  activeSentenceIndex: -1,
  setActiveSentenceIndex: (activeSentenceIndex) => set({ activeSentenceIndex }),

  selectedEngine: "piper",
  setSelectedEngine: (selectedEngine) => set({ selectedEngine }),
  selectedVoiceId: "id_ID-news_tts-medium",
  setSelectedVoiceId: (selectedVoiceId) => set({ selectedVoiceId }),
  speed: 1.0,
  setSpeed: (speed) => set({ speed }),
  pitch: 0.0,
  setPitch: (pitch) => set({ pitch }),
  pauseScale: 1.0,
  setPauseScale: (pauseScale) => set({ pauseScale }),
  audioEffect: "none",
  setAudioEffect: (audioEffect) => set({ audioEffect }),

  // Style Presets (Tahap 11)
  presetsCatalog: [],
  selectedPresetId: null,
  fetchPresetsList: async () => {
    try {
      const presets = await fetchPresetsApi();
      if (Array.isArray(presets)) {
        set({ presetsCatalog: presets });
      }
    } catch (e) {
      console.warn("Gagal mengambil daftar preset:", e);
    }
  },
  applyPreset: (presetId: string) => {
    const { presetsCatalog } = get();
    const found = presetsCatalog.find((p) => p.id === presetId);
    if (!found) return;

    set({
      selectedPresetId: found.id,
      speed: found.speed,
      pitch: found.pitch,
      pauseScale: found.pause_scale,
      audioEffect: found.audio_effect || "none",
      selectedEmotion: found.emotion || "neutral",
      emotionIntensity: found.emotion_intensity ?? 100,
      ...(found.voice_id ? { selectedVoiceId: found.voice_id } : {}),
    });
  },

  // Emotion System
  emotionsCatalog: [],
  fetchEmotionsList: async () => {
    try {
      const emos = await fetchEmotions();
      if (Array.isArray(emos) && emos.length > 0) {
        set({ emotionsCatalog: emos });
        const { text, audioDuration, sentenceEmotions } = get();
        const emotionsMap: Record<string, EmotionPresetDTO> = {};
        emos.forEach((e) => (emotionsMap[e.id] = e));
        set({ sentences: splitSentencesClient(text, audioDuration, sentenceEmotions, emotionsMap) });
      }
    } catch (e) {
      console.warn("Gagal mengambil katalog emosi:", e);
    }
  },
  selectedEmotion: "neutral",
  setSelectedEmotion: (selectedEmotion) => set({ selectedEmotion }),
  emotionIntensity: 100,
  setEmotionIntensity: (emotionIntensity) => set({ emotionIntensity }),
  sentenceEmotions: {},
  setSentenceEmotion: (sentenceIndex, emotionId) => {
    const currentMap = { ...get().sentenceEmotions, [sentenceIndex]: emotionId };
    const { text, audioDuration, emotionsCatalog } = get();
    const emotionsMap: Record<string, EmotionPresetDTO> = {};
    emotionsCatalog.forEach((e) => (emotionsMap[e.id] = e));
    set({
      sentenceEmotions: currentMap,
      sentences: splitSentencesClient(text, audioDuration, currentMap, emotionsMap),
    });
  },
  isAutoEmotionMode: false,
  setIsAutoEmotionMode: (isAutoEmotionMode) => set({ isAutoEmotionMode }),
  runAutoEmotionAnalysis: async () => {
    try {
      const { text, emotionsCatalog, audioDuration } = get();
      const res = await analyzeScriptEmotionsApi(text);
      if (res && res.sentences) {
        const newMap: Record<number, string> = {};
        res.sentences.forEach((s: any) => {
          newMap[s.sentence_index] = s.emotion_id;
        });
        const emotionsMap: Record<string, EmotionPresetDTO> = {};
        emotionsCatalog.forEach((e) => (emotionsMap[e.id] = e));
        set({
          sentenceEmotions: newMap,
          sentences: splitSentencesClient(text, audioDuration, newMap, emotionsMap),
          isAutoEmotionMode: true,
        });
      }
    } catch (e) {
      console.error("Gagal menjalankan analisis auto emotion:", e);
    }
  },

  isClonedVoice: false,
  setIsClonedVoice: (isClonedVoice) => set({ isClonedVoice }),
  cloneConsentGiven: false,
  setCloneConsentGiven: (cloneConsentGiven) => set({ cloneConsentGiven }),

  voices: [],
  isLoadingVoices: false,
  fetchVoicesList: async () => {
    try {
      set({ isLoadingVoices: true });
      const voicesList = await fetchVoices();
      if (Array.isArray(voicesList) && voicesList.length > 0) {
        set({
          voices: voicesList,
          isLoadingVoices: false,
          selectedVoiceId: get().selectedVoiceId || voicesList[0].id,
        });
      } else {
        set({ isLoadingVoices: false });
      }
    } catch (e) {
      console.error("Gagal mengambil suara:", e);
      set({ isLoadingVoices: false });
    }
  },

  isGenerating: false,
  generationProgress: 0,
  generationStep: "idle",
  generationMessage: "",
  generationError: null,
  currentJobId: null,

  generateSpeech: async () => {
    const {
      text,
      selectedVoiceId,
      speed,
      pitch,
      pauseScale,
      audioEffect,
      selectedEmotion,
      emotionIntensity,
      sentenceEmotions,
      isAutoEmotionMode,
      sentences,
      isClonedVoice,
      cloneConsentGiven,
    } = get();

    if (!text.trim()) {
      set({ generationError: "Silakan masukkan teks naskah terlebih dahulu." });
      return;
    }

    if (isClonedVoice && !cloneConsentGiven) {
      set({
        generationError:
          "Persetujuan pemilik suara wajib dicentang untuk model klon suara.",
      });
      return;
    }

    set({
      isGenerating: true,
      generationProgress: 10,
      generationStep: "normalizing",
      generationMessage: "Menormalkan teks bahasa Indonesia...",
      generationError: null,
      isPlaying: false,
      activeSentenceIndex: -1,
    });

    try {
      // Susun list emosi per kalimat jika ada manual / auto
      const orderedSentenceEmos: string[] = [];
      sentences.forEach((_, idx) => {
        const emo = sentenceEmotions[idx] || (isAutoEmotionMode ? "auto" : selectedEmotion);
        orderedSentenceEmos.push(emo);
      });

      const payload: SynthesizePayload = {
        text,
        voice_id: selectedVoiceId,
        speed,
        pitch,
        pause_scale: pauseScale,
        audio_effect: audioEffect,
        emotion: isAutoEmotionMode ? "auto" : selectedEmotion,
        emotion_intensity: emotionIntensity,
        sentence_emotions: orderedSentenceEmos.length > 0 ? orderedSentenceEmos : undefined,
        is_cloned_voice: isClonedVoice,
        voice_clone_consent: cloneConsentGiven,
      };

      const progressTimer = setInterval(() => {
        const cur = get().generationProgress;
        if (cur < 85) {
          const nextProg = cur + Math.floor(Math.random() * 12) + 5;
          let step = "synthesizing";
          let msg = "Menyintesis modulasi emosi vokal...";
          if (nextProg > 80) {
            step = "crossfading";
            msg = "Equal-power crossfade & mastering FFmpeg...";
          }
          set({
            generationProgress: Math.min(85, nextProg),
            generationStep: step,
            generationMessage: msg,
          });
        }
      }, 350);

      const result = await synthesizeTTS(payload);
      clearInterval(progressTimer);

      const audioUrl = result.audio_url;
      const duration = result.duration_sec || 0;
      const emotionsMap: Record<string, EmotionPresetDTO> = {};
      get().emotionsCatalog.forEach((e) => (emotionsMap[e.id] = e));
      const sentenceTimings = splitSentencesClient(text, duration, sentenceEmotions, emotionsMap);

      set({
        isGenerating: false,
        generationProgress: 100,
        generationStep: "completed",
        generationMessage: "Audio berhasil disintesis!",
        currentJobId: result.job_id,
        audioUrl,
        audioDuration: duration,
        sentences: sentenceTimings,
        generationError: null,
      });
    } catch (err: any) {
      set({
        isGenerating: false,
        generationProgress: 0,
        generationStep: "failed",
        generationMessage: "",
        generationError:
          err.message || "Terjadi kesalahan saat memproses audio di backend.",
      });
    }
  },

  audioUrl: null,
  audioDuration: 0,
  isPlaying: false,
  currentTime: 0,
  playbackSpeed: 1.0,

  setIsPlaying: (isPlaying) => set({ isPlaying }),
  setCurrentTime: (currentTime) => {
    const { sentences } = get();
    let foundIdx = -1;
    for (let i = 0; i < sentences.length; i++) {
      if (currentTime >= sentences[i].startTime && currentTime < sentences[i].endTime) {
        foundIdx = i;
        break;
      }
    }
    if (foundIdx === -1 && sentences.length > 0 && currentTime >= sentences[sentences.length - 1].startTime) {
      foundIdx = sentences.length - 1;
    }
    set({ currentTime, activeSentenceIndex: foundIdx });
  },
  setPlaybackSpeed: (playbackSpeed) => set({ playbackSpeed }),

  setAudioResult: (url, duration = 0, jobId) => {
    const { text, sentenceEmotions, emotionsCatalog } = get();
    const emotionsMap: Record<string, EmotionPresetDTO> = {};
    emotionsCatalog.forEach((e) => (emotionsMap[e.id] = e));
    const sentenceTimings = splitSentencesClient(text, duration, sentenceEmotions, emotionsMap);
    set({
      audioUrl: url,
      audioDuration: duration,
      currentJobId: jobId || null,
      sentences: sentenceTimings,
      generationError: null,
    });
  },

  seekToSentence: (sentenceIndex: number) => {
    const { sentences } = get();
    if (sentenceIndex >= 0 && sentenceIndex < sentences.length) {
      const targetTime = sentences[sentenceIndex].startTime;
      set({ currentTime: targetTime, activeSentenceIndex: sentenceIndex });
    }
  },

  // 3-Second Voice Preview
  previewingVoiceId: null,
  previewAudioUrl: null,
  isPlayingPreview: false,

  playVoicePreview: async (voiceId: string) => {
    const current = get().previewingVoiceId;
    if (current === voiceId && get().isPlayingPreview) {
      get().stopVoicePreview();
      return;
    }

    set({ previewingVoiceId: voiceId, isPlayingPreview: true });

    try {
      const previewText = "Halo! Ini adalah contoh pratinjau suara tiga detik dari TaSTP Studio.";
      const res = await synthesizeTTS({
        text: previewText,
        voice_id: voiceId,
        speed: 1.0,
        pitch: 0.0,
      });

      set({ previewAudioUrl: res.audio_url });
    } catch (e) {
      console.error("Gagal memuat pratinjau suara:", e);
      set({ isPlayingPreview: false, previewingVoiceId: null });
    }
  },

  stopVoicePreview: () => {
    set({ isPlayingPreview: false, previewingVoiceId: null, previewAudioUrl: null });
  },
}));
