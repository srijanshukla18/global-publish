
import litellm
from dotenv import load_dotenv
import os

load_dotenv()

class PlatformAdapter:
    def __init__(self, model="gemini/gemini-2.5-pro", api_key=None):
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def adapt_content(self, full_prompt):
        """
        Adapts the content to a specific platform based on the full prompt.
        """
        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": full_prompt}],
            api_key=self.api_key
        )
        return response.choices[0].message.content
