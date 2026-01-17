import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# ==================== 可调整的常量 ====================
# 每个用户可上传的歌曲数量限制
MAX_SONGS_PER_USER = 2

# 每个用户可以竞标的歌曲数量限制
MAX_BIDS_PER_USER = 5

# 互评系统常量
PEER_REVIEW_TASKS_PER_USER = 8  # 每个用户需要完成的评分任务数
PEER_REVIEW_MAX_SCORE = 50      # 互评满分（可通过settings配置覆盖）


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
    
    # 用户关系（ForeignKey 允许多首歌）
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='songs'
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


class BiddingRound(models.Model):
    """竞标轮次"""
    
    STATUS_CHOICES = [
        ('pending', '待开始'),
        ('active', '进行中'),
        ('completed', '已完成'),
    ]
    
    name = models.CharField(
        max_length=100,
        help_text='竞标轮次名称'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='竞标状态'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='创建时间'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='开始时间'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='完成时间'
    )
    
    class Meta:
        verbose_name = '竞标轮次'
        verbose_name_plural = '竞标轮次'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class Bid(models.Model):
    """用户竞标（用户对歌曲的出价）"""
    
    bidding_round = models.ForeignKey(
        BiddingRound,
        on_delete=models.CASCADE,
        related_name='bids',
        help_text='所属竞标轮次'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bids',
        help_text='竞标用户'
    )
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name='bids',
        help_text='目标歌曲'
    )
    amount = models.IntegerField(
        help_text='竞标金额（代币）'
    )
    is_dropped = models.BooleanField(
        default=False,
        help_text='是否已被drop（歌曲被更高出价者获得）'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='竞标时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='最后更新时间'
    )
    
    class Meta:
        # 一个用户在同一轮竞标中，对同一歌曲只能出价一次
        unique_together = ('bidding_round', 'user', 'song')
        verbose_name = '竞标'
        verbose_name_plural = '竞标'
        ordering = ['-amount', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} 竞标 {self.song.title} - {self.amount}代币"
    
    def clean(self):
        """验证竞标"""
        # 验证用户在该轮次中的竞标数量不超过限制
        bid_count = Bid.objects.filter(
            bidding_round=self.bidding_round,
            user=self.user,
            is_dropped=False
        ).exclude(song=self.song).count()
        
        if bid_count >= MAX_BIDS_PER_USER:
            raise ValidationError(
                f'超过每轮最多竞标 {MAX_BIDS_PER_USER} 个歌曲的限制'
            )
        
        # 验证竞标金额
        if self.amount <= 0:
            raise ValidationError('竞标金额必须大于0')


class BidResult(models.Model):
    """竞标结果（分配结果）"""
    
    ALLOCATION_TYPE_CHOICES = [
        ('win', '中标'),
        ('random', '随机分配'),
    ]
    
    bidding_round = models.ForeignKey(
        BiddingRound,
        on_delete=models.CASCADE,
        related_name='results',
        help_text='所属竞标轮次'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bid_results',
        help_text='获得歌曲的用户'
    )
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name='bid_results',
        help_text='分配的歌曲'
    )
    bid_amount = models.IntegerField(
        help_text='最终成交的竞标金额'
    )
    allocation_type = models.CharField(
        max_length=20,
        choices=ALLOCATION_TYPE_CHOICES,
        default='win',
        help_text='分配类型（中标或随机分配）'
    )
    allocated_at = models.DateTimeField(
        auto_now_add=True,
        help_text='分配时间'
    )
    
    class Meta:
        # 一个用户在同一轮竞标中，对同一歌曲只能有一个分配结果
        unique_together = ('bidding_round', 'user', 'song')
        verbose_name = '竞标结果'
        verbose_name_plural = '竞标结果'
        ordering = ['-allocated_at']
    
    def __str__(self):
        allocation_type_display = dict(self.ALLOCATION_TYPE_CHOICES)[self.allocation_type]
        return f"{self.user.username} {allocation_type_display} {self.song.title} - {self.bid_amount}代币"


