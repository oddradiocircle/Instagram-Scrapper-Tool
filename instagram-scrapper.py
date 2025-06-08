import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import json
import os
import time
from urllib.parse import urljoin

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1'
}

class InstagramScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.stop_event = threading.Event()
        self.request_delay = 2 

    def make_request(self, url, gui_logger=None):
        if self.stop_event.is_set():
            return None
            
        try:
            time.sleep(self.request_delay) 
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                if 'login' in response.url.lower():
                    if gui_logger:
                        gui_logger("[!] Instagram is requiring login (got redirected to login page)")
                    return None
                return response.text
            elif response.status_code == 429:
                if gui_logger:
                    gui_logger("[!] Rate limited - try again later or use proxies")
                return None
            else:
                if gui_logger:
                    gui_logger(f"[!] HTTP {response.status_code} error")
                return None
                
        except Exception as e:
            if gui_logger:
                gui_logger(f"[!] Request error: {str(e)}")
            return None

    def get_profile_info(self, username, gui_logger=None):
        url = f"https://www.instagram.com/{username}/"
        html = self.make_request(url, gui_logger)
        if not html:
            return None
            
        soup = BeautifulSoup(html, 'html.parser')
        script_tags = soup.find_all('script', type='text/javascript')
        
        for script in script_tags:
            if 'window._sharedData' in script.text:
                try:
                    json_str = script.text.split('window._sharedData = ')[1].rstrip(';')
                    data = json.loads(json_str)
                    profile_data = data['entry_data']['ProfilePage'][0]['graphql']['user']
                    return profile_data
                except Exception as e:
                    if gui_logger:
                        gui_logger(f"[!] Error parsing profile data: {str(e)}")
                    return None
                    
        if gui_logger:
            gui_logger("[!] Could not find profile data in page source")
        return None

    def get_posts(self, username, count=12, gui_logger=None):
        profile_data = self.get_profile_info(username, gui_logger)
        if not profile_data:
            return []
            
        posts = []
        edges = profile_data['edge_owner_to_timeline_media']['edges']
        
        for edge in edges[:count]:
            if self.stop_event.is_set():
                break
            node = edge['node']
            post = {
                'id': node['id'],
                'shortcode': node['shortcode'],
                'display_url': node['display_url'],
                'is_video': node['is_video'],
                'likes': node['edge_liked_by']['count'],
                'comments': node['edge_media_to_comment']['count'],
                'timestamp': node['taken_at_timestamp'],
                'caption': node['edge_media_to_caption']['edges'][0]['node']['text'] if node['edge_media_to_caption']['edges'] else ''
            }
            posts.append(post)
            if gui_logger:
                gui_logger(f"[+] Found post: {post['shortcode']}")
                
        return posts

    def stop(self):
        self.stop_event.set()


