#!/usr/bin/env python3
"""
Instagram Post Markdown Table Generator
Genera una tabla en Markdown con información detallada de posts de Instagram
"""

import json
import datetime
from typing import List, Dict, Any
import os

def load_instagram_data(filename: str) -> Dict[Any, Any]:
    """Carga los datos del archivo JSON de Instagram"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {filename}")
        return {}
    except json.JSONDecodeError:
        print(f"❌ Error: El archivo {filename} no tiene un formato JSON válido")
        return {}

def format_date(timestamp: int) -> str:
    """Convierte timestamp a fecha legible"""
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

def get_best_image_url(post: Dict[Any, Any]) -> str:
    """Obtiene la mejor resolución de imagen disponible"""
    image_versions = post.get('image_versions', [])
    if image_versions:
        # Ordenar por resolución (ancho * alto) y tomar la mayor
        best_image = max(image_versions, key=lambda x: x.get('width', 0) * x.get('height', 0))
        return best_image.get('url', 'N/A')
    return 'N/A'

def get_post_url(code: str) -> str:
    """Genera la URL de la publicación de Instagram"""
    if code and code != 'N/A':
        return f"https://www.instagram.com/p/{code}/"
    return 'N/A'

def get_top_comment(post: Dict[Any, Any]) -> str:
    """Obtiene el comentario con más likes"""
    comments = post.get('comments_detailed', [])
    if not comments:
        return 'Sin comentarios'
    
    # Buscar el comentario con más likes
    top_comment = max(comments, key=lambda x: x.get('like_count', 0))
    comment_text = top_comment.get('text', 'Sin texto')
    likes = top_comment.get('like_count', 0)
    
    # Truncar comentario si es muy largo
    if len(comment_text) > 100:
        comment_text = comment_text[:97] + "..."
    
    return f"{comment_text} ({likes} likes)"

def clean_caption(caption: str) -> str:
    """Limpia el caption completo para la tabla"""
    if not caption:
        return 'Sin caption'
    
    # Remover saltos de línea pero mantener el texto completo
    cleaned = caption.replace('\n', ' ').replace('\r', ' ')
    # Solo eliminar espacios extra
    cleaned = ' '.join(cleaned.split())
    
    # NO truncar - devolver el caption completo
    return cleaned

def escape_markdown(text: str) -> str:
    """Escapa caracteres especiales de Markdown"""
    if not text:
        return text
    
    # Escapar caracteres que pueden romper la tabla
    text = text.replace('|', '\\|')
    text = text.replace('[', '\\[')
    text = text.replace(']', '\\]')
    text = text.replace('*', '\\*')
    text = text.replace('_', '\\_')
    
    return text

def generate_markdown_table(data: Dict[Any, Any]) -> str:
    """Genera la tabla en formato Markdown"""
    if not data or 'posts' not in data:
        return "❌ No se encontraron datos de posts en el archivo"
    
    posts = data['posts']
    profile = data.get('profile', {})
    
    # Ordenar posts por fecha (más recientes primero)
    sorted_posts = sorted(posts, key=lambda x: x.get('taken_at', 0), reverse=True)
    
    # Encabezado de la tabla
    markdown = f"""# 📊 Posts de Instagram - @{profile.get('username', 'N/A')}

**Perfil:** {profile.get('full_name', 'N/A')}  
**Seguidores:** {profile.get('followers_count', 'N/A'):,}  
**Total de posts:** {len(posts)}  
**Última actualización:** {data.get('metadata', {}).get('last_full_scrape', 'N/A')}

---

| # | Fecha | Imagen | Caption | Likes | Comentarios | Top Comentario | Link Post |
|---|-------|--------|---------|-------|-------------|----------------|-----------|"""
    
    for i, post in enumerate(sorted_posts, 1):
        date = format_date(post.get('taken_at', 0)) if post.get('taken_at') else 'N/A'
        
        # Obtener imagen de mejor calidad
        image_url = get_best_image_url(post)
        image_link = f"![Imagen]({image_url})" if image_url != 'N/A' else 'Sin imagen'
        
        # Caption limpio
        caption = escape_markdown(clean_caption(post.get('caption', '')))
        
        # Likes y comentarios - ARREGLAR EL PROBLEMA DE LIKES
        likes = post.get('like_count', 0)
        
        # Si like_count es 3 o menor, usar el conteo real de likes_detailed
        likes_detailed = post.get('likes_detailed', [])
        if likes <= 3 and len(likes_detailed) > 3:
            likes = len(likes_detailed)  # Usar el conteo real
            
        if likes is None:
            likes = 0
        
        comments_count = post.get('comment_count', 0)
        if comments_count is None:
            comments_count = 0
        
        # Comentario top
        top_comment = escape_markdown(get_top_comment(post))
        
        # Link del post
        post_code = post.get('code', 'N/A')
        post_url = get_post_url(post_code)
        post_link = f"[Ver post]({post_url})" if post_url != 'N/A' else 'N/A'
        
        # Agregar fila a la tabla
        markdown += f"\n| {i} | {date} | {image_link} | {caption} | {likes} | {comments_count} | {top_comment} | {post_link} |"
    
    markdown += "\n\n---\n\n"
    
    # Estadísticas adicionales - USAR LIKES CORREGIDOS
    def get_real_likes(post):
        """Obtiene el conteo real de likes"""
        likes = post.get('like_count', 0)
        likes_detailed = post.get('likes_detailed', [])
        if likes <= 3 and len(likes_detailed) > 3:
            return len(likes_detailed)
        return likes if likes else 0
    
    total_likes = sum(get_real_likes(post) for post in posts)
    avg_likes = total_likes / len(posts) if posts else 0
    max_likes = max(get_real_likes(post) for post in posts) if posts else 0
    min_likes = min(get_real_likes(post) for post in posts) if posts else 0
    
    markdown += f"""## 📈 Estadísticas Resumen

- **Total de likes:** {total_likes:,}
- **Promedio de likes por post:** {avg_likes:.1f}
- **Post con más engagement:** {max_likes} likes
- **Post con menos engagement:** {min_likes} likes

---

*Generado el {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return markdown

def save_markdown_table(markdown_content: str, filename: str = "instagram_posts_table.md") -> None:
    """Guarda la tabla en un archivo Markdown"""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(markdown_content)
        print(f"✅ Tabla guardada en: {filename}")
    except Exception as e:
        print(f"❌ Error al guardar el archivo: {e}")

def main():
    """Función principal"""
    json_file = "instagram_cliniqmedellin.json"
    
    if not os.path.exists(json_file):
        print(f"❌ Error: No se encontró el archivo {json_file}")
        return
    
    print("🔍 Cargando datos de Instagram...")
    data = load_instagram_data(json_file)
    
    if not data:
        print("❌ No se pudieron cargar los datos")
        return
    
    print("📝 Generando tabla en Markdown...")
    markdown_table = generate_markdown_table(data)
    
    # Mostrar primeras líneas como preview
    lines = markdown_table.split('\n')
    print("\n📋 PREVIEW DE LA TABLA:")
    print('\n'.join(lines[:15]))
    print("...")
    print('\n'.join(lines[-5:]))
    
    # Guardar archivo
    output_file = "instagram_posts_table.md"
    save_markdown_table(markdown_table, output_file)
    
    print(f"\n🎉 ¡Tabla completa generada en {output_file}!")

if __name__ == "__main__":
    main()
