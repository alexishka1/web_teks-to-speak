"""
Pemetaan 22 Preset Emosi TaSTP ke Instruksi Gaya Bicara Gemini TTS (speech_metadata.style).
Struktur data terpusat untuk kontrol akting dan intonasi alami dalam Bahasa Indonesia/Inggris.
"""

GEMINI_EMOTION_STYLES: dict[str, dict[str, str]] = {
    "neutral": {
        "low": "calm, natural conversational tone in Indonesian",
        "medium": "clear, neutral, and balanced conversational delivery in Indonesian",
        "high": "extremely steady, neutral, and articulate speech in Indonesian",
    },
    "happy": {
        "low": "slightly cheerful and pleasant in Indonesian",
        "medium": "cheerful, warm, and uplifting tone in Indonesian",
        "high": "very joyful, enthusiastic, and bubbling with happiness in Indonesian",
    },
    "sad": {
        "low": "slightly somber and soft-spoken in Indonesian",
        "medium": "sad, sorrowful, and quiet reflective delivery in Indonesian",
        "high": "deeply heartbreaking, mournful, and emotional sorrow in Indonesian",
    },
    "angry": {
        "low": "stern and firm tone in Indonesian",
        "medium": "angry, authoritative, and sharp articulation in Indonesian",
        "high": "fierce, furious, intense and commanding rage in Indonesian",
    },
    "fearful": {
        "low": "mildly hesitant and uneasy tone in Indonesian",
        "medium": "fearful, trembling, and anxious delivery in Indonesian",
        "high": "terrified, breathless, and deeply panicking in Indonesian",
    },
    "disgusted": {
        "low": "mildly displeased and skeptical tone in Indonesian",
        "medium": "disgusted, dismissive, and sneering delivery in Indonesian",
        "high": "strongly repulsed, scornful, and contemptuous tone in Indonesian",
    },
    "surprised": {
        "low": "mildly surprised and curious in Indonesian",
        "medium": "surprised, amazed, with raised pitch of astonishment in Indonesian",
        "high": "shocked, astonished, and gasping in disbelief in Indonesian",
    },
    "calm": {
        "low": "relaxed and peaceful speech in Indonesian",
        "medium": "calm, soothing, serene meditation tone in Indonesian",
        "high": "deeply tranquil, tranquilizing, and serene whisper-like calm in Indonesian",
    },
    "enthusiastic": {
        "low": "positive and energized tone in Indonesian",
        "medium": "enthusiastic, spirited, and motivational speech in Indonesian",
        "high": "overwhelmingly excited, vibrant, and bursting with energy in Indonesian",
    },
    "somber": {
        "low": "subdued and serious tone in Indonesian",
        "medium": "somber, grave, solemn, and respectful mourning in Indonesian",
        "high": "deeply grieving, heavily weighted, and grief-stricken delivery in Indonesian",
    },
    "hopeful": {
        "low": "gently optimistic tone in Indonesian",
        "medium": "hopeful, inspiring, and uplifting reassurance in Indonesian",
        "high": "radiantly optimistic, inspiring, and deeply passionate hope in Indonesian",
    },
    "anxious": {
        "low": "mildly nervous and hurried pace in Indonesian",
        "medium": "anxious, uneasy, and jittery pacing in Indonesian",
        "high": "fretful, intensely stressed, nervous, and flustered delivery in Indonesian",
    },
    "confident": {
        "low": "assured and steady speech in Indonesian",
        "medium": "confident, persuasive, and authoritative presence in Indonesian",
        "high": "unshakably commanding, bold, charismatic, and powerful in Indonesian",
    },
    "storytelling": {
        "low": "narrative, engaging cadence in Indonesian",
        "medium": "expressive storytelling narrator, rich with descriptive cadence in Indonesian",
        "high": "magical, theatrical, and deeply immersive audiobook narrator in Indonesian",
    },
    "news_anchor": {
        "low": "informative broadcast tone in Indonesian",
        "medium": "professional television news anchor, formal, crisp, and objective in Indonesian",
        "high": "authoritative national news broadcast anchor, urgent, precise, and formal in Indonesian",
    },
    "podcast_intimate": {
        "low": "relaxed host tone in Indonesian",
        "medium": "intimate podcast host, close-mic warmth, friendly and personal in Indonesian",
        "high": "deeply personal, late-night radio host, whisper-warm and deeply connected in Indonesian",
    },
    "radio_announcer": {
        "low": "clear public announcer voice in Indonesian",
        "medium": "dynamic FM radio DJ announcer, punchy and rhythmic cadence in Indonesian",
        "high": "hyper-energetic commercial radio DJ, high-tempo, crisp, and driving punch in Indonesian",
    },
    "tutorial_instructive": {
        "low": "clear step-by-step guidance in Indonesian",
        "medium": "patient instructional teacher, articulate, methodical, and easy to follow in Indonesian",
        "high": "exceptionally patient masterclass instructor, crystal-clear and encouraging in Indonesian",
    },
    "whisper": {
        "low": "soft, lowered voice in Indonesian",
        "medium": "hushed whisper, conspiratorial and intimate in Indonesian",
        "high": "pure breathless secret whisper, very close and confidential in Indonesian",
    },
    "telephone": {
        "low": "conversational phone call tone in Indonesian",
        "medium": "clear phone call voice, conversational and direct in Indonesian",
        "high": "urgent phone call transmission, fast and direct in Indonesian",
    },
    "dramatic": {
        "low": "cinematic and deliberate tone in Indonesian",
        "medium": "dramatic movie trailer voice, epic and suspenseful in Indonesian",
        "high": "epic theatrical climax narration, thunderous and profound gravity in Indonesian",
    },
    "energetic_hook": {
        "low": "catchy upbeat intro tone in Indonesian",
        "medium": "creator viral hook delivery, attention-grabbing, punchy, and modern in Indonesian",
        "high": "explosive viral creator hook, irresistible energy and immediate punch in Indonesian",
    },
}


def get_gemini_style_instruction(emotion_id: str, intensity: float = 100.0) -> str:
    """
    Mengambil instruksi gaya akting untuk dikirim ke speech_metadata.style.
    Skala intensitas:
    < 40.0: low ('slightly...')
    40.0 - 75.0: medium (standar terkalibrasi)
    > 75.0: high ('very...' / ekspresif penuh)
    """
    norm_id = emotion_id.lower().strip()
    styles = GEMINI_EMOTION_STYLES.get(norm_id, GEMINI_EMOTION_STYLES["neutral"])
    if intensity < 40.0:
        return styles["low"]
    elif intensity > 75.0:
        return styles["high"]
    return styles["medium"]
