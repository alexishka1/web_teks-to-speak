"use client";

import React from "react";
import { EmotionPresetDTO } from "@/lib/api";
import { X, Sparkles, Shield, Check } from "lucide-react";

interface EmotionPickerProps {
  isOpen: boolean;
  onClose: () => void;
  sentenceIndex: number;
  sentenceText: string;
  currentEmotion: string;
  emotionsCatalog: EmotionPresetDTO[];
  onSelectEmotion: (sentenceIndex: number, emotionId: string) => void;
}

export function EmotionPicker({
  isOpen,
  onClose,
  sentenceIndex,
  sentenceText,
  currentEmotion,
  emotionsCatalog,
  onSelectEmotion,
}: EmotionPickerProps) {
  if (!isOpen) return null;

  // Group by category
  const categories: Record<string, string> = {
    dasar: "Emosi Dasar",
    nuansa: "Nuansa & Mood",
    gaya: "Gaya Bicara & Format",
    karakter: "Karakter & Non-Verbal",
  };

  const grouped: Record<string, EmotionPresetDTO[]> = {
    dasar: [],
    nuansa: [],
    gaya: [],
    karakter: [],
  };

  emotionsCatalog.forEach((emo) => {
    if (grouped[emo.category]) {
      grouped[emo.category].push(emo);
    } else {
      grouped.dasar.push(emo);
    }
  });

  return (
    <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4">
      <div className="bg-surface border border-border rounded-lg w-full max-w-2xl max-h-[85vh] flex flex-col shadow-xl overflow-hidden animate-in fade-in duration-150">
        {/* Header */}
        <div className="p-4 border-b border-border flex items-center justify-between shrink-0 bg-surface">
          <div>
            <h3 className="font-semibold text-sm text-fg flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-fg" strokeWidth={1.5} />
              Pilih Emosi Kalimat #{sentenceIndex + 1}
            </h3>
            <p className="text-xs text-muted line-clamp-1 mt-0.5 max-w-md">
              &ldquo;{sentenceText}&rdquo;
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-md text-muted hover:text-fg hover:bg-hover border border-transparent hover:border-border transition-colors duration-150"
            title="Tutup"
          >
            <X className="w-4 h-4" strokeWidth={1.5} />
          </button>
        </div>

        {/* Emotion Preset Grid */}
        <div className="flex-1 p-4 overflow-y-auto space-y-5">
          {Object.entries(categories).map(([catKey, catLabel]) => {
            const list = grouped[catKey] || [];
            if (list.length === 0) return null;

            return (
              <div key={catKey} className="space-y-2.5">
                <div className="text-xs font-semibold text-fg tracking-wider uppercase flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-fg" />
                  {catLabel}
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {list.map((emo) => {
                    const isSelected = currentEmotion === emo.id;
                    return (
                      <button
                        key={emo.id}
                        type="button"
                        onClick={() => {
                          onSelectEmotion(sentenceIndex, emo.id);
                          onClose();
                        }}
                        className={`p-3 rounded-md border text-left transition-colors duration-150 flex flex-col justify-between ${
                          isSelected
                            ? "bg-panel border-2 border-primary text-fg font-semibold shadow-sm"
                            : "bg-surface border-border hover:bg-hover hover:border-fg/40 text-fg"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-1 mb-1">
                          <span className="font-semibold text-xs text-fg truncate">
                            {emo.name}
                          </span>
                          {isSelected && (
                            <Check className="w-3.5 h-3.5 text-fg shrink-0" strokeWidth={2} />
                          )}
                        </div>
                        <div className="text-[11px] text-muted line-clamp-2 leading-relaxed">
                          {emo.description}
                        </div>
                        <div className="flex items-center gap-1.5 mt-2.5 text-[10px] font-mono text-muted">
                          <span>{emo.speed}x laju</span>
                          <span>•</span>
                          <span>{emo.pitch > 0 ? `+${emo.pitch}` : emo.pitch} nada</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-border bg-panel flex items-center justify-between text-xs text-muted shrink-0">
          <span className="flex items-center gap-1.5 text-xs">
            <Shield className="w-3.5 h-3.5 text-fg" strokeWidth={1.5} />
            <span>Prosodi nada dan laju dihitung otomatis oleh server</span>
          </span>
          <button
            type="button"
            onClick={onClose}
            className="btn-secondary h-8 px-3 text-xs"
          >
            Batal
          </button>
        </div>
      </div>
    </div>
  );
}
