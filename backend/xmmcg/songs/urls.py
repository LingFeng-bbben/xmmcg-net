from django.urls import path
from . import views

urlpatterns = [
    # 根路径：GET 列表，POST 上传
    path('', views.songs_root, name='songs-root'),
    
    # 用户自己的歌曲操作
    path('me/', views.get_my_song, name='get-my-song'),
    path('me/', views.update_my_song, name='update-my-song'),
    path('me/', views.delete_my_song, name='delete-my-song'),
    
    # 获取特定歌曲
    path('<int:song_id>/', views.get_song_detail, name='get-song-detail'),
]
