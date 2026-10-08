"use client";

import React, { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";
import { useTTSStore } from "@/store/ttsStore";

interface WaveformViewProps {
  audioUrl?: string | null;
  onReady?: (duration: number) => void;
  onTimeUpdate?: (currentTime: number) => void;
  onFinish?: () => void;
  onPlayStateChange?: (isPlaying: boolean) => void;
}

export function WaveformView({
  audioUrl,
  onReady,
  onTimeUpdate,
  onFinish,
  onPlayStateChange,
}: WaveformViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const [isLoadingWave, setIsLoadingWave] = useState(false);
  const [totalDur, setTotalDur] = useState(0);

  const {
    isPlaying,
    playbackSpeed,
    sentences,
    activeSentenceIndex,
    seekToSentence,
    emotionsCatalog,
  } = useTTSStore();

  useEffect(() => {
    if (!containerRef.current || !audioUrl) return;

    setIsLoadingWave(true);

    if (wavesurferRef.current) {
      wavesurferRef.current.destroy();
      wavesurferRef.current = null;
    }

    try {
      const progressColor = "#0A0A0A";
      const waveColor = "#D4D4D4";
      const cursorColor = "#0A0A0A";

      const ws = WaveSurfer.create({
        container: containerRef.current,
        waveColor,
        progressColor,
        cursorColor,
        cursorWidth: 1.5,
        barWidth: 2,
        barGap: 2,
        barRadius: 2,
        height: 32,
        normalize: true,
        url: audioUrl,
      });

      wavesurferRef.current = ws;

      ws.on("ready", () => {
        setIsLoadingWave(false);
        const dur = ws.getDuration();
        setTotalDur(dur);
        onReady?.(dur);
        ws.setPlaybackRate(playbackSpeed);
      });

      ws.on("timeupdate", (curr) => {
        onTimeUpdate?.(curr);
      });

      ws.on("finish", () => {
        onFinish?.();
        onPlayStateChange?.(false);
      });

      ws.on("play", () => {
        onPlayStateChange?.(true);
      });

      ws.on("pause", () => {
        onPlayStateChange?.(false);
      });

      ws.on("error", (err) => {
        console.warn("WaveSurfer render error:", err);
        setIsLoadingWave(false);
      });

      return () => {
        ws.destroy();
        wavesurferRef.current = null;
      };
    } catch (e) {
      console.warn("Gagal inisialisasi wavesurfer:", e);
      setIsLoadingWave(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audioUrl]);

  // Sync play/pause
  useEffect(() => {
    if (!wavesurferRef.current) return;
    const isWsPlaying = wavesurferRef.current.isPlaying();
    if (isPlaying && !isWsPlaying) {
      wavesurferRef.current.play().catch(() => {});
    } else if (!isPlaying && isWsPlaying) {
      wavesurferRef.current.pause();
    }
  }, [isPlaying]);

  // Sync playback rate
  useEffect(() => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setPlaybackRate(playbackSpeed);
    }
  }, [playbackSpeed]);

  if (!audioUrl) return null;

  const validDuration = totalDur > 0 ? totalDur : sentences.length > 0 ? sentences[sentences.length - 1].endTime : 1;

  // Monochrome grayscale tones for sentence segments
  const monoTones = ["#737373", "#525252", "#A3A3A3", "#404040", "#8C8C8C"];

  return (
    <div className="relative w-full bg-surface rounded-md border border-border p-2 flex flex-col justify-center gap-1.5 overflow-hidden">
      {isLoadingWave && (
        <div className="absolute inset-0 bg-surface/80 flex items-center justify-center text-xs text-muted z-10 font-mono">
          Merender gelombang audio...
        </div>
      )}

      {/* Main Waveform Canvas */}
      <div ref={containerRef} className="w-full cursor-pointer" />

      {/* Timeline Segmen Kalimat (Monochrome Regions Bar) */}
      {sentences.length > 0 && validDuration > 0 && (
        <div className="w-full flex h-1.5 rounded-full overflow-hidden bg-panel border border-border">
          {sentences.map((sent, idx) => {
            const widthPct = Math.max(1, ((sent.endTime - sent.startTime) / validDuration) * 100);
            const isActive = activeSentenceIndex === idx;
            const emoPreset = emotionsCatalog.find((e) => e.id === sent.emotion);
            const toneColor = monoTones[idx % monoTones.length];

            return (
              <div
                key={idx}
                onClick={() => {
                  seekToSentence(idx);
                  if (wavesurferRef.current) {
                    wavesurferRef.current.setTime(sent.startTime);
                  }
                }}
                className={`h-full transition-opacity cursor-pointer relative ${
                  isActive ? "opacity-100 ring-1 ring-fg" : "opacity-50 hover:opacity-100"
                }`}
                style={{
                  width: `${widthPct}%`,
                  backgroundColor: toneColor,
                }}
                title={`Kalimat #${idx + 1} (${emoPreset?.name || sent.emotion || "Netral"}) - Klik untuk melompat`}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
