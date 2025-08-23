import json
import discord
import re
from discord_webhook import DiscordWebhook, DiscordEmbed
from discord.ext import commands
from datetime import datetime, timezone
from typing import Optional, Union

class EmbedManager:
    def __init__(self, bot: commands.Bot, webhook_url: str):
        self.bot = bot
        self.webhook_url = webhook_url
        self.webhook = DiscordWebhook(url=webhook_url)
        self.stored_message_id = None
        webhook_pattern = r'https://discord\.com/api/webhooks/(\d+)/.*'
        match = re.match(webhook_pattern, webhook_url)
        if match:
            self.channel_id = int(match.group(1))
        else:
            raise ValueError("Invalid webhook URL format")

    def _build_embed(self, data: dict) -> DiscordEmbed:
        """Build a DiscordEmbed object from data dictionary"""
        embed = DiscordEmbed()

        # Author
        if 'author' in data:
            author_data = data['author']
            embed.set_author(
                name=author_data.get('name'),
                icon_url=author_data.get('icon_url'),
            )

        # Basic properties
        for prop in ['title', 'color', 'description', 'url']:
            if prop in data:
                setattr(embed, prop, data[prop])

        # Fields
        if 'fields' in data:
            for field in data['fields']:
                embed.add_embed_field(
                    name=field.get('name'),
                    value=field.get('value'),
                    inline=field.get('inline', False)
                )

        # Image and thumbnail
        if 'image' in data:
            embed.set_image(url=data['image'])
        if 'thumbnail' in data:
            embed.set_thumbnail(url=data['thumbnail'])

        # Footer
        if 'footer' in data:
            footer_data = data['footer']
            embed.set_footer(
                text=footer_data.get('text'),
                icon_url=footer_data.get('icon_url')
            )

        embed.set_timestamp(str(datetime.now(timezone.utc)))
        return embed

    async def _fetch_message_from_response(self, response, message_id: str = None) -> Optional[discord.Message]:
        """Fetch Discord message object from webhook response"""
        if response.status_code != 200:
            return None

        try:
            if not message_id:
                message_data = json.loads(response.text)
                message_id = message_data['id']

            # Get the webhook channel
            webhook = await self.bot.fetch_webhook(self.channel_id)
            channel = webhook.channel

            # Fetch the message object
            if channel:
                try:
                    return await channel.fetch_message(int(message_id))
                except (discord.NotFound, discord.HTTPException) as e:
                    print(f"Error fetching message: {e}")
                    return None

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error processing webhook response: {e}")
            return None

        return None

    async def create_embed(self, data: dict) -> Optional[discord.Message]:
        embed = self._build_embed(data)

        self.webhook.remove_embeds()
        self.webhook.add_embed(embed)
        response = self.webhook.execute()
        print(response)
        if response.status_code == 200:
            message_data = json.loads(response.text)
            self.stored_message_id = message_data['id']

        return await self._fetch_message_from_response(response)

    async def edit_embed(self, message: Union[discord.Message, str], data: dict) -> Optional[discord.Message]:
        if isinstance(message, discord.Message):
            msg_id = str(message.id)
        else:
            msg_id = message or self.stored_message_id

        if not msg_id:
            raise ValueError("No message ID provided or stored")

        # Create webhook with message ID
        self.webhook = DiscordWebhook(url=self.webhook_url, id=msg_id)
        embed = self._build_embed(data)

        self.webhook.remove_embeds()
        self.webhook.add_embed(embed)
        response = self.webhook.edit()

        return await self._fetch_message_from_response(response, msg_id)