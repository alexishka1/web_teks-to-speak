"""
Preset Emosi dan Gaya Bicara TaSTP (22 Emosi):
1. Emosi Dasar: neutral, happy, sad, angry, fearful, disgusted, surprised
2. Nuansa Emosi: calm, enthusiastic, somber, hopeful, anxious, confident
3. Gaya Bicara: storytelling, news_anchor, podcast_intimate, radio_announcer, tutorial_instructive
4. Karakter & Non-Verbal: whisper, telephone, dramatic, energetic_hook
"""

from typing import Any


class EmotionPreset:
    def __init__(
        self,
        id: str,
        name: str,
        category: str,
        speed: float,
        pitch: float,
        pause_scale: float,
        effect: str = "none",
        color: str = "#94a3b8",
        description: str = "",
        is_active: bool = True,
    ):
        self.id = id
        self.name = name
        self.category = category
        self.speed = speed
        self.pitch = pitch
        self.pause_scale = pause_scale
        self.effect = effect
        self.color = color
        self.description = description
        self.is_active = is_active

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "speed": self.speed,
            "pitch": self.pitch,
            "pause_scale": self.pause_scale,
            "effect": self.effect,
            "color": self.color,
            "description": self.description,
            "is_active": self.is_active,
        }


# Katalog 22 Preset Emosi TaSTP
EMOTION_CATALOG: dict[str, EmotionPreset] = {
    # A. Emosi Dasar
    "neutral": EmotionPreset(
        id="neutral",
        name="Netral (Standar)",
        category="dasar",
        speed=1.0,
        pitch=0.0,
        pause_scale=1.0,
        effect="none",
        color="#94a3b8",
        description="Tutur kata alami tanpa penekanan emosi berlebih.",
    ),
    "happy": EmotionPreset(
        id="happy",
        name="Gembira / Ceria",
        category="dasar",
        speed=1.12,
        pitch=1.8,
        pause_scale=0.85,
        effect="none",
        color="#fbbf24",
        description="Tempo cepat dan nada ceria optimis.",
    ),
    "sad": EmotionPreset(
        id="sad",
        name="Sedih / Haru",
        category="dasar",
        speed=0.84,
        pitch=-1.5,
        pause_scale=1.35,
        effect="reverb",
        color="#60a5fa",
        description="Laju lambat, nada rendah, dan jeda reflektif.",
    ),
    "angry": EmotionPreset(
        id="angry",
        name="Marah / Tegas",
        category="dasar",
        speed=1.18,
        pitch=1.2,
        pause_scale=0.75,
        effect="none",
        color="#ef4444",
        description="Artikulasi agresif dan jeda sangat pendek.",
    ),
    "fearful": EmotionPreset(
        id="fearful",
        name="Takut / Khawatir",
        category="dasar",
        speed=1.15,
        pitch=2.2,
        pause_scale=1.25,
        effect="none",
        color="#c084fc",
        description="Nada tinggi gemetar dengan jeda tergesa.",
    ),
    "disgusted": EmotionPreset(
        id="disgusted",
        name="Muak / Menolak",
        category="dasar",
        speed=0.88,
        pitch=-1.2,
        pause_scale=1.15,
        effect="none",
        color="#a3e635",
        description="Intonasi mencemooh dan melambat di akhir frasa.",
    ),
    "surprised": EmotionPreset(
        id="surprised",
        name="Terkejut / Kaget",
        category="dasar",
        speed=1.24,
        pitch=2.8,
        pause_scale=0.70,
        effect="none",
        color="#f97316",
        description="Lonjakan nada tinggi dan tempo tiba-tiba.",
    ),
    # B. Nuansa Emosi
    "calm": EmotionPreset(
        id="calm",
        name="Tenang / Rileks",
        category="nuansa",
        speed=0.90,
        pitch=-0.6,
        pause_scale=1.20,
        effect="none",
        color="#38bdf8",
        description="Cocok untuk meditasi, cerita santai, dan narasi damai.",
    ),
    "enthusiastic": EmotionPreset(
        id="enthusiastic",
        name="Antusias / Semangat",
        category="nuansa",
        speed=1.16,
        pitch=1.9,
        pause_scale=0.80,
        effect="none",
        color="#f59e0b",
        description="Energi positif yang menarik perhatian penonton.",
    ),
    "somber": EmotionPreset(
        id="somber",
        name="Kelam / Berduka",
        category="nuansa",
        speed=0.82,
        pitch=-1.8,
        pause_scale=1.40,
        effect="none",
        color="#64748b",
        description="Suara rendah berbobot untuk suasana berkabung atau duka.",
    ),
    "hopeful": EmotionPreset(
        id="hopeful",
        name="Penuh Harap / Inspiratif",
        category="nuansa",
        speed=1.04,
        pitch=0.8,
        pause_scale=1.05,
        effect="none",
        color="#34d399",
        description="Lembut hangat dan membangun motivasi batin pendengar.",
    ),
    "anxious": EmotionPreset(
        id="anxious",
        name="Gelisah / Cemas",
        category="nuansa",
        speed=1.14,
        pitch=1.4,
        pause_scale=0.85,
        effect="none",
        color="#e879f9",
        description="Ritme terputus-putus dan terburu-buru.",
    ),
    "confident": EmotionPreset(
        id="confident",
        name="Percaya Diri / Mantap",
        category="nuansa",
        speed=1.05,
        pitch=-0.4,
        pause_scale=0.95,
        effect="none",
        color="#2dd4bf",
        description="Berwibawa, tegas, dan meyakinkan audiens.",
    ),
    # C. Gaya Bicara
    "storytelling": EmotionPreset(
        id="storytelling",
        name="Bercerita / Mendongeng",
        category="gaya",
        speed=0.92,
        pitch=-0.2,
        pause_scale=1.30,
        effect="reverb",
        color="#fb7185",
        description="Dinamika intonasi luas untuk cerita fiksi atau sejarah.",
    ),
    "news_anchor": EmotionPreset(
        id="news_anchor",
        name="Penyiar Berita",
        category="gaya",
        speed=1.08,
        pitch=0.2,
        pause_scale=0.85,
        effect="none",
        color="#38bdf8",
        description="Artikulasi baku, tegas, dan berbobot faktual.",
    ),
    "podcast_intimate": EmotionPreset(
        id="podcast_intimate",
        name="Podcast Intim",
        category="gaya",
        speed=0.94,
        pitch=-0.8,
        pause_scale=1.15,
        effect="podcast_eq",
        color="#f43f5e",
        description="Vokal hangat dekat dengan mikrofon (efek proximity).",
    ),
    "radio_announcer": EmotionPreset(
        id="radio_announcer",
        name="Radio Komunikasi / HT",
        category="gaya",
        speed=1.10,
        pitch=0.5,
        pause_scale=0.90,
        effect="radio",
        color="#eab308",
        description="Efek transmisi radio walkie-talkie berkarakter.",
    ),
    "tutorial_instructive": EmotionPreset(
        id="tutorial_instructive",
        name="Tutorial / Edukasi",
        category="gaya",
        speed=0.96,
        pitch=0.0,
        pause_scale=1.10,
        effect="none",
        color="#06b6d4",
        description="Kecepatan pas agar instruksi mudah dicerna langkah demi langkah.",
    ),
    # D. Karakter & Non-Verbal
    "whisper": EmotionPreset(
        id="whisper",
        name="Bisikan Rahasia",
        category="karakter",
        speed=0.88,
        pitch=-1.0,
        pause_scale=1.20,
        effect="whisper",
        color="#a855f7",
        description="Vokal redam desis untuk pesan rahasia atau misterius.",
    ),
    "telephone": EmotionPreset(
        id="telephone",
        name="Panggilan Telepon",
        category="karakter",
        speed=1.02,
        pitch=0.3,
        pause_scale=0.95,
        effect="telephone",
        color="#14b8a6",
        description="Karakter suara melalui filter frekuensi seluler.",
    ),
    "dramatic": EmotionPreset(
        id="dramatic",
        name="Dramatis / Epik",
        category="karakter",
        speed=0.86,
        pitch=-1.0,
        pause_scale=1.45,
        effect="reverb",
        color="#d946ef",
        description="Penekanan kata dramatis untuk momen puncak narasi video.",
    ),
    "energetic_hook": EmotionPreset(
        id="energetic_hook",
        name="Hook Kreator (TikTok / Reels)",
        category="karakter",
        speed=1.22,
        pitch=1.6,
        pause_scale=0.75,
        effect="none",
        color="#ec4899",
        description="Menangkap perhatian penonton dalam 3 detik pertama.",
    ),
}


