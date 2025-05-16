import os
import pygame
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import time
import random
from mutagen.mp3 import MP3

class SpotifyLikePlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify-like Player")
        self.root.geometry("1000x800")
        self.root.configure(bg="#121212")
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Player state
        self.paused = False
        self.stopped = True
        self.current_track = ""
        self.playlist = []
        self.filtered_playlist = []
        self.current_index = 0
        self.volume = 0.7
        self.repeat = False
        self.shuffle = False
        self.liked_songs = set()
        
        # UI Setup
        self.setup_ui()
        
        # Bind keyboard shortcuts
        self.root.bind("<space>", lambda e: self.toggle_play_pause())
        self.root.bind("<Left>", lambda e: self.prev_track())
        self.root.bind("<Right>", lambda e: self.next_track())
        self.root.bind("<Up>", lambda e: self.volume_up())
        self.root.bind("<Down>", lambda e: self.volume_down())
        
    def setup_ui(self):
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TScale", background="#121212", troughcolor="#535353")
        style.configure("Horizontal.TProgressbar", background="#1DB954", troughcolor="#535353")
        
        # Main frames
        self.sidebar_frame = tk.Frame(self.root, bg="#000000", width=200)
        self.sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        self.main_frame = tk.Frame(self.root, bg="#121212")
        self.main_frame.pack(side="right", fill="both", expand=True)
        
        # Sidebar content
        self.logo_label = tk.Label(self.sidebar_frame, text="Spotify", 
                                  font=("Helvetica", 16, "bold"), bg="#000000", fg="#1DB954")
        self.logo_label.pack(pady=20)
        
        self.home_btn = self.create_sidebar_button("Home", self.show_home)
        self.search_btn = self.create_sidebar_button("Search", self.show_search)
        self.library_btn = self.create_sidebar_button("Your Library", self.show_library)
        self.liked_btn = self.create_sidebar_button("Liked Songs", self.show_liked_songs)
        self.playlists_btn = self.create_sidebar_button("Playlists", self.show_playlists)
        
        # Search frame (initially hidden)
        self.search_frame = tk.Frame(self.main_frame, bg="#121212")
        
        self.search_entry = tk.Entry(self.search_frame, bg="#535353", fg="white", 
                                   insertbackground="white", font=("Helvetica", 14),
                                   relief="flat")
        self.search_entry.pack(fill="x", padx=20, pady=20)
        self.search_entry.bind("<KeyRelease>", self.search_songs)
        
        self.search_results_frame = tk.Frame(self.search_frame, bg="#121212")
        self.search_results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Main content frame
        self.content_frame = tk.Frame(self.main_frame, bg="#121212")
        
        # Current track info
        self.track_info_frame = tk.Frame(self.content_frame, bg="#121212")
        self.track_info_frame.pack(pady=20)
        
        # Album art placeholder (using a default image)
        self.album_art_img = Image.new('RGB', (200, 200), color='#535353')
        self.album_art_photo = ImageTk.PhotoImage(self.album_art_img)
        self.album_art = tk.Label(self.track_info_frame, image=self.album_art_photo, bg="#121212")
        self.album_art.pack(pady=10)
        
        self.current_track_label = tk.Label(self.track_info_frame, text="No track selected", 
                                           font=("Helvetica", 14), bg="#121212", fg="white")
        self.current_track_label.pack()
        
        self.current_artist_label = tk.Label(self.track_info_frame, text="", 
                                           font=("Helvetica", 12), bg="#121212", fg="#b3b3b3")
        self.current_artist_label.pack()
        
        # Like button
        self.like_btn = tk.Button(self.track_info_frame, text="♡", font=("Helvetica", 14), 
                                bg="#121212", fg="white", bd=0, command=self.toggle_like)
        self.like_btn.pack(pady=5)
        
        # Progress bar
        self.progress_frame = tk.Frame(self.content_frame, bg="#121212")
        self.progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", 
                                          length=600, mode="determinate")
        self.progress_bar.pack(fill="x")
        
        self.time_labels = tk.Frame(self.progress_frame, bg="#121212")
        self.time_labels.pack(fill="x")
        
        self.current_time = tk.Label(self.time_labels, text="0:00", bg="#121212", fg="white")
        self.current_time.pack(side="left")
        
        self.track_length = tk.Label(self.time_labels, text="0:00", bg="#121212", fg="white")
        self.track_length.pack(side="right")
        
        # Controls
        self.controls_frame = tk.Frame(self.content_frame, bg="#121212")
        self.controls_frame.pack(pady=20)
        
        # Buttons
        self.shuffle_btn = self.create_control_button("🔀", self.toggle_shuffle, "#535353")
        self.prev_btn = self.create_control_button("⏮", self.prev_track)
        self.play_btn = self.create_control_button("⏯", self.toggle_play_pause)
        self.next_btn = self.create_control_button("⏭", self.next_track)
        self.repeat_btn = self.create_control_button("🔁", self.toggle_repeat, "#535353")
        
        # Volume control
        self.volume_frame = tk.Frame(self.content_frame, bg="#121212")
        self.volume_frame.pack(pady=10)
        
        self.vol_down_btn = self.create_control_button("🔉", self.volume_down, size=20)
        self.vol_down_btn.pack(side="left", padx=5)
        
        self.volume_slider = ttk.Scale(self.volume_frame, from_=0, to=1, value=self.volume, 
                                      command=self.set_volume, orient="horizontal", length=100)
        self.volume_slider.pack(side="left", padx=5)
        
        self.vol_up_btn = self.create_control_button("🔊", self.volume_up, size=20)
        self.vol_up_btn.pack(side="left", padx=5)
        
        # Playlist
        self.playlist_frame = tk.Frame(self.content_frame, bg="#121212")
        self.playlist_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.playlist_label = tk.Label(self.playlist_frame, text="Playlist", 
                                      font=("Helvetica", 12), bg="#121212", fg="white")
        self.playlist_label.pack(anchor="w")
        
        # Create a scrollable frame for playlist
        self.playlist_canvas = tk.Canvas(self.playlist_frame, bg="#121212", highlightthickness=0)
        self.playlist_scrollbar = ttk.Scrollbar(self.playlist_frame, orient="vertical", 
                                              command=self.playlist_canvas.yview)
        self.playlist_scrollable_frame = tk.Frame(self.playlist_canvas, bg="#121212")
        
        self.playlist_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.playlist_canvas.configure(
                scrollregion=self.playlist_canvas.bbox("all")
            )
        )
        
        self.playlist_canvas.create_window((0, 0), window=self.playlist_scrollable_frame, anchor="nw")
        self.playlist_canvas.configure(yscrollcommand=self.playlist_scrollbar.set)
        
        self.playlist_canvas.pack(side="left", fill="both", expand=True)
        self.playlist_scrollbar.pack(side="right", fill="y")
        
        # Menu
        self.menubar = tk.Menu(self.root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Open File", command=self.add_file)
        self.filemenu.add_command(label="Open Folder", command=self.add_folder)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.root.config(menu=self.menubar)
        
        # Show home by default
        self.show_home()
        
        # Update progress bar
        self.update_progress()
    
    def create_sidebar_button(self, text, command):
        btn = tk.Button(self.sidebar_frame, text=text, font=("Helvetica", 12), 
                        bg="#000000", fg="white", bd=0, padx=20, pady=10,
                        command=command, anchor="w", width=15)
        btn.pack(fill="x")
        return btn
    
    def create_control_button(self, text, command, bg="#1DB954", size=30):
        btn = tk.Button(self.controls_frame, text=text, font=("Helvetica", size), 
                        bg=bg, fg="white", bd=0, padx=10, command=command)
        btn.pack(side="left", padx=5)
        return btn
    
    def show_home(self):
        self.hide_all_frames()
        self.content_frame.pack(fill="both", expand=True)
        
        # Add welcome message
        welcome_label = tk.Label(self.content_frame, text="Welcome to SpotifyPy", 
                               font=("Helvetica", 24), bg="#121212", fg="white")
        welcome_label.pack(pady=50)
        
        # Add recent tracks or other home content
    
    def show_search(self):
        self.hide_all_frames()
        self.search_frame.pack(fill="both", expand=True)
        self.search_entry.focus()
    
    def show_library(self):
        self.hide_all_frames()
        self.content_frame.pack(fill="both", expand=True)
        # Implement library view
    
    def show_liked_songs(self):
        self.hide_all_frames()
        self.content_frame.pack(fill="both", expand=True)
        # Show only liked songs
        self.filtered_playlist = [track for track in self.playlist if track in self.liked_songs]
        self.update_playlist_display()
    
    def show_playlists(self):
        self.hide_all_frames()
        self.content_frame.pack(fill="both", expand=True)
        # Implement playlists view
    
    def hide_all_frames(self):
        for frame in [self.content_frame, self.search_frame]:
            frame.pack_forget()
    
    def search_songs(self, event=None):
        query = self.search_entry.get().lower()
        
        # Clear previous results
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
        
        if not query:
            return
            
        # Filter playlist
        self.filtered_playlist = [track for track in self.playlist 
                                 if query in os.path.basename(track).lower()]
        
        # Display results
        if not self.filtered_playlist:
            no_results = tk.Label(self.search_results_frame, text="No results found", 
                                 bg="#121212", fg="white")
            no_results.pack(pady=20)
        else:
            for i, track in enumerate(self.filtered_playlist):
                frame = tk.Frame(self.search_results_frame, bg="#121212")
                frame.pack(fill="x", pady=5)
                
                # Track number
                tk.Label(frame, text=str(i+1), bg="#121212", fg="white", width=3).pack(side="left")
                
                # Track name
                tk.Label(frame, text=os.path.basename(track), bg="#121212", fg="white", 
                       width=40, anchor="w").pack(side="left")
                
                # Play button
                play_btn = tk.Button(frame, text="▶", font=("Helvetica", 10), 
                                   bg="#121212", fg="white", bd=0,
                                   command=lambda t=track: self.play_from_search(t))
                play_btn.pack(side="right", padx=10)
    
    def play_from_search(self, track_path):
        # Find the track in main playlist
        try:
            index = self.playlist.index(track_path)
            self.load_track(index)
            self.show_home()  # Switch back to main view
        except ValueError:
            messagebox.showerror("Error", "Track not found in playlist")
    
    def add_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg")])
        if file_path:
            self.add_track_to_playlist(file_path)
    
    def add_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            for file in os.listdir(folder_path):
                if file.lower().endswith(('.mp3', '.wav', '.ogg')):
                    file_path = os.path.join(folder_path, file)
                    self.add_track_to_playlist(file_path)
    
    def add_track_to_playlist(self, file_path):
        self.playlist.append(file_path)
        self.update_playlist_display()
        
        if len(self.playlist) == 1:  # First track added
            self.load_track(0)
    
    def update_playlist_display(self):
        # Clear current display
        for widget in self.playlist_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Display current playlist (or filtered playlist)
        display_list = self.filtered_playlist if hasattr(self, 'filtered_playlist') and self.filtered_playlist else self.playlist
        
        for i, track in enumerate(display_list):
            frame = tk.Frame(self.playlist_scrollable_frame, bg="#121212")
            frame.pack(fill="x", pady=2)
            
            # Track number
            tk.Label(frame, text=str(i+1), bg="#121212", fg="white", width=3).pack(side="left")
            
            # Track name
            tk.Label(frame, text=os.path.basename(track), bg="#121212", fg="white", 
                   width=40, anchor="w").pack(side="left")
            
            # Play button
            play_btn = tk.Button(frame, text="▶", font=("Helvetica", 10), 
                               bg="#121212", fg="white", bd=0,
                               command=lambda idx=i: self.load_track(idx))
            play_btn.pack(side="right", padx=10)
    
    def load_track(self, index):
        if not self.playlist:
            return
            
        # Use filtered playlist if available, otherwise main playlist
        playlist_to_use = self.filtered_playlist if self.filtered_playlist else self.playlist
        
        if 0 <= index < len(playlist_to_use):
            # Find the index in the main playlist
            track_path = playlist_to_use[index]
            self.current_index = self.playlist.index(track_path)
            self.current_track = track_path
            
            # Update UI
            track_name = os.path.basename(self.current_track)
            self.current_track_label.config(text=track_name)
            self.current_artist_label.config(text="Artist")  # Would extract from metadata in a real app
            
            # Update like button
            if self.current_track in self.liked_songs:
                self.like_btn.config(text="♥", fg="#1DB954")
            else:
                self.like_btn.config(text="♡", fg="white")
            
            # Load and play the track
            pygame.mixer.music.load(self.current_track)
            pygame.mixer.music.play()
            self.stopped = False
            self.paused = False
            self.play_btn.config(text="⏸")
            
            # Update track length
            try:
                audio = MP3(self.current_track)
                self.track_duration = audio.info.length
            except:
                # Fallback if mutagen can't read the file
                sound = pygame.mixer.Sound(self.current_track)
                self.track_duration = sound.get_length()
                
            self.track_length.config(text=self.format_time(self.track_duration))
    
    def toggle_play_pause(self):
        if not self.playlist:
            return
            
        if self.stopped:
            self.load_track(self.current_index)
        elif self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
            self.play_btn.config(text="⏸")
        else:
            pygame.mixer.music.pause()
            self.paused = True
            self.play_btn.config(text="⏯")
    
    def stop(self):
        pygame.mixer.music.stop()
        self.stopped = True
        self.paused = False
        self.play_btn.config(text="⏯")
    
    def prev_track(self):
        if not self.playlist:
            return
            
        if self.shuffle:
            self.current_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_index = (self.current_index - 1) % len(self.playlist)
        self.load_track(self.current_index)
    
    def next_track(self):
        if not self.playlist:
            return
            
        if self.shuffle:
            self.current_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)
        self.load_track(self.current_index)
    
    def set_volume(self, val):
        self.volume = float(val)
        pygame.mixer.music.set_volume(self.volume)
    
    def volume_up(self):
        new_vol = min(1.0, self.volume + 0.1)
        self.volume_slider.set(new_vol)
        self.set_volume(new_vol)
    
    def volume_down(self):
        new_vol = max(0.0, self.volume - 0.1)
        self.volume_slider.set(new_vol)
        self.set_volume(new_vol)
    
    def toggle_repeat(self):
        self.repeat = not self.repeat
        if self.repeat:
            self.repeat_btn.config(bg="#1DB954")
            pygame.mixer.music.set_endevent(pygame.USEREVENT)
        else:
            self.repeat_btn.config(bg="#535353")
            pygame.mixer.music.set_endevent()
    
    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        if self.shuffle:
            self.shuffle_btn.config(bg="#1DB954")
        else:
            self.shuffle_btn.config(bg="#535353")
    
    def toggle_like(self):
        if self.current_track:
            if self.current_track in self.liked_songs:
                self.liked_songs.remove(self.current_track)
                self.like_btn.config(text="♡", fg="white")
            else:
                self.liked_songs.add(self.current_track)
                self.like_btn.config(text="♥", fg="#1DB954")
    
    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def update_progress(self):
        if not self.stopped and not self.paused:
            current_pos = pygame.mixer.music.get_pos() / 1000  # Convert to seconds
            if current_pos > 0:
                progress = (current_pos / self.track_duration) * 100
                self.progress_bar["value"] = progress
                self.current_time.config(text=self.format_time(current_pos))
                
                # Check if track ended
                if current_pos >= self.track_duration - 0.1:
                    if self.repeat:
                        self.load_track(self.current_index)
                    else:
                        self.next_track()
        
        self.root.after(1000, self.update_progress)

if __name__ == "__main__":
    root = tk.Tk()
    app = SpotifyLikePlayer(root)
    root.mainloop()