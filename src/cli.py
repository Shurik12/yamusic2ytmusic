import json

from .yamusic import YaMusicHandle
from .ytmusic import YTMusicClient

class CLI:
    def __init__(self, yamusic: YaMusicHandle, ytmusic: YTMusicClient, args):
        self.yamusic = yamusic
        self.ytmusic = ytmusic
        self.args = args
        self.running = True
        
    def print_menu(self):
        """Display the main menu"""
        print("\n" + "="*50)
        print("YouTube Music CLI Menu")
        print("="*50)
        print("1. List playlists")
        print("2. Get playlist artists")
        print("3. Transfer tracks from Yandex Music to YouTube Music")
        print("4. Get tracks from liked playlist")
        print("5. Print tracks to file")
        print("6. Update playlist map")
        print("7. Distribute tracks by playlists")
        print("8. Download playlists")
        print("9. Download like tracks as playlist")
        print("q, quit, exit - Exit program")
        print("="*50)
    
    def list_playlists(self):
        """List all playlists"""
        try:
            playlists = self.ytmusic.get_playlists()
            self.ytmusic.print_playlists(playlists)
        except Exception as e:
            print(f"Error listing playlists: {e}")
    
    def get_playlist_artists(self):
        """Get artists from a specific playlist"""
        try:
            playlists = self.ytmusic.get_playlists()
            playlist = self.ytmusic.get_playlist(playlists[1]["playlistId"])
            artists = self.ytmusic.get_playlist_artists(playlist)
            print (playlist["title"])
            for artist in artists:
                print (artist)
        except Exception as e:
            print(f"Error getting playlist artists: {e}")

    def move_tracks(self, out_path: str) -> None:
        data = {
            'liked_tracks': [],
            'not_found': [],
            'errors': [],
        }
        
        print('Exporting liked tracks from Yandex Music...')
        tracks = self.yamusic.export_liked_tracks()
        tracks.reverse()

        for track in tracks:
            data['liked_tracks'].append({
                'artist': track.artist,
                'name': track.name
            })

        print('Importing liked tracks to Youtube Music...')
        not_found, errors = self.ytmusic.import_liked_tracks(tracks)

        for track in not_found:
            data['not_found'].append({
                'artist': track.artist,
                'name': track.name
            })
            print(f'Not found: {track.artist} - {track.name}')
        
        for track in errors:
            data['errors'].append({
                'artist': track.artist,
                'name': track.name
            })
            print(f'Error: {track.artist} - {track.name}')
        
        print(f'\nSummary: {len(tracks)} total tracks')
        print(f'Successfully imported: {len(tracks) - len(not_found) - len(errors)}')
        print(f'Not found: {len(not_found)} tracks')
        print(f'Errors: {len(errors)} tracks')

        str_data = json.dumps(data, indent=2, ensure_ascii=False)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(str_data)
    
    def transfer_tracks(self):
        """Transfer tracks from Yandex Music to YouTube Music"""
        confirm = input("\nThis will transfer liked tracks from Yandex Music to YouTube Music. Continue? (y/n): ")
        if confirm.lower() in ['y', 'yes']:
            self.move_tracks(self.args.output)
        else:
            print("Transfer cancelled.")
    
    def run(self):
        """Main CLI loop"""
        print("\n" + "="*50)
        print("YouTube Music CLI Started")
        self.print_menu()
        print("Type 'help' to see this menu again")
        print("="*50)
        
        while self.running:
            try:
                command = input("\nEnter command (or 'help' for menu): ").strip().lower()
                
                if command in ['q', 'quit', 'exit']:
                    print("Goodbye!")
                    self.running = False
                elif command in ['help', '?', '']:
                    self.print_menu()
                elif command in ['1', 'list']:
                    self.list_playlists()
                elif command in ['2', 'artists']:
                    self.get_playlist_artists()
                elif command in ['3', 'transfer']:
                    self.transfer_tracks()
                elif command in ['4', 'tracks']:
                    tracks = self.ytmusic.get_track_out_playlist()
                    print(f"Found {len(tracks)} tracks in liked playlist")
                elif command in ['5', 'print']:
                    tracks = self.ytmusic.get_track_out_playlist()
                    self.ytmusic.print_tracks(tracks)
                    print(f"Printed {len(tracks)} tracks to tracks.txt")
                elif command in ['6', 'playlist_map']:
                    self.ytmusic.update_playlists_map("1.yaml")
                elif command in ['7', 'distribute']:
                    self.ytmusic.distribute_tracks()
                elif command in ['8']:
                    self.yamusic.download_playlists()
                elif command in ['9']:
                    self.yamusic.download_like_tracks()
                else:
                    print("Unknown command. Type 'help' to see available commands.")
            
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                self.running = False
            except Exception as e:
                print(f"Error: {e}")