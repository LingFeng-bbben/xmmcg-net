"""
Majdata.net 上传集成说明

本文档说明如何使用 MajdataService 上传谱面到 Majdata.net
"""

# ============= 配置说明 =============

## 环境变量配置（在 settings.py 或 .env 中设置）

MAJDATA_USERNAME=your_username
MAJDATA_PASSWD_HASHED=your_password


# ============= 使用示例 =============

## 示例 1: 在 views.py 中使用（已集成）

当用户提交谱面时，系统会自动：
1. 保存谱面到本地数据库
2. 调用 MajdataService.upload_chart() 上传到 Majdata.net
3. 即使上传失败，本地保存仍然成功（不影响用户体验）

相关代码位置：songs/views.py 第1109行


## 示例 2: 手动上传谱面

from songs.majdata_service import MajdataService
from songs.models import Chart

# 获取谱面对象
chart = Chart.objects.get(id=1)

# 读取 maidata.txt 内容
with chart.chart_file.open('r') as f:
    maidata_content = f.read()

# 准备上传数据
upload_data = {
    'maidata_content': maidata_content,
    'audio_file': chart.song.audio_file,          # 音频文件
    'cover_file': chart.cover_image,              # 封面图片
    'video_file': chart.background_video,         # 背景视频（可选）
    'is_part_chart': chart.status == 'part_submitted',
    'folder_name': f"{chart.song.title}_{chart.user.username}"
}

# 执行上传
result = MajdataService.upload_chart(upload_data)

if result:
    print(f"✅ 上传成功: {result}")
else:
    print("❌ 上传失败")


## 示例 3: 批量上传所有已提交的谱面

from songs.majdata_service import MajdataService
from songs.models import Chart

# 获取所有已提交的谱面
charts = Chart.objects.filter(status__in=['submitted', 'reviewed'])

for chart in charts:
    print(f"正在上传: {chart.song.title} - {chart.user.username}")
    
    # 读取 maidata 内容
    with chart.chart_file.open('r') as f:
        maidata_content = f.read()
    
    upload_data = {
        'maidata_content': maidata_content,
        'audio_file': chart.song.audio_file,
        'cover_file': chart.cover_image,
        'video_file': chart.background_video,
        'is_part_chart': False,
        'folder_name': f"{chart.song.title}_{chart.user.username}"
    }
    
    result = MajdataService.upload_chart(upload_data)
    
    if result:
        print(f"  ✅ 成功")
    else:
        print(f"  ❌ 失败")


# ============= 文件要求说明 =============

## Majdata.net 上传要求

按照以下顺序上传（固定字段名 "formfiles"）：

1. **maidata.txt** (必需)
   - MIME: text/plain
   - 包含谱面数据

2. **bg.png 或 bg.jpg** (必需)
   - MIME: image/png 或 image/jpeg
   - 谱面封面图片

3. **track.mp3** (必需)
   - MIME: audio/mpeg
   - 音频文件

4. **bg.mp4 或 pv.mp4** (可选)
   - MIME: video/mp4
   - 背景视频


# ============= 半成品谱面处理 =============

## 自动标题修改

当 `is_part_chart=True` 时，上传前会自动修改 maidata.txt 的标题：

**修改规则：**
- 在 `&title=` 行的标题前添加 `[谱面碎片]` 标记
- 示例：`&title=14平米にスーベニア` → `&title=[谱面碎片]14平米にスーベニア`
- 已有 `[谱面碎片]` 标记时不会重复添加
- 其他内容（artist、des、难度等）保持不变

**实现位置：** `songs/majdata_service.py` 中的 `_modify_maidata_for_part_chart()` 方法

**测试：**
```bash
python test_maidata_modification.py
```

**示例：**

原始 maidata.txt:
```
&title=夏日海风
&artist=测试歌手
&des=设计师
&lv_1=3

# 谱面数据
E1,
```

半成品上传后（is_part_chart=True）:
```
&title=[谱面碎片]夏日海风
&artist=测试歌手
&des=设计师
&lv_1=3

# 谱面数据
E1,
```


# ============= 日志和调试 =============

## 查看上传日志

所有上传操作都会记录日志，可以在 Django 日志中查看：

- ✅ 表示成功
- ❌ 表示失败
- ⬆️ 表示正在上传

日志级别：
- INFO: 正常操作
- WARNING: 可选文件缺失等警告
- ERROR: 上传失败、文件缺失等错误


## 测试上传功能

可以使用 Django shell 测试：

python manage.py shell

>>> from songs.majdata_service import MajdataService
>>> session = MajdataService.get_session()
>>> if session:
...     print("✅ 登录成功")
... else:
...     print("❌ 登录失败")


# ============= 常见问题 =============

Q: 上传失败怎么办？
A: 检查日志，确认：
   1. MAJDATA_USERNAME 和 MAJDATA_PASSWD_HASHED 配置正确
   2. 网络连接正常
   3. 文件格式符合要求
   4. 调用 MajdataService.reset_session() 强制重新登录

Q: 如何重新上传已失败的谱面？
A: 使用示例3的批量上传代码，筛选需要重新上传的谱面

Q: 视频文件上传失败会影响整个上传吗？
A: 不会。视频是可选的，如果上传失败会记录警告但继续上传其他文件

Q: 如何验证上传是否成功？
A: 检查返回的 result 字典，成功时会包含 Majdata.net 返回的信息
