import openai
from sqlalchemy.orm import Session
from crud import update_user_task
from dotenv import load_dotenv

import time
from openai.error import RateLimitError, OpenAIError


def perform_query(task_id: int, text: str, languages: list, db: Session):
    queries = {}
    for lang in languages:
        retries = 3
        while retries > 0:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",  # Update model ID as needed
                    messages=[
                        {"role": "system", "content": f"You are a helpful assistant that translates text into {lang}."},
                        {"role": "user", "content": text}
                    ],
                    max_tokens=1000
                )
                translated_text = response['choices'][0]['message']['content'].strip()
                queries[lang] = translated_text
                break  # Exit the retry loop if successful
            except RateLimitError as e:
                print(f"Rate limit exceeded for {lang}: {e}. Retrying...")
                retries -= 1
                time.sleep(2 ** (3 - retries))  # Exponential backoff
            except OpenAIError as e:
                print(f"Error translating to {lang}: {e}")
                queries[lang] = f"Error: {e}"
                break
        else:
            # If retries are exhausted, mark the error
            queries[lang] = "Error: Failed after multiple retries"
    
    # Update the database after processing all languages
    update_user_task(db, task_id, queries)
