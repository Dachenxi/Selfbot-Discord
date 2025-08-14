import logging
import datetime
from discord import Message
from discord.ext import commands
import json

logger = logging.getLogger(__name__)

class Utilities(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping", aliases=["p"])
    async def ping(self, message: commands.Context):
        """
        Command simple untuk ping atau
        test koneksi bot ke server discord
        """
        try:
            await message.channel.send("pong")
            logger.info("Mengirim pong")
        except Exception as e:
            logger.warning(f"Kesalahan terjadi dengan error {e}")

    @commands.command(name="testdm", aliases=["tdm"])
    async def testdm(self, message: commands.Context):
        try:
            people = self.bot.get_user(669886098906021918)
            await people.send("TestDM")

        except Exception as e:
            logger.warning(f"Gagal mengirim DM. {e}")

    @commands.command(name="scrap",aliases=['sc'])
    async def scrap(self, ctx: Message):
        fetch_message = await ctx.channel.fetch_message(ctx.reference.message_id)
        scrapped_data = {
            "content": fetch_message.content,
            "author": fetch_message.author.name,
            # convert datetime to ISO 8601 string so it is JSON serializable
            "timestamp": fetch_message.created_at.isoformat(),
            "embeds": []
        }
        for embed in fetch_message.embeds:
            scrapped_data["embeds"].append(embed.to_dict())

        # default=str is a safeguard if something else non-serializable sneaks in
        scrapped_data = json.dumps(scrapped_data, indent=2, ensure_ascii=False, default=str)
        await ctx.channel.send(f"```json\n{scrapped_data}\n```")

    @commands.command(name="scrapvf")
    async def scrapvf(self, ctx: Message):
        """Scrap data dari pesan virtualfisher."""
        fetch_message = await ctx.channel.fetch_message(ctx.reference.message_id)
        if fetch_message.embeds:
            for embed in fetch_message.embeds:
                title_lower = (embed.title or "").lower()
                if "inventory" in title_lower:
                    description = (embed.description or "")
                    # Parse the VirtualFisher data
                    vf_data = {
                        "clan": "",
                        "balance": "",
                        "level": "",
                        "xp": "",
                        "current_rod": "",
                        "current_biome": "",
                        "pet": "",
                        "bait": "",
                        "fish_inventory": {},
                        "exotic_fish": {},
                        "special": {}
                    }

                    lines = description.split('\n')
                    current_section = None

                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue

                        # Parse basic info
                        if line.startswith("Clan:"):
                            vf_data["clan"] = line.split("**")[1]
                        elif line.startswith("Balance:"):
                            vf_data["balance"] = line.split("**")[1].replace(".", "")
                        elif line.startswith("**Level"):
                            parts = line.split(",")
                            vf_data["level"] = parts[0].split("**")[1]
                            if len(parts) > 1:
                                vf_data["xp"] = parts[1].strip()
                        elif line.startswith("Currently using"):
                            vf_data["current_rod"] = line.split("**")[1]
                        elif line.startswith("Current biome:"):
                            vf_data["current_biome"] = line.split("**")[1]
                        elif line.startswith("Pet:"):
                            vf_data["pet"] = line.split("**")[1]
                        elif line.startswith("Bait:"):
                            bait_parts = line.split("**")
                            if len(bait_parts) >= 2:
                                vf_data["bait"] = bait_parts[1]

                        # Detect sections
                        elif line == "**Fish Inventory**":
                            current_section = "fish_inventory"
                        elif line == "**Exotic Fish**":
                            current_section = "exotic_fish"
                        elif line == "**Special**":
                            current_section = "special"
                        elif line.startswith("Fish Value:"):
                            vf_data["fish_value"] = line.split("**")[1]

                        # Parse fish data
                        elif current_section and line.startswith("**") and "**" in line[2:]:
                            try:
                                # Extract quantity and fish name
                                parts = line.split("**")
                                if len(parts) >= 3:
                                    quantity = parts[1]
                                    fish_name = parts[2].strip()
                                    # Remove emoji and extra spaces
                                    fish_name = ' '.join(fish_name.split()[1:]) if fish_name.split() else fish_name
                                    vf_data[current_section][fish_name] = quantity
                            except:
                                continue

                    # Convert to JSON
                    json_data = json.dumps(vf_data, indent=2, ensure_ascii=False)
                    await ctx.channel.send(f"```json\n{json_data}\n```")
        else:
            await ctx.channel.send("Pesan yang direferensikan bukan data VirtualFisher inventory.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Utilities(bot))
    logger.info("Utilies command berhasil di load")