# Ejemplo de uso de Instagram Scraper con extracción de comentarios y likes

## 🚀 Guía de Uso para Extraer Comentarios, Likes y Respuestas

### Pasos para usar la aplicación:

1. **Ejecutar la aplicación:**
   ```bash
   python instagram-scrapper.py
   ```

2. **Configurar Login:**
   - Username: [Tu usuario de Instagram]
   - Password: [Tu contraseña]
   - Hacer clic en "Login"

3. **Configurar Target:**
   - Target Username: cliniqmedellin
   - Max Posts: 400

4. **Opciones de Extracción:**
   ✅ Save to JSON
   ✅ Extract Comments (extrae comentarios detallados)
   ✅ Extract Likes (extrae lista de usuarios que dieron like)
   ✅ Extract Replies (extrae respuestas a comentarios)
   
   - Max Comments/Post: 100
   - Max Likes/Post: 50

5. **Hacer clic en "Scrape Profile"**

### 📊 Datos que se extraen:

#### Para cada POST:
```json
{
  "id": "123456789",
  "code": "ABC123",
  "like_count": 150,
  "comment_count": 25,
  "caption": "Texto del post...",
  "comments_detailed": [
    {
      "id": "comment_id",
      "text": "Texto del comentario",
      "created_at": 1234567890,
      "like_count": 5,
      "user": {
        "username": "usuario_comentario",
        "full_name": "Nombre Completo",
        "is_verified": false
      },
      "replies": [
        {
          "id": "reply_id",
          "text": "Respuesta al comentario",
          "user": {
            "username": "usuario_respuesta"
          }
        }
      ]
    }
  ],
  "likes_detailed": [
    {
      "user_id": "user_123",
      "username": "usuario_like",
      "full_name": "Nombre Usuario",
      "is_verified": false,
      "is_private": false
    }
  ]
}
```

### 📁 Archivo de salida:
- Nombre: `instagram_cliniqmedellin.json`
- Ubicación: Misma carpeta del script
- Formato: JSON con todos los datos extraídos

### ⚠️ Recomendaciones:
1. **Límites conservadores:** Usa máximo 100 comentarios y 50 likes por post
2. **Paciencia:** La extracción detallada toma más tiempo
3. **Cuentas públicas:** Solo funciona con perfiles públicos
4. **Uso responsable:** Respeta los términos de servicio de Instagram

### 🔧 Configuración optimizada para Clínica Medellín:
- Target: cliniqmedellin
- Max Posts: 400
- Max Comments: 100
- Max Likes: 50
- Todas las opciones de extracción activadas

Esta configuración te dará un análisis completo de la interacción en los posts.
