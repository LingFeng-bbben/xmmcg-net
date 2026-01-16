import hashlib
from django.core.files.base import File
from django.conf import settings


def calculate_file_hash(file: File) -> str:
    """
    计算文件的 SHA256 哈希值
    用于识别相同的音频文件
    """
    file.seek(0)  # 重置文件指针到开头
    hash_sha256 = hashlib.sha256()
    
    # 分块读取文件（适合大文件）
    for chunk in file.chunks():
        hash_sha256.update(chunk)
    
    file.seek(0)  # 重置文件指针到开头
    return hash_sha256.hexdigest()


def validate_audio_file(file: File) -> tuple[bool, str]:
    """
    验证音频文件
    
    Returns:
        (is_valid, error_message)
    """
    if not file:
        return False, '音频文件不能为空'
    
    # 检查文件大小（10MB）
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        size_mb = max_size / (1024 * 1024)
        return False, f'音频文件过大，最大允许 {int(size_mb)}MB'
    
    # 检查文件扩展名
    allowed_extensions = getattr(settings, 'ALLOWED_AUDIO_EXTENSIONS', 
                                 ['mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg', 'wma'])
    ext = file.name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        return False, f'不支持的音频格式: {ext}，允许的格式: {", ".join(allowed_extensions)}'
    
    return True, ''


def validate_cover_image(file: File) -> tuple[bool, str]:
    """
    验证封面图片
    
    Returns:
        (is_valid, error_message)
    """
    if not file:
        return True, ''  # 封面是可选的
    
    # 检查文件大小（2MB）
    max_size = 2 * 1024 * 1024  # 2MB
    if file.size > max_size:
        size_mb = max_size / (1024 * 1024)
        return False, f'封面图片过大，最大允许 {int(size_mb)}MB'
    
    # 检查文件扩展名
    allowed_extensions = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS',
                                 ['jpg', 'jpeg', 'png', 'gif', 'webp'])
    ext = file.name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        return False, f'不支持的图片格式: {ext}，允许的格式: {", ".join(allowed_extensions)}'
    
    return True, ''


def validate_title(title: str) -> tuple[bool, str]:
    """
    验证歌曲标题
    
    Returns:
        (is_valid, error_message)
    """
    if not title or not title.strip():
        return False, '歌曲标题不能为空'
    
    if len(title) > 100:
        return False, '歌曲标题过长，最多 100 个字符'
    
    return True, ''
