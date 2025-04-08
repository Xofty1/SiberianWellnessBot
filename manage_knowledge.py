import asyncio
import argparse
import os
import json
from data_loader import DataLoader

async def list_knowledge_base(data_dir: str):
    """Отображает содержимое базы знаний."""
    loader = DataLoader(data_dir)
    if not os.path.exists(loader.kb_file):
        print(f"База знаний не найдена в {loader.kb_file}")
        return
        
    with open(loader.kb_file, 'r', encoding='utf-8') as f:
        kb = json.load(f)
    
    if not kb:
        print("База знаний пуста")
        return
        
    print(f"\n=== База знаний ({len(kb)} файлов) ===")
    
    pdf_files = [f for f, data in kb.items() if data['type'] == 'pdf']
    img_files = [f for f, data in kb.items() if data['type'] == 'image']
    txt_files = [f for f, data in kb.items() if data['type'] == 'text']
    
    if pdf_files:
        print("\nPDF файлы:")
        for f in pdf_files:
            print(f"  - {f}")
    
    if img_files:
        print("\nИзображения:")
        for f in img_files:
            print(f"  - {f}")
    
    if txt_files:
        print("\nТекстовые файлы:")
        for f in txt_files:
            print(f"  - {f}")

async def clear_knowledge_base(data_dir: str):
    """Очищает базу знаний."""
    loader = DataLoader(data_dir)
    if not os.path.exists(loader.kb_file):
        print(f"База знаний не найдена в {loader.kb_file}")
        return
        
    confirm = input("Вы уверены, что хотите очистить всю базу знаний? (да/нет): ")
    if confirm.lower() != 'да':
        print("Операция отменена")
        return
        
    # Сохраняем пустую базу знаний
    loader.knowledge_base = {}
    loader.save_knowledge_base()
    print("База знаний очищена")

async def test_query(data_dir: str, query: str):
    """Тестирует поиск по базе знаний."""
    loader = DataLoader(data_dir)
    if not os.path.exists(loader.kb_file):
        print(f"База знаний не найдена в {loader.kb_file}")
        return
        
    result = loader.search_knowledge_base(query)
    if result:
        print("\n=== Найденная информация ===")
        print(result)
    else:
        print("По вашему запросу ничего не найдено")

async def main():
    parser = argparse.ArgumentParser(description='Управление базой знаний бота.')
    parser.add_argument('--data-dir', type=str, default='training_data',
                      help='Директория с данными (по умолчанию: training_data)')
    
    subparsers = parser.add_subparsers(dest='command', help='Команда')
    
    # Команда list
    list_parser = subparsers.add_parser('list', help='Показать содержимое базы знаний')
    
    # Команда clear
    clear_parser = subparsers.add_parser('clear', help='Очистить базу знаний')
    
    # Команда test
    test_parser = subparsers.add_parser('test', help='Протестировать поиск по базе знаний')
    test_parser.add_argument('query', type=str, help='Поисковый запрос')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        await list_knowledge_base(args.data_dir)
    elif args.command == 'clear':
        await clear_knowledge_base(args.data_dir)
    elif args.command == 'test':
        await test_query(args.data_dir, args.query)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main()) 