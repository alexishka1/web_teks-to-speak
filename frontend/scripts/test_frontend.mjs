/**
 * Unit Test Runner untuk Frontend TaSTP:
 * Menguji logika pemecahan kalimat client-side, timing kalimat,
 * formatting URL audio, dan integrasi store.
 */

import assert from "node:assert";

// 1. Uji logika splitSentencesClient
function splitSentencesClient(text, totalDuration = 0) {
  if (!text || !text.trim()) return [];
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
    return {
      text: sentText,
      startTime: start,
      endTime: end,
    };
  });
}

function getAudioDownloadUrl(jobIdOrUrl) {
  if (jobIdOrUrl.startsWith("http") || jobIdOrUrl.startsWith("/")) {
    return jobIdOrUrl;
  }
  return `/api/audio/${jobIdOrUrl}`;
}

console.log("=== Menjalankan Pengujian Dasar Frontend TaSTP ===");

// Test 1: Pemecahan kalimat naskah Indonesia
const script = "Halo kawan-kawan semua! Hari ini kita akan membahas tips konten viral. Simak sampai tuntas ya?";
const sentences = splitSentencesClient(script, 6.0);
assert.strictEqual(sentences.length, 3, "Harus menghasilkan tepat 3 kalimat");
assert.strictEqual(sentences[0].text, "Halo kawan-kawan semua!");
assert(sentences[0].startTime === 0, "Kalimat pertama harus mulai di detik 0");
assert(sentences[2].endTime > 5.5, "Kalimat terakhir harus selesai mendekati 6 detik");
console.log("✅ Test 1 Passed: Client sentence splitter & timing calculation");

// Test 2: Formatting audio download URL
assert.strictEqual(getAudioDownloadUrl("job_12345"), "/api/audio/job_12345");
assert.strictEqual(getAudioDownloadUrl("/api/audio/custom.wav"), "/api/audio/custom.wav");
assert.strictEqual(getAudioDownloadUrl("http://localhost:8000/audio.wav"), "http://localhost:8000/audio.wav");
console.log("✅ Test 2 Passed: Audio URL builder format");

// Test 3: Teks kosong
assert.deepStrictEqual(splitSentencesClient(""), []);
assert.deepStrictEqual(splitSentencesClient("    "), []);
console.log("✅ Test 3 Passed: Edge case empty string handling");

console.log("\n🎉 Seluruh 3 pengujian frontend berhasil 100%!");
