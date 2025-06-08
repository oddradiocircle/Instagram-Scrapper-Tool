import requests
import json
import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import os
import time
from datetime import datetime

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

        self.save_json = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Save to JSON", variable=self.save_json).pack(side=tk.LEFT, padx=5)

        self.save_media = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Download Media", variable=self.save_media).pack(side=tk.LEFT, padx=5)

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
                posts = self.api.get_user_posts(user_info['id'], max_posts, self.log)
                result['posts'] = posts
                self.log(f"\n[+] Retrieved {len(posts)} posts")

            if self.save_json.get():
                filename = f"instagram_{username}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                self.log(f"\n[+] Data saved to {filename}")

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
