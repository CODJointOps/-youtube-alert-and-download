import discord
from discord.ext import commands, tasks
import feedparser
import yt_dlp as youtube_dl
from config import DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, YOUTUBE_CHANNEL_IDS
import os

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

download_dir = 'downloads'
os.makedirs(download_dir, exist_ok=True)

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': f'{download_dir}/%(title)s [%(id)s].%(ext)s',
}

downloaded_videos_file = 'downloaded_videos.txt'
def get_downloaded_videos():
    if not os.path.exists(downloaded_videos_file):
        return set()
    with open(downloaded_videos_file, 'r') as file:
        return set(file.read().splitlines())

def add_downloaded_video(video_id):
    with open(downloaded_videos_file, 'a') as file:
        file.write(video_id + '\n')

def get_latest_video_url(channel_id):
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(rss_url)
    latest_entry = feed.entries[0] if feed.entries else None
    return latest_entry.link, latest_entry.yt_videoid if latest_entry else (None, None)

@tasks.loop(minutes=10)
async def check_new_videos():
    downloaded_videos = get_downloaded_videos()
    for channel_id in YOUTUBE_CHANNEL_IDS:
        video_url, video_id = get_latest_video_url(channel_id)
        if video_url and video_id not in downloaded_videos:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            add_downloaded_video(video_id)
            channel = bot.get_channel(int(DISCORD_CHANNEL_ID))
            await channel.send(f"@everyone New tard video dropped and has been archived: {video_url}")

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    check_new_videos.start()

bot.run(DISCORD_BOT_TOKEN)
