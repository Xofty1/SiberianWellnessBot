import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config import TG_TOKEN
from handlers import router, init_data_loader

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        # Инициализируем бота и диспетчер
        bot = Bot(token=TG_TOKEN)
        dp = Dispatcher()
        dp.include_router(router)
        
        # Загружаем базу знаний
        logger.info("Загрузка базы знаний...")
        await init_data_loader()
        logger.info("База знаний загружена")
        
        # Запускаем бота
        logger.info("Бот запущен")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Произошла ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())