def get_emotion_preset(emotion_id: str) -> EmotionPreset:
    """Mengambil objek preset emosi berdasarkan ID, default ke neutral."""
    return EMOTION_CATALOG.get(emotion_id, EMOTION_CATALOG["neutral"])


def calculate_scaled_parameters(
    emotion_id: str,
    intensity: float = 100.0,
    base_speed: float = 1.0,
    base_pitch: float = 0.0,
    base_pause: float = 1.0,
) -> dict[str, Any]:
    """
    Interpolasi parameter dari baseline netral menuju preset emosi
    berdasarkan slider intensitas 0-100.
    """
    preset = get_emotion_preset(emotion_id)
    clamped_intensity = max(0.0, min(100.0, float(intensity))) / 100.0

    # Interpolasi kecepatan
    speed_diff = preset.speed - 1.0
    final_speed = base_speed * (1.0 + (speed_diff * clamped_intensity))

    # Interpolasi pitch
    pitch_diff = preset.pitch
    final_pitch = base_pitch + (pitch_diff * clamped_intensity)

    # Interpolasi jeda
    pause_diff = preset.pause_scale - 1.0
    final_pause = base_pause * (1.0 + (pause_diff * clamped_intensity))

    # Efek hanya diaktifkan jika intensitas > 30
    final_effect = preset.effect if clamped_intensity >= 0.3 else "none"

    return {
        "emotion_id": preset.id,
        "emotion_name": preset.name,
        "intensity": clamped_intensity * 100.0,
        "speed": round(final_speed, 3),
        "pitch": round(final_pitch, 2),
        "pause_scale": round(final_pause, 2),
        "effect": final_effect,
        "color": preset.color,
        "is_approximated": True,  # Penanda badge "emosi didekati" untuk engine tanpa embedding diskrit
    }


