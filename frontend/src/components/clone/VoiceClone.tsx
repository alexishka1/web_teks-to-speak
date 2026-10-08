"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Sparkles,
  UploadCloud,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Clock,
  UserCheck,
  FileAudio,
  Loader2,
  Play,
  Pause,
  Mic,
  Square,
  RotateCcw,
  Volume2,
  Copy,
  Check,
  Layers,
  Info,
} from "lucide-react";
import {
  uploadVoiceCloneApi,
  fetchVoiceCloneLogsApi,
  compareVoiceCloneABApi,
  VoiceCloneLogDTO,
  VoiceCompareABResponseDTO,
} from "@/lib/api";
import { useTTSStore } from "@/store/ttsStore";

interface ScriptSample {
  id: string;
  title: string;
  description: string;
  content: string;
}

const READING_SCRIPTS: ScriptSample[] = [
  {
    id: "creator",
    title: "Kreator Konten & Edukasi",
    description: "Kombinasi kalimat tanya, kalimat seru, dan angka untuk vokal ekspresif.",
    content:
      "Apakah kamu siap membawa konten video dan podcast milikmu ke tingkat profesional? Luar biasa! " +
      "Hari ini, tanggal 7 Oktober 2026, tercatat lebih dari 15.000 kreator telah menggunakan teknologi suara cerdas ini. " +
      "Cobalah dengarkan artikulasi dan ritme napas yang begitu alami, tanpa jeda yang kaku ataupun terdengar robotik.",
  },
  {
    id: "podcast",
    title: "Podcaster & Percakapan Santai",
    description: "Gaya bicara akrab dengan variasi panjang kalimat dan penekanan kata.",
    content:
      "Halo semuanya, senang sekali bisa menyapa kalian kembali di sini! Pernahkah kamu merasa lelah saat harus mengulang rekaman berkali-kali? " +
      "Tenang saja, kini cukup sediakan sampel vokal terbaikmu selama 20 detik, dan biarkan sistem menghasilkan narasi yang kaya emosi dan berkarakter unik.",
  },
  {
    id: "documentary",
    title: "Narator Dokumenter & Berita",
    description: "Artikulasi formal, tempo teratur, dan intonasi berwibawa.",
    content:
      "Di balik riuhnya perkembangan teknologi informasi, tercipta sebuah revolusi dalam sintesis suara manusia. " +
      "Dari pelosok nusantara hingga panggung internasional, suara kita menjadi jendela bagi cerita-cerita inspiratif yang belum terungkap.",
  },
];

