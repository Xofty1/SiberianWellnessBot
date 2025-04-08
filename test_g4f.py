import asyncio
from generate import ask_gpt

async def test_g4f():
    print("Тестирование G4F сервиса...")
    
    # Тестовый запрос
    test_query = "Привет! Как тебя зовут и что ты умеешь?"
    
    print(f"Отправка запроса: {test_query}")
    response = await ask_gpt(test_query)
    
    print("\nОтвет от G4F:")
    print("="*50)
    print(response)
    print("="*50)
    
    # Тест с контекстом
    test_context = "Информация о компании: ООО 'ТехноСервис' - компания, основанная в 2010 году, занимающаяся разработкой программного обеспечения."
    test_query_with_context = "Когда была основана компания и чем она занимается?"
    
    print(f"\nОтправка запроса с контекстом: {test_query_with_context}")
    response_with_context = await ask_gpt(test_query_with_context, test_context)
    
    print("\nОтвет от G4F (с контекстом):")
    print("="*50)
    print(response_with_context)
    print("="*50)

if __name__ == "__main__":
    asyncio.run(test_g4f()) 