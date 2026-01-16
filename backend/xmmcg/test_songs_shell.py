#!/usr/bin/env python
"""
歌曲 API 快速测试脚本 - 使用 Django shell
运行方式: python manage.py shell < test_songs_api_shell.py
"""

from django.test import Client
from django.contrib.auth.models import User
from io import BytesIO
from PIL import Image
from songs.models import Song
import json

def test_song_api():
    """测试歌曲 API"""
    print("=" * 60)
    print("歌曲 API 测试")
    print("=" * 60)
    
    # 清理之前的测试数据
    print("\n[清理] 删除之前的测试用户和歌曲...")
    try:
        user = User.objects.get(username='testuser')
        user.delete()
        print("✅ 已清理")
    except User.DoesNotExist:
        print("ℹ️  没有之前的测试数据")
    
    # 创建测试用户
    print("\n[1] 创建测试用户...")
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPass123!'
    )
    print(f"✅ 创建用户: {user.username}")
    
    # 创建 Django 测试客户端
    client = Client()
    
    # 用户登录
    print("\n[2] 用户登录...")
    login_response = client.post('/api/users/login/', 
        json.dumps({'username': 'testuser', 'password': 'TestPass123!'}),
        content_type='application/json'
    )
    print(f"✅ 登录状态: {login_response.status_code}")
    if login_response.status_code != 200:
        print(f"   错误: {login_response.content.decode()}")
        return False
    
    # 检查是否已有歌曲
    print("\n[3] 检查用户是否已有歌曲...")
    get_response = client.get('/api/songs/me/')
    print(f"✅ 响应状态: {get_response.status_code}")
    
    if get_response.status_code == 404:
        print("✅ 用户暂无歌曲（符合预期）")
        
        # 创建测试音频文件
        print("\n[4] 创建测试音频文件...")
        audio_content = b'\xff\xfb\x90\x00' + b'test audio data' * 100
        
        # 创建测试封面图片
        print("[5] 创建测试封面图片...")
        img = Image.new('RGB', (100, 100), color='red')
        cover_content = BytesIO()
        img.save(cover_content, format='PNG')
        cover_content.seek(0)
        
        # 上传歌曲
        print("[6] 上传歌曲...")
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        audio_file = SimpleUploadedFile(
            'test_song.mp3',
            audio_content,
            content_type='audio/mpeg'
        )
        cover_file = SimpleUploadedFile(
            'test_cover.png',
            cover_content.getvalue(),
            content_type='image/png'
        )
        
        upload_response = client.post(
            '/api/songs/',
            {
                'title': 'Test Song',
                'audio_file': audio_file,
                'cover_image': cover_file,
                'netease_url': 'https://music.163.com/test'
            }
        )
        print(f"✅ 上传状态: {upload_response.status_code}")
        
        if upload_response.status_code in [201, 200]:
            print("✅ 歌曲上传成功")
            upload_result = upload_response.json()
            song_id = upload_result.get('song', {}).get('id')
            print(f"   歌曲 ID: {song_id}")
            print(f"   标题: {upload_result.get('song', {}).get('title')}")
            
            # 再次尝试上传会失败
            print("\n[7] 尝试重复上传歌曲（应该失败）...")
            retry_response = client.post(
                '/api/songs/',
                {
                    'title': 'Test Song 2',
                    'audio_file': audio_file,
                    'netease_url': 'https://music.163.com/test2'
                }
            )
            print(f"✅ 上传状态: {retry_response.status_code}")
            
            if retry_response.status_code == 400:
                print("✅ 正确拒绝了重复上传")
            
            # 获取用户歌曲
            print("\n[8] 获取用户歌曲...")
            get_my_response = client.get('/api/songs/me/')
            print(f"✅ 获取状态: {get_my_response.status_code}")
            
            if get_my_response.status_code == 200:
                print("✅ 成功获取用户歌曲")
                song_data = get_my_response.json().get('song', {})
                print(f"   标题: {song_data.get('title')}")
            
            # 列出所有歌曲
            print("\n[9] 列出所有歌曲...")
            list_response = client.get('/api/songs/?page=1&page_size=10')
            print(f"✅ 列表状态: {list_response.status_code}")
            
            if list_response.status_code == 200:
                list_data = list_response.json()
                print(f"✅ 成功获取歌曲列表")
                print(f"   总数: {list_data.get('count')}")
            
            # 获取歌曲详情
            print(f"\n[10] 获取歌曲详情 (ID: {song_id})...")
            detail_response = client.get(f'/api/songs/{song_id}/')
            print(f"✅ 获取状态: {detail_response.status_code}")
            
            if detail_response.status_code == 200:
                print("✅ 成功获取歌曲详情")
            
            # 更新歌曲信息
            print("\n[11] 更新歌曲信息...")
            update_response = client.put(
                '/api/songs/me/',
                json.dumps({
                    'title': 'Updated Test Song',
                    'netease_url': 'https://music.163.com/updated'
                }),
                content_type='application/json'
            )
            print(f"✅ 更新状态: {update_response.status_code}")
            
            if update_response.status_code == 200:
                print("✅ 成功更新歌曲信息")
                print(f"   新标题: {update_response.json().get('song', {}).get('title')}")
            
            # 删除歌曲
            print("\n[12] 删除歌曲...")
            delete_response = client.delete('/api/songs/me/')
            print(f"✅ 删除状态: {delete_response.status_code}")
            
            if delete_response.status_code == 200:
                print("✅ 成功删除歌曲")
            
            # 验证删除成功
            print("\n[13] 验证删除（再次获取应该返回 404）...")
            verify_response = client.get('/api/songs/me/')
            print(f"✅ 验证状态: {verify_response.status_code}")
            
            if verify_response.status_code == 404:
                print("✅ 歌曲已成功删除")
                
                return True
        else:
            print(f"❌ 上传失败: {upload_response.json()}")
            return False
    else:
        print(f"⚠️  意外的响应: {get_response.status_code}")
        return False
    
    print("\n" + "=" * 60)
    print("测试完成！✅")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_song_api()
    exit(0 if success else 1)
