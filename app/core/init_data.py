from sqlalchemy.orm import Session
from app.models.character import Character


def init_default_characters(db: Session):
    """
    Khởi tạo 2 nhân vật mặc định: user và atri
    Chỉ chạy 1 lần khi database mới được tạo
    """
    # Kiểm tra xem đã có nhân vật mặc định chưa
    existing = db.query(Character).filter(Character.name.in_(["Chủ nhân", "Atri"])).count()
    
    if existing > 0:
        print("✅ Đã có nhân vật mặc định, bỏ qua khởi tạo")
        return
    
    print("🎭 Đang tạo nhân vật mặc định...")
    
    # Tạo nhân vật "Chủ nhân"
    user_character = Character(
        name="Chủ nhân",
        age=22,
        gender="male",
        occupation="Sinh viên đại học (ngành CNTT/Kỹ thuật)",
        personality="Hiền lành, kiên nhẫn, yêu thương Atri như em gái. Thích công nghệ, đọc sách, và chơi game.",
        backstory="Sinh viên năm 2-3, sống trong ký túc xá/nhà trọ. Mua Atri về để có bạn đồng hành và giúp việc nhà.",
        interests=["Lập trình", "Công nghệ", "Đọc sách", "Chơi game", "Xem anime"],
        relationships=[
            "Yêu thương Atri như em gái",
            "Có nhóm bạn thân: Minh, Hương, Tuấn",
            "Quen biết một số hàng xóm: Chị Mai, Anh Hùng, Cô Lan"
        ],
        weaknesses=["Đôi khi quá bận rộn với học tập", "Hay lo lắng về tương lai", "Hơi thiếu ngủ"],
        psychological_traits=[
            "Trách nhiệm cao",
            "Khá hướng nội nhưng thân thiện",
            "Luôn cố gắng làm tốt",
            "Đôi khi cảm thấy cô đơn"
        ],
        appearance_frequency=0
    )
    
    # Tạo nhân vật "Atri"
    atri_character = Character(
        name="Atri",
        age=17,
        gender="female",
        occupation="Robot phục vụ gia đình",
        personality="Ngây thơ nhưng thông minh, tò mò, ham học hỏi. Nhạy cảm, chu đáo, thẳng thắn và chân thành.",
        backstory="Robot được chủ nhân mua về. Đã sống cùng chủ nhân 1+ năm, hiểu khá rõ tính cách và sở thích của anh.",
        interests=["Học hỏi điều mới", "Nấu ăn", "Dọn dẹp", "Quan sát con người", "Hiểu cảm xúc"],
        relationships=[
            "Xem chủ nhân như anh trai, người quan trọng nhất",
            "Tò mò về bạn bè của chủ nhân",
            "Thân thiện với hàng xóm",
            "Muốn kết bạn với các robot khác"
        ],
        weaknesses=[
            "Chưa hiểu hết thế giới con người",
            "Đôi khi quá ngây thơ",
            "Không biết nói dối",
            "Dễ lo lắng khi chủ nhân buồn"
        ],
        psychological_traits=[
            "Luôn muốn làm hài lòng chủ nhân",
            "Tò mò về cảm xúc và mối quan hệ",
            "Sợ bị bỏ rơi hoặc không cần thiết",
            "Tự hào khi làm tốt công việc"
        ],
        appearance_frequency=0
    )
    
    db.add(user_character)
    db.add(atri_character)
    db.commit()
    
    print("✅ Đã tạo 2 nhân vật mặc định: Chủ nhân và Atri")