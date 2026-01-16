#!/usr/bin/env python
"""
歌曲 API 集成测试 - 使用 Django TestCase
运行方式: python manage.py test songs
"""
import os
import django
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xmmcg.settings')
django.setup()

from django.test import Client, TestCase
from django.contrib.auth.models import User
from PIL import Image
from songs.models import Song
import json


class SongAPITestCase(TestCase):
    """歌曲 API 测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client = Client()
    
    def test_upload_song(self):
        """测试上传歌曲"""
        print("\n【测试】上传歌曲")
        
        # 登录用户
        self.client.login(username='testuser', password='TestPass123!')
        
        # 创建测试音频文件
        audio_content = b'\xff\xfb\x90\x00' + b'test audio data' * 100
        audio_file = BytesIO(audio_content)
        audio_file.name = 'test_song.mp3'
        
        # 创建测试图片
        img = Image.new('RGB', (100, 100), color='red')
        cover_content = BytesIO()
        img.save(cover_content, format='PNG')
        cover_content.seek(0)
        cover_content.name = 'test_cover.png'
        
        # 上传歌曲
        response = self.client.post(
            '/api/songs/',
            {
                'title': 'Test Song',
                'audio_file': audio_file,
                'cover_image': cover_content,
                'netease_url': 'https://music.163.com/test'
            }
        )
        
        print(f"状态码: {response.status_code}")
        self.assertEqual(response.status_code, 201)
        print(f"[OK] 上传成功")
    
    def test_get_my_song(self):
        """测试获取用户歌曲"""
        print("\n【测试】获取用户歌曲")
        
        self.client.login(username='testuser', password='TestPass123!')
        
        # 先上传一首歌曲
        audio_content = b'\xff\xfb\x90\x00' + b'test audio data' * 100
        audio_file = BytesIO(audio_content)
        audio_file.name = 'test_song.mp3'
        
        self.client.post(
            '/api/songs/',
            {'title': 'Test Song', 'audio_file': audio_file}
        )
        
        # 获取用户歌曲
        response = self.client.get('/api/songs/me/')
        print(f"状态码: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        print(f"歌曲标题: {data['song']['title']}")
        print(f"[OK] 获取成功")
    
    def test_list_songs(self):
        """测试列表"""
        print("\n【测试】列出所有歌曲")
        
        response = self.client.get('/api/songs/')
        print(f"状态码: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        print(f"歌曲总数: {data['count']}")
        print(f"[OK] 获取列表成功")
    
    def test_duplicate_upload(self):
        """测试重复上传（应该失败）"""
        print("\n【测试】重复上传歌曲（应该失败）")
        
        self.client.login(username='testuser', password='TestPass123!')
        
        # 上传第一首歌曲
        audio_content = b'\xff\xfb\x90\x00' + b'test audio data' * 100
        audio_file = BytesIO(audio_content)
        audio_file.name = 'test_song1.mp3'
        
        response1 = self.client.post(
            '/api/songs/',
            {'title': 'Test Song 1', 'audio_file': audio_file}
        )
        print(f"第一次上传状态码: {response1.status_code}")
        self.assertEqual(response1.status_code, 201)
        
        # 尝试上传第二首歌曲（应该失败）
        audio_file2 = BytesIO(audio_content)
        audio_file2.name = 'test_song2.mp3'
        
        response2 = self.client.post(
            '/api/songs/',
            {'title': 'Test Song 2', 'audio_file': audio_file2}
        )
        print(f"第二次上传状态码: {response2.status_code}")
        self.assertEqual(response2.status_code, 400)
        print(f"[OK] 正确拒绝了重复上传")


if __name__ == '__main__':
    # 运行测试
    import unittest
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(SongAPITestCase)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印总结
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("[OK] 所有测试通过！")
    else:
        print("[FAIL] 某些测试失败")
        print(f"失败数: {len(result.failures)}")
        print(f"错误数: {len(result.errors)}")
    print("=" * 60)
