"use client";

import React from "react";
import { useTTSStore } from "@/store/ttsStore";
import { WaveformView } from "./WaveformView";
import {
  Play,
  Pause,
  Download,
  Volume2,
  RotateCcw,
} from "lucide-react";

export function AudioPlayerBar() {
  const {
    audioUrl,
    audioDuration,
    isGenerating,
    isPlaying,
    setIsPlaying,
    currentTime,
    setCurrentTime,
    playbackSpeed,
    setPlaybackSpeed,
    currentJobId,
  } = useTTSStore();

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const handleRestart = () => {
    setCurrentTime(0);
    if (!isPlaying) setIsPlaying(true);
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  const duration = audioDuration > 0 ? audioDuration : 3.5;

  if (!audioUrl && !isGenerating) {
    return null;
  }

  const downloadFilename = currentJobId
    ? `tastp_${currentJobId}.wav`
    : "tastp_narasi_ai.wav";

  return (
    <div className="border-t border-border bg-surface px-4 py-3 flex flex-col md:flex-row items-center justify-between gap-4 shrink-0 select-none">
      {/* Kiri: Play/Pause, Replay & Status Suara */}
      <div className="flex items-center gap-3 shrink-0 w-full md:w-auto justify-between md:justify-start">
        <div className="flex items-center gap-1.5">
          <button
            id="play-audio-button"
            type="button"
            onClick={togglePlay}
            disabled={!audioUrl}
            className="w-9 h-9 rounded-md bg-primary text-primary-fg flex items-center justify-center hover:bg-primary-hover transition-colors duration-150 disabled:opacity-40"
            aria-label={isPlaying ? "Jeda" : "Putar"}
            title={isPlaying ? "Jeda Audio" : "Putar Audio"}
          >
            {isPlaying ? (
              <Pause className="w-4 h-4 fill-current" strokeWidth={1.5} />
            ) : (
              <Play className="w-4 h-4 fill-current ml-0.5" strokeWidth={1.5} />
            )}
          </button>

          <button
            type="button"
            onClick={handleRestart}
            disabled={!audioUrl}
            className="p-2 rounded-md text-muted hover:text-fg hover:bg-hover border border-transparent hover:border-border transition-colors duration-150 disabled:opacity-40"
            title="Mulai Ulang dari Awal"
          >
            <RotateCcw className="w-4 h-4" strokeWidth={1.5} />
          </button>
        </div>

        <div>
          <div className="text-xs font-semibold text-fg flex items-center gap-2">
            <Volume2 className="w-3.5 h-3.5 text-fg" strokeWidth={1.5} />
            <span>Hasil Narasi Studio</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-panel border border-border text-muted">
              AI Watermarked
            </span>
          </div>
          <div className="text-[11px] text-muted font-mono mt-0.5">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>
        </div>
      </div>

      {/* Tengah: Waveform Visualizer */}
      <div className="flex-1 max-w-2xl w-full">
        <WaveformView
          audioUrl={audioUrl}
          onTimeUpdate={(t) => setCurrentTime(t)}
          onFinish={() => {
            setIsPlaying(false);
            setCurrentTime(0);
          }}
          onPlayStateChange={(playing) => setIsPlaying(playing)}
        />
      </div>

      {/* Kanan: Kecepatan Playback & Tombol Unduh */}
      <div className="flex items-center gap-2.5 shrink-0 w-full md:w-auto justify-end">
        {/* Playback speed selector */}
        <div className="flex items-center bg-panel rounded-md p-0.5 border border-border text-xs">
          {[1.0, 1.25, 1.5].map((spd) => (
            <button
              key={spd}
              type="button"
              onClick={() => setPlaybackSpeed(spd)}
              className={`px-2 py-0.5 rounded text-xs font-mono transition-colors duration-150 ${
                playbackSpeed === spd
                  ? "bg-primary text-primary-fg font-semibold"
                  : "text-muted hover:text-fg"
              }`}
            >
              {spd}x
            </button>
          ))}
        </div>

        {audioUrl && (
          <a
            id="download-audio-button"
            href={audioUrl}
            download={downloadFilename}
            className="btn-secondary h-8 px-3 text-xs"
            title="Unduh Master Audio WAV (16-bit 22.050 Hz)"
          >
            <Download className="w-3.5 h-3.5" strokeWidth={1.5} />
            <span>Unduh WAV</span>
          </a>
        )}
      </div>
    </div>
  );
}
