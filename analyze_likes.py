#!/usr/bin/env python3
"""
Instagram Post Likes Analyzer
Genera un consolidado de likes por post del archivo JSON de Instagram
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
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')

def analyze_likes_by_post(data: Dict[Any, Any]) -> None:
    """Analiza y muestra el consolidado de likes por post"""
    
    if not data or 'posts' not in data:
        print("❌ No se encontraron datos de posts en el archivo")
        return
    
    posts = data['posts']
    profile = data.get('profile', {})
    
    print("=" * 80)
    print("📊 CONSOLIDADO DE LIKES POR POST - CLINIQ MEDELLÍN")
    print("=" * 80)
    print(f"👤 Perfil: @{profile.get('username', 'N/A')}")
    print(f"📝 Nombre: {profile.get('full_name', 'N/A')}")
    print(f"👥 Seguidores: {profile.get('followers_count', 'N/A'):,}")
    print(f"📅 Última actualización: {data.get('metadata', {}).get('last_full_scrape', 'N/A')}")
    print(f"📱 Total de posts analizados: {len(posts)}")
    print("=" * 80)
    
    # Ordenar posts por fecha (más recientes primero)
    sorted_posts = sorted(posts, key=lambda x: x.get('taken_at', 0), reverse=True)
    
    total_likes = 0
    post_counter = 1
    
    print("📋 DETALLE POR POST:")
    print("-" * 80)
    print(f"{'#':<3} {'Fecha':<16} {'Likes':<6} {'Comentarios':<11} {'Código':<11} {'Tipo'}")
    print("-" * 80)
    
    for post in sorted_posts:
        post_id = post.get('id', 'N/A')
        code = post.get('code', 'N/A')
        likes = post.get('like_count', 0)
        comments = post.get('comment_count', 0)
        taken_at = post.get('taken_at', 0)
        media_type = post.get('media_type', 0)
        
        # Determinar tipo de contenido
        if media_type == 1:
            content_type = "Imagen"
        elif media_type == 2:
            content_type = "Video"
        elif media_type == 8:
            content_type = "Carrusel"
        else:
            content_type = f"Tipo {media_type}"
        
        date_str = format_date(taken_at) if taken_at else "N/A"
        
        print(f"{post_counter:<3} {date_str:<16} {likes:<6} {comments:<11} {code:<11} {content_type}")
        
        total_likes += likes
        post_counter += 1
    
    print("-" * 80)
    
    # Estadísticas generales
    if posts:
        avg_likes = total_likes / len(posts)
        max_likes_post = max(posts, key=lambda x: x.get('like_count', 0))
        min_likes_post = min(posts, key=lambda x: x.get('like_count', 0))
        
        print("\n📈 ESTADÍSTICAS GENERALES:")
        print("-" * 40)
        print(f"💯 Total de likes: {total_likes:,}")
        print(f"📊 Promedio de likes por post: {avg_likes:.1f}")
        print(f"🔝 Post con más likes: {max_likes_post.get('like_count', 0)} likes (Código: {max_likes_post.get('code', 'N/A')})")
        print(f"🔻 Post con menos likes: {min_likes_post.get('like_count', 0)} likes (Código: {min_likes_post.get('code', 'N/A')})")
        
        # Análisis por tipo de contenido
        content_stats = {}
        for post in posts:
            media_type = post.get('media_type', 0)
            likes = post.get('like_count', 0)
            
            if media_type == 1:
                content_type = "Imagen"
            elif media_type == 2:
                content_type = "Video"
            elif media_type == 8:
                content_type = "Carrusel"
            else:
                content_type = f"Tipo {media_type}"
            
            if content_type not in content_stats:
                content_stats[content_type] = {'count': 0, 'total_likes': 0}
            
            content_stats[content_type]['count'] += 1
            content_stats[content_type]['total_likes'] += likes
        
        print(f"\n🎯 ANÁLISIS POR TIPO DE CONTENIDO:")
        print("-" * 40)
        for content_type, stats in content_stats.items():
            avg = stats['total_likes'] / stats['count'] if stats['count'] > 0 else 0
            print(f"{content_type}: {stats['count']} posts, {avg:.1f} likes promedio")

def main():
    """Función principal"""
    # Buscar el archivo JSON de Instagram en el directorio actual
    json_file = "instagram_cliniqmedellin.json"
    
    if not os.path.exists(json_file):
        print(f"❌ Error: No se encontró el archivo {json_file}")
        print("💡 Asegúrate de que el archivo esté en el mismo directorio que este script")
        return
    
    print("🔍 Cargando datos de Instagram...")
    data = load_instagram_data(json_file)
    
    if data:
        analyze_likes_by_post(data)
    else:
        print("❌ No se pudieron cargar los datos")

if __name__ == "__main__":
    main()
