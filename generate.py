from openai import AsyncOpenAI, OpenAI
from config import AI_TOKEN

# Создаем клиента с минимальными параметрами, чтобы избежать ошибки
# client = AsyncOpenAI(
#     api_key=AI_TOKEN,
#     base_url="https://openrouter.ai/api/v1"
# )

client = AsyncOpenAI(
    api_key=AI_TOKEN,
    base_url="https://openrouter.ai/api/v1"
)

async def ai_generate(text: str, context: str = None):
    messages = []
    
    if context:
        messages.append({
            "role": "system",
            "content": "Вы - полезный ассистент, который отвечает на вопросы на основе предоставленного контекста. Отвечайте точно и информативно."
        })
        messages.append({
            "role": "user",
            "content": f"Контекст: {context}\n\nВопрос: {text}"
        })
    else:
        messages.append({
            "role": "user",
            "content": text
        })
    
    try:
        completion = await client.chat.completions.create(
            model="meta-llama/llama-3.3-8b-instruct:free",
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Ошибка при вызове OpenAI API: {str(e)}")
        # Запасной вариант для ответа, если API недоступен
        return "Извините, в данный момент я не могу сгенерировать ответ. Попробуйте позже."

async def ask_gpt(prompt: str, context: str = None):
    """Отправляет запрос в ChatGPT с возможностью добавления контекста."""
    try:
        response = await ai_generate(prompt, context)
        return response.strip()
    except Exception as e:
        return f"Произошла ошибка при генерации ответа: {str(e)}"