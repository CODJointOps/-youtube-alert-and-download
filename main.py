import discord
from discord.ext import commands, tasks
import feedparser
import yt_dlp as youtube_dl
from config import DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, YOUTUBE_CHANNEL_IDS
import os
import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

download_dir = 'downloads'
os.makedirs(download_dir, exist_ok=True)

downloaded_videos_file = 'downloaded_videos.txt'

def get_downloaded_videos():
    if not os.path.exists(downloaded_videos_file):
        return set()
    with open(downloaded_videos_file, 'r') as file:
        return set(file.read().splitlines())

def add_downloaded_video(video_id):
    with open(downloaded_videos_file, 'a') as file:
        file.write(video_id + '\n')

def get_all_videos(channel_id):
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(rss_url)
    return [
        (entry.link, entry.yt_videoid, entry.published_parsed)
        for entry in feed.entries
    ]

@tasks.loop(minutes=5)
async def check_new_videos():
    downloaded_videos = get_downloaded_videos()
    max_videos_to_download = 9

    for channel_id in YOUTUBE_CHANNEL_IDS:
        print(f"Checking new videos for channel: {channel_id}")
        try:
            videos = get_all_videos(channel_id)
            videos.sort(key=lambda x: x[2])
            undownloaded_videos = [(video_url, video_id) for video_url, video_id, _ in videos if video_id not in downloaded_videos]
            videos_to_download = undownloaded_videos[-max_videos_to_download:]
            for video_url, video_id in videos_to_download:
                if video_url and video_id:
                    channel_download_dir = os.path.join(download_dir, channel_id)
                    os.makedirs(channel_download_dir, exist_ok=True)
                    ydl_opts = {
                        'format': 'bestvideo+bestaudio/best',
                        'outtmpl': f'{channel_download_dir}/%(title)s [%(id)s].%(ext)s',
                        'cookiefile': 'cookies.txt',
                    }
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([video_url])
                    add_downloaded_video(video_id)
                    channel = bot.get_channel(int(DISCORD_CHANNEL_ID))
                    await channel.send(f"@everyone New video dropped and has been archived: {video_url}")
                    print(f"Downloaded and notified for video {video_id} from channel: {channel_id}")
                else:
                    print(f"Video URL or ID missing for video ID {video_id} from channel: {channel_id}")
        except Exception as e:
            print(f"Error processing channel {channel_id}: {e}")
        await asyncio.sleep(5)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    check_new_videos.start()

bot.run(DISCORD_BOT_TOKEN)