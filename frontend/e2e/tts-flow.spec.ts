import { test, expect } from "@playwright/test";

test.describe("TaSTP End-to-End Synthesis Flow", () => {
  test("Pengguna dapat membuka UI, mengetik teks, men-generate suara, memutar audio, dan mengunduh file audio", async ({
    page,
  }) => {
    // 1. Buka antarmuka utama TaSTP
    await page.goto("/");
    await expect(page).toHaveTitle(/TaSTP/i);

    // Pastikan editor naskah tampil
    const textarea = page.locator("#tts-textarea");
    await expect(textarea).toBeVisible();

    // 2. Ketik naskah narasi
    const sampleScript =
      "Halo sahabat kreator, selamat datang kembali di channel teknologi masa depan. Hari ini kita membahas inovasi terbaru.";
    await textarea.fill(sampleScript);
    await expect(textarea).toHaveValue(sampleScript);

    // 3. Klik tombol 'Generate Suara'
    const generateBtn = page.locator("#generate-button");
    await expect(generateBtn).toBeVisible();
    await generateBtn.click();

    // 4. Tunggu hingga proses sintesis selesai (maks 30 detik untuk CPU inference)
    // Tombol generate akan disable sementara saat proses berlangsung lalu enable kembali
    await expect(generateBtn).toBeEnabled({ timeout: 35000 });

    // 5. Pastikan Audio Player Bar muncul dan aktif
    const playBtn = page.locator("#play-audio-button");
    await expect(playBtn).toBeVisible();
    await expect(playBtn).toBeEnabled();

    // 6. Uji Play Audio
    await playBtn.click();
    // Tunggu status tombol play berganti atau audio mulai diputar
    await page.waitForTimeout(1000);

    // 7. Uji Tombol Unduh Audio (Download WAV)
    const downloadBtn = page.locator("#download-audio-button");
    await expect(downloadBtn).toBeVisible();
    const downloadHref = await downloadBtn.getAttribute("href");
    expect(downloadHref).toBeTruthy();
    expect(downloadHref).toMatch(/\/api\/audio\/|\.wav$/i);

    const downloadAttr = await downloadBtn.getAttribute("download");
    expect(downloadAttr).toMatch(/\.wav$/i);

    // Tangani event unduhan
    const downloadPromise = page.waitForEvent("download", { timeout: 15000 });
    await downloadBtn.click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toMatch(/\.wav$/i);
  });
});
