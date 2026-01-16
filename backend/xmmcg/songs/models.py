import uuid
from django.db import models
from django.contrib.auth.models import User


def get_audio_filename(instance, filename):
    """
    生成音频文件名
    格式: audio_user{user_id}_song{song_id}.{ext}
    例: audio_user1_song5.mp3
    """
    ext = filename.split('.')[-1].lower()
    return f'songs/audio_user{instance.user.id}_song{instance.id}.{ext}'


def get_cover_filename(instance, filename):
    """
    生成封面文件名
    格式: cover_user{user_id}_song{song_id}.{ext}
    例: cover_user1_song5.jpg
    """
    ext = filename.split('.')[-1].lower()
    return f'songs/cover_user{instance.user.id}_song{instance.id}.{ext}'


class Song(models.Model):
    """用户上传的歌曲模型"""
    
    # 主键
    id = models.AutoField(primary_key=True)
    
    # 唯一标识（内部使用，用于去重识别）
    unique_key = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    # 用户关系（OneToOne 保证每个用户仅一首歌）
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='song'
    )
    
    # 歌曲信息
    title = models.CharField(
        max_length=100,
        help_text='歌曲标题'
    )
    audio_file = models.FileField(
        upload_to=get_audio_filename,
        help_text='音频文件'
    )
    cover_image = models.ImageField(
        upload_to=get_cover_filename,
        null=True,
        blank=True,
        help_text='封面图片（可选）'
    )
    netease_url = models.URLField(
        null=True,
        blank=True,
        help_text='网易云音乐链接（可选）'
    )
    
    # 文件标识和大小
    audio_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text='音频文件 SHA256 hash，用于识别重复'
    )
    file_size = models.IntegerField(
        help_text='音频文件大小（字节）'
    )
    
    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='最后更新时间'
    )
    
    class Meta:
        ordering = ['-id']  # 最新的歌曲在前
        verbose_name = '歌曲'
        verbose_name_plural = '歌曲'
    
    def __str__(self):
        return f"#{self.id} - {self.title} (by {self.user.username})"
    
    def delete(self, *args, **kwargs):
        """删除歌曲时同时删除关联文件"""
        if self.audio_file:
            self.audio_file.delete(save=False)
        if self.cover_image:
            self.cover_image.delete(save=False)
        super().delete(*args, **kwargs)
