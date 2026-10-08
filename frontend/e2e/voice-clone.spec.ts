import { test, expect } from "@playwright/test";

function createWavBuffer(durationSec: number = 15, sampleRate: number = 22050): Buffer {
  const numChannels = 1;
  const bytesPerSample = 2;
  const numSamples = Math.floor(durationSec * sampleRate);
  const dataSize = numSamples * numChannels * bytesPerSample;
  const buffer = Buffer.alloc(44 + dataSize);

  // RIFF chunk
  buffer.write("RIFF", 0);
  buffer.writeUInt32LE(36 + dataSize, 4);
  buffer.write("WAVE", 8);

  // fmt subchunk
  buffer.write("fmt ", 12);
  buffer.writeUInt32LE(16, 16);
  buffer.writeUInt16LE(1, 20); // PCM
  buffer.writeUInt16LE(numChannels, 22);
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(sampleRate * numChannels * bytesPerSample, 28);
  buffer.writeUInt16LE(numChannels * bytesPerSample, 32);
  buffer.writeUInt16LE(16, 34); // 16-bit

  // data subchunk
  buffer.write("data", 36);
  buffer.writeUInt32LE(dataSize, 40);

  // Sinyal audio
  for (let i = 0; i < numSamples; i++) {
    const val = Math.floor(8000 * Math.sin((2 * Math.PI * 440 * i) / sampleRate));
    buffer.writeInt16LE(val, 44 + i * 2);
  }

  return buffer;
}

test.describe("Fitur Suara Saya - Voice Clone End-to-End Workflow", () => {
  test("Navigasi ke Voice Clone, unggah sampel vokal 15 detik, simpan consent log, dan jalankan pengujian A/B", async ({
    page,
  }) => {
    const timestamp = Date.now().toString().slice(-6);
    const testVoiceName = `Kloning E2E ${timestamp}`;
    const testSpeakerName = `Kreator ${timestamp}`;

    // 1. Buka antarmuka utama TaSTP
    await page.goto("/");
    await expect(page).toHaveTitle(/TaSTP/i);

    // 2. Navigasi ke halaman Voice Clone melalui Sidebar
    const cloneNavBtn = page.locator("#nav-item-clone");
    await expect(cloneNavBtn).toBeVisible({ timeout: 10000 });
    await cloneNavBtn.click();

    // Verifikasi halaman Voice Clone termuat
    await expect(
      page.getByRole("heading", { name: "Suara Saya (Voice Clone Studio)" })
    ).toBeVisible({ timeout: 15000 });

    // 3. Beralih ke Tab Unggah File (#tab-mode-upload)
    const uploadModeTab = page.locator("#tab-mode-upload");
    await expect(uploadModeTab).toBeVisible();
    await uploadModeTab.click();

    // Unggah file audio 15 detik yang valid
    const audioInput = page.locator("#sample-file-input");
    const sampleBuffer = createWavBuffer(16, 22050);
    await audioInput.setInputFiles({
      name: `sampel_${timestamp}.wav`,
      mimeType: "audio/wav",
      buffer: sampleBuffer,
    });

    // 4. Isi Form Informasi Suara & Pemilik
    const voiceNameInput = page.locator("#input-voice-name");
    await voiceNameInput.fill(testVoiceName);

    const speakerNameInput = page.locator("#input-speaker-name");
    await speakerNameInput.fill(testSpeakerName);

    // 5. Centang Checkbox Persetujuan Etika Suara (WAJIB)
    const consentCheckbox = page.locator("#consent-checkbox-voice");
    await consentCheckbox.check();
    await expect(consentCheckbox).toBeChecked();

    // 6. Submit Kloning Suara
    const submitBtn = page.locator("#btn-submit-clone");
    await expect(submitBtn).toBeEnabled({ timeout: 5000 });
    await submitBtn.click();

    // Tunggu pesan sukses muncul
    await expect(page.getByText(/Klon suara .* berhasil diproses/i)).toBeVisible({
      timeout: 25000,
    });

    // 7. Pengujian Komparasi A/B
    const selectCloneVoice = page.locator("#select-ab-clone-voice");
    await expect(selectCloneVoice).toBeVisible();

    const runABBtn = page.locator("#btn-run-ab-compare");
    await expect(runABBtn).toBeVisible();
    await runABBtn.click();

    // Verifikasi hasil komparasi Sample A dan Sample B muncul
    await expect(page.getByText("Sample A (Klon Anda)")).toBeVisible({ timeout: 30000 });
    await expect(page.getByText("Sample B (Piper Base)")).toBeVisible({ timeout: 30000 });

    // 8. Navigasi kembali ke Text to Speech dan pastikan suara klon muncul di katalog
    const ttsNavBtn = page.locator("#nav-item-tts");
    await ttsNavBtn.click();

    const voiceList = page.locator("#voice-selection-list");
    await expect(voiceList).toBeVisible();
    await expect(voiceList).toContainText(testVoiceName);
  });
});

