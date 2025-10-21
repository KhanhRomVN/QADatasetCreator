from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai
from typing import Optional, List, Dict
from config import settings
import uuid


class PineconeService:
    """Service quản lý Pinecone Vector Database"""
    
    def __init__(self):
        self.pc = None
        self.index = None
        self.initialized = False
        
    def initialize(self):
        """Khởi tạo kết nối Pinecone"""
        if self.initialized:
            return
            
        if not settings.pinecone_api_key:
            print("⚠️  Chưa có Pinecone API Key - chức năng kiểm tra trùng bị TẮT")
            return
        
        try:
            # Khởi tạo Pinecone client
            self.pc = Pinecone(api_key=settings.pinecone_api_key)
            
            # Kiểm tra index có tồn tại chưa
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if settings.pinecone_index_name not in existing_indexes:
                print(f"🔨 Tạo Pinecone index mới: {settings.pinecone_index_name}")
                self.pc.create_index(
                    name=settings.pinecone_index_name,
                    dimension=768,  # gemini-embedding-001 dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.pinecone_environment
                    )
                )
            
            # Kết nối tới index
            self.index = self.pc.Index(settings.pinecone_index_name)
            self.initialized = True
            
            print(f"✅ Pinecone đã sẵn sàng: {settings.pinecone_index_name}")
            print(f"📊 Tổng vectors hiện có: {self.index.describe_index_stats()['total_vector_count']}")
            
        except Exception as e:
            print(f"❌ Lỗi khởi tạo Pinecone: {str(e)}")
            print("⚠️  Chức năng kiểm tra trùng bị TẮT")
    
    async def get_story_embedding(self, story: str) -> Optional[List[float]]:
        """
        Convert câu chuyện thành vector bằng gemini-embedding-001
        
        Args:
            story: Câu chuyện tóm tắt
            
        Returns:
            List[float]: Vector 768 chiều hoặc None nếu lỗi
        """
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=story,
                task_type="retrieval_document"
            )
            return result['embedding']
            
        except Exception as e:
            print(f"❌ Lỗi tạo embedding: {str(e)}")
            return None
    
    async def check_story_duplicate(
        self,
        story: str,
        embedding: Optional[List[float]] = None
    ) -> tuple[bool, float]:
        """
        Kiểm tra câu chuyện có trùng lặp không
        
        Args:
            story: Câu chuyện tóm tắt
            embedding: Vector đã tạo sẵn (nếu có)
            
        Returns:
            tuple[bool, float]: (is_duplicate, max_similarity)
        """
        if not self.initialized:
            return False, 0.0
        
        try:
            # Tạo embedding nếu chưa có
            if embedding is None:
                embedding = await self.get_story_embedding(story)
                if embedding is None:
                    return False, 0.0
            
            # Query top 1 similar vector
            results = self.index.query(
                vector=embedding,
                top_k=1,
                include_metadata=True
            )
            
            if not results['matches']:
                return False, 0.0
            
            max_similarity = results['matches'][0]['score']
            is_duplicate = max_similarity > settings.similarity_threshold
            
            if is_duplicate:
                print(f"🔍 Phát hiện câu chuyện tương tự (similarity: {max_similarity:.4f})")
                print(f"📝 Câu chuyện gốc: {results['matches'][0]['metadata'].get('story', 'N/A')[:100]}...")
            
            return is_duplicate, max_similarity
            
        except Exception as e:
            print(f"❌ Lỗi kiểm tra duplicate: {str(e)}")
            return False, 0.0
    
    async def save_story_vector(
        self,
        story: str,
        embedding: Optional[List[float]] = None,
        conversation_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Lưu vector của câu chuyện vào Pinecone
        
        Args:
            story: Câu chuyện tóm tắt
            embedding: Vector đã tạo sẵn (nếu có)
            conversation_id: ID của conversation trong Neon
            
        Returns:
            str: Vector ID hoặc None nếu lỗi
        """
        if not self.initialized:
            return None
        
        try:
            # Tạo embedding nếu chưa có
            if embedding is None:
                embedding = await self.get_story_embedding(story)
                if embedding is None:
                    return None
            
            # Tạo unique ID
            vector_id = str(uuid.uuid4())
            
            # Upsert vào Pinecone
            self.index.upsert(
                vectors=[{
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "story": story,
                        "conversation_id": conversation_id,
                    }
                }]
            )
            
            print(f"✅ Đã lưu vector vào Pinecone: {vector_id}")
            return vector_id
            
        except Exception as e:
            print(f"❌ Lỗi lưu vector: {str(e)}")
            return None
    
    def get_total_stories(self) -> int:
        """Lấy tổng số câu chuyện đã lưu"""
        if not self.initialized:
            return 0
        
        try:
            stats = self.index.describe_index_stats()
            return stats['total_vector_count']
        except:
            return 0


# Singleton instance
pinecone_service = PineconeService()