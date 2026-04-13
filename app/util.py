from openai import OpenAI
from sqlalchemy.orm import Session
from crud import update_user_task
from providers import get_base_url, get_default_model, PROVIDERS
from dotenv import load_dotenv

import os
import time
from openai import AuthenticationError, RateLimitError, OpenAIError


def perform_query(task_id: int, text: str, languages: list, db: Session, llm_config: dict = None):
    load_dotenv()

    provider = (llm_config or {}).get("provider", "openai")
    model = (llm_config or {}).get("model") or get_default_model(provider)
    cfg = PROVIDERS.get(provider, {})
    api_key = (llm_config or {}).get("api_key") or os.getenv(cfg.get("env_key", "OPENAI_API_KEY"))
    base_url = get_base_url(provider)

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
    except Exception as e:
        update_user_task(db, task_id, {lang: f"Error: {e}" for lang in languages}, status="Failed")
        return

    queries = {}
    try:
        for lang in languages:
            retries = 3
            while retries > 0:
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": f"You are a helpful assistant that translates text into {lang}."},
                            {"role": "user", "content": text}
                        ],
                        max_tokens=1000
                    )
                    translated_text = response.choices[0].message.content.strip()
                    queries[lang] = translated_text
                    break
                except AuthenticationError as e:
                    print(f"Authentication error: {e}")
                    queries = {l: "Error: Invalid API key or authentication failed" for l in languages}
                    update_user_task(db, task_id, queries, status="Failed")
                    return
                except RateLimitError as e:
                    print(f"Rate limit exceeded for {lang}: {e}. Retrying...")
                    retries -= 1
                    time.sleep(2 ** (3 - retries))
                except OpenAIError as e:
                    print(f"Error translating to {lang}: {e}")
                    queries[lang] = f"Error: {e}"
                    break
            else:
                queries[lang] = "Error: Failed after multiple retries"

        status = "Completed" if all(not v.startswith("Error:") for v in queries.values()) else "Completed with errors"
        update_user_task(db, task_id, queries, status=status)
    except Exception as e:
        print(f"Unexpected error in perform_query: {e}")
        for lang in languages:
            if lang not in queries:
                queries[lang] = f"Error: {e}"
        update_user_task(db, task_id, queries, status="Failed")
