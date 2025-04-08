import asyncio
import argparse
import sys
import os
from data_loader import DataLoader

async def train_bot():
    parser = argparse.ArgumentParser(description='Обучение бота на данных.')
    parser.add_argument('--data-dir', type=str, default='training_data',
                      help='Директория с обучающими данными (по умолчанию: training_data)')
    
    args = parser.parse_args()
    
    print(f"Начинаю обработку данных из директории: {args.data_dir}")
    
    # Проверяем наличие директории с данными
    if not os.path.exists(args.data_dir):
        os.makedirs(args.data_dir, exist_ok=True)
        print(f"Создана директория {args.data_dir}")
        print(f"Пожалуйста, добавьте ваши файлы в следующие поддиректории:")
        print(f"  - {os.path.join(args.data_dir, 'pdf')} для PDF файлов")
        print(f"  - {os.path.join(args.data_dir, 'images')} для изображений")
        print(f"  - {os.path.join(args.data_dir, 'text')} для текстовых файлов")
        return
    
    # Инициализируем загрузчик данных
    loader = DataLoader(args.data_dir)
    
    # Обрабатываем все файлы
    knowledge_base = await loader.process_directory()
    
    # Выводим статистику
    pdf_count = sum(1 for _, data in knowledge_base.items() if data['type'] == 'pdf')
    img_count = sum(1 for _, data in knowledge_base.items() if data['type'] == 'image')
    text_count = sum(1 for _, data in knowledge_base.items() if data['type'] == 'text')
    
    print("\n=== Результаты обработки ===")
    print(f"Обработано PDF файлов: {pdf_count}")
    print(f"Обработано изображений: {img_count}")
    print(f"Обработано текстовых файлов: {text_count}")
    print(f"Всего файлов в базе знаний: {len(knowledge_base)}")
    print(f"\nБаза знаний сохранена в: {os.path.join(args.data_dir, 'knowledge_base.json')}")
    print("\nТеперь бот готов отвечать на вопросы с использованием этих данных.")

if __name__ == "__main__":
    asyncio.run(train_bot()) 