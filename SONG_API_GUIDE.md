# 歌曲上传 API 文档

## 概述
歌曲上传 API 提供了完整的歌曲管理功能，包括上传、更新、删除和浏览歌曲。

### 核心特性
- 每个用户仅能上传一首歌曲
- 音频文件支持多种格式，最大 10MB
- 可选封面图片，最大 2MB
- 可选的网易音乐链接
- 自动去重：使用 SHA256 哈希识别重复音频
- 文件自动管理：删除歌曲时自动清理文件

---

## API 端点

### 1. 上传歌曲
**请求**
```
POST /api/songs/
Content-Type: multipart/form-data
Authorization: 需要认证
```

**参数**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| title | string | ✅ | 歌曲标题，1-100 个字符 |
| audio_file | file | ✅ | 音频文件，最大 10MB，支持 mp3, wav, flac, m4a, aac, ogg |
| cover_image | file | ❌ | 封面图片，最大 2MB，支持 jpg, png, gif |
| netease_url | string | ❌ | 网易音乐链接 |

**成功响应** (201 Created)
```json
{
  "success": true,
  "message": "歌曲上传成功",
  "song": {
    "id": 1,
    "title": "My Song",
    "audio_url": "http://localhost:8000/media/songs/audio_user1_song1.mp3",
    "cover_url": "http://localhost:8000/media/songs/cover_user1_song1.jpg",
    "netease_url": "https://music.163.com/...",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**错误响应** (400 Bad Request)
```json
{
  "success": false,
  "message": "您已上传过歌曲，如需更新请先删除后重新上传",
  "existing_song": {
    "id": 1,
    "title": "My Song",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**cURL 示例**
```bash
curl -X POST http://localhost:8000/api/songs/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -F "title=My Song" \
  -F "audio_file=@/path/to/song.mp3" \
  -F "cover_image=@/path/to/cover.jpg"
```

---

### 2. 获取当前用户的歌曲
**请求**
```
GET /api/songs/me/
Authorization: 需要认证
```

**成功响应** (200 OK)
```json
{
  "success": true,
  "song": {
    "id": 1,
    "title": "My Song",
    "audio_url": "http://localhost:8000/media/songs/audio_user1_song1.mp3",
    "cover_url": "http://localhost:8000/media/songs/cover_user1_song1.jpg",
    "netease_url": "https://music.163.com/...",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**错误响应** (404 Not Found)
```json
{
  "success": false,
  "message": "您尚未上传过歌曲"
}
```

**cURL 示例**
```bash
curl -X GET http://localhost:8000/api/songs/me/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

---

### 3. 更新当前用户的歌曲
**请求**
```
PUT /api/songs/me/
Content-Type: application/json
Authorization: 需要认证
```

**参数**（仅支持以下字段）
| 参数 | 类型 | 说明 |
|------|------|------|
| title | string | 新的歌曲标题 |
| netease_url | string | 新的网易音乐链接 |

**注意**: 不能通过此端点更新音频文件和封面图片，需要删除后重新上传

**成功响应** (200 OK)
```json
{
  "success": true,
  "message": "歌曲信息已更新",
  "song": {
    "id": 1,
    "title": "Updated Song Title",
    "audio_url": "http://localhost:8000/media/songs/audio_user1_song1.mp3",
    "cover_url": "http://localhost:8000/media/songs/cover_user1_song1.jpg",
    "netease_url": "https://music.163.com/...",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
  }
}
```

**cURL 示例**
```bash
curl -X PUT http://localhost:8000/api/songs/me/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Song Title"}'
```

---

### 4. 删除当前用户的歌曲
**请求**
```
DELETE /api/songs/me/
Authorization: 需要认证
```

**成功响应** (200 OK)
```json
{
  "success": true,
  "message": "歌曲已删除",
  "deleted_song": {
    "id": 1,
    "title": "My Song"
  }
}
```

**错误响应** (404 Not Found)
```json
{
  "success": false,
  "message": "您尚未上传过歌曲"
}
```

**cURL 示例**
```bash
curl -X DELETE http://localhost:8000/api/songs/me/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

---

### 5. 列出所有歌曲
**请求**
```
GET /api/songs/?page=1&page_size=10
Authorization: 不需要
```

**查询参数**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码 |
| page_size | integer | 10 | 每页数量 |

**成功响应** (200 OK)
```json
{
  "success": true,
  "count": 25,
  "page": 1,
  "page_size": 10,
  "total_pages": 3,
  "results": [
    {
      "id": 1,
      "title": "Song 1",
      "user": {
        "id": 1,
        "username": "user1"
      },
      "audio_url": "http://localhost:8000/media/songs/audio_user1_song1.mp3",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "title": "Song 2",
      "user": {
        "id": 2,
        "username": "user2"
      },
      "audio_url": "http://localhost:8000/media/songs/audio_user2_song2.mp3",
      "created_at": "2024-01-15T11:00:00Z"
    }
  ]
}
```

**cURL 示例**
```bash
curl -X GET "http://localhost:8000/api/songs/?page=1&page_size=20"
```

---

### 6. 获取特定歌曲详情
**请求**
```
GET /api/songs/{id}/
Authorization: 不需要
```

**URL 参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 歌曲 ID |

**成功响应** (200 OK)
```json
{
  "success": true,
  "song": {
    "id": 1,
    "title": "My Song",
    "user": {
      "id": 1,
      "username": "user1"
    },
    "audio_url": "http://localhost:8000/media/songs/audio_user1_song1.mp3",
    "cover_url": "http://localhost:8000/media/songs/cover_user1_song1.jpg",
    "netease_url": "https://music.163.com/...",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**错误响应** (404 Not Found)
```json
{
  "detail": "Not found."
}
```

**cURL 示例**
```bash
curl -X GET http://localhost:8000/api/songs/1/
```

---

## 文件管理

### 文件命名规则
上传的文件会根据用户 ID 和歌曲 ID 自动重命名，规则如下：

```
音频文件: audio_user{user_id}_song{song_id}.{ext}
封面图片: cover_user{user_id}_song{song_id}.{ext}
```

**示例**
- 用户 ID 为 1 上传的音频文件：`audio_user1_song1.mp3`
- 用户 ID 为 2 上传的封面图片：`cover_user2_song2.jpg`

### 支持的文件格式

**音频文件**
- mp3, wav, flac, m4a, aac, ogg

**图片文件**
- jpg, png, gif

### 文件大小限制
- 音频文件：≤ 10MB
- 封面图片：≤ 2MB
- 单次请求：≤ 10MB

---

## 错误处理

### 常见错误状态码

| 状态码 | 说明 | 常见原因 |
|--------|------|--------|
| 201 | Created | 歌曲上传成功 |
| 200 | OK | 请求成功 |
| 400 | Bad Request | 参数错误、文件大小超限、格式不支持 |
| 401 | Unauthorized | 未认证或会话过期 |
| 404 | Not Found | 歌曲不存在 |
| 413 | Payload Too Large | 上传文件过大 |

### 错误响应示例

**文件大小超限**
```json
{
  "success": false,
  "errors": {
    "audio_file": ["音频文件不能超过 10MB"]
  }
}
```

**不支持的文件格式**
```json
{
  "success": false,
  "errors": {
    "audio_file": ["不支持的文件格式，仅支持: mp3, wav, flac, m4a, aac, ogg"]
  }
}
```

**标题为空**
```json
{
  "success": false,
  "errors": {
    "title": ["标题不能为空"]
  }
}
```

---

## 去重机制

系统使用 SHA256 哈希来识别重复的音频文件。

### 去重流程
1. 上传时，系统会计算音频文件的 SHA256 哈希
2. 存储用户信息和音频文件
3. 不同用户可以上传相同的音频文件（哈希相同）
4. 系统能够识别哪些用户上传了相同的音频

### 好处
- **节省空间**：通过后期优化可以实现硬链接或符号链接来节省存储
- **去重检测**：能够检测到重复上传
- **版权追踪**：便于追踪哪些用户上传了相同音频

---

## 使用示例

### JavaScript (Fetch)

**上传歌曲**
```javascript
const formData = new FormData();
formData.append('title', 'My Song');
formData.append('audio_file', audioFileInput.files[0]);
formData.append('cover_image', coverImageInput.files[0]);
formData.append('netease_url', 'https://music.163.com/...');

const response = await fetch('http://localhost:8000/api/songs/', {
  method: 'POST',
  credentials: 'include',  // 包含认证 cookie
  body: formData
});

const data = await response.json();
console.log(data);
```

**获取用户的歌曲**
```javascript
const response = await fetch('http://localhost:8000/api/songs/me/', {
  method: 'GET',
  credentials: 'include'
});

const data = await response.json();
console.log(data.song);
```

**更新歌曲信息**
```javascript
const response = await fetch('http://localhost:8000/api/songs/me/', {
  method: 'PUT',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'Updated Song Title',
    netease_url: 'https://music.163.com/...'
  })
});

const data = await response.json();
console.log(data);
```

**删除歌曲**
```javascript
const response = await fetch('http://localhost:8000/api/songs/me/', {
  method: 'DELETE',
  credentials: 'include'
});

const data = await response.json();
console.log(data);
```

**浏览所有歌曲**
```javascript
const response = await fetch('http://localhost:8000/api/songs/?page=1&page_size=20', {
  method: 'GET'
});

const data = await response.json();
console.log(data.results);  // 歌曲列表
console.log(data.total_pages);  // 总页数
```

### Python (Requests)

**上传歌曲**
```python
import requests

files = {
    'audio_file': open('/path/to/song.mp3', 'rb'),
    'cover_image': open('/path/to/cover.jpg', 'rb')
}
data = {
    'title': 'My Song',
    'netease_url': 'https://music.163.com/...'
}

response = requests.post(
    'http://localhost:8000/api/songs/',
    files=files,
    data=data,
    cookies={'sessionid': 'YOUR_SESSION_ID'}
)

print(response.json())
```

---

## 常见问题

### Q: 如何更换上传的音频文件？
A: 使用 DELETE /api/songs/me/ 删除当前歌曲，然后重新 POST /api/songs/ 上传新的文件。

### Q: 为什么会显示"您已上传过歌曲"？
A: 每个用户仅能上传一首歌曲。如果需要上传新歌曲，必须先删除旧的。

### Q: 支持哪些音频格式？
A: mp3, wav, flac, m4a, aac, ogg。如需其他格式请联系管理员。

### Q: 文件上传后会被重命名吗？
A: 是的。文件会按照规则 `audio_user{user_id}_song{song_id}.{ext}` 重命名。

### Q: 如何确保两个用户的歌曲不会覆盖？
A: 系统使用用户 ID 和歌曲 ID 作为文件名的一部分，确保唯一性。每个用户的歌曲 ID 都是唯一的。

### Q: 删除歌曲后文件会被清理吗？
A: 是的。删除歌曲时，系统会自动删除对应的音频文件和封面图片。

---

## 相关 API

- [用户认证 API](./API_DOCS.md)
- [虚拟货币系统 API](./TOKEN_API_GUIDE.md)
