#!/usr/bin/env python3
"""
Script de diagnóstico para verificar los datos del JSON
"""

import json

def diagnose_json_data():
    """Diagnostica los datos del JSON para encontrar el problema"""
    
    # Cargar datos
    with open('instagram_cliniqmedellin.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posts = data.get('posts', [])
    
    print("🔍 DIAGNÓSTICO DE DATOS")
    print(f"Total de posts: {len(posts)}")
    print("\n" + "="*60)
    
    # Verificar primeros 5 posts
    print("\n📊 ANÁLISIS DE LOS PRIMEROS 5 POSTS:")
    
    for i, post in enumerate(posts[:5]):
        print(f"\n--- POST {i+1} ---")
        print(f"ID: {post.get('id', 'N/A')}")
        print(f"Like count (directo): {post.get('like_count')}")
        print(f"Like count (tipo): {type(post.get('like_count'))}")
        print(f"Comment count: {post.get('comment_count')}")
        
        # Verificar si hay likes_detailed
        likes_detailed = post.get('likes_detailed', [])
        print(f"Likes detallados disponibles: {len(likes_detailed)}")
        
        # Caption (solo primeros 100 chars)
        caption = post.get('caption', '')
        print(f"Caption (preview): {caption[:100]}...")
        
        # Verificar estructura completa
        print(f"Campos disponibles: {list(post.keys())}")
    
    # Estadísticas generales
    print("\n" + "="*60)
    print("\n📈 ESTADÍSTICAS GENERALES:")
    
    like_counts = [post.get('like_count', 0) for post in posts]
    print(f"Likes mínimos: {min(like_counts)}")
    print(f"Likes máximos: {max(like_counts)}")
    print(f"Promedio de likes: {sum(like_counts) / len(like_counts):.1f}")
    
    # Verificar cuántos posts tienen 3 likes exactamente
    posts_with_3_likes = [post for post in posts if post.get('like_count') == 3]
    print(f"Posts con exactamente 3 likes: {len(posts_with_3_likes)}")
    
    # Mostrar algunos posts con diferentes cantidades de likes
    print("\n🎯 MUESTRA DE POSTS CON DIFERENTES LIKES:")
    sorted_posts = sorted(posts, key=lambda x: x.get('like_count', 0), reverse=True)
    
    for i, post in enumerate(sorted_posts[:10]):
        likes = post.get('like_count', 0)
        caption_preview = post.get('caption', '')[:50] + "..." if post.get('caption') else "Sin caption"
        print(f"{i+1}. {likes} likes - {caption_preview}")
    
    print("\n🔍 VERIFICANDO POSTS CON MENOS LIKES:")
    for i, post in enumerate(sorted_posts[-10:]):
        likes = post.get('like_count', 0)
        caption_preview = post.get('caption', '')[:50] + "..." if post.get('caption') else "Sin caption"
        print(f"{i+1}. {likes} likes - {caption_preview}")

if __name__ == "__main__":
    diagnose_json_data()
