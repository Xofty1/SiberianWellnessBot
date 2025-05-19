from aiogram import F, Router
from aiogram.types import Message, Document, PhotoSize
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import os
import tempfile
import aiohttp
from bs4 import BeautifulSoup
import re
import json

from generate import ask_gpt
from document_processor import DocumentProcessor
from data_loader import DataLoader

router = Router()

# Создаем экземпляр DataLoader только один раз при старте
data_loader = None

# Указываем сайт для поиска
SEARCH_SITE = "ru.siberianhealth.com/ru/"

# Заголовки для имитации браузера
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Инициализация data_loader отложена до запуска бота
async def init_data_loader():
    global data_loader
    data_loader = DataLoader()
    await data_loader.process_directory()
    return data_loader

class Gen(StatesGroup):
    wait = State()
    context = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Добро пожаловать! Я бот, обученный на специальных данных. Задайте мне вопрос, и я постараюсь на него ответить.')

@router.message(Gen.wait)
async def stop_flood(message: Message):
    await message.answer('Подождите, ваш запрос генерируется.')

@router.message(F.document)
async def handle_document(message: Message, state: FSMContext):
    await state.set_state(Gen.wait)
    doc = message.document
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{doc.file_name.split('.')[-1]}") as temp_file:
        await message.bot.download(doc, destination=temp_file.name)
        
        # Process document
        file_type = doc.file_name.split('.')[-1].lower()
        extracted_text = await DocumentProcessor.process_document(temp_file.name, file_type)
        
        # Clean up
        os.unlink(temp_file.name)
        
        if extracted_text:
            # Store context in state
            await state.update_data(context=extracted_text)
            await message.answer("Документ обработан. Теперь вы можете задать вопрос по его содержимому.")
            await state.set_state(Gen.context)
        else:
            await message.answer("Не удалось обработать документ. Пожалуйста, попробуйте другой файл.")
            await state.clear()

@router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext):
    await state.set_state(Gen.wait)
    photo = message.photo[-1]  # Get the largest photo
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        await message.bot.download(photo, destination=temp_file.name)
        
        # Process image
        extracted_text = await DocumentProcessor.process_image(temp_file.name)
        
        # Clean up
        os.unlink(temp_file.name)
        
        if extracted_text:
            # Store context in state
            await state.update_data(context=extracted_text)
            await message.answer("Изображение обработано. Теперь вы можете задать вопрос по его содержимому.")
            await state.set_state(Gen.context)
        else:
            await message.answer("Не удалось обработать изображение. Пожалуйста, попробуйте другое изображение.")
            await state.clear()

@router.message(Gen.context)
async def handle_context_question(message: Message, state: FSMContext):
    await state.set_state(Gen.wait)
    data = await state.get_data()
    context = data.get('context', '')
    
    # Combine context with question
    prompt = f"Контекст: {context}\n\nВопрос: {message.text}"
    response = await ask_gpt(prompt)
    await message.answer(response)
    await state.clear()

async def search_web(query: str) -> str:
    """Поиск информации на сайте Siberian Health"""
    async with aiohttp.ClientSession() as session:
        try:
            # Формируем URL для поиска
            search_url = f"https://{SEARCH_SITE}search/?q={query}"
            
            async with session.get(search_url, headers=HEADERS) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    results = []
                    
                    # Ищем результаты поиска
                    search_results = soup.find_all('div', class_='search-result-item')
                    
                    if not search_results:
                        # Если не нашли результаты в стандартном формате, ищем любые релевантные блоки
                        search_results = soup.find_all(['div', 'article'], class_=lambda x: x and ('product' in x.lower() or 'article' in x.lower() or 'content' in x.lower()))
                    
                    for result in search_results[:3]:  # Берем первые 3 результата
                        # Извлекаем заголовок
                        title = result.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'div'], class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower()))
                        if not title:
                            title = result.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a'])
                        
                        # Извлекаем описание
                        description = result.find(['p', 'div'], class_=lambda x: x and ('description' in x.lower() or 'text' in x.lower() or 'content' in x.lower()))
                        if not description:
                            description = result.find(['p', 'div'])
                        
                        # Извлекаем ссылку
                        link = result.find('a')
                        
                        result_text = ""
                        if title:
                            result_text += f"Заголовок: {title.get_text(strip=True)}\n"
                        if link and link.get('href'):
                            result_text += f"Ссылка: {link['href']}\n"
                        if description:
                            result_text += f"Описание: {description.get_text(strip=True)}\n"
                        
                        if result_text:
                            results.append(result_text)
                    
                    if results:
                        return "\n\n".join(results)
                    
                    # Если не нашли результатов в поиске, пробуем получить главную страницу
                    main_url = f"https://{SEARCH_SITE}"
                    async with session.get(main_url, headers=HEADERS) as main_response:
                        if main_response.status == 200:
                            main_html = await main_response.text()
                            main_soup = BeautifulSoup(main_html, 'html.parser')
                            
                            # Ищем релевантный контент на главной странице
                            content = main_soup.find_all(['div', 'article', 'section'], class_=lambda x: x and ('content' in x.lower() or 'main' in x.lower()))
                            
                            if content:
                                return f"Найдена информация на главной странице:\n{content[0].get_text(strip=True)[:500]}..."
                    
                    return "Не удалось найти информацию на сайте."
                else:
                    return f"Ошибка доступа к сайту. Статус: {response.status}"
        except Exception as e:
            return f"Произошла ошибка при поиске: {str(e)}"

@router.message()
async def handle_message(message: Message, state: FSMContext):
    global data_loader
    
    # Проверка инициализации data_loader
    if data_loader is None:
        await message.answer('Загрузка базы знаний. Пожалуйста, подождите...')
        try:
            data_loader = await init_data_loader()
        except Exception as e:
            await message.answer(f'Ошибка загрузки базы знаний: {str(e)}')
            return
    
    await state.set_state(Gen.wait)
    
    try:
        # Ищем релевантную информацию в базе знаний
        relevant_context = data_loader.search_knowledge_base(message.text)
        
        if relevant_context:
            # Если найдена релевантная информация, используем ее
            response = await ask_gpt(message.text, relevant_context, "siberian_health")
        else:
            # Если нет релевантной информации, ищем на указанном сайте
            web_results = await search_web(message.text)
            if web_results and "Не удалось найти информацию" not in web_results:
                # Используем результаты поиска как контекст
                response = await ask_gpt(message.text, web_results, "siberian_health")
            else:
                # Если поиск не дал результатов, просто отвечаем на вопрос
                response = await ask_gpt(message.text, system_prompt_type="siberian_health")
        
        await message.answer(response)
    except Exception as e:
        await message.answer(f'Произошла ошибка: {str(e)}')
    finally:
        await state.clear()