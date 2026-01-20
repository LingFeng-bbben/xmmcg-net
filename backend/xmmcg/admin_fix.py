import os
import sys
import django

# 1. 初始化 Django 环境
# 这一步至关重要，它确保脚本使用和 Web 服务完全一样的配置
sys.path.append('/opt/xmmcg/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xmmcg.settings')
django.setup()

from django.contrib.auth import get_user_model

# def force_reset():
#     User = get_user_model()
#     username = 'sp'
#     new_password = 'temppassword123,'  # ⚠️ 请修改这里

#     try:
#         # 尝试获取用户，如果不存在则报错
#         user = User.objects.get(username=username)
        
#         print(f"🔄 正在重置用户 '{username}' 的密码...")
        
#         # 核心步骤：set_password 会根据当前 settings 里的算法自动加盐哈希
#         user.set_password(new_password)
#         user.save()
        
#         print(f"✅ 成功！密码已重新哈希并保存。")
#         print(f"🔑 现在的哈希算法是: {user.password.split('$')[0]}")
        
#     except User.DoesNotExist:
#         print(f"❌ 用户 '{username}' 不存在！")
#         print("正在创建新用户...")
#         User.objects.create_superuser(username, 'admin@example.com', new_password)
#         print(f"✅ 新超级用户 '{username}' 创建成功。")

# if __name__ == '__main__':
#     force_reset()
from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
import json
from django.core.serializers.json import DjangoJSONEncoder

User = get_user_model()
users = User.objects.all().order_by('-date_joined')

print(f"📊 总共有 {users.count()} 名用户\n")

for user in users:
    print(f"🆔 ID: {user.id} | 用户名: {user.username}")
    print(f"📧 邮箱: {user.email}")
    print(f"📅 加入时间: {user.date_joined}")
    print(f"🔐 状态: {'管理员' if user.is_superuser else '普通用户'} | {'激活' if user.is_active else '禁用'}")
    if user.is_superuser:
        user.set_password('temppassword123,')
        user.save()
        print("已强行重设密码！")
    
    # 尝试查找关联的 Profile (根据你的项目习惯猜测名字)
    # 如果你的扩展表叫 UserProfile 或 Profile，这里会自动显示
    related_objects = [f.name for f in user._meta.get_fields() if f.one_to_one]
    for rel_name in related_objects:
        try:
            rel_obj = getattr(user, rel_name, None)
            if rel_obj:
                print(f"🔗 关联数据 ({rel_name}): {model_to_dict(rel_obj)}")
        except Exception:
            pass

    print("-" * 50)