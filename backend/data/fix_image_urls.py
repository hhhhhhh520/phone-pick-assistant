"""修复数据库中的图片URL格式"""
from backend.models.domain import SessionLocal, Phone

db = SessionLocal()
phones = db.query(Phone).filter(Phone.image_url != None).all()
fixed = 0

for p in phones:
    if p.image_url:
        original = p.image_url
        # 修复 Windows 反斜杠路径
        if '\\' in p.image_url:
            p.image_url = p.image_url.replace('\\', '/')
        # 确保以 /images/ 开头
        if p.image_url.startswith('images/'):
            p.image_url = '/' + p.image_url
        if original != p.image_url:
            fixed += 1
            print(f'Fixed: {p.brand} {p.model}')
            print(f'  Old: {original}')
            print(f'  New: {p.image_url}')

db.commit()
print(f'\nTotal fixed: {fixed}')
db.close()
