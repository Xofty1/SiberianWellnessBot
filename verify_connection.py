import requests
import asyncio
import sys
import time

def check_site(url, timeout=5):
    """Check if a site is reachable"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        elapsed = time.time() - start_time
        
        if response.status_code < 400:
            print(f"✓ {url} - Доступен (статус: {response.status_code}, время: {elapsed:.2f}с)")
            return True
        else:
            print(f"✗ {url} - Недоступен (статус: {response.status_code}, время: {elapsed:.2f}с)")
            return False
    except Exception as e:
        print(f"✗ {url} - Ошибка: {str(e)}")
        return False

async def main():
    print("\n" + "="*60)
    print("Проверка подключения к сервисам, используемым в G4F")
    print("="*60)
    
    sites = [
        "https://www.bing.com",
        "https://huggingface.co",
        "https://gptgo.ai",
        "https://deepai.org",
        "https://you.com",
        "https://chatgpt.com",
        "https://www.google.com",
        "https://gemini.google.com",
        "https://openai.com"
    ]
    
    print("\nПроверка доступа к основным сайтам:")
    print("-"*60)
    
    # Check sites
    successful = 0
    for site in sites:
        if check_site(site):
            successful += 1
    
    # Summary
    print("\nРезультаты проверки:")
    print(f"- Доступно: {successful}/{len(sites)} сайтов")
    
    if successful < len(sites) * 0.5:
        print("\nРекомендации:")
        print("- Проверьте подключение к интернету")
        print("- Некоторые сервисы могут быть заблокированы вашим провайдером")
        print("- Попробуйте использовать VPN для доступа к заблокированным сервисам")
        print("- Убедитесь, что ваш брандмауэр не блокирует исходящие соединения")
    elif successful < len(sites):
        print("\nРекомендации:")
        print("- Попробуйте использовать провайдеров, сайты которых доступны")
        print("- Для доступа к заблокированным сервисам может потребоваться VPN")
    else:
        print("\nВсе сайты доступны. G4F должен работать корректно.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПроверка прервана пользователем")
        sys.exit(0) 