import { test, expect } from "@playwright/test";

test.describe("Studio Manager End-to-End Dynamic Workflow", () => {
  test("Tambah 1 suara dan 1 preset lewat Studio Manager, lalu langsung bisa dipakai di Text to Speech tanpa restart", async ({
    page,
  }) => {
    const timestamp = Date.now().toString().slice(-6);
    const testVoiceName = `Suara E2E ${timestamp}`;
    const testPresetName = `Preset E2E ${timestamp}`;

    // 1. Buka antarmuka utama TaSTP
    await page.goto("/");
    await expect(page).toHaveTitle(/TaSTP/i);

    // 2. Navigasi ke halaman Studio Manager via Sidebar (#nav-item-studio)
    const studioNavBtn = page.locator("#nav-item-studio");
    await expect(studioNavBtn).toBeVisible({ timeout: 10000 });
    await studioNavBtn.click();

    // Pastikan halaman Studio Manager termuat
    await expect(page.getByRole("heading", { name: "Studio Manager" })).toBeVisible({ timeout: 15000 });

    // 3. Tambah Suara Baru lewat Upload Modal (#btn-upload-voice)
    const uploadVoiceBtn = page.locator("#btn-upload-voice");
    await expect(uploadVoiceBtn).toBeVisible();
    await uploadVoiceBtn.click();

    // Unggah file .onnx dan .json yang valid
    const onnxFileInput = page.locator("#input-file-onnx");
    await onnxFileInput.setInputFiles({
      name: `voice_${timestamp}.onnx`,
      mimeType: "application/octet-stream",
      buffer: Buffer.from("mock onnx binary stream e2e test"),
    });

    const jsonFileInput = page.locator("#input-file-json");
    const sampleConfigJson = JSON.stringify({
      audio: { sample_rate: 22050 },
      language: { code: "id_ID" },
    });
    await jsonFileInput.setInputFiles({
      name: `voice_${timestamp}.json`,
      mimeType: "application/json",
      buffer: Buffer.from(sampleConfigJson),
    });

    const voiceNameInput = page.locator("#input-voice-name");
    await voiceNameInput.fill(testVoiceName);

    // Klik tombol Uji & Simpan Suara
    const submitVoiceBtn = page.locator("#btn-submit-upload-voice");
    await submitVoiceBtn.click();

    // Tunggu hingga modal tertutup dan kartu suara muncul di daftar
    await expect(page.getByRole("heading", { name: testVoiceName })).toBeVisible({ timeout: 15000 });

    // 4. Tambah Preset Gaya Baru (#tab-btn-presets)
    const presetTabBtn = page.locator("#tab-btn-presets");
    await presetTabBtn.click();

    const addPresetBtn = page.locator("#btn-add-preset");
    await expect(addPresetBtn).toBeVisible({ timeout: 10000 });
    await addPresetBtn.click();

    const presetNameInput = page.locator("#input-preset-name");
    await presetNameInput.fill(testPresetName);

    const submitPresetBtn = page.locator("#btn-submit-preset");
    await submitPresetBtn.click();

    // Tunggu hingga modal tertutup dan preset baru muncul di daftar
    await expect(page.getByRole("heading", { name: testPresetName })).toBeVisible({ timeout: 10000 });

    // 5. Kembali ke halaman Text to Speech via Sidebar (Hot-Reload Verification)
    const ttsNavBtn = page.locator("#nav-item-tts");
    await ttsNavBtn.click();

    // Pastikan editor Text to Speech aktif
    const textarea = page.locator("#tts-textarea");
    await expect(textarea).toBeVisible({ timeout: 10000 });

    // 6. Verifikasi Preset Baru langsung muncul di Dropdown Preset Gaya tanpa restart
    const presetSelect = page.locator("#select-style-preset");
    await expect(presetSelect).toBeVisible({ timeout: 10000 });
    // Tunggu opsi preset baru tersedia di dropdown
    const presetOption = presetSelect.locator(`option:has-text("${testPresetName}")`);
    await expect(presetOption).toBeAttached({ timeout: 10000 });
    const presetValue = await presetOption.getAttribute("value");
    if (presetValue) {
      await presetSelect.selectOption(presetValue);
    }

    // 7. Verifikasi Suara Baru langsung muncul di panel suara dan dapat dipilih
    const voiceCard = page.locator(`button:has-text("${testVoiceName}")`);
    await expect(voiceCard).toBeVisible({ timeout: 10000 });
    await voiceCard.click();

    // 8. Uji sintesis menggunakan suara dan preset baru tersebut
    const testScript = "Pengujian suara dan preset baru dari Studio Manager berhasil.";
    await textarea.fill(testScript);

    const generateBtn = page.locator("#generate-button");
    await expect(generateBtn).toBeVisible();
    await generateBtn.click();

    // Tunggu proses sintesis selesai
    await expect(generateBtn).toBeEnabled({ timeout: 35000 });

    // 9. Pastikan Audio Player Bar dan kontrol Play/Download muncul
    const playBtn = page.locator("#play-audio-button");
    await expect(playBtn).toBeVisible();
    await expect(playBtn).toBeEnabled();

    const downloadBtn = page.locator("#download-audio-button");
    await expect(downloadBtn).toBeVisible();
  });
});
