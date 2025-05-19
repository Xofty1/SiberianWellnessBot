from aiogram import F, Router
from aiogram.types import Message, Document, PhotoSize
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
import os
import tempfile

from generate import ask_gpt
from document_processor import DocumentProcessor
from data_loader import DataLoader

router = Router()

# Создаем экземпляр DataLoader только один раз при старте
data_loader = None

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

def escape_markdown(text: str) -> str:
    """Экранирует специальные символы для Markdown V2."""
    special_chars = ['_', '*', '[', ']', '(', ')', '`', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

@router.message(Gen.context)
async def handle_context_question(message: Message, state: FSMContext):
    await state.set_state(Gen.wait)
    data = await state.get_data()
    context = data.get('context', '')
    
    # Combine context with question
    prompt = f"Контекст: {context}\n\nВопрос: {message.text}"
    response = await ask_gpt(prompt)
    escaped_response = escape_markdown(response)
    await message.answer(escaped_response, parse_mode=ParseMode.MARKDOWN_V2)
    await state.clear()

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
            response = await ask_gpt(message.text, relevant_context)
        else:
            # Если нет релевантной информации, просто отвечаем на вопрос
            response = await ask_gpt(message.text)
        
        escaped_response = escape_markdown(response)
        await message.answer(escaped_response, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await message.answer(f'Произошла ошибка: {str(e)}')
    finally:
        await state.clear()