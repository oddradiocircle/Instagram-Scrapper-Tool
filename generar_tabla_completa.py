#!/usr/bin/env python3
"""
Ejecutor directo para generar tabla completa de Instagram
"""

import json
import datetime

# Cargar datos
with open('instagram_danielduquevel.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

def format_date(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

def get_best_image_url(post):
    image_versions = post.get('image_versions', [])
    if image_versions:
        best_image = max(image_versions, key=lambda x: x.get('width', 0) * x.get('height', 0))
        return best_image.get('url', 'N/A')
    return 'N/A'

def get_post_url(code):
    if code and code != 'N/A':
        return f"https://www.instagram.com/p/{code}/"
    return 'N/A'

def get_top_comment(post):
    comments = post.get('comments_detailed', [])
    if not comments:
        return 'Sin comentarios'
    
    top_comment = max(comments, key=lambda x: x.get('like_count', 0))
    comment_text = top_comment.get('text', 'Sin texto')
    likes = top_comment.get('like_count', 0)
    
    if len(comment_text) > 100:
        comment_text = comment_text[:97] + "..."
    
    return f"{comment_text} ({likes} likes)"

def escape_markdown(text):
    if not text:
        return text
    
    text = text.replace('|', '\\|')
    text = text.replace('[', '\\[')
    text = text.replace(']', '\\]')
    text = text.replace('*', '\\*')
    text = text.replace('_', '\\_')
    
    return text

def clean_caption_complete(caption):
    if not caption:
        return 'Sin caption'
    
    # Remover saltos de línea pero mantener el texto completo
    cleaned = caption.replace('\n', ' ').replace('\r', ' ')
    cleaned = ' '.join(cleaned.split())
    
    # NO truncar - devolver el caption completo
    return cleaned

# Procesar datos
posts = data['posts']
profile = data.get('profile', {})

# Filtrar posts válidos
valid_posts = [post for post in posts if post.get('id') and post.get('taken_at')]
sorted_posts = sorted(valid_posts, key=lambda x: x.get('taken_at', 0), reverse=True)

# Generar tabla
markdown = f"""# 📊 Posts de Instagram - @{profile.get('username', 'N/A')}

**Perfil:** {profile.get('full_name', 'N/A')}  
**Seguidores:** {profile.get('followers_count', 'N/A'):,}  
**Total de posts:** {len(valid_posts)}  
**Última actualización:** {data.get('metadata', {}).get('last_full_scrape', 'N/A')}

---

| # | Fecha | Imagen | Caption Completo | Likes | Comentarios | Top Comentario | Link Post |
|---|-------|--------|------------------|-------|-------------|----------------|-----------|"""

for i, post in enumerate(sorted_posts, 1):
    date = format_date(post.get('taken_at', 0)) if post.get('taken_at') else 'N/A'
    
    # Imagen
    image_url = get_best_image_url(post)
    image_link = f"![Imagen]({image_url})" if image_url != 'N/A' else 'Sin imagen'
    
    # Caption completo
    caption = escape_markdown(clean_caption_complete(post.get('caption', '')))
    
    # Likes
    likes = post.get('like_count', 0)
    likes_detailed = post.get('likes_detailed', [])
    if likes <= 3 and len(likes_detailed) > 3:
        likes = len(likes_detailed)
    if likes is None:
        likes = 0
    
    # Comentarios
    comments_count = post.get('comment_count', 0)
    if comments_count is None:
        comments_count = 0
    
    # Top comentario
    top_comment = escape_markdown(get_top_comment(post))
    
    # Link
    post_code = post.get('code', 'N/A')
    post_url = get_post_url(post_code)
    post_link = f"[Ver post]({post_url})" if post_url != 'N/A' else 'N/A'
    
    # Agregar fila
    markdown += f"\n| {i} | {date} | {image_link} | {caption} | {likes} | {comments_count} | {top_comment} | {post_link} |"

# Estadísticas
def get_real_likes(post):
    likes = post.get('like_count', 0)
    likes_detailed = post.get('likes_detailed', [])
    if likes <= 3 and len(likes_detailed) > 3:
        return len(likes_detailed)
    return likes if likes else 0

total_likes = sum(get_real_likes(post) for post in valid_posts)
avg_likes = total_likes / len(valid_posts) if valid_posts else 0
max_likes = max(get_real_likes(post) for post in valid_posts) if valid_posts else 0
min_likes = min(get_real_likes(post) for post in valid_posts) if valid_posts else 0

markdown += f"""

---

## 📈 Estadísticas Resumen

- **Total de posts válidos:** {len(valid_posts)}
- **Total de likes:** {total_likes:,}
- **Promedio de likes por post:** {avg_likes:.1f}
- **Post con más engagement:** {max_likes} likes
- **Post con menos engagement:** {min_likes} likes

---

*Generado el {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

# Guardar archivo
with open('instagram_danielduque_table_completo.md', 'w', encoding='utf-8') as file:
    file.write(markdown)

print("✅ Tabla completa generada en: instagram_danielduque_table_completo.md")
print(f"📊 Se procesaron {len(valid_posts)} posts")
