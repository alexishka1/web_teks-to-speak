"use client";

import React, { useEffect, useState } from "react";
import { useTTSStore, ActiveTab } from "@/store/ttsStore";
import {
  Mic,
  Library,
  Sparkles,
  FolderKanban,
  History,
  Terminal,
  Cpu,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
} from "lucide-react";

interface MenuItem {
  id: ActiveTab;
  label: string;
  icon: React.ComponentType<{ className?: string; strokeWidth?: string | number }>;
  badge?: string;
}

export function Sidebar() {
  const { activeTab, setActiveTab, voices, fetchVoicesList } = useTTSStore();
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    fetchVoicesList();
  }, [fetchVoicesList]);

  // Ensure Light mode is enforced
  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const menuItems: MenuItem[] = [
    { id: "tts", label: "Text to Speech", icon: Mic },
    {
      id: "library",
      label: "Voice Library",
      icon: Library,
      badge: voices.length > 0 ? String(voices.length) : "5",
    },
    { id: "studio", label: "Studio Manager", icon: SlidersHorizontal, badge: "Admin" },
    { id: "clone", label: "Voice Clone", icon: Sparkles, badge: "Beta" },
    { id: "projects", label: "Projects", icon: FolderKanban },
    { id: "history", label: "History", icon: History },
    { id: "playground", label: "API Playground", icon: Terminal },
  ];

  return (
    <aside
      className={`border-r border-border bg-surface flex flex-col justify-between select-none shrink-0 h-screen sticky top-0 transition-all duration-150 z-20 ${
        isCollapsed ? "w-16" : "w-64"
      }`}
    >
      {/* Top Branding */}
      <div>
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-8 h-8 rounded-md bg-primary text-primary-fg flex items-center justify-center font-semibold text-sm shrink-0">
              T
            </div>
            {!isCollapsed && (
              <div className="min-w-0">
                <div className="font-semibold text-sm tracking-tight text-fg truncate">
                  TaSTP Studio
                </div>
                <p className="text-xs text-muted truncate">Self-Hosted TTS</p>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 rounded-md text-muted hover:text-fg hover:bg-hover border border-transparent hover:border-border transition-colors hidden md:flex"
            title={isCollapsed ? "Buka Sidebar" : "Perkecil Sidebar"}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" strokeWidth={1.5} />
            ) : (
              <ChevronLeft className="w-4 h-4" strokeWidth={1.5} />
            )}
          </button>
        </div>

        {/* Hardware Status Card */}
        {!isCollapsed && (
          <div className="m-3 p-3 rounded-md bg-panel border border-border text-xs space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-muted flex items-center gap-1.5 text-xs">
                <Cpu className="w-3.5 h-3.5 text-fg" strokeWidth={1.5} />
                Hardware
              </span>
              <span className="text-[10px] font-semibold text-fg px-1.5 py-0.5 rounded border border-border bg-surface">
                ACTIVE
              </span>
            </div>
            <div className="text-fg font-semibold text-xs truncate">
              Intel Iris • Piper ONNX
            </div>
            <p className="text-[11px] text-muted truncate">
              CPU-Only • Zero Cloud Fee
            </p>
          </div>
        )}

        {/* Navigation Menus */}
        <nav className="p-2 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                id={`nav-item-${item.id}`}
                type="button"
                onClick={() => setActiveTab(item.id)}
                title={item.label}
                className={`w-full flex items-center ${
                  isCollapsed ? "justify-center px-2" : "justify-between px-3"
                } py-2 rounded-md text-xs transition-colors duration-150 ${
                  isActive
                    ? "bg-primary text-primary-fg font-semibold shadow-sm"
                    : "text-muted hover:text-fg hover:bg-hover font-normal"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={`w-4 h-4 shrink-0 ${
                      isActive ? "text-primary-fg" : "text-muted"
                    }`}
                    strokeWidth={1.5}
                  />
                  {!isCollapsed && <span className="truncate">{item.label}</span>}
                </div>
                {!isCollapsed && item.badge && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-semibold shrink-0 border ${
                      isActive
                        ? "border-primary-fg/40 text-primary-fg"
                        : "border-border text-muted bg-surface"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Controls & Status */}
      <div className="p-3 border-t border-border space-y-2">
        <div
          className={`w-full flex items-center ${
            isCollapsed ? "justify-center" : "justify-between"
          } px-2.5 py-1.5 rounded-md text-xs text-muted border border-border bg-surface select-none`}
        >
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-fg" />
            {!isCollapsed && <span className="font-medium text-fg">Studio Light</span>}
          </div>
          {!isCollapsed && (
            <span className="text-[10px] font-mono px-1 py-0.2 rounded border border-border text-muted">
              v1.0
            </span>
          )}
        </div>

        {!isCollapsed && (
          <div className="p-2.5 rounded-md border border-border bg-panel text-xs space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-fg font-semibold">
              <ShieldCheck className="w-3.5 h-3.5" strokeWidth={1.5} />
              <span>Etika AI Mandiri</span>
            </div>
            <p className="text-[11px] text-muted leading-relaxed">
              Metadata &ldquo;Dibuat dengan AI&rdquo; tersemat otomatis pada seluruh file audio WAV.
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