class Chart(models.Model):
    """用户提交的谱面（beatmap）"""
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('under_review', '评分中'),
        ('reviewed', '已评分'),
    ]
    
    # 关系
    bidding_round = models.ForeignKey(
        BiddingRound,
        on_delete=models.CASCADE,
        related_name='charts',
        help_text='所属竞标轮次'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='charts',
        help_text='谱面创建者'
    )
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name='charts',
        help_text='谱面对应的歌曲'
    )
    bid_result = models.ForeignKey(
        BidResult,
        on_delete=models.CASCADE,
        related_name='charts',
        null=True,
        blank=True,
        help_text='对应的竞标结果（第一部分必需，第二部分可选）'
    )
    
    # 谱面信息
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='谱面状态'
    )
    
    # 文件引用（不在本服务器托管，仅记录URL或标识）
    # 假设另一个网站提供的谱面URL格式为: https://chart-server.com/charts/{chart_id}/maidata.txt
    chart_url = models.URLField(
        null=True,
        blank=True,
        help_text='谱面URL（指向外部文件服务器）'
    )
    
    # 谱面标识（由外部服务器提供，用于定位maidata.txt）
    chart_id_external = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='外部服务器的谱面标识'
    )
    
    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='创建时间'
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='提交时间'
    )
    review_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='评分完成时间'
    )
    
    # 评分统计（冗余字段，便于查询）
    review_count = models.IntegerField(
        default=0,
        help_text='收到的评分数'
    )
    total_score = models.IntegerField(
        default=0,
        help_text='总评分（用于快速计算平均分）'
    )
    average_score = models.FloatField(
        default=0.0,
        help_text='平均分（0-50）'
    )
    
    # 二部分谱面支持（第二轮竞标续写）
    is_part_one = models.BooleanField(
        default=True,
        help_text='是否是第一部分谱面（True=第一部分，False=第二部分）'
    )
    part_one_chart = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='part_two_chart',
        help_text='如果是第二部分，指向对应的第一部分谱面'
    )
    completion_bid_result = models.ForeignKey(
        BidResult,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completion_charts',
        help_text='第二轮竞标获得的一部分，用于续写'
    )
    
    class Meta:
        verbose_name = '谱面'
        verbose_name_plural = '谱面'
        ordering = ['-created_at']
        # 一个用户对同一歌曲在同一轮中只能提交一个谱面
        unique_together = ('bidding_round', 'user', 'song')
    
    def __str__(self):
        part_info = '（二部分）' if not self.is_part_one else ''
        return f"{self.user.username} - {self.song.title} {part_info}({self.get_status_display()})"
    
    def calculate_average_score(self):
        """计算平均分"""
        if self.review_count == 0:
            self.average_score = 0.0
        else:
            self.average_score = round(self.total_score / self.review_count, 2)
        self.save()


class PeerReviewAllocation(models.Model):
    """互评任务分配（保证每个选手收到8个评分，每个评分者评分8个选手）"""
    
    bidding_round = models.ForeignKey(
        BiddingRound,
        on_delete=models.CASCADE,
        related_name='peer_review_allocations',
        help_text='所属竞标轮次'
    )
    
    # 分配信息
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_peer_reviews',
        help_text='评分者'
    )
    
    chart = models.ForeignKey(
        Chart,
        on_delete=models.CASCADE,
        related_name='review_allocations',
        help_text='被评分的谱面'
    )
    
    # 状态
    STATUS_CHOICES = [
        ('pending', '待评分'),
        ('completed', '已完成'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='任务状态'
    )
    
    # 时间戳
    allocated_at = models.DateTimeField(
        auto_now_add=True,
        help_text='分配时间'
    )
    
    class Meta:
        verbose_name = '互评分配'
        verbose_name_plural = '互评分配'
        ordering = ['allocated_at']
        # 同一个评分者不能多次评同一个谱面
        unique_together = ('bidding_round', 'reviewer', 'chart')
    
    def __str__(self):
        return f"{self.reviewer.username} -> {self.chart.user.username}的{self.chart.song.title}"


class PeerReview(models.Model):
    """互评打分记录"""
    
    # 关系
    allocation = models.OneToOneField(
        PeerReviewAllocation,
        on_delete=models.CASCADE,
        related_name='review',
        help_text='对应的分配任务'
    )
    
    bidding_round = models.ForeignKey(
        BiddingRound,
        on_delete=models.CASCADE,
        related_name='peer_reviews',
        help_text='所属竞标轮次'
    )
    
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_peer_reviews',
        help_text='评分者'
    )
    
    chart = models.ForeignKey(
        Chart,
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text='被评分的谱面'
    )
    
    # 评分内容
    score = models.IntegerField(
        help_text='评分（0-50）'
    )
    
    comment = models.TextField(
        blank=True,
        null=True,
        help_text='评论（可选）'
    )
    
    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='评分时间'
    )
    
    class Meta:
        verbose_name = '互评记录'
        verbose_name_plural = '互评记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reviewer.username} 给 {self.chart.user.username} 打分 {self.score}"
    
    def clean(self):
        """验证评分"""
        if self.score < 0 or self.score > PEER_REVIEW_MAX_SCORE:
            raise ValidationError(
                f'评分必须在0-{PEER_REVIEW_MAX_SCORE}之间'
            )


# ==================== 第二轮竞标系统 ====================