export function VoiceClone() {
  const { fetchVoicesList, voices } = useTTSStore();

  // Mode: Record vs Upload
  const [inputMode, setInputMode] = useState<"record" | "upload">("record");

  // Metadata form
  const [voiceName, setVoiceName] = useState("");
  const [speakerName, setSpeakerName] = useState("");
  const [gender, setGender] = useState<"male" | "female" | "custom">("custom");
  const [transcript, setTranscript] = useState("");
  const [consentChecked, setConsentChecked] = useState(false);

  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileDuration, setFileDuration] = useState<number | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const audioPreviewRef = useRef<HTMLAudioElement | null>(null);
  const [isPlayingPreview, setIsPlayingPreview] = useState(false);

  // Perekam Browser (MediaRecorder)
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Audio VU Meter Analyser
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const [volumeLevel, setVolumeLevel] = useState<number>(0);
  const [clippingAlert, setClippingAlert] = useState(false);

  // Status & Submit
  const [isUploading, setIsUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{
    type: "success" | "error" | "info";
    text: string;
  } | null>(null);
  const [logs, setLogs] = useState<VoiceCloneLogDTO[]>([]);
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);

  // Naskah panduan
  const [selectedScriptId, setSelectedScriptId] = useState<string>("creator");
  const [copiedScript, setCopiedScript] = useState(false);

  // Pengujian Komparasi A/B
  const [compareVoiceId, setCompareVoiceId] = useState<string>("");
  const [compareText, setCompareText] = useState<string>(
    "Halo, ini adalah pengujian perbandingan suara hasil kloning saya melawan suara default Piper."
  );
  const [isComparing, setIsComparing] = useState(false);
  const [compareResult, setCompareResult] = useState<VoiceCompareABResponseDTO | null>(null);
  const compareAudioARef = useRef<HTMLAudioElement | null>(null);
  const compareAudioBRef = useRef<HTMLAudioElement | null>(null);

  const loadLogs = React.useCallback(async () => {
    setIsLoadingLogs(true);
    try {
      const data = await fetchVoiceCloneLogsApi();
      setLogs(data);
      if (data.length > 0) {
        setCompareVoiceId((prev) => prev || data[0].id);
      }
    } catch {
      // ignore
    } finally {
      setIsLoadingLogs(false);
    }
  }, []);

  useEffect(() => {
    loadLogs();
    return () => {
      stopMicrophoneStream();
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [loadLogs]);


  // --- AUDIO ANALYSER & RECORDING ---
  const startRecording = async () => {
    try {
      setStatusMessage(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 24000,
          echoCancellation: false,
          noiseSuppression: false,
        },
      });

      // Siapkan AudioContext untuk VU Meter
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const checkVolume = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        let peak = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
          if (dataArray[i] > peak) peak = dataArray[i];
        }
        const avg = sum / bufferLength;
        const normalized = Math.min(100, Math.round((avg / 128) * 100));
        setVolumeLevel(normalized);

        // Deteksi clipping jika peak menyentuh ambang atas
        if (peak >= 250) {
          setClippingAlert(true);
        } else {
          setClippingAlert(false);
        }

        animFrameRef.current = requestAnimationFrame(checkVolume);
      };
      checkVolume();

      // Inisialisasi MediaRecorder
      const options = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? { mimeType: "audio/webm;codecs=opus" }
        : undefined;

      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const mimeType = mediaRecorder.mimeType || "audio/webm";
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        setRecordedBlob(blob);
        const url = URL.createObjectURL(blob);
        setPreviewUrl(url);

        const tempAudio = new Audio(url);
        tempAudio.onloadedmetadata = () => {
          setFileDuration(tempAudio.duration);
        };

        stopMicrophoneStream();
      };

      mediaRecorder.start(250);
      setIsRecording(true);
      setIsPaused(false);
      setRecordingSeconds(0);

      timerIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: `Tidak dapat mengakses mikrofon: ${err.message || "Izin akses ditolak."}`,
      });
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      if (!isPaused) {
        mediaRecorderRef.current.pause();
        setIsPaused(true);
        if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      } else {
        mediaRecorderRef.current.resume();
        setIsPaused(false);
        timerIntervalRef.current = setInterval(() => {
          setRecordingSeconds((prev) => prev + 1);
        }, 1000);
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }
    }
  };

  const resetRecording = () => {
    stopRecording();
    stopMicrophoneStream();
    setRecordedBlob(null);
    setPreviewUrl(null);
    setFileDuration(null);
    setRecordingSeconds(0);
    setVolumeLevel(0);
    setClippingAlert(false);
  };

  const stopMicrophoneStream = () => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.stream) {
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }
    setVolumeLevel(0);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setStatusMessage(null);

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    const tempAudio = new Audio(url);
    tempAudio.onloadedmetadata = () => {
      setFileDuration(tempAudio.duration);
    };
  };

  // --- SUBMIT CLONE ---
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    let audioToUpload: File | Blob | null = null;
    let fileName = "recording.webm";

    if (inputMode === "record") {
      if (!recordedBlob) {
        setStatusMessage({
          type: "error",
          text: "Silakan rekam suara Anda terlebih dahulu (minimal 10 detik, ideal 15-30 detik).",
        });
        return;
      }
      audioToUpload = recordedBlob;
    } else {
      if (!selectedFile) {
        setStatusMessage({
          type: "error",
          text: "Pilih file sampel audio terlebih dahulu (WAV/MP3/M4A).",
        });
        return;
      }
      audioToUpload = selectedFile;
      fileName = selectedFile.name;
    }

    if (!consentChecked) {
      setStatusMessage({
        type: "error",
        text: "Persetujuan pemilik suara wajib dicentang demi etika dan regulasi AI.",
      });
      return;
    }

    const durationToCheck = inputMode === "record" ? recordingSeconds : (fileDuration || 0);
    if (durationToCheck < 9.5) {
      setStatusMessage({
        type: "error",
        text: `Durasi sampel adalah ${durationToCheck.toFixed(1)} detik. Sampel wajib minimal 10 detik agar karakteristik vokal terbentuk akurat.`,
      });
      return;
    }
    if (durationToCheck > 35.0) {
      setStatusMessage({
        type: "error",
        text: `Durasi sampel adalah ${durationToCheck.toFixed(1)} detik. Maksimal durasi sampel vokal adalah 30 detik.`,
      });
      return;
    }

    setIsUploading(true);
    setStatusMessage({
      type: "info",
      text: "Memproses standarisasi 24 kHz, pemangkasan hening, dan normalisasi volume...",
    });

    const formData = new FormData();
    formData.append("file", audioToUpload, fileName);
    formData.append("voice_name", voiceName);
    formData.append("speaker_name", speakerName);
    formData.append("gender", gender);
    if (transcript.trim()) {
      formData.append("transcript", transcript.trim());
    }
    formData.append("consent_checkbox", "true");
    formData.append(
      "consent_text",
      `Saya (${speakerName} / pengguna berizin sah) memberikan izin penuh untuk pengklonan vokal di TaSTP Studio secara legal dan beretika.`
    );

    try {
      const res = await uploadVoiceCloneApi(formData);
      setStatusMessage({
        type: "success",
        text: res.message || "Klon vokal baru berhasil dibuat dan consent log telah dicatat!",
      });
      setCompareVoiceId(res.id);
      setVoiceName("");
      setSpeakerName("");
      setTranscript("");
      setConsentChecked(false);
      resetRecording();
      setSelectedFile(null);
      await fetchVoicesList();
      await loadLogs();
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || "Gagal memproses kloning suara.",
      });
    } finally {
      setIsUploading(false);
    }
  };

  // --- KOMPARASI A/B ---
  const handleCompareAB = async () => {
    if (!compareVoiceId) {
      setStatusMessage({
        type: "error",
        text: "Pilih suara klon dari daftar terlebih dahulu untuk melakukan komparasi A/B.",
      });
      return;
    }

    setIsComparing(true);
    setStatusMessage(null);
    setCompareResult(null);

    try {
      const result = await compareVoiceCloneABApi({
        voice_id: compareVoiceId,
        text: compareText,
      });
      setCompareResult(result);
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || "Gagal menjalankan sintesis uji A/B.",
      });
    } finally {
      setIsComparing(false);
    }
  };

  const copyScriptText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedScript(true);
    setTranscript(text);
    setTimeout(() => setCopiedScript(false), 2000);
  };

  const currentDuration = inputMode === "record" ? recordingSeconds : (fileDuration || 0);
  const isDurationValid = currentDuration >= 9.8 && currentDuration <= 30.5;
  const isDurationIdeal = currentDuration >= 14.5 && currentDuration <= 30.0;

  const currentScript =
    READING_SCRIPTS.find((s) => s.id === selectedScriptId) || READING_SCRIPTS[0];

  return (
    <div className="flex-1 h-screen overflow-y-auto p-4 md:p-8 bg-background max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="border-b border-border pb-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2.5 text-fg mb-1">
            <Sparkles className="w-5 h-5" />
            <h1 className="text-xl font-bold text-fg">Suara Saya (Voice Clone Studio)</h1>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-panel border border-border border border-border text-fg font-semibold uppercase">
              24 kHz HD
            </span>
          </div>
          <p className="text-xs text-muted leading-relaxed">
            Kloning karakter vokal Anda dalam 15–30 detik. Otomatis distandardisasi ke 24 kHz mono,
            dipangkas hening, dan dilabeli metadata &ldquo;Dibuat dengan AI&rdquo;.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-muted font-medium flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-panel border border-border">
            <ShieldCheck className="w-4 h-4 text-fg font-semibold" />
            Consent Log Aktif
          </span>
        </div>
      </div>

      {/* Grid Utama: Panel Kiri (Input & Naskah) & Panel Kanan (A/B Test & Riwayat) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Kolom Kiri: Perekaman / Unggah & Form (7 Kolom) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Card Panduan Naskah Vokal */}
          <div className="card p-4 space-y-3 bg-panel/50 border-border">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <h2 className="text-xs font-semibold text-fg flex items-center gap-1.5">
                <FileAudio className="w-4 h-4 text-fg" />
                Naskah Panduan Bacaan Ekspresif
              </h2>
              <button
                type="button"
                onClick={() => copyScriptText(currentScript.content)}
                className="text-[11px] text-fg hover:text-fg/80 flex items-center gap-1 font-medium transition-colors"
                title="Salin dan gunakan sebagai transkrip"
              >
                {copiedScript ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-fg font-semibold" />
                    Tersalin ke Transkrip!
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    Gunakan Teks Ini
                  </>
                )}
              </button>
            </div>

            {/* Selector Kategori Naskah */}
            <div className="flex flex-wrap gap-1.5">
              {READING_SCRIPTS.map((script) => (
                <button
                  key={script.id}
                  type="button"
                  onClick={() => setSelectedScriptId(script.id)}
                  className={`text-[11px] px-2.5 py-1 rounded-md font-medium transition-all ${
                    selectedScriptId === script.id
                      ? "bg-panel border border-border text-fg border border-border"
                      : "bg-surface text-muted hover:text-fg border border-border/60"
                  }`}
                >
                  {script.title}
                </button>
              ))}
            </div>

            <p className="text-[11px] text-muted italic">{currentScript.description}</p>

            <div className="p-3 rounded-lg bg-surface border border-border/80 text-xs text-fg leading-relaxed font-sans select-text">
              {currentScript.content}
            </div>
          </div>

          {/* Form Perekaman / Upload */}
          <form onSubmit={handleSubmit} className="card p-5 space-y-4">
            {/* Tab Pilihan: Rekam Mic vs Upload File */}
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h2 className="text-sm font-semibold text-fg flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-fg" />
                Sampel Rekaman Vokal
              </h2>

              <div className="flex items-center gap-1 bg-surface p-1 rounded-lg border border-border">
                <button
                  type="button"
                  id="tab-mode-record"
                  onClick={() => {
                    setInputMode("record");
                    setSelectedFile(null);
                  }}
                  className={`text-xs px-3 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
                    inputMode === "record"
                      ? "bg-primary text-primary-fg text-primary-fg font-semibold"
                      : "text-muted hover:text-fg"
                  }`}
                >
                  <Mic className="w-3.5 h-3.5" />
                  Rekam Browser
                </button>
                <button
                  type="button"
                  id="tab-mode-upload"
                  onClick={() => {
                    setInputMode("upload");
                    resetRecording();
                  }}
                  className={`text-xs px-3 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
                    inputMode === "upload"
                      ? "bg-primary text-primary-fg text-primary-fg font-semibold"
                      : "text-muted hover:text-fg"
                  }`}
                >
                  <UploadCloud className="w-3.5 h-3.5" />
                  Unggah File
                </button>
              </div>
            </div>

            {/* AREA 1: RECORDING LANGSUNG DARI BROWSER */}
            {inputMode === "record" ? (
              <div className="p-4 rounded-xl bg-surface border border-border space-y-4">
                <div className="flex flex-col items-center justify-center text-center space-y-3 py-2">
                  {/* Timer Display */}
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        isRecording && !isPaused
                          ? "bg-red-500 animate-ping"
                          : isPaused
                          ? "bg-fg"
                          : "bg-muted/40"
                      }`}
                    />
                    <span className="font-mono text-2xl font-bold text-fg tracking-wider">
                      {Math.floor(recordingSeconds / 60)
                        .toString()
                        .padStart(2, "0")}
                      :{(recordingSeconds % 60).toString().padStart(2, "0")}
                    </span>
                    <span className="text-xs text-muted">(Target: 15–30s)</span>
                  </div>

                  {/* VU Level Meter Bar & Clipping Alert */}
                  {isRecording && (
                    <div className="w-full max-w-md space-y-1">
                      <div className="flex items-center justify-between text-[10px] text-muted">
                        <span>Level Input Mikrofon</span>
                        {clippingAlert ? (
                          <span className="text-fg font-semibold font-semibold">⚠️ Clipping terdeteksi! Mundurkan mic.</span>
                        ) : (
                          <span>Optimal: 40–80%</span>
                        )}
                      </div>
                      <div className="h-2 w-full bg-panel rounded-full overflow-hidden border border-border">
                        <div
                          className={`h-full transition-all duration-75 ${
                            clippingAlert
                              ? "bg-red-500"
                              : volumeLevel > 40
                              ? "bg-emerald-400"
                              : "bg-fg"
                          }`}
                          style={{ width: `${volumeLevel}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Tombol Kontrol Perekaman */}
                  <div className="flex items-center gap-2.5 pt-2">
                    {!isRecording ? (
                      <button
                        type="button"
                        id="btn-start-record"
                        onClick={startRecording}
                        className="py-2.5 px-5 rounded-lg bg-red-600 hover:bg-red-700 text-fg font-semibold text-xs flex items-center gap-2 shadow-lg shadow-red-600/20 transition-all cursor-pointer"
                      >
                        <Mic className="w-4 h-4" />
                        Mulai Rekam Suara
                      </button>
                    ) : (
                      <>
                        <button
                          type="button"
                          onClick={pauseRecording}
                          className="py-2 px-3 rounded-lg bg-panel hover:bg-panel/80 text-fg font-medium text-xs border border-border flex items-center gap-1.5 transition-colors"
                        >
                          {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
                          {isPaused ? "Lanjutkan" : "Jeda"}
                        </button>
                        <button
                          type="button"
                          id="btn-stop-record"
                          onClick={stopRecording}
                          className="py-2 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-fg font-semibold text-xs flex items-center gap-1.5 shadow-md transition-colors cursor-pointer"
                        >
                          <Square className="w-3.5 h-3.5" />
                          Selesai Rekam
                        </button>
                      </>
                    )}

                    {recordedBlob && !isRecording && (
                      <button
                        type="button"
                        onClick={resetRecording}
                        className="py-2 px-3 rounded-lg bg-surface hover:bg-panel text-muted hover:text-fg text-xs border border-border flex items-center gap-1 transition-colors"
                        title="Rekam ulang"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Ulangi
                      </button>
                    )}
                  </div>
                </div>

                {/* Indikator Status Kualitas Durasi */}
                {recordingSeconds > 0 && !isRecording && (
                  <div className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-panel border border-border">
                    <span className="text-muted">
                      Durasi Terambil: <strong className="text-fg">{recordingSeconds}s</strong>
                    </span>
                    {isDurationIdeal ? (
                      <span className="text-fg font-semibold text-[11px] font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Sangat Ideal (15–30s)
                      </span>
                    ) : isDurationValid ? (
                      <span className="text-fg font-semibold text-[11px] font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Memenuhi Syarat Minimal (&gt; 10s)
                      </span>
                    ) : (
                      <span className="text-fg font-semibold text-[11px] font-semibold flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" /> Terlalu Pendek (&lt; 10s)
                      </span>
                    )}
                  </div>
                )}
              </div>
            ) : (
              /* AREA 2: UPLOAD FILE AUDIO */
              <div>
                <div className="border-2 border-dashed border-border hover:border-border rounded-xl p-5 text-center transition-colors bg-surface">
                  <input
                    type="file"
                    accept="audio/*,.wav,.mp3,.m4a,.ogg,.webm"
                    onChange={handleFileChange}
                    className="hidden"
                    id="sample-file-input"
                  />
                  <label
                    htmlFor="sample-file-input"
                    className="cursor-pointer flex flex-col items-center justify-center gap-2"
                  >
                    <UploadCloud className="w-8 h-8 text-muted hover:text-fg transition-colors" />
                    <div className="text-xs font-medium text-fg">
                      {selectedFile ? selectedFile.name : "Pilih File Sampel Audio (WAV / MP3 / M4A)"}
                    </div>
                    <p className="text-[11px] text-muted">
                      Durasi ideal 15–30 detik tanpa musik latar (maks. 25 MB).
                    </p>
                  </label>
                </div>

                {fileDuration !== null && (
                  <div className="mt-2.5 flex items-center justify-between text-xs p-2.5 rounded-lg bg-panel border border-border">
                    <span className="text-muted">
                      Durasi: <strong className="text-fg">{fileDuration.toFixed(1)}s</strong>
                    </span>
                    {isDurationIdeal ? (
                      <span className="text-fg font-semibold text-[11px] font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Durasi Ideal
                      </span>
                    ) : isDurationValid ? (
                      <span className="text-fg font-semibold text-[11px] font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Memenuhi Syarat
                      </span>
                    ) : (
                      <span className="text-fg font-semibold text-[11px] font-semibold flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" /> Durasi Tidak Valid (10–30s)
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Audio Preview Bar */}
            {previewUrl && (
              <div className="p-3 rounded-lg bg-panel border border-border flex items-center gap-3">
                <Volume2 className="w-4 h-4 text-fg shrink-0" />
                <audio
                  ref={audioPreviewRef}
                  src={previewUrl}
                  controls
                  className="w-full h-8"
                  onPlay={() => setIsPlayingPreview(true)}
                  onPause={() => setIsPlayingPreview(false)}
                />
              </div>
            )}

            {/* Input Metadata Karakter & Pemilik Suara */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-2">
              <div>
                <label className="text-xs font-medium text-fg block mb-1">
                  Nama Karakter Suara <span className="text-fg font-semibold">*</span>
                </label>
                <input
                  type="text"
                  required
                  id="input-voice-name"
                  placeholder="Mis. Clarissa - Podcaster Kasual"
                  value={voiceName}
                  onChange={(e) => setVoiceName(e.target.value)}
                  className="input-base text-xs py-2 w-full"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-fg block mb-1">
                  Nama Pemilik Asli Suara <span className="text-fg font-semibold">*</span>
                </label>
                <input
                  type="text"
                  required
                  id="input-speaker-name"
                  placeholder="Mis. Clarissa Putri"
                  value={speakerName}
                  onChange={(e) => setSpeakerName(e.target.value)}
                  className="input-base text-xs py-2 w-full"
                />
              </div>
            </div>

            {/* Gender & Transkrip Opsional */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
              <div>
                <label className="text-xs font-medium text-fg block mb-1">Gender Vokal</label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value as any)}
                  className="input-base text-xs py-2 w-full"
                >
                  <option value="female">Wanita</option>
                  <option value="male">Pria</option>
                  <option value="custom">Kustom / Netral</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="text-xs font-medium text-fg block mb-1">
                  Transkrip Rekaman (Opsional)
                </label>
                <input
                  type="text"
                  placeholder="Isi kalimat yang Anda baca (membantu model remote)"
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  className="input-base text-xs py-2 w-full"
                />
              </div>
            </div>

            {/* WAJIB Checkbox Persetujuan Etika Suara */}
            <div className="p-3.5 rounded-xl bg-panel border border-border border border-amber-500/40 text-xs space-y-1.5">
              <div className="flex items-start gap-2.5">
                <input
                  type="checkbox"
                  id="consent-checkbox-voice"
                  checked={consentChecked}
                  onChange={(e) => setConsentChecked(e.target.checked)}
                  className="mt-0.5 rounded border-amber-500/50 text-fg focus:ring-fg cursor-pointer"
                />
                <label
                  htmlFor="consent-checkbox-voice"
                  className="cursor-pointer text-fg leading-relaxed select-none"
                >
                  <strong className="text-amber-300 block mb-0.5 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-fg font-semibold" />
                    Persetujuan Hak Suara (Consent Wajib):
                  </strong>
                  Saya menyatakan bahwa saya memiliki izin tertulis atau hak legal penuh atas sampel suara ini.
                  Saya menyetujui pencatatan audit log persetujuan dan pelabelan otomatis &ldquo;Dibuat dengan AI&rdquo;.
                </label>
              </div>
            </div>

            {/* Status Pesan */}
            {statusMessage && (
              <div
                className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
                  statusMessage.type === "success"
                    ? "bg-panel border border-border border border-border text-fg font-semibold"
                    : statusMessage.type === "error"
                    ? "bg-surface border-2 border-dashed border-fg border border-fg text-fg font-semibold"
                    : "bg-panel border border-border border border-border text-fg"
                }`}
              >
                {statusMessage.type === "success" ? (
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                ) : statusMessage.type === "error" ? (
                  <AlertCircle className="w-4 h-4 shrink-0" />
                ) : (
                  <Loader2 className="w-4 h-4 animate-spin shrink-0" />
                )}
                <span>{statusMessage.text}</span>
              </div>
            )}

            {/* Tombol Simpan Suara Klon */}
            <button
              type="submit"
              id="btn-submit-clone"
              disabled={
                isUploading ||
                !consentChecked ||
                !voiceName.trim() ||
                !speakerName.trim() ||
                !isDurationValid
              }
              className={`w-full py-2.5 px-4 rounded-lg font-semibold text-xs flex items-center justify-center gap-2 transition-all ${
                isUploading ||
                !consentChecked ||
                !voiceName.trim() ||
                !speakerName.trim() ||
                !isDurationValid
                  ? "bg-panel text-muted border border-border cursor-not-allowed opacity-60"
                  : "bg-primary text-primary-fg text-primary-fg hover:bg-primary text-primary-fg/90 shadow-md shadow-accent/20 cursor-pointer"
              }`}
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Mengonversi ke 24 kHz Mono & Menyimpan Klon...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Proses Kloning Suara & Simpan Consent Log
                </>
              )}
            </button>
          </form>
        </div>

        {/* Kolom Kanan: Pengujian A/B & Riwayat Log (5 Kolom) */}
        <div className="lg:col-span-5 space-y-5">
          {/* FITUR KOMPARASI A/B: Klon Suara vs Baseline Piper */}
          <div className="card p-5 space-y-4 border-border bg-panel/30">
            <div className="border-b border-border pb-2.5 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-fg flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-fg" />
                Pengujian Komparasi A/B
              </h2>
              <span className="text-[10px] px-2 py-0.5 rounded bg-panel text-fg font-semibold border border-border">
                A/B Listen
              </span>
            </div>

            <p className="text-[11px] text-muted leading-relaxed">
              Bandingkan ekspresivitas dan kemiripan suara hasil kloning Anda (A) melawan suara default
              Piper (B) menggunakan kalimat yang sama.
            </p>

            {/* Pilih Suara Klon untuk Diuji */}
            <div className="space-y-1">
              <label className="text-[11px] font-medium text-fg block">Pilih Suara Klon (A):</label>
              <select
                id="select-ab-clone-voice"
                value={compareVoiceId}
                onChange={(e) => setCompareVoiceId(e.target.value)}
                className="input-base text-xs py-2 w-full"
              >
                {logs.length === 0 ? (
                  <option value="">Belum ada suara kloning yang dibuat</option>
                ) : (
                  logs.map((log) => (
                    <option key={log.id} value={log.id}>
                      {log.voice_name} ({log.speaker_name})
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Teks Kalimat Uji */}
            <div className="space-y-1">
              <label className="text-[11px] font-medium text-fg block">Kalimat Uji Perbandingan:</label>
              <textarea
                id="input-ab-test-text"
                rows={2}
                value={compareText}
                onChange={(e) => setCompareText(e.target.value)}
                className="input-base text-xs p-2.5 w-full resize-none"
                placeholder="Ketik kalimat uji..."
              />
            </div>

            {/* Tombol Run A/B */}
            <button
              type="button"
              id="btn-run-ab-compare"
              onClick={handleCompareAB}
              disabled={isComparing || !compareVoiceId || !compareText.trim()}
              className={`w-full py-2 px-3 rounded-lg font-semibold text-xs flex items-center justify-center gap-2 transition-all ${
                isComparing || !compareVoiceId || !compareText.trim()
                  ? "bg-panel text-muted border border-border cursor-not-allowed opacity-60"
                  : "bg-surface hover:bg-panel border border-border text-fg border border-border cursor-pointer"
              }`}
            >
              {isComparing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Menyintesis 2 Audio Komparasi...
                </>
              ) : (
                <>
                  <Layers className="w-3.5 h-3.5" />
                  Uji Sintesis A/B Sekarang
                </>
              )}
            </button>

            {/* Hasil Komparasi A/B */}
            {compareResult && (
              <div className="pt-2 space-y-3">
                <div className="text-[11px] font-medium text-muted border-b border-border pb-1">
                  Hasil Komparasi Audio:
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Kartu Audio A: Klon Suara */}
                  <div className="p-3 rounded-lg bg-surface border border-border space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-fg uppercase tracking-wider">
                        Sample A (Klon Anda)
                      </span>
                      <span className="text-[9px] text-muted font-mono">
                        {compareResult.sample_a.duration.toFixed(1)}s
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-fg truncate">
                      {compareResult.sample_a.name}
                    </div>
                    <audio
                      ref={compareAudioARef}
                      src={compareResult.sample_a.audio_url}
                      controls
                      className="w-full h-7"
                    />
                    <div className="text-[9px] text-muted/80">
                      Engine: {compareResult.sample_a.engine_used} (24 kHz)
                    </div>
                  </div>

                  {/* Kartu Audio B: Piper Baseline */}
                  <div className="p-3 rounded-lg bg-surface border border-border space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-muted uppercase tracking-wider">
                        Sample B (Piper Base)
                      </span>
                      <span className="text-[9px] text-muted font-mono">
                        {compareResult.sample_b.duration.toFixed(1)}s
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-fg truncate">
                      {compareResult.sample_b.name}
                    </div>
                    <audio
                      ref={compareAudioBRef}
                      src={compareResult.sample_b.audio_url}
                      controls
                      className="w-full h-7"
                    />
                    <div className="text-[9px] text-muted/80">
                      Engine: {compareResult.sample_b.engine_used}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Card Riwayat Consent Log */}
          <div className="card p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <h3 className="text-xs font-semibold text-fg flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-fg font-semibold" />
                Daftar Suara Kloning ({logs.length})
              </h3>
              <span className="text-[10px] text-muted">Tersimpan di DB</span>
            </div>

            {isLoadingLogs ? (
              <div className="py-4 text-center text-xs text-muted flex items-center justify-center gap-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-fg" />
                Memuat riwayat...
              </div>
            ) : logs.length === 0 ? (
              <p className="text-[11px] text-muted py-3 text-center">
                Belum ada suara yang dikloning. Rekam suara Anda di sebelah kiri.
              </p>
            ) : (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {logs.map((log) => (
                  <div
                    key={log.id}
                    className="p-2.5 rounded-lg bg-panel/70 border border-border/80 text-[11px] space-y-1.5"
                  >
                    <div className="flex items-center justify-between font-semibold text-fg">
                      <span className="truncate">{log.voice_name}</span>
                      <span className="text-[9px] text-fg font-semibold font-medium bg-panel border border-border px-1.5 py-0.5 rounded border border-border">
                        Consent Legal
                      </span>
                    </div>
                    <div className="text-muted text-[10px] flex items-center justify-between">
                      <span>Narasumber: {log.speaker_name}</span>
                      <span>{log.sample_duration_sec}s</span>
                    </div>
                    <div className="flex items-center justify-between pt-1">
                      <span className="text-[9px] text-muted font-mono">
                        {new Date(log.created_at).toLocaleDateString("id-ID")}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          setCompareVoiceId(log.id);
                        }}
                        className="text-[10px] text-fg hover:underline font-medium"
                      >
                        Pilih untuk Uji A/B
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
