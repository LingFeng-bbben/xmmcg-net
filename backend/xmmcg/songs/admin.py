from django.contrib import admin
from .models import Song, Banner, Announcement, CompetitionPhase, BiddingRound, Bid, BidResult


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
        return True


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'priority', 'created_at')
    list_filter = ('is_active', 'created_at')
    ordering = ('-priority', '-created_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'content', 'button_text', 'color')
        }),
        ('链接配置', {
            'fields': ('image_url', 'link')
        }),
        ('管理', {
            'fields': ('priority', 'is_active')
        }),
    )


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_pinned', 'is_active', 'created_at')
    list_filter = ('category', 'is_pinned', 'is_active', 'created_at')
    ordering = ('-is_pinned', '-priority', '-created_at')
    search_fields = ('title', 'content')
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'category', 'content')
        }),
        ('管理', {
            'fields': ('priority', 'is_pinned', 'is_active')
        }),
    )


@admin.register(CompetitionPhase)
class CompetitionPhaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'phase_key', 'status', 'start_time', 'end_time', 'order', 'is_active')
    list_filter = ('is_active', 'start_time', 'created_at')
    ordering = ('order', 'start_time')
    search_fields = ('name', 'phase_key', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'phase_key', 'description')
        }),
        ('时间配置', {
            'fields': ('start_time', 'end_time', 'order')
        }),
        ('页面访问权限', {
            'fields': ('page_access',),
            'description': '配置该阶段允许访问的功能页面。格式: {"songs": true, "charts": false, "profile": true}。注：首页、登录、注册页总是可访问，无需配置。'
        }),
        ('管理', {
            'fields': ('is_active',)
        }),
        ('系统', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BiddingRound)
class BiddingRoundAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_at', 'started_at', 'completed_at')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)
    search_fields = ('name',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'status')
        }),
        ('时间信息', {
            'fields': ('started_at', 'completed_at', 'created_at')
        }),
    )


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('bidding_round', 'user', 'song', 'amount', 'is_dropped', 'created_at')
    list_filter = ('bidding_round', 'is_dropped', 'created_at')
    ordering = ('-created_at',)
    search_fields = ('user__username', 'song__title', 'bidding_round__name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('竞标信息', {
            'fields': ('bidding_round', 'user', 'song', 'amount', 'is_dropped')
        }),
        ('系统', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(BidResult)
class BidResultAdmin(admin.ModelAdmin):
    list_display = ('bidding_round', 'song', 'user', 'bid_amount', 'allocation_type', 'allocated_at')
    list_filter = ('bidding_round', 'allocation_type', 'allocated_at')
    ordering = ('-allocated_at',)
    search_fields = ('song__title', 'user__username', 'bidding_round__name')
    readonly_fields = ('allocated_at',)
    
    fieldsets = (
        ('竞标结果', {
            'fields': ('bidding_round', 'song', 'user', 'bid_amount', 'allocation_type')
        }),
        ('系统', {
            'fields': ('allocated_at',),
            'classes': ('collapse',)
        }),
    )
