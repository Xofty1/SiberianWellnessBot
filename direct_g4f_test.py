import asyncio
import g4f
import time
import sys

async def test_provider(provider_class, messages):
    """Test a specific provider and return result"""
    start_time = time.time()
    result = {
        "provider": provider_class.__name__,
        "success": False,
        "response": None,
        "error": None,
        "time_taken": 0
    }
    
    try:
        print(f"Testing {provider_class.__name__}...", end="", flush=True)
        response = await asyncio.wait_for(
            asyncio.to_thread(
                g4f.ChatCompletion.create,
                model="gpt-3.5-turbo",
                provider=provider_class,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            ),
            timeout=25
        )
        
        result["success"] = True
        result["response"] = response
        print(" ✓ Success")
    except Exception as e:
        result["error"] = str(e)
        print(f" ✗ Failed: {str(e)[:100]}...")
    
    result["time_taken"] = time.time() - start_time
    return result

async def test_g4f():
    print("\n" + "="*50)
    print("G4F (GPT for Free) Provider Test")
    print("="*50)
    
    # Simple test message
    messages = [
        {"role": "user", "content": "Напиши короткое стихотворение о программировании"}
    ]
    
    # Providers to test - these tend to be more reliable
    providers_to_test = [
        g4f.Provider.Bing,
        g4f.Provider.HuggingChat,
        g4f.Provider.GptGo,
        g4f.Provider.DeepAi,
        g4f.Provider.OpenaiChat,
        g4f.Provider.Gemini,
        g4f.Provider.You,
        g4f.Provider.ChatGpt,
        g4f.Provider.GeminiPro,
        g4f.Provider.Aichat,
        g4f.Provider.Koala
    ]
    
    # Store results
    results = []
    
    # Test each provider
    print("\nTesting individual providers:")
    print("-"*50)
    for provider in providers_to_test:
        result = await test_provider(provider, messages)
        results.append(result)
        await asyncio.sleep(1)  # Small delay between requests
    
    # Test auto provider selection
    print("\nTesting automatic provider selection:")
    print("-"*50)
    try:
        print("Testing automatic selection...", end="", flush=True)
        response = await asyncio.wait_for(
            asyncio.to_thread(
                g4f.ChatCompletion.create,
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            ),
            timeout=30
        )
        print(" ✓ Success")
        print("\nResponse from automatic selection:")
        print("="*50)
        print(response)
        print("="*50)
    except Exception as e:
        print(f" ✗ Failed: {str(e)}")
    
    # Display successful providers
    successful = [r for r in results if r["success"]]
    if successful:
        print(f"\n{len(successful)} working providers found:")
        for i, result in enumerate(successful, 1):
            provider_name = result["provider"]
            time_taken = result["time_taken"]
            print(f"{i}. {provider_name} (responded in {time_taken:.2f} seconds)")
        
        # Display one successful response as an example
        example = successful[0]
        print(f"\nExample response from {example['provider']}:")
        print("="*50)
        print(example["response"])
        print("="*50)
    else:
        print("\nNo working providers found. Possible reasons:")
        print("- Network connectivity issues")
        print("- Provider services are temporarily down")
        print("- Your IP might be blocked or rate-limited")
        print("- VPN might be required for some providers")
    
    # Recommendations for generate.py
    if successful:
        print("\nRecommended providers for your generate.py file:")
        print("-"*50)
        providers_code = "provider_classes = [\n"
        for result in successful:
            providers_code += f"    g4f.Provider.{result['provider']},\n"
        providers_code += "]"
        print(providers_code)

if __name__ == "__main__":
    try:
        asyncio.run(test_g4f())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(0) 