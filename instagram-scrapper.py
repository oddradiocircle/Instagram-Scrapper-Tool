import requests
import json
import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import os
import time
from datetime import datetime

class IncrementalDataManager:
    """Gestiona la carga y actualización incremental de datos"""
    
    def __init__(self, filename):
        self.filename = filename
        self.existing_data = None
        
    def load_existing_data(self):
        """Carga datos existentes del archivo JSON"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.existing_data = json.load(f)
                    return True
            except Exception as e:
                print(f"Error loading existing data: {e}")
                return False
        return False
    
    def get_existing_post_ids(self):
        """Obtiene los IDs de posts existentes"""
        if not self.existing_data:
            return set()
        return {post['id'] for post in self.existing_data.get('posts', [])}
    
    def get_existing_comment_ids(self, post_id):
        """Obtiene los IDs de comentarios existentes para un post específico"""
        if not self.existing_data:
            return set()
        
        for post in self.existing_data.get('posts', []):
            if post['id'] == post_id:
                comments = post.get('comments_detailed', [])
                return {comment['id'] for comment in comments if 'id' in comment}
        return set()
    
    def get_existing_like_usernames(self, post_id):
        """Obtiene los usernames que ya dieron like a un post"""
        if not self.existing_data:
            return set()
        
        for post in self.existing_data.get('posts', []):
            if post['id'] == post_id:
                likes = post.get('likes_detailed', [])
                return {like['username'] for like in likes if 'username' in like}
        return set()
    
    def merge_posts_data(self, new_posts):
        """Combina posts nuevos con existentes de forma inteligente"""
        if not self.existing_data:
            return new_posts
        
        existing_posts = {post['id']: post for post in self.existing_data.get('posts', [])}
        merged_posts = []
        
        for new_post in new_posts:
            post_id = new_post['id']
            
            if post_id in existing_posts:
                # Post existe, hacer merge inteligente
                existing_post = existing_posts[post_id]
                merged_post = self.merge_single_post(existing_post, new_post)
                merged_posts.append(merged_post)
            else:
                # Post nuevo, agregar directamente
                merged_posts.append(new_post)
        
        # Agregar posts existentes que no estaban en los nuevos
        for existing_id, existing_post in existing_posts.items():
            if not any(post['id'] == existing_id for post in new_posts):
                merged_posts.append(existing_post)
        
        return merged_posts
    
    def merge_single_post(self, existing_post, new_post):
        """Combina un post existente con datos nuevos"""
        merged = existing_post.copy()
        
        # Actualizar campos básicos (likes, comentarios pueden haber cambiado)
        # Siempre usar los valores más recientes para contadores
        merged.update({
            'like_count': new_post.get('like_count', existing_post.get('like_count', 0)),
            'comment_count': new_post.get('comment_count', existing_post.get('comment_count', 0))
        })
        
        # Merge comentarios
        if 'comments_detailed' in new_post:
            merged['comments_detailed'] = self.merge_comments(
                existing_post.get('comments_detailed', []),
                new_post.get('comments_detailed', [])
            )
        
        # Merge likes
        if 'likes_detailed' in new_post:
            merged['likes_detailed'] = self.merge_likes(
                existing_post.get('likes_detailed', []),
                new_post.get('likes_detailed', [])
            )
        
        # Agregar timestamp de última actualización
        merged['last_updated'] = datetime.now().isoformat()
        
        return merged
    
    def merge_comments(self, existing_comments, new_comments):
        """Combina comentarios existentes con nuevos"""
        existing_ids = {comment.get('id') for comment in existing_comments if 'id' in comment}
        merged_comments = existing_comments.copy()
        
        for new_comment in new_comments:
            if new_comment.get('id') not in existing_ids:
                merged_comments.append(new_comment)
        
        return merged_comments
    
    def merge_likes(self, existing_likes, new_likes):
        """Combina likes existentes con nuevos"""
        existing_usernames = {like.get('username') for like in existing_likes if 'username' in like}
        merged_likes = existing_likes.copy()
        
        for new_like in new_likes:
            if new_like.get('username') not in existing_usernames:
                merged_likes.append(new_like)
        
        return merged_likes
    
    def save_merged_data(self, profile_data, merged_posts):
        """Guarda los datos combinados"""
        result = {
            'profile': profile_data,
            'posts': merged_posts,
            'metadata': {
                'last_full_scrape': datetime.now().isoformat(),
                'total_posts': len(merged_posts),
                'incremental_updates': self.existing_data.get('metadata', {}).get('incremental_updates', 0) + 1 if self.existing_data else 1
            }
        }
        
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return result

class InstagramAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session_id = None
        self.csrf_token = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'X-IG-App-ID': '936619743392459',
            'X-Requested-With': 'XMLHttpRequest',
        }
        self.logged_in = False
        self.request_delay = 3 

    def login(self, username, password, gui_logger=None):
        try:
            self.session.get('https://www.instagram.com/', headers=self.headers)
            self.csrf_token = self.session.cookies.get('csrftoken')

            login_url = 'https://www.instagram.com/accounts/login/ajax/'
            login_data = {
                'username': username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(datetime.now().timestamp())}:{password}',
                'queryParams': {},
                'optIntoOneTap': 'false'
            }

            self.headers.update({
                'X-CSRFToken': self.csrf_token,
                'Referer': 'https://www.instagram.com/',
                'Content-Type': 'application/x-www-form-urlencoded'
            })

            response = self.session.post(login_url, data=login_data, headers=self.headers)
            response_data = response.json()

            if response_data.get('authenticated'):
                self.logged_in = True
                self.session_id = self.session.cookies.get('sessionid')
                self.csrf_token = self.session.cookies.get('csrftoken')
                if gui_logger:
                    gui_logger("[+] Successfully logged in to Instagram")
                return True
            else:
                if gui_logger:
                    gui_logger(f"[!] Login failed: {response_data.get('message', 'Unknown error')}")
                return False

        except Exception as e:
            if gui_logger:
                gui_logger(f"[!] Login error: {str(e)}")
            return False

    def get_user_info(self, username, gui_logger=None):
        if not self.logged_in:
            if gui_logger:
                gui_logger("[!] Not logged in")
            return None

        try:
            time.sleep(self.request_delay)
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            self.headers.update({
                'X-CSRFToken': self.csrf_token,
                'Referer': f'https://www.instagram.com/{username}/'
            })

            response = self.session.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get('data', {}).get('user', None)
            elif response.status_code == 404:
                if gui_logger:
                    gui_logger(f"[!] User @{username} not found")
            else:
                if gui_logger:
                    gui_logger(f"[!] API Error: HTTP {response.status_code}")
            return None

        except Exception as e:
            if gui_logger:
                gui_logger(f"[!] User info error: {str(e)}")
            return None

    def get_user_posts(self, user_id, count=12, gui_logger=None):
        if not self.logged_in:
            if gui_logger:
                gui_logger("[!] Not logged in")
            return []

        try:
            posts = []
            next_max_id = None
            retrieved = 0

            while retrieved < count:
                time.sleep(self.request_delay)
                url = f"https://www.instagram.com/api/v1/feed/user/{user_id}/?count={min(12, count-retrieved)}"
                if next_max_id:
                    url += f"&max_id={next_max_id}"

                self.headers.update({
                    'X-CSRFToken': self.csrf_token,
                    'Referer': f'https://www.instagram.com/'
                })

                response = self.session.get(url, headers=self.headers)
                if response.status_code != 200:
                    if gui_logger:
                        gui_logger(f"[!] Posts API Error: HTTP {response.status_code}")
                    break

                data = response.json()
                for item in data.get('items', []):
                    if retrieved >= count:
                        break

                    post = {
                        'id': item.get('id'),
                        'code': item.get('code'),
                        'media_type': item.get('media_type'),
                        'like_count': item.get('like_count'),
                        'comment_count': item.get('comment_count'),
                        'caption': item.get('caption', {}).get('text', '') if item.get('caption') else '',
                        'taken_at': item.get('taken_at'),
                        'image_versions': item.get('image_versions2', {}).get('candidates', []),
                        'video_versions': item.get('video_versions', []) if item.get('media_type') == 2 else []
                    }
                    posts.append(post)
                    retrieved += 1
                    if gui_logger:
                        gui_logger(f"[+] Retrieved post {retrieved}/{count}")

                next_max_id = data.get('next_max_id')
                if not next_max_id:
                    break

            return posts

        except Exception as e:
            if gui_logger:
                gui_logger(f"[!] Posts error: {str(e)}")
            return posts

    def get_post_comments(self, media_id, count=50, gui_logger=None):
        """Extrae comentarios detallados de un post específico"""
        if not self.logged_in:
            if gui_logger:
                gui_logger("[!] Not logged in")
            return []

        try:
            comments = []
            next_max_id = None
            retrieved = 0

            while retrieved < count:
                time.sleep(self.request_delay)
                url = f"https://www.instagram.com/api/v1/media/{media_id}/comments/"
                if next_max_id:
                    url += f"?max_id={next_max_id}"

                self.headers.update({
                    'X-CSRFToken': self.csrf_token,
                    'Referer': f'https://www.instagram.com/'
                })

                response = self.session.get(url, headers=self.headers)
                if response.status_code != 200:
                    if gui_logger:
                        gui_logger(f"[!] Comments API Error: HTTP {response.status_code}")
                    break

                data = response.json()
                for comment in data.get('comments', []):
                    if retrieved >= count:
                        break

                    comment_data = {
                        'id': comment.get('pk'),
                        'text': comment.get('text'),
                        'created_at': comment.get('created_at'),
                        'like_count': comment.get('comment_like_count'),
                        'user': {
                            'id': comment.get('user', {}).get('pk'),
                            'username': comment.get('user', {}).get('username'),
                            'full_name': comment.get('user', {}).get('full_name'),
                            'is_verified': comment.get('user', {}).get('is_verified')
                        },
                        'replies': []
                    }
                    
                    # Extraer respuestas al comentario si existen
                    if comment.get('child_comment_count', 0) > 0:
                        replies = self.get_comment_replies(comment.get('pk'), gui_logger)
                        comment_data['replies'] = replies

                    comments.append(comment_data)
                    retrieved += 1

                next_max_id = data.get('next_max_id')
                if not next_max_id:
                    break

            return comments

        except Exception as e:
            if gui_logger:
                gui_logger(f"[!] Comments error: {str(e)}")
            return []

    def get_comment_replies(self, comment_id, gui_logger=None):
        """Extrae respuestas a un comentario específico"""
        try:
            time.sleep(self.request_delay)
            url = f"https://www.instagram.com/api/v1/media/{comment_id}/comments/"

            self.headers.update({
                'X-CSRFToken': self.csrf_token,
                'Referer': f'https://www.instagram.com/'
            })

            response = self.session.get(url, headers=self.headers)
            if response.status_code != 200:
                return []

            data = response.json()
            replies = []
            
            for reply in data.get('comments', []):
                reply_data = {
                    'id': reply.get('pk'),
                    'text': reply.get('text'),
                    'created_at': reply.get('created_at'),
                    'like_count': reply.get('comment_like_count'),
                    'user': {
                        'id': reply.get('user', {}).get('pk'),
                        'username': reply.get('user', {}).get('username'),
                        'full_name': reply.get('user', {}).get('full_name'),
                        'is_verified': reply.get('user', {}).get('is_verified')
                    }
                }
                replies.append(reply_data)

            return replies

        except Exception as e:
            if gui_logger:
                gui_logger(f"[!] Replies error: {str(e)}")
            return []

    def get_post_likes(self, media_id, count=50, gui_logger=None):
        """Extrae la lista de usuarios que dieron like a un post"""
        if not self.logged_in:
            if gui_logger:
                gui_logger("[!] Not logged in")
            return []

        try:
            likes = []
            next_max_id = None
            retrieved = 0

            while retrieved < count:
                time.sleep(self.request_delay)
                url = f"https://www.instagram.com/api/v1/media/{media_id}/likers/"
                if next_max_id:
                    url += f"?max_id={next_max_id}"

                self.headers.update({
                    'X-CSRFToken': self.csrf_token,
                    'Referer': f'https://www.instagram.com/'
                })

                response = self.session.get(url, headers=self.headers)
                if response.status_code != 200:
                    if gui_logger:
                        gui_logger(f"[!] Likes API Error: HTTP {response.status_code}")
                    break

                data = response.json()
                for user in data.get('users', []):
                    if retrieved >= count:
                        break

                    like_data = {
                        'user_id': user.get('pk'),
                        'username': user.get('username'),
                        'full_name': user.get('full_name'),
                        'profile_pic_url': user.get('profile_pic_url'),
                        'is_verified': user.get('is_verified'),
                        'is_private': user.get('is_private')
                    }
                    likes.append(like_data)
                    retrieved += 1

                next_max_id = data.get('next_max_id')
                if not next_max_id:
                    break

            return likes

        except Exception as e:
            if gui_logger:
                gui_logger(f"[!] Likes error: {str(e)}")
            return []

class InstagramScraperApp:
    def __init__(self, root):
        self.root = root
        root.title("🔍 Advanced Instagram Scraper")
        root.geometry("1000x800")
        root.configure(bg="#1a1a2e")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#1a1a2e')
        
        self.configure_styles()

        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        login_frame = ttk.LabelFrame(main_frame, text=" Instagram Login ", padding=10)
        login_frame.pack(fill=tk.X, pady=5)

        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ig_username = ttk.Entry(login_frame, width=30)
        self.ig_username.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.ig_password = ttk.Entry(login_frame, width=30, show="*")
        self.ig_password.grid(row=1, column=1, padx=5, pady=5)

        self.login_btn = ttk.Button(login_frame, text="Login", command=self.do_login)
        self.login_btn.grid(row=0, column=2, rowspan=2, padx=10, pady=5, sticky=tk.NSEW)

        target_frame = ttk.LabelFrame(main_frame, text=" Target Profile ", padding=10)
        target_frame.pack(fill=tk.X, pady=5)

        ttk.Label(target_frame, text="Target Username:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.target_username = ttk.Entry(target_frame, width=30)
        self.target_username.grid(row=0, column=1, padx=5, pady=5)
        self.target_username.insert(0, "instagram")

        ttk.Label(target_frame, text="Max Posts:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.max_posts = ttk.Spinbox(target_frame, from_=1, to=1000, width=10)
        self.max_posts.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.max_posts.set(12)

        self.scrape_btn = ttk.Button(target_frame, text="Scrape Profile", command=self.start_scrape, state=tk.DISABLED)
        self.scrape_btn.grid(row=0, column=2, rowspan=2, padx=10, pady=5, sticky=tk.NSEW)

        options_frame = ttk.LabelFrame(main_frame, text=" Options ", padding=10)
        options_frame.pack(fill=tk.X, pady=5)

        # Primera fila de opciones
        options_row1 = ttk.Frame(options_frame)
        options_row1.pack(fill=tk.X, pady=2)

        self.save_json = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_row1, text="Save to JSON", variable=self.save_json).pack(side=tk.LEFT, padx=5)

        self.save_media = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_row1, text="Download Media", variable=self.save_media).pack(side=tk.LEFT, padx=5)

        # Segunda fila de opciones - Extracción detallada
        options_row2 = ttk.Frame(options_frame)
        options_row2.pack(fill=tk.X, pady=2)

        self.extract_comments = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_row2, text="Extract Comments", variable=self.extract_comments).pack(side=tk.LEFT, padx=5)

        self.extract_likes = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_row2, text="Extract Likes", variable=self.extract_likes).pack(side=tk.LEFT, padx=5)

        self.extract_replies = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_row2, text="Extract Replies", variable=self.extract_replies).pack(side=tk.LEFT, padx=5)

        self.incremental_mode = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_row2, text="Incremental Update", variable=self.incremental_mode).pack(side=tk.LEFT, padx=5)

        # Tercera fila - Límites
        options_row3 = ttk.Frame(options_frame)
        options_row3.pack(fill=tk.X, pady=2)

        ttk.Label(options_row3, text="Max Comments/Post:").pack(side=tk.LEFT, padx=5)
        self.max_comments = ttk.Spinbox(options_row3, from_=10, to=500, width=8)
        self.max_comments.pack(side=tk.LEFT, padx=5)
        self.max_comments.set(100)

        ttk.Label(options_row3, text="Max Likes/Post:").pack(side=tk.LEFT, padx=5)
        self.max_likes = ttk.Spinbox(options_row3, from_=10, to=200, width=8)
        self.max_likes.pack(side=tk.LEFT, padx=5)
        self.max_likes.set(50)

        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text=" Log ", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=100, height=25)
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X, pady=5)

        # Initialize API
        self.api = InstagramAPI()
        self.stop_event = threading.Event()

    def configure_styles(self):
        style = ttk.Style()
        style.configure('TLabel', background='#1a1a2e', foreground='#e6e6e6')
        style.configure('TLabelframe', background='#1a1a2e', foreground='#4cc9f0')
        style.configure('TLabelframe.Label', background='#1a1a2e', foreground='#4cc9f0')
        style.configure('TButton', background='#4361ee', foreground='white', padding=5)
        style.map('TButton',
                background=[('active', '#3a0ca3'), ('disabled', '#4a4a4a')],
                foreground=[('active', 'white'), ('disabled', '#7a7a7a')])
        style.configure('TEntry', fieldbackground='#16213e', foreground='white')
        style.configure('TSpinbox', fieldbackground='#16213e', foreground='white')
        style.configure('Vertical.TScrollbar', background='#16213e')

    def log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.status_var.set(message[:100])
        self.root.update()

    def do_login(self):
        username = self.ig_username.get().strip()
        password = self.ig_password.get().strip()

        if not username or not password:
            self.log("[!] Please enter both username and password")
            return

        self.login_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.perform_login, args=(username, password), daemon=True).start()

    def perform_login(self, username, password):
        self.log(f"[+] Attempting login as {username}...")
        success = self.api.login(username, password, self.log)
        if success:
            self.scrape_btn.config(state=tk.NORMAL)
            self.log("[+] Login successful! You can now scrape profiles")
        else:
            self.log("[!] Login failed. Check credentials and try again")
        self.login_btn.config(state=tk.NORMAL)

    def start_scrape(self):
        username = self.target_username.get().strip()
        if not username:
            self.log("[!] Please enter a target username")
            return

        try:
            max_posts = int(self.max_posts.get())
        except ValueError:
            self.log("[!] Please enter a valid number for max posts")
            return

        self.stop_event.clear()
        self.scrape_btn.config(state=tk.DISABLED)
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)

        threading.Thread(target=self.run_scrape, args=(username, max_posts), daemon=True).start()

    def run_scrape(self, username, max_posts):
        self.log(f"[+] Starting scrape for @{username}")

        # Inicializar gestor de datos incrementales
        filename = f"instagram_{username}.json"
        data_manager = IncrementalDataManager(filename)
        
        # Cargar datos existentes si el modo incremental está activado
        if self.incremental_mode.get():
            if data_manager.load_existing_data():
                self.log(f"[+] Loaded existing data from {filename}")
                existing_posts = len(data_manager.existing_data.get('posts', []) if data_manager.existing_data else [])
                self.log(f"[+] Found {existing_posts} existing posts")
            else:
                self.log(f"[+] No existing data found, starting fresh scrape")

        try:
            user_info = self.api.get_user_info(username, self.log)
            if not user_info:
                self.log("[!] Failed to get user info")
                return

            result = {
                'profile': {
                    'id': user_info.get('id'),
                    'username': user_info.get('username'),
                    'full_name': user_info.get('full_name'),
                    'biography': user_info.get('biography'),
                    'profile_pic_url': user_info.get('profile_pic_url_hd'),
                    'followers_count': user_info.get('edge_followed_by', {}).get('count'),
                    'following_count': user_info.get('edge_follow', {}).get('count'),
                    'is_private': user_info.get('is_private'),
                    'is_verified': user_info.get('is_verified'),
                    'external_url': user_info.get('external_url')
                },
                'posts': []
            }

            self.log("\n[+] Profile Information:")
            self.log(f"ID: {result['profile']['id']}")
            self.log(f"Username: @{result['profile']['username']}")
            self.log(f"Full Name: {result['profile']['full_name']}")
            self.log(f"Bio: {result['profile']['biography']}")
            self.log(f"Followers: {result['profile']['followers_count']}")
            self.log(f"Following: {result['profile']['following_count']}")
            self.log(f"Private: {'Yes' if result['profile']['is_private'] else 'No'}")
            self.log(f"Verified: {'Yes' if result['profile']['is_verified'] else 'No'}")

            if not user_info.get('is_private'):
                self.log("\n[+] Fetching posts...")
                new_posts = self.api.get_user_posts(user_info['id'], max_posts, self.log)
                
                # Determinar posts nuevos vs existentes
                if self.incremental_mode.get() and data_manager.existing_data:
                    existing_post_ids = data_manager.get_existing_post_ids()
                    truly_new_posts = [post for post in new_posts if post['id'] not in existing_post_ids]
                    self.log(f"\n[+] Found {len(truly_new_posts)} new posts out of {len(new_posts)} total")
                else:
                    truly_new_posts = new_posts
                    self.log(f"\n[+] Retrieved {len(new_posts)} posts")

                # Extraer detalles adicionales según las opciones seleccionadas
                if self.extract_comments.get() or self.extract_likes.get():
                    self.log("\n[+] Fetching post details...")
                    
                    # Procesar solo posts nuevos para detalles si es modo incremental
                    posts_to_process = truly_new_posts if self.incremental_mode.get() and data_manager.existing_data else new_posts
                    
                    for i, post in enumerate(posts_to_process):
                        post_id = post['id']
                        like_count = post.get('like_count', 0)
                        self.log(f"[+] Processing post {i+1}/{len(posts_to_process)} - ID: {post_id} - Likes: {like_count}")

                        # Extraer comentarios si está habilitado
                        if self.extract_comments.get():
                            max_comments = int(self.max_comments.get())
                            
                            # En modo incremental, obtener solo comentarios nuevos
                            if self.incremental_mode.get() and data_manager.existing_data:
                                existing_comment_ids = data_manager.get_existing_comment_ids(post_id)
                                all_comments = self.api.get_post_comments(post_id, max_comments, self.log)
                                new_comments = [c for c in all_comments if c.get('id') not in existing_comment_ids]
                                self.log(f"[+] Retrieved {len(new_comments)} new comments (total: {len(all_comments)})")
                            else:
                                new_comments = self.api.get_post_comments(post_id, max_comments, self.log)
                                self.log(f"[+] Retrieved {len(new_comments)} comments")
                            
                            post['comments_detailed'] = new_comments

                        # Extraer likes si está habilitado
                        if self.extract_likes.get():
                            max_likes = int(self.max_likes.get())
                            
                            # En modo incremental, obtener solo likes nuevos
                            if self.incremental_mode.get() and data_manager.existing_data:
                                existing_like_usernames = data_manager.get_existing_like_usernames(post_id)
                                all_likes = self.api.get_post_likes(post_id, max_likes, self.log)
                                new_likes = [l for l in all_likes if l.get('username') not in existing_like_usernames]
                                self.log(f"[+] Retrieved {len(new_likes)} new likes (total: {len(all_likes)})")
                            else:
                                new_likes = self.api.get_post_likes(post_id, max_likes, self.log)
                                self.log(f"[+] Retrieved {len(new_likes)} likes")
                            
                            post['likes_detailed'] = new_likes

                        # Pequeña pausa entre posts para evitar límites
                        time.sleep(2)
                else:
                    # Mostrar información de likes incluso cuando no se extraen detalles
                    self.log("\n[+] Posts summary with like counts:")
                    for i, post in enumerate(new_posts):
                        like_count = post.get('like_count', 0)
                        comment_count = post.get('comment_count', 0)
                        self.log(f"[+] Post {i+1}: ID: {post['id']} - Likes: {like_count} - Comments: {comment_count}")

                # Combinar datos si es modo incremental
                if self.incremental_mode.get() and data_manager.existing_data:
                    self.log("\n[+] Merging with existing data...")
                    final_posts = data_manager.merge_posts_data(new_posts)
                    self.log(f"[+] Final dataset: {len(final_posts)} posts")
                else:
                    final_posts = new_posts

                result['posts'] = final_posts

            if self.save_json.get():
                if self.incremental_mode.get():
                    # Usar el gestor para guardar datos combinados
                    final_result = data_manager.save_merged_data(result['profile'], result['posts'])
                    self.log(f"\n[+] Incremental data saved to {filename}")
                    incremental_count = final_result.get('metadata', {}).get('incremental_updates', 1)
                    self.log(f"[+] This is incremental update #{incremental_count}")
                else:
                    # Guardar normalmente
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    self.log(f"\n[+] Data saved to {filename}")

            # Mostrar estadísticas finales de likes
            if result['posts']:
                total_likes = sum(post.get('like_count', 0) for post in result['posts'])
                total_comments = sum(post.get('comment_count', 0) for post in result['posts'])
                avg_likes = total_likes / len(result['posts']) if result['posts'] else 0
                avg_comments = total_comments / len(result['posts']) if result['posts'] else 0
                
                self.log(f"\n[+] === FINAL STATISTICS ===")
                self.log(f"[+] Total Posts: {len(result['posts'])}")
                self.log(f"[+] Total Likes: {total_likes:,}")
                self.log(f"[+] Total Comments: {total_comments:,}")
                self.log(f"[+] Average Likes per Post: {avg_likes:.1f}")
                self.log(f"[+] Average Comments per Post: {avg_comments:.1f}")

            self.log("\n[+] Scrape completed successfully!")

        except Exception as e:
            self.log(f"[!] Scrape error: {str(e)}")
        finally:
            self.scrape_btn.config(state=tk.NORMAL)

def main():
    root = tk.Tk()
    app = InstagramScraperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