class InstagramScraperApp:
    def __init__(self, root):
        self.root = root
        root.title("⚡ Instagram Scraper Tool ⚡")
        root.geometry("900x700")
        root.configure(bg="#0f0f1e")

        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TButton",
                      font=("Consolas", 12, "bold"),
                      foreground="#FF00AA",
                      background="#111122",
                      borderwidth=0,
                      padding=8)
        style.map("TButton",
                foreground=[('active', '#FF00FF')],
                background=[('active', '#220022')])

        style.configure("TEntry",
                      fieldbackground="#111122",
                      foreground="#FF00AA",
                      font=("Consolas", 12),
                      bordercolor="#FF00AA",
                      borderwidth=2,
                      padding=5)

        title = tk.Label(root, text="⚡ Instagram Scraper Tool ⚡",
                        font=("Consolas", 24, "bold"),
                        fg="#FF00AA", bg="#0f0f1e")
        title.pack(pady=15)

        input_frame = tk.Frame(root, bg="#0f0f1e")
        input_frame.pack(pady=10)

        self.username_entry = ttk.Entry(input_frame, width=40)
        self.username_entry.pack(side=tk.LEFT, padx=10)
        self.username_entry.insert(0, "instagram")

        self.scrape_button = ttk.Button(input_frame, text="SCRAPE PROFILE", command=self.start_scrape)
        self.scrape_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = ttk.Button(input_frame, text="STOP", command=self.stop_scrape, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)

        options_frame = tk.Frame(root, bg="#0f0f1e")
        options_frame.pack(pady=10)

        self.posts_var = tk.IntVar(value=1)
        self.save_var = tk.IntVar(value=1)

        ttk.Checkbutton(options_frame, text="Get Posts", variable=self.posts_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(options_frame, text="Save to JSON", variable=self.save_var).pack(side=tk.LEFT, padx=10)

        count_frame = tk.Frame(root, bg="#0f0f1e")
        count_frame.pack(pady=5)

        tk.Label(count_frame, text="Max Posts:", fg="#FF00AA", bg="#0f0f1e").pack(side=tk.LEFT)
        self.count_entry = ttk.Entry(count_frame, width=5)
        self.count_entry.pack(side=tk.LEFT, padx=5)
        self.count_entry.insert(0, "12")

        self.log_area = scrolledtext.ScrolledText(root, width=100, height=30,
                                               bg="#111122", fg="#FF00AA",
                                               font=("Consolas", 10),
                                               insertbackground="#FF00AA",
                                               borderwidth=0)
        self.log_area.pack(padx=20, pady=10)
        self.log_area.config(state=tk.DISABLED)

        self.scraper = InstagramScraper()

    def gui_logger(self, msg):
        def append():
            self.log_area.config(state=tk.NORMAL)
            self.log_area.insert(tk.END, msg + "\n")
            self.log_area.see(tk.END)
            self.log_area.config(state=tk.DISABLED)
        self.root.after(0, append)

    def start_scrape(self):
        username = self.username_entry.get().strip()
        if not username:
            self.gui_logger("[!] Please enter a username.")
            return

        try:
            max_items = int(self.count_entry.get())
        except ValueError:
            self.gui_logger("[!] Please enter a valid number for max items.")
            return

        self.scraper.stop_event.clear()
        self.scrape_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)

        threading.Thread(target=self.run_scrape, args=(username, max_items), daemon=True).start()

    def stop_scrape(self):
        self.gui_logger("[!] Stop requested...")
        self.scraper.stop()
        self.stop_button.config(state=tk.DISABLED)
        self.scrape_button.config(state=tk.NORMAL)

    def run_scrape(self, username, max_items):
        self.gui_logger(f"[+] Starting scrape for @{username}")
        
        try:
            # Get profile info
            profile_data = self.scraper.get_profile_info(username, self.gui_logger)
            if not profile_data:
                self.gui_logger("[!] Failed to get profile data - Instagram may be blocking requests")
                self.gui_logger("[!] Try again later or use a VPN/proxy")
                return

            result = {
                'profile': {
                    'username': profile_data['username'],
                    'full_name': profile_data['full_name'],
                    'biography': profile_data['biography'],
                    'profile_pic_url': profile_data['profile_pic_url_hd'],
                    'followers': profile_data['edge_followed_by']['count'],
                    'following': profile_data['edge_follow']['count'],
                    'is_private': profile_data['is_private'],
                    'is_verified': profile_data['is_verified'],
                    'external_url': profile_data['external_url']
                }
            }

            self.gui_logger("\n[+] Profile Information:")
            self.gui_logger(f"Username: @{result['profile']['username']}")
            self.gui_logger(f"Full Name: {result['profile']['full_name']}")
            self.gui_logger(f"Bio: {result['profile']['biography']}")
            self.gui_logger(f"Followers: {result['profile']['followers']:,}")
            self.gui_logger(f"Following: {result['profile']['following']:,}")
            self.gui_logger(f"Private: {'Yes' if result['profile']['is_private'] else 'No'}")
            self.gui_logger(f"Verified: {'Yes' if result['profile']['is_verified'] else 'No'}")

            if self.posts_var.get():
                self.gui_logger("\n[+] Fetching posts...")
                posts = self.scraper.get_posts(username, max_items, self.gui_logger)
                result['posts'] = posts
                self.gui_logger(f"\n[+] Found {len(posts)} posts")

            if self.save_var.get():
                filename = f"instagram_{username}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                self.gui_logger(f"\n[+] Data saved to {filename}")

            self.gui_logger("\n[+] Scrape complete!")

        except Exception as e:
            self.gui_logger(f"[!] Error during scrape: {str(e)}")
        finally:
            self.stop_button.config(state=tk.DISABLED)
            self.scrape_button.config(state=tk.NORMAL)


def main():
    root = tk.Tk()
    app = InstagramScraperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
