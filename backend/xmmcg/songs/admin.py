from django.contrib import admin
from .models import Song


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('unique_key', 'audio_hash', 'created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'title', 'unique_key')
        }),
        ('媒体文件', {
            'fields': ('audio_file', 'audio_hash', 'cover_image')
        }),
        ('链接', {
            'fields': ('netease_url',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # 不允许在后台直接添加歌曲，只能通过 API 上传
        return False
