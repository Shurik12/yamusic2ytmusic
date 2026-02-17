import os
import yaml
from yandex_music import Client, Artist, Playlist
from typing import List, Set

from .track import Track
from tqdm import tqdm


class YaMusicHandle:
    def __init__(self, token: str):
        self.client = Client(token).init()

    def export_liked_tracks(self) -> List[Track]:
        tracks = self.client.users_likes_tracks().tracks

        result = []
        skipped_count = 0
        
        with tqdm(total=len(tracks), position=0, desc='Export tracks') as pbar:
            with tqdm(total=0, bar_format='{desc}', position=1) as trank_log:
                for i, track_short in enumerate(tracks):
                    try:
                        track = track_short.fetch_track()
                        
                        # Safely handle the case where there are no artists
                        if track.artists_name():
                            artist = track.artists_name()[0]
                        else:
                            artist = "Unknown Artist"
                        name = track.title
                        
                        result.append(Track(artist, name))
                        pbar.update(1)
                        trank_log.set_description_str(f'{i+1}/{len(tracks)}: {artist} - {name}')
                        
                    except TypeError as e:
                        # Skip tracks with the "missing id" error
                        if "missing 1 required positional argument: 'id'" in str(e):
                            skipped_count += 1
                            pbar.update(1)
                            pbar.write(f"Skipped track {i+1}: Missing artist ID")
                        else:
                            # Re-raise other TypeErrors
                            raise e
                            
                    except Exception as e:
                        # Skip tracks with any other errors
                        skipped_count += 1
                        pbar.update(1)
                        pbar.write(f"Skipped track {i+1}: {type(e).__name__}: {str(e)[:50]}...")
        
        print(f"\nSuccessfully exported {len(result)} tracks")
        if skipped_count > 0:
            print(f"Skipped {skipped_count} tracks due to errors")
        
        return result

    def get_playlists(self) -> List[Playlist]:
        try:
            playlists = self.client.users_playlists_list()
            return playlists
        except Exception as e:
            print(f"Error getting library playlists: {e}")
            return []
        
    def get_playlist_artists(self, playlist: Playlist) -> Set[str]:
        artists = set()
        try:
            tracks = playlist.fetch_tracks()
            for track in tracks:
                for artist in track.track.artists:
                    artists.add(artist.name)
        except:
            artists = set()
        return artists
        
        
    def print_playlists(self, playlists: List[Playlist]):
        for playlist in playlists:
            print (f"{playlist.title}: {playlist.kind}")

    def playlist_map(self, output_file: str = "yamusic.yaml"):
        print("Fetching playlists...")
        playlists = self.get_playlists()
        
        if not playlists:
            print("No playlists found.")
            return
        
        print(f"Found {len(playlists)} playlists")
        
        playlists_map = {}
        
        for playlist in tqdm(playlists, desc="Processing playlists"):
            
            artists = self.get_playlist_artists(playlist)
            key = playlist["title"].replace(":", " -")  # Avoid YAML key issues with colons
            
            playlists_map[key] = {
                "kind": playlist["kind"],
                "artists": sorted(list(artists))
            }
        
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(playlists_map, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        print(f"\n✓ Updated playlists map saved to {output_file}")
        print(f"Total playlists in map: {len(playlists_map)}")

    def download_tracks(self, tracks, name):
        chars_to_remove = ['/', '"', ':', "?", "*", "¿"]
        folder = f"downloads/{name}"
        os.makedirs(folder, exist_ok=True)
        existed_tracks = [f"{folder}/{f}" for f in os.listdir(folder)]
        for track in tqdm(tracks, desc="Downloading tracks"):
            title = track["title"]
            for char in chars_to_remove:
                title = title.replace(char, "")

            if track["artists"] and len(track["artists"]) > 0:
                artist = track["artists"][0]["name"]
                for char in chars_to_remove:
                    artist = artist.replace(char, "")
                filename = f"{folder}/{artist} - {title}.mp3"
            else:
                filename = f"{folder}/{title}.mp3"
            if filename not in existed_tracks: 
                download_infos = track.get_download_info()
                bitrate = 192
                for download_info in download_infos:
                    bitrate = max(download_info["bitrate_in_kbps"], bitrate)
                track.download(filename, 'mp3', bitrate)

    def download_playist(self, playlist: Playlist):
        short_tracks = playlist.fetch_tracks()
        print(f"Get {len(short_tracks)} tracks from playlist {playlist["title"]}")
        track_ids = [track["id"] for track in short_tracks]
        tracks = self.client.tracks(track_ids)
        self.download_tracks(tracks, playlist["title"])

    def download_playlists(self):
        playlists = self.get_playlists()
        for playlist in playlists:
            self.download_playist(playlist)

    def download_like_tracks(self):
        trackslist = self.client.users_likes_tracks()
        if trackslist:
            tracks = trackslist.fetch_tracks()
            self.download_tracks(tracks, "Like")

