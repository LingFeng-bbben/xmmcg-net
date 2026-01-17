from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Song
from .utils import (
    calculate_file_hash,
    validate_audio_file,
    validate_cover_image,
    validate_title
)


class SongUserSerializer(serializers.ModelSerializer):
    """歌曲所属用户的简介信息"""
    
    class Meta:
        model = User
        fields = ('id', 'username')


class SongUploadSerializer(serializers.ModelSerializer):
    """歌曲上传序列化器"""
    
    class Meta:
        model = Song
        fields = ('title', 'audio_file', 'cover_image', 'netease_url')
        extra_kwargs = {
            'title': {'required': True},
            'audio_file': {'required': True},
            'cover_image': {'required': False},
            'netease_url': {'required': False},
        }
    
    def validate_title(self, value):
        """验证标题"""
        is_valid, error_msg = validate_title(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value
    
    def validate_audio_file(self, value):
        """验证音频文件"""
        is_valid, error_msg = validate_audio_file(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value
    
    def validate_cover_image(self, value):
        """验证封面图片"""
        if value:  # 封面是可选的
            is_valid, error_msg = validate_cover_image(value)
            if not is_valid:
                raise serializers.ValidationError(error_msg)
        return value
    
    def create(self, validated_data):
        """创建歌曲"""
        user = self.context['request'].user
        audio_file = validated_data['audio_file']
        
        # 计算音频文件哈希
        audio_hash = calculate_file_hash(audio_file)
        
        song = Song.objects.create(
            user=user,
            audio_hash=audio_hash,
            file_size=audio_file.size,
            **validated_data
        )
        return song


class SongDetailSerializer(serializers.ModelSerializer):
    """歌曲详情序列化器（返回完整信息）"""
    user = SongUserSerializer(read_only=True)
    audio_url = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Song
        fields = (
            'id',
            'title',
            'user',
            'audio_url',
            'cover_url',
            'netease_url',
            'file_size',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'user', 'file_size', 'created_at', 'updated_at')
    
    def get_audio_url(self, obj):
        """获取音频文件 URL"""
        if obj.audio_file:
            return obj.audio_file.url
        return None
    
    def get_cover_url(self, obj):
        """获取封面文件 URL"""
        if obj.cover_image:
            return obj.cover_image.url
        return None


class SongListSerializer(serializers.ModelSerializer):
    """歌曲列表序列化器（返回精简信息）"""
    user = SongUserSerializer(read_only=True)
    cover_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Song
        fields = (
            'id',
            'title',
            'user',
            'cover_url',
            'file_size',
            'created_at'
        )
        read_only_fields = fields
    
    def get_cover_url(self, obj):
        """获取封面文件 URL"""
        if obj.cover_image:
            return obj.cover_image.url
        return None


class SongUpdateSerializer(serializers.ModelSerializer):
    """歌曲更新序列化器（仅允许更新非文件字段）"""
    
    class Meta:
        model = Song
        fields = ('title', 'netease_url')
    
    def validate_title(self, value):
        """验证标题"""
        is_valid, error_msg = validate_title(value)
        if not is_valid:
            raise serializers.ValidationError(error_msg)
        return value


# ==================== 竞标相关序列化器 ====================

from .models import Bid, BidResult, BiddingRound


class BiddingRoundSerializer(serializers.ModelSerializer):
    """竞标轮次序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = BiddingRound
        fields = ('id', 'name', 'status', 'status_display', 'created_at', 'started_at', 'completed_at')
        read_only_fields = ('id', 'created_at')


class BidSerializer(serializers.ModelSerializer):
    """竞标序列化器"""
    song = SongListSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Bid
        fields = ('id', 'username', 'song', 'amount', 'is_dropped', 'created_at')
        read_only_fields = ('id', 'username', 'is_dropped', 'created_at')


class BidResultSerializer(serializers.ModelSerializer):
    """竞标结果序列化器"""
    song = SongListSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    allocation_type_display = serializers.CharField(source='get_allocation_type_display', read_only=True)
    
    class Meta:
        model = BidResult
        fields = ('id', 'username', 'song', 'bid_amount', 'allocation_type', 'allocation_type_display', 'allocated_at')
        read_only_fields = ('id', 'username', 'allocated_at')


# ==================== 谱面和互评相关序列化器 ====================

from .models import Chart, PeerReview, PeerReviewAllocation


class ChartSerializer(serializers.ModelSerializer):
    """谱面序列化器"""
    song = SongListSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Chart
        fields = (
            'id', 'username', 'song', 'status', 'status_display',
            'chart_url', 'chart_id_external', 'review_count', 'average_score',
            'created_at', 'submitted_at', 'review_completed_at'
        )
        read_only_fields = (
            'id', 'username', 'review_count', 'average_score',
            'created_at', 'submitted_at', 'review_completed_at'
        )


class ChartCreateSerializer(serializers.ModelSerializer):
    """谱面创建序列化器"""
    
    class Meta:
        model = Chart
        fields = ('chart_url', 'chart_id_external')
        extra_kwargs = {
            'chart_url': {'required': False},
            'chart_id_external': {'required': False},
        }
    
    def validate(self, data):
        """至少提供一个标识符"""
        if not data.get('chart_url') and not data.get('chart_id_external'):
            raise serializers.ValidationError(
                '必须提供 chart_url 或 chart_id_external 中的至少一个'
            )
        return data


class PeerReviewAllocationSerializer(serializers.ModelSerializer):
    """互评任务序列化器（用于获取待评分任务）"""
    chart_id = serializers.IntegerField(source='chart.id', read_only=True)
    song_title = serializers.CharField(source='chart.song.title', read_only=True)
    chart_url = serializers.URLField(source='chart.chart_url', read_only=True, required=False)
    chart_id_external = serializers.CharField(source='chart.chart_id_external', read_only=True, required=False)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PeerReviewAllocation
        fields = (
            'id', 'chart_id', 'song_title', 'chart_url', 'chart_id_external',
            'status', 'status_display', 'allocated_at'
        )
        read_only_fields = fields


class PeerReviewSerializer(serializers.ModelSerializer):
    """互评记录序列化器（包含评分内容）"""
    
    class Meta:
        model = PeerReview
        fields = ('id', 'score', 'comment', 'created_at')
        read_only_fields = ('id', 'created_at')


class PeerReviewSubmitSerializer(serializers.ModelSerializer):
    """互评提交序列化器"""
    
    class Meta:
        model = PeerReview
        fields = ('score', 'comment')
        extra_kwargs = {
            'score': {'required': True},
            'comment': {'required': False},
        }
    
    def validate_score(self, value):
        """验证评分范围"""
        from .models import PEER_REVIEW_MAX_SCORE
        if value < 0 or value > PEER_REVIEW_MAX_SCORE:
            raise serializers.ValidationError(
                f'评分必须在0-{PEER_REVIEW_MAX_SCORE}之间'
            )
        return value


class ChartDetailSerializer(serializers.ModelSerializer):
    """谱面详情序列化器（包含评分统计）"""
    song = SongListSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Chart
        fields = (
            'id', 'username', 'song', 'status', 'status_display',
            'chart_url', 'chart_id_external', 'review_count', 'total_score', 'average_score',
            'reviews', 'created_at', 'submitted_at', 'review_completed_at'
        )
        read_only_fields = fields
    
    def get_reviews(self, obj):
        """获取该谱面的所有评分（匿名）"""
        reviews = PeerReview.objects.filter(
            chart=obj
        ).values('score', 'comment', 'created_at').order_by('-created_at')
        return PeerReviewSerializer(reviews, many=True).data


# ==================== 第二轮竞标相关序列化器 ====================

from .models import SecondBiddingRound, SecondBid, SecondBidResult


class SecondBiddingRoundSerializer(serializers.ModelSerializer):
    """第二轮竞标轮次序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    bidding_round_name = serializers.CharField(source='first_bidding_round.name', read_only=True)
    
    class Meta:
        model = SecondBiddingRound
        fields = (
            'id', 'first_bidding_round', 'bidding_round_name', 'status', 'status_display',
            'created_at', 'started_at', 'completed_at'
        )
        read_only_fields = ('id', 'created_at')


class AvailableChartSerializer(serializers.ModelSerializer):
    """可竞标的一半谱面序列化器"""
    song = SongListSerializer(read_only=True)
    creator_username = serializers.CharField(source='user.username', read_only=True)
    part_one_chart_url = serializers.CharField(source='part_one_chart.chart_url', read_only=True, required=False)
    part_one_chart_id_external = serializers.CharField(
        source='part_one_chart.chart_id_external', read_only=True, required=False
    )
    
    class Meta:
        model = Chart
        fields = (
            'id', 'song', 'creator_username', 'part_one_chart_url', 'part_one_chart_id_external',
            'average_score', 'created_at'
        )
        read_only_fields = fields


class SecondBidSerializer(serializers.ModelSerializer):
    """第二轮竞标序列化器"""
    song_title = serializers.CharField(source='target_chart_part_one.song.title', read_only=True)
    creator_username = serializers.CharField(source='target_chart_part_one.user.username', read_only=True)
    bidder_username = serializers.CharField(source='bidder.username', read_only=True)
    
    class Meta:
        model = SecondBid
        fields = (
            'id', 'target_chart_part_one', 'song_title', 'creator_username',
            'bidder_username', 'amount', 'is_dropped', 'created_at'
        )
        read_only_fields = ('id', 'bidder_username', 'is_dropped', 'created_at')
    
    def validate_amount(self, value):
        """验证竞标金额"""
        if value <= 0:
            raise serializers.ValidationError('竞标金额必须大于0')
        if value > 999:
            raise serializers.ValidationError('竞标金额不能超过999')
        return value
    
    def validate(self, data):
        """验证不能对自己的谱面进行竞标"""
        user = self.context['request'].user
        target_chart = data.get('target_chart_part_one')
        
        if target_chart and target_chart.user == user:
            raise serializers.ValidationError('不能对自己的谱面进行竞标')
        
        return data


class SecondBidResultSerializer(serializers.ModelSerializer):
    """第二轮竞标结果序列化器"""
    song_title = serializers.CharField(source='part_one_chart.song.title', read_only=True)
    part_one_creator_username = serializers.CharField(
        source='part_one_chart.user.username', read_only=True
    )
    winner_username = serializers.CharField(source='winner.username', read_only=True)
    allocation_type_display = serializers.CharField(source='get_allocation_type_display', read_only=True)
    completed_chart_id = serializers.IntegerField(source='completed_chart.id', read_only=True, required=False)
    
    class Meta:
        model = SecondBidResult
        fields = (
            'id', 'song_title', 'part_one_creator_username', 'winner_username',
            'allocation_type', 'allocation_type_display', 'completed_chart_id', 'allocated_at'
        )
        read_only_fields = fields
