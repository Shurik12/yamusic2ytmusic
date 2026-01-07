### Set up
1. Create python virtual environment
```bash
python3 -m venv venv
```
2. Create alias in .bashrc
```bash
alias activate='source venv/bin/activate'
```
3. Activate/deactivate venv
```bash
activate
deactivate
```

### Download tracks
```bash
sudo apt install yt-dlp
mkdir -p ~/.config/yt-dlp
cat > ~/.config/yt-dlp/config << 'EOF'
--proxy socks5://127.0.0.1:9150
--user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
--referer "https://music.youtube.com"
--cookies-from-browser firefox  # If you exported from Firefox
--extract-audio
--audio-format mp3
--audio-quality 0
--embed-thumbnail
EOF
yt-dlp https://music.youtube.com/watch?v=vtNFAKSsgOU # download Sum41 - Screaming bloody murder
```