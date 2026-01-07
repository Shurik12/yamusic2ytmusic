import argparse
import yaml

from src.yamusic import YaMusicHandle
from src.ytmusic import YTMusicClient
from src.cli import CLI


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file {config_path} not found!")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config.yaml: {e}")
        exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transfer tracks from Yandex.Music to YouTube Music"
    )
    parser.add_argument(
        "--config", type=str, default="config.yaml", help="Path to config.yaml file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="tracks.json",
        help="Output json file for transfer results",
    )
    parser.add_argument(
        "--no-tor", action="store_true", help="Disable Tor proxy (overrides config)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    # Initialize Yandex Music exporter
    yandex_token = config["yandex_music"]["token"]
    if yandex_token == "YOUR_YANDEX_MUSIC_TOKEN_HERE":
        print("Please update your Yandex Music token in config.yaml")
        exit(1)

    yamusic = YaMusicHandle(yandex_token)

    # Tor proxy configuration
    tor_config = config.get("tor_proxy", {})
    use_tor = tor_config.get("enabled", True) and not args.no_tor
    proxy_host = tor_config.get("host", "127.0.0.1")
    proxy_port = tor_config.get("port", 9150)

    if use_tor:
        print(f"Using Tor proxy: {proxy_host}:{proxy_port}")
    else:
        print("Tor proxy disabled")

    ytmusic = YTMusicClient(
        client_id=config["youtube_music"]["client_id"],
        client_secret=config["youtube_music"]["client_secret"],
        use_tor=use_tor,
        tor_host=proxy_host,
        tor_port=proxy_port,
    )

    # Start CLI interface
    cli = CLI(yamusic, ytmusic, args)
    cli.run()


if __name__ == "__main__":
    main()
