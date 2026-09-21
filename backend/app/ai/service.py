from app.providers.base import AIService

class OpenAIAnalysisService(AIService):
    async def explain(self, payload: dict) -> str:
        return ('Interpretation is generated only from verified structured data supplied by the backend. '
                'It is not a prediction, guarantee, or investment advice.')
