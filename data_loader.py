import os
import json
from typing import Dict, List, Optional
from document_processor import DocumentProcessor

class DataLoader:
    def __init__(self, data_dir: str = "training_data"):
        """Initialize data loader with directory for training data."""
        self.data_dir = data_dir
        self.knowledge_base = {}
        
        # Create data directory if not exists
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "pdf"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "text"), exist_ok=True)
        
        # Knowledge base file path
        self.kb_file = os.path.join(data_dir, "knowledge_base.json")
        
        # Load existing knowledge base if available
        if os.path.exists(self.kb_file):
            with open(self.kb_file, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
    
    async def process_directory(self) -> Dict:
        """Process all training data in the directory."""
        # Process PDFs
        pdf_dir = os.path.join(self.data_dir, "pdf")
        for filename in os.listdir(pdf_dir):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(pdf_dir, filename)
                if filename not in self.knowledge_base:
                    print(f"Processing PDF: {filename}")
                    text = await DocumentProcessor.process_pdf(file_path)
                    if text:
                        self.knowledge_base[filename] = {
                            "type": "pdf",
                            "content": text
                        }
        
        # Process images
        img_dir = os.path.join(self.data_dir, "images")
        for filename in os.listdir(img_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(img_dir, filename)
                if filename not in self.knowledge_base:
                    print(f"Processing image: {filename}")
                    text = await DocumentProcessor.process_image(file_path)
                    if text:
                        self.knowledge_base[filename] = {
                            "type": "image",
                            "content": text
                        }
        
        # Process text files
        text_dir = os.path.join(self.data_dir, "text")
        for filename in os.listdir(text_dir):
            if filename.lower().endswith('.txt'):
                file_path = os.path.join(text_dir, filename)
                if filename not in self.knowledge_base:
                    print(f"Processing text file: {filename}")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                            self.knowledge_base[filename] = {
                                "type": "text",
                                "content": text
                            }
                    except Exception as e:
                        print(f"Error processing text file {filename}: {str(e)}")
        
        # Save updated knowledge base
        self.save_knowledge_base()
        return self.knowledge_base
    
    def save_knowledge_base(self):
        """Save knowledge base to file."""
        with open(self.kb_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
    
    def get_full_context(self) -> str:
        """Get the full context from all processed files."""
        context = []
        for filename, data in self.knowledge_base.items():
            context.append(f"--- Содержимое файла: {filename} ---\n{data['content']}\n")
        return "\n".join(context)
    
    def search_knowledge_base(self, query: str) -> Optional[str]:
        """
        Simple search function that returns content 
        from knowledge base that might be relevant to the query
        """
        # This is a very basic implementation
        # In a real application, you would use vector search or another more sophisticated method
        query_terms = set(query.lower().split())
        results = []
        
        for filename, data in self.knowledge_base.items():
            content = data['content'].lower()
            score = sum(1 for term in query_terms if term in content)
            if score > 0:
                results.append((filename, data, score))
        
        # Sort by relevance score
        results.sort(key=lambda x: x[2], reverse=True)
        
        # Return top relevant contexts concatenated
        if results:
            context = []
            for filename, data, score in results[:3]:  # Top 3 most relevant
                context.append(f"--- Информация из {filename} ---\n{data['content']}\n")
            return "\n".join(context)
        
        return None 