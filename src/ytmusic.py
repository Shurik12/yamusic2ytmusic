import requests
from tqdm import tqdm
from ytmusicapi import YTMusic
from typing import List, Dict, Any, Optional, Set, Union, Tuple
import yaml

from src.track import Track


class YTMusicClient:
    def __init__(
        self,
    ):
        session = requests.Session()
        session.proxies = {
            "http": "socks5://127.0.0.1:1080",
            "https": "socks5://127.0.0.1:1080"
        }
        session.trust_env = False

        self.ytmusic = YTMusic(
            auth="browser.json",
            requests_session=session,
        )

    def import_liked_tracks(
        self, tracks: List[Track]
    ) -> Tuple[List[Track], List[Track]]:
        not_found: List[Track] = []
        errors: List[Track] = []

        with tqdm(total=len(tracks), position=0, desc="Import tracks") as pbar:
            with tqdm(total=0, bar_format="{desc}", position=1) as trank_log:
                for track in tracks:
                    query = f"{track.artist} {track.name}"

                    try:
                        results = self.ytmusic.search(query, filter="songs")
                    except Exception as e:
                        errors.append(track)
                        pbar.write(f"Search error: {query}, {e}")
                        pbar.update(1)
                        continue

                    if not results:
                        not_found.append(track)
                        pbar.update(1)
                        continue

                    result = self._get_best_result(results, track)
                    try:
                        self.ytmusic.rate_song(result["videoId"], "LIKE")  # type: ignore
                    except Exception as e:
                        errors.append(track)
                        pbar.write(f"Error: {track.artist} - {track.name}, {e}")

                    pbar.update(1)
                    trank_log.set_description_str(f"{track.artist} - {track.name}")

        return not_found, errors

    def _get_best_result(self, results: List[dict], track: Track) -> dict:
        songs = []
        for result in results:
            if "videoId" not in result.keys():
                continue
            if result.get("category") == "Top result":
                return result
            if result.get("title") == track.name:
                return result
            songs.append(result)
        if len(songs) == 0:
            return results[0]
        return songs[0]

    # ===== Playlist Management Methods =====

    def get_playlists(self, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        """
        Retrieves the playlists in the user's library.

        Args:
            limit: Number of playlists to retrieve. None retrieves them all.

        Returns:
            List of owned playlists.
        """
        try:
            playlists = self.ytmusic.get_library_playlists(limit=limit)
            return playlists
        except Exception as e:
            print(f"Error getting library playlists: {e}")
            return []

    def print_playlists(self, playlists: List[Dict[str, Any]]):
        for playlist in playlists:
            print(f"{playlist["title"]}: {playlist["playlistId"]}")

    def create_playlist(
        self,
        title: str,
        description: str = str(),
        privacy_status: str = "PUBLIC",
        video_ids: Optional[List[str]] = None,
        source_playlist: Optional[str] = None,
    ) -> Union[str, Dict[str, Any]]:
        """
        Creates a new empty playlist and returns its id.

        Args:
            title: Playlist title
            description: Playlist description
            privacy_status: Playlists can be PUBLIC, PRIVATE, or UNLISTED. Default: PRIVATE
            video_ids: IDs of songs to create the playlist with
            source_playlist: Another playlist whose songs should be added to the new playlist

        Returns:
            ID of the YouTube playlist or full response if there was an error
        """
        try:
            result = self.ytmusic.create_playlist(
                title=title,
                description=description,
                privacy_status=privacy_status,
                video_ids=video_ids,
                source_playlist=source_playlist,
            )
            return result
        except Exception as e:
            error_msg = f"Exception creating playlist: {type(e).__name__}: {e}"
            return {"status": "ERROR", "error": error_msg}

    def get_playlist(self, playlist_id: str, limit: int = 5000) -> Dict[str, Any]:
        """Get playlist details and tracks"""
        try:
            return self.ytmusic.get_playlist(playlist_id, limit)
        except Exception as e:
            print(f"Error getting playlist {playlist_id}: {e}")
            return {}
        
    def get_playlist_artists(self, playlist: Dict[str, Any]) -> Set[str]:
        artists = set()
        for track in playlist["tracks"]:
            for artist in track["artists"]:
                artists.add(artist["name"])
        return artists

    def add_playlist_items(
        self, playlist_id: str, video_ids: List[str]
    ) -> Dict[str, Any]:
        """Add tracks to a playlist"""
        try:
            print (f"Add {video_ids} tracks to playlist {playlist_id}")
            return self.ytmusic.add_playlist_items(playlist_id, video_ids)  # type: ignore
        except Exception as e:
            print(f"Error adding items to playlist {playlist_id}: {e}")
            return {}

    def delete_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Delete a playlist"""
        try:
            return self.ytmusic.delete_playlist(playlist_id)  # type: ignore
        except Exception as e:
            error_msg = f"Error deleting playlist {playlist_id}: {e}"
            return {"status": "ERROR", "error": error_msg}

    def edit_playlist(
        self,
        playlist_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        privacy_status: Optional[str] = None,
        move_item: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """Edit playlist metadata"""
        try:
            return self.ytmusic.edit_playlist(
                playlist_id,
                title,
                description,
                privacy_status,
                move_item,  # type: ignore
            )
        except Exception as e:
            error_msg = f"Error editing playlist {playlist_id}: {e}"
            return {"status": "ERROR", "error": error_msg}

    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get all tracks from a playlist"""
        playlist = self.get_playlist(playlist_id, limit=5000)  # Large limit to get all
        return playlist.get("tracks", [])

    def search_and_add_to_playlist(
        self, playlist_id: str, tracks: List[Track], max_results: int = 5
    ) -> Tuple[int, int, int]:
        """
        Search for tracks and add them to a playlist.

        Args:
            playlist_id: Target playlist ID
            tracks: List of Track objects to search for
            max_results: Maximum number of search results to consider per track

        Returns:
            Tuple of (added_count, not_found_count, error_count)
        """
        added = 0
        not_found = 0
        errors = 0

        for track in tracks:
            query = f"{track.artist} {track.name}"

            try:
                results = self.ytmusic.search(query, filter="songs", limit=max_results)

                if not results:
                    not_found += 1
                    continue

                # Get the best result
                best_result = None
                for result in results:
                    if "videoId" in result:
                        best_result = result
                        break

                if best_result:
                    self.add_playlist_items(playlist_id, [best_result["videoId"]])
                    added += 1
                else:
                    not_found += 1

            except Exception as e:
                errors += 1
                print(f"Error processing {track.artist} - {track.name}: {e}")

        return added, not_found, errors

    def get_track_out_playlist(self) -> List[Dict[str, Any]]:
        """Get tracks from liked music that are not in any mapped playlist"""
        skip_track_videoId = set()
        like_playlist = {}
        playlists = self.get_playlists()

        for playlist_metadata in tqdm(
            playlists,
            desc="Getting playlists",
            total=len(playlists),
            unit="playlists",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
        ):
            if playlist_metadata["playlistId"] == "SE":
                continue
            else:
                playlist = self.get_playlist(playlist_metadata["playlistId"])
                if playlist["id"] == "LM":
                    like_playlist = playlist
                else:
                    skip_track_videoId.update(
                        [track["videoId"] for track in playlist["tracks"]]
                    )
        track_out_playlist = []

        for track in tqdm(
            like_playlist["tracks"],
            desc="Choosing tracks out playlist",
            total=len(like_playlist["tracks"]),
            unit="tracks",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
        ):
            if track["videoId"] not in skip_track_videoId:
                track_out_playlist.append(track)
        print(f"{len(track_out_playlist)} tracks out playlist")

        return track_out_playlist

    def print_tracks(self, tracks: List[Dict[str, Any]]):
        total_tracks = len(tracks)
        with open("tracks.txt", "w") as fw:
            for track in tqdm(
                tracks,
                desc="Writing tracks to file",
                total=total_tracks,
                unit="tracks",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            ):
                fw.write(
                    f"{track['artists'][0]['name']}\t{track['title']}\t{track['videoId']}\n"
                )

        print(f"Successfully wrote {total_tracks} tracks to tracks.txt")

    def distribute_tracks(self):
        with open("playlists_map.yaml", "r", encoding="utf-8") as f:
            playlists_map = yaml.safe_load(f)

        track_out_playlist = self.get_track_out_playlist()

        for playlist_info in playlists_map.values():
            add_tracks = []
            for track in track_out_playlist:
                if track["artists"][0]["name"] in playlist_info["artists"]:
                    add_tracks.append(track["videoId"])
            print (f"Add {len(add_tracks)} tracks to playlist {playlist_info["id"]}")
            if (len(add_tracks)):
                self.add_playlist_items(playlist_info["id"], add_tracks)
    
    def update_playlists_map(self, output_file: str = "playlists_map_updated.yaml"):
        """
        Update playlists_map.yaml file with current playlists and their artists.
        Excludes playlists with IDs in ["LM", "SE"].
        
        Args:
            output_file: Path to save the updated playlists map
        """
        print("Fetching playlists...")
        playlists = self.get_playlists()
        
        if not playlists:
            print("No playlists found.")
            return
        
        # Filter out excluded playlists
        excluded_ids = ["LM", "SE"]
        filtered_playlists = [ p for p in playlists if p.get("playlistId") not in excluded_ids ]
        
        print(f"Found {len(filtered_playlists)} playlists (excluding LM and SE)")
        
        playlists_map = {}
        
        for playlist_metadata in tqdm(filtered_playlists, desc="Processing playlists"):
            
            playlist = self.get_playlist(playlist_metadata["playlistId"])
            artists = self.get_playlist_artists(playlist)
            key = playlist_metadata["title"].replace(":", " -")  # Avoid YAML key issues with colons
            
            playlists_map[key] = {
                "id": playlist["id"],
                "artists": sorted(list(artists))
            }
        
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(playlists_map, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        print(f"\n✓ Updated playlists map saved to {output_file}")
        print(f"Total playlists in map: {len(playlists_map)}")