class SecondBiddingRound(models.Model):
    """第二轮竞标轮次（竞标其他选手已提交的一半谱面来续写）"""
    
    STATUS_CHOICES = [
        ('pending', '待开始'),
        ('active', '进行中'),
        ('completed', '已完成'),
    ]
    
    # 关联的第一轮竞标
    first_bidding_round = models.OneToOneField(
        BiddingRound,
        on_delete=models.CASCADE,
        related_name='second_bidding_round',
        help_text='对应的第一轮竞标轮次'
    )
    
    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='第二轮竞标状态'
    )
    
    # 说明：参与者为第一轮的所有竞标者，可竞标标的为其他人已提交的一半谱面
    name = models.CharField(
        max_length=100,
        help_text='第二轮名称'
    )
    
    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='创建时间'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='开始时间'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='完成时间'
    )
    
    class Meta:
        verbose_name = '第二轮竞标轮次'
        verbose_name_plural = '第二轮竞标轮次'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class SecondBid(models.Model):
    """第二轮竞标（用户竞标其他人的一半谱面）"""
    
    second_bidding_round = models.ForeignKey(
        SecondBiddingRound,
        on_delete=models.CASCADE,
        related_name='second_bids',
        help_text='所属第二轮竞标轮次'
    )
    
    bidder = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='second_bids',
        help_text='竞标者（需要续写的选手）'
    )
    
    # 标的物：第一轮已提交的一半谱面
    target_chart_part_one = models.ForeignKey(
        Chart,
        on_delete=models.CASCADE,
        related_name='second_bids',
        help_text='竞标的目标：其他选手的一半谱面'
    )
    
    # 竞标金额（从剩余token中消耗）
    amount = models.IntegerField(
        help_text='竞标金额（代币）'
    )
    
    # 状态
    is_dropped = models.BooleanField(
        default=False,
        help_text='是否已被drop（被更高出价者竞走）'
    )
    
    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='竞标时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='最后更新时间'
    )
    
    class Meta:
        verbose_name = '第二轮竞标'
        verbose_name_plural = '第二轮竞标'
        ordering = ['-amount', '-created_at']
        # 同一选手在同一轮次中，对同一个一半谱面只能出价一次
        unique_together = ('second_bidding_round', 'bidder', 'target_chart_part_one')
    
    def __str__(self):
        return f"{self.bidder.username} 竞标 {self.target_chart_part_one.user.username}的一半谱面 - {self.amount}代币"
    
    def clean(self):
        """验证第二轮竞标"""
        # 不能竞标自己的谱面
        if self.bidder == self.target_chart_part_one.user:
            raise ValidationError('不能竞标自己的谱面')
        
        # 验证竞标金额
        if self.amount <= 0:
            raise ValidationError('竞标金额必须大于0')


class SecondBidResult(models.Model):
    """第二轮竞标结果（分配结果）"""
    
    ALLOCATION_TYPE_CHOICES = [
        ('win', '中标'),
        ('random', '随机分配'),
    ]
    
    second_bidding_round = models.ForeignKey(
        SecondBiddingRound,
        on_delete=models.CASCADE,
        related_name='second_results',
        help_text='所属第二轮竞标轮次'
    )
    
    winner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='second_bid_results',
        help_text='获得一半谱面的选手（续写者）'
    )
    
    # 获得的一半谱面
    part_one_chart = models.ForeignKey(
        Chart,
        on_delete=models.CASCADE,
        related_name='second_bid_results',
        help_text='获得的第一部分谱面'
    )
    
    # 最终成交价格
    bid_amount = models.IntegerField(
        help_text='最终成交的竞标金额'
    )
    
    # 分配类型
    allocation_type = models.CharField(
        max_length=20,
        choices=ALLOCATION_TYPE_CHOICES,
        default='win',
        help_text='分配类型（中标或随机分配）'
    )
    
    # 时间戳
    allocated_at = models.DateTimeField(
        auto_now_add=True,
        help_text='分配时间'
    )
    
    # 关联的完成谱面（二部分）
    completed_chart = models.OneToOneField(
        Chart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='second_bid_result_completion',
        help_text='基于此分配创建的完成谱面'
    )
    
    class Meta:
        verbose_name = '第二轮竞标结果'
        verbose_name_plural = '第二轮竞标结果'
        ordering = ['-allocated_at']
        # 同一选手对同一个一半谱面只能有一个分配结果
        unique_together = ('second_bidding_round', 'winner', 'part_one_chart')
    
    def __str__(self):
        allocation_type_display = dict(self.ALLOCATION_TYPE_CHOICES)[self.allocation_type]
        return f"{self.winner.username} {allocation_type_display} {self.part_one_chart.user.username}的一半谱面 - {self.bid_amount}代币"