def list_all_emotion_presets(active_only: bool = False) -> list[dict[str, Any]]:
    """Daftar preset emosi untuk response API, opsional filter hanya yang aktif."""
    preset_list: list[EmotionPreset] = list(EMOTION_CATALOG.values())
    if active_only:
        preset_list = [p for p in preset_list if getattr(p, "is_active", True)]
    return [preset.to_dict() for preset in preset_list]


def sync_emotions_from_db(records: list[Any]) -> None:
    """Sinkronisasi katalog emosi in-memory dari data database."""
    for r in records:
        EMOTION_CATALOG[r.id] = EmotionPreset(
            id=r.id,
            name=r.name,
            category=r.category,
            speed=r.speed,
            pitch=r.pitch,
            pause_scale=r.pause_scale,
            effect=r.effect,
            color=r.color,
            description=r.description or "",
            is_active=getattr(r, "is_active", True),
        )


def register_emotion_preset(preset: EmotionPreset) -> None:
    """Mendaftarkan atau memperbarui preset emosi secara dinamis."""
    EMOTION_CATALOG[preset.id] = preset


def unregister_emotion_preset(emotion_id: str) -> None:
    """Menghapus preset emosi non-netral secara dinamis."""
    if emotion_id in EMOTION_CATALOG and emotion_id != "neutral":
        del EMOTION_CATALOG[emotion_id]
