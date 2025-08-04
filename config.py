# Configuración personalizada para Instagram Scraper

class Config:
    # Configuración de requests
    REQUEST_DELAY = 5  # Segundos entre requests (recomendado: 2-5)
    MAX_RETRIES = 3    # Número máximo de reintentos
    TIMEOUT = 30       # Timeout en segundos
    
    # Configuración de la interfaz
    WINDOW_SIZE = "1000x800"
    THEME_COLORS = {
        'bg_primary': '#1a1a2e',
        'bg_secondary': '#16213e', 
        'text_primary': '#e6e6e6',
        'text_accent': '#4cc9f0',
        'button_primary': '#4361ee',
        'button_hover': '#3a0ca3'
    }
    
    # Configuración de scraping
    DEFAULT_MAX_POSTS = 400      # Valor por defecto para posts
    DEFAULT_TARGET = "cliniqmedellin"  # Usuario por defecto
    
    # Configuración de comentarios y likes
    EXTRACT_COMMENTS = True      # Extraer comentarios detallados
    EXTRACT_LIKES = True         # Extraer lista de likes
    MAX_COMMENTS_PER_POST = 100  # Máximo comentarios por post
    MAX_LIKES_PER_POST = 50      # Máximo likes por post
    EXTRACT_COMMENT_REPLIES = True  # Extraer respuestas a comentarios
    
    # Configuración de modo incremental
    INCREMENTAL_MODE = True      # Activar modo incremental por defecto
    BACKUP_PREVIOUS_DATA = True  # Crear backup antes de actualizar
    
    # User Agent (actualizable)
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Configuración de archivos
    SAVE_JSON_DEFAULT = True
    SAVE_MEDIA_DEFAULT = True
    OUTPUT_FORMAT = "instagram_{username}_{timestamp}.json"
    
    # Configuración de logs
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_TO_FILE = False
    LOG_FILENAME = "scraper.log"
