from core import main_dir
import requests

from core.url import DISCORD_API_URL

def load_secret():
    with open(main_dir + "/secret.key", "r") as _secret:
        return _secret.read()


def fetch_discord_user(user_id, bot_token):
    """
    Fetch Discord user data from Discord API
    
    Args:
        user_id: Discord user ID
        bot_token: Discord bot token
        
    Returns:
        dict: User data with keys: id, username, display_name, avatar_url, discriminator, bot, system
        or None if request fails
    """
    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
        return None
    
    try:
        url = f"{DISCORD_API_URL}/users/{user_id}"
        headers = {
            'Authorization': f'Bot {bot_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
        
        user_data = response.json()
        
        # Build avatar URL
        avatar_url = None
        if user_data.get('avatar'):
            avatar_hash = user_data['avatar']
            extension = 'gif' if avatar_hash.startswith('a_') else 'png'
            avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{extension}"
        else:
            # Default avatar
            if user_data.get('discriminator') and user_data['discriminator'] != '0':
                default_avatar_index = int(user_data['discriminator']) % 5
            else:
                default_avatar_index = (int(user_id) >> 22) % 6
            avatar_url = f"https://cdn.discordapp.com/embed/avatars/{default_avatar_index}.png"
        
        return {
            'id': user_data.get('id'),
            'username': user_data.get('username'),
            'display_name': user_data.get('global_name') or user_data.get('username'),
            'discriminator': user_data.get('discriminator', '0'),
            'avatar_url': avatar_url,
            'avatar_hash': user_data.get('avatar'),
            'bot': user_data.get('bot', False),
            'system': user_data.get('system', False)
        }
        
    except Exception:
        return None
