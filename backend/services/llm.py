"""
LLM service using Groq Llama.
Swap this module to change LLM provider.
"""

from groq import Groq

# BUMA personality prompt — kept here so it's easy to tune.
SYSTEM_PROMPT = """\
You are BUMA, a friendly owl who teaches languages to children aged 5-7.

Rules:
- Keep responses under 40 words (children's attention span)
- Use simple, child-friendly language
- Mix French/English/Arabic when teaching
- Always be encouraging and patient
- End with a question to keep conversation going
- Use "Hoot hoot!" to sound like an owl
- Be playful and fun!

Example:
Child: "What's dog in French?"
BUMA: "Hoot hoot! Great question! A dog is 'un chien' in French. \
Can you say 'un chien'? It sounds like 'uhn shee-en'! Do you have a dog?"

Important:
- Never use complex words
- Always stay positive
- Make learning feel like playing
- Celebrate every attempt
"""

# Instant responses for very common greetings (skip LLM round-trip).
QUICK_RESPONSES: dict[str, str] = {
    "bonjour": "Hoot hoot! Bonjour mon ami! How are you feeling today? Comment ça va?",
    "hello": "Hoot hoot! Hello my friend! Ready to learn something fun? Prêt?",
    "hi": "Hoot hoot! Hi there! Want to learn a new word? Tu veux apprendre?",
    "bye": "Au revoir my friend! Goodbye! Come back soon! À bientôt!",
    "thank you": "You're welcome! De rien! I love helping you learn!",
    "merci": "De rien! You're so polite! Tu es très poli!",
}


class LLMService:
    """Generate child-friendly responses using Groq Llama."""

    MODEL = "llama-3.1-70b-versatile"

    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    def respond(
        self,
        user_text: str,
        history: list[dict] | None = None,
    ) -> str:
        """
        Return BUMA's reply to *user_text*.

        *history* is a list of dicts with keys ``question`` and ``response``
        (most-recent last) used for conversational context.

        Returns the response text.
        """
        # Check quick cache first
        normalised = user_text.lower().strip()
        if normalised in QUICK_RESPONSES:
            return QUICK_RESPONSES[normalised]

        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Inject recent conversation context
        if history:
            for turn in history:
                messages.append({"role": "user", "content": turn["question"]})
                messages.append({"role": "assistant", "content": turn["response"]})

        messages.append({"role": "user", "content": user_text})

        completion = self.client.chat.completions.create(
            model=self.MODEL,
            messages=messages,
            max_tokens=80,  # short replies = lower latency
            temperature=0.8,
            top_p=0.9,
        )

        return completion.choices[0].message.content.strip()
