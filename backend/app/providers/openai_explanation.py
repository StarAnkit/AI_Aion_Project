import json

from app.schemas.explanation import GeneratedExplanation
from app.services.artwork_explanation import ApprovedArtworkInput


class OpenAIExplanationProvider:
    """Optional Responses API adapter. It sends a URL; it never fetches image bytes."""

    def __init__(self, *, api_key: str | None, model: str) -> None:
        self._api_key = api_key
        self._model = model

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def explain(self, artwork: ApprovedArtworkInput) -> GeneratedExplanation:
        if not self._api_key:
            raise RuntimeError("OpenAI provider is not configured")
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key)
        response = client.responses.parse(
            model=self._model,
            store=False,
            max_output_tokens=1200,
            input=[
                {
                    "role": "system",
                    "content": _SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Approved museum facts:\n"
                            + json.dumps(_fact_payload(artwork), ensure_ascii=True),
                        },
                        {
                            "type": "input_image",
                            "image_url": artwork.image_url,
                            "detail": "low",
                        },
                    ],
                },
            ],
            text_format=GeneratedExplanation,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("OpenAI returned no structured explanation")
        return parsed


def _fact_payload(artwork: ApprovedArtworkInput) -> dict[str, str | None]:
    return {
        "title": artwork.title,
        "creator": artwork.creator_display,
        "date": artwork.date_text,
        "medium": artwork.medium,
        "culture": artwork.culture,
        "department": artwork.department,
    }


_SYSTEM_PROMPT = """You explain one museum artwork using only the supplied approved facts and image.
Keep verified facts separate: do not repeat them as newly discovered visual claims.
visual_observations must contain only directly visible features. inferences must be cautious,
clearly interpretive, and never identify a person, event, place, artist, or date from appearance.
If the image or facts do not support a useful explanation, set insufficient_context true and say
what is missing. State uncertainty explicitly. Do not use outside knowledge, browse, or claim that
the generated prose is CC0. Use plain, accessible language."""
