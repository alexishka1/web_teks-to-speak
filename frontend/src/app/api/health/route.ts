import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "ok",
    app_name: "TaSTP - Self-Hosted TTS",
    version: "1.0.0",
    hardware: {
      mode: "cpu_only",
      target: "Intel Iris / CPU",
      max_threads: 4,
      cuda_enabled: false,
    },
    default_engine: "piper",
    remote_available: false,
    ai_disclosure_enabled: true,
    timestamp: new Date().toISOString(),
  });
}
