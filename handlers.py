from aiogram import F, Router
from aiogram.types import Message, Document, PhotoSize
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import os
import tempfile
import aiohttp
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

from generate import ask_gpt
from document_processor import DocumentProcessor
from data_loader import DataLoader

router = Router()

# Создаем экземпляр DataLoader только один раз при старте
data_loader = None

# Указываем сайт для поиска
SEARCH_SITE = "ru.siberianhealth.com/ru/"

# Инициализация data_loader отложена до запуска бота
async def init_data_loader():
    global data_loader
    data_loader = DataLoader()
    await data_loader.process_directory()
    return data_loader

class Gen(StatesGroup):
    wait = State()
    context = State()

class AddInfo(StatesGroup):
    waiting_for_info = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Добро пожаловать! Я тут для того, чтобы помочь разобраться в компании Siberian Wellenss, ответить на вопросы о здоровье и рассказать о том как построить бизнес. Можешь задавать свои вопросы! Будем разбираться!')

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
    await message.answer(response, parse_mode="Markdown")
    await state.clear()

@router.message(Command("addinfo"))
async def cmd_addinfo(message: Message, state: FSMContext):
    await message.answer("Отправьте информацию, которую должен знать бот. Мы проверим её и добавим.")
    await state.set_state(AddInfo.waiting_for_info)

@router.message(AddInfo.waiting_for_info)
async def handle_new_info(message: Message, state: FSMContext):
    # Здесь можно добавить логику для проверки и сохранения информации
    # Например, сохранить в текстовый файл в директории training_data/text/
    info_text = message.text
    
    # Создаем директорию, если её нет
    text_dir = os.path.join("training_data", "text")
    os.makedirs(text_dir, exist_ok=True)
    
    # Генерируем уникальное имя файла на основе timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"user_info_{timestamp}.txt"
    file_path = os.path.join(text_dir, filename)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(info_text)
        
        await message.answer("Спасибо! Ваша информация получена и будет проверена администратором.")
    except Exception as e:
        await message.answer(f"Произошла ошибка при сохранении информации: {str(e)}")
    
    await state.clear()

@router.message(F.text)  # Добавляем фильтр для текстовых сообщений
async def handle_message(message: Message, state: FSMContext):
    global data_loader
    
    # Проверка инициализации data_loader
    if data_loader is None:
        await message.answer('Загрузка базы знаний. Пожалуйста, подождите...')
        try:
            data_loader = await init_data_loader()
        except Exception as e:
            await message.answer(f'Ошибка загрузки базы знаний: {str(e)}, parse_mode="Markdown"')
            return
    
    await state.set_state(Gen.wait)
    
    try:
        # Ищем релевантную информацию в базе знаний
        relevant_context = data_loader.search_knowledge_base(message.text)
        
        if relevant_context:
            # Если найдена релевантная информация, используем ее
            response = await ask_gpt(message.text, relevant_context, "siberian_health")
        else:
            response = await ask_gpt(message.text, system_prompt_type="siberian_health")
        
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f'Произошла ошибка: {str(e)}', parse_mode="Markdown")
    finally:
        await state.clear()