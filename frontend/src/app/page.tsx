"use client";

import React, { useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { EditorSection } from "@/components/editor/EditorSection";
import { ControlPanel } from "@/components/controls/ControlPanel";
import { AudioPlayerBar } from "@/components/player/AudioPlayerBar";
import { VoiceLibrary } from "@/components/library/VoiceLibrary";
import { VoiceClone } from "@/components/clone/VoiceClone";
import { ProjectsView } from "@/components/projects/ProjectsView";
import { HistoryView } from "@/components/history/HistoryView";
import { ApiPlayground } from "@/components/playground/ApiPlayground";
import { StudioManagerView } from "@/components/studio/StudioManagerView";
import { useTTSStore } from "@/store/ttsStore";

export default function StudioPage() {
  const { activeTab, setActiveTab, fetchVoicesList } = useTTSStore();

  useEffect(() => {
    fetchVoicesList();
  }, [fetchVoicesList]);

  return (
    <main className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Kolom 1: Sidebar Navigasi Kiri */}
      <Sidebar />

      {/* Tampilan Sesuai Tab Aktif */}
      {activeTab === "tts" ? (
        <div className="flex-1 flex flex-col lg:flex-row min-w-0 h-screen overflow-hidden">
          {/* Kolom 2: Editor Teks Tengah & Player Bar */}
          <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
            <EditorSection />
            <AudioPlayerBar />
          </div>

          {/* Kolom 3: Panel Pengaturan Kanan */}
          <ControlPanel />
        </div>
      ) : activeTab === "library" ? (
        <VoiceLibrary />
      ) : activeTab === "studio" ? (
        <StudioManagerView />
      ) : activeTab === "clone" ? (
        <VoiceClone />
      ) : activeTab === "projects" ? (
        <ProjectsView />
      ) : activeTab === "history" ? (
        <HistoryView />
      ) : activeTab === "playground" ? (
        <ApiPlayground />
      ) : null}
    </main>
  );
}
