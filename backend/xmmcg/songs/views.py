from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Song
from .serializers import (
    SongUploadSerializer,
    SongDetailSerializer,
    SongListSerializer,
    SongUpdateSerializer,
)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def songs_root(request):
    """
    根路径处理：
    GET /api/songs/ - 列出所有歌曲（任何人）
    POST /api/songs/ - 上传歌曲（需要认证）
    """
    if request.method == 'GET':
        # 列出所有歌曲
        songs = Song.objects.all()
        
        # 分页处理
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = songs.count()
        songs_page = songs[start:end]
        
        serializer = SongListSerializer(songs_page, many=True)
        
        return Response({
            'success': True,
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': serializer.data
        }, status=status.HTTP_200_OK)
    
    else:  # POST - 上传歌曲
        # 检查认证
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': '需要认证'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = request.user
        
        # 检查用户是否已上传过歌曲
        try:
            existing_song = Song.objects.get(user=user)
            return Response({
                'success': False,
                'message': '您已上传过歌曲，如需更新请先删除后重新上传',
                'existing_song': {
                    'id': existing_song.id,
                    'title': existing_song.title,
                    'created_at': existing_song.created_at
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        except Song.DoesNotExist:
            pass  # 允许上传
        
        # 序列化并验证数据
        serializer = SongUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            song = serializer.save()
            return Response({
                'success': True,
                'message': '歌曲上传成功',
                'song': SongDetailSerializer(song).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_song(request):
    """
    获取当前用户上传的歌曲
    GET /api/songs/me/
    
    权限: 需要认证
    """
    user = request.user
    
    try:
        song = Song.objects.get(user=user)
    except Song.DoesNotExist:
        return Response({
            'success': False,
            'message': '您尚未上传过歌曲'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'success': True,
        'song': SongDetailSerializer(song).data
    }, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_my_song(request):
    """
    更新当前用户的歌曲信息
    PUT/PATCH /api/songs/me/
    
    权限: 需要认证
    可更新字段: title, netease_url
    """
    user = request.user
    
    try:
        song = Song.objects.get(user=user)
    except Song.DoesNotExist:
        return Response({
            'success': False,
            'message': '您尚未上传过歌曲'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = SongUpdateSerializer(song, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': '歌曲信息已更新',
            'song': SongDetailSerializer(song).data
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_my_song(request):
    """
    删除当前用户的歌曲
    DELETE /api/songs/me/
    
    权限: 需要认证
    删除后可重新上传新歌曲
    """
    user = request.user
    
    try:
        song = Song.objects.get(user=user)
    except Song.DoesNotExist:
        return Response({
            'success': False,
            'message': '您尚未上传过歌曲'
        }, status=status.HTTP_404_NOT_FOUND)
    
    song_id = song.id
    song_title = song.title
    song.delete()
    
    return Response({
        'success': True,
        'message': '歌曲已删除',
        'deleted_song': {
            'id': song_id,
            'title': song_title
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_song_detail(request, song_id):
    """
    获取特定歌曲的详情
    GET /api/songs/{id}/
    
    权限: 任何人
    用途: 竞标前查看详情
    """
    song = get_object_or_404(Song, id=song_id)
    
    return Response({
        'success': True,
        'song': SongDetailSerializer(song).data
    }, status=status.HTTP_200_OK)
