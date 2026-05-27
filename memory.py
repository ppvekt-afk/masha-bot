import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import hashlib

class MemorySystem:
    def __init__(self):
        self.memory_file = "masha_memory.json"
        self.conversations_file = "conversations.json"
        self.memory = self._load_memory()
        self.conversations = self._load_conversations()
    
    def _load_memory(self) -> Dict:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _load_conversations(self) -> Dict:
        if os.path.exists(self.conversations_file):
            try:
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_memory(self):
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)
    
    def _save_conversations(self):
        with open(self.conversations_file, 'w', encoding='utf-8') as f:
            json.dump(self.conversations, f, ensure_ascii=False, indent=2)
    
    def save_interaction(self, user_id: int, user_message: str, bot_response: str, context: Dict = None):
        """Сохраняет взаимодействие для обучения"""
        user_key = str(user_id)
        
        if user_key not in self.conversations:
            self.conversations[user_key] = {
                "history": [],
                "topics": {},
                "user_info": {},
                "first_seen": datetime.now().isoformat()
            }
        
        # Сохраняем сообщение
        self.conversations[user_key]["history"].append({
            "user": user_message,
            "bot": bot_response,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        })
        
        # Ограничиваем историю 200 сообщениями
        if len(self.conversations[user_key]["history"]) > 200:
            self.conversations[user_key]["history"] = self.conversations[user_key]["history"][-200:]
        
        self._save_conversations()
    
    def get_conversation_context(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Возвращает последние сообщения для контекста"""
        user_key = str(user_id)
        if user_key not in self.conversations:
            return []
        
        history = self.conversations[user_key]["history"]
        return history[-limit:]
    
    def get_user_profile(self, user_id: int) -> Dict:
        """Возвращает профиль пользователя"""
        user_key = str(user_id)
        if user_key not in self.conversations:
            return {}
        
        data = self.conversations[user_key]
        
        # Анализируем предпочтения
        topics = {}
        for msg in data["history"]:
            # Простой анализ тем
            text = msg["user"].lower()
            if "текст" in text or "статья" in text:
                topics["writing"] = topics.get("writing", 0) + 1
            if "ошибка" in text or "исправить" in text:
                topics["editing"] = topics.get("editing", 0) + 1
            if "стиль" in text or "как написать" in text:
                topics["style"] = topics.get("style", 0) + 1
        
        return {
            "total_messages": len(data["history"]),
            "topics": topics,
            "first_seen": data.get("first_seen"),
            "user_info": data.get("user_info", {})
        }
    
    def update_user_info(self, user_id: int, info: Dict):
        """Обновляет информацию о пользователе"""
        user_key = str(user_id)
        if user_key not in self.conversations:
            self.conversations[user_key] = {"history": [], "topics": {}, "user_info": {}}
        
        self.conversations[user_key]["user_info"].update(info)
        self._save_conversations()
    
    def get_learning_insights(self) -> Dict:
        """Анализирует все диалоги для самообучения"""
        total_users = len(self.conversations)
        total_messages = 0
        common_topics = {}
        
        for user_data in self.conversations.values():
            total_messages += len(user_data["history"])
            for msg in user_data["history"]:
                # Сбор статистики по темам
                pass
        
        return {
            "total_users": total_users,
            "total_messages": total_messages,
            "common_topics": common_topics
        }
EOF
