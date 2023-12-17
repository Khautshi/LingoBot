import discord
import json
import random
import langdetect
import pinyin as py
import os
from discord.ext import commands
from chinese_converter import to_traditional, to_simplified
from googleapiclient.errors import HttpError
from lingua import Language, LanguageDetectorBuilder
from wiktionaryparser import WiktionaryParser
from google_images_search import GoogleImagesSearch
from unidecode import unidecode


BOT_TOKEN = os.environ.get("BOT_TOKEN")
GCS_DEVELOPER_KEY = os.environ.get("GCS_DEVELOPER_KEY")
GCS_CX = os.environ.get("GCS_CX")

with open('JSON/immersion.json', mode='r', encoding='utf-8') as file:
    IMMERSION_CATEGORIES = {int(key): value for (key, value) in json.load(file).items()}
with open('JSON/welcome.json', mode='r', encoding='utf-8') as file:
    WELCOME_MSGS = list(json.load(file).values())


def match_lang(text, iso_lang):
    detector = LanguageDetectorBuilder.from_all_languages().build()
    result_a = langdetect.detect(text)
    result_b = detector.detect_language_of(text).iso_code_639_1.name.lower()
    for each in iso_lang:
        if result_a == each or result_b == each:
            return True
    return False


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())


@bot.event
async def on_ready():
    await bot.tree.sync()


@bot.event
async def on_member_join(member: discord.Member):
    channel = discord.utils.get(member.guild.channels, name="welcome")
    if channel:
        message = f"<@{member.id}> {random.choice(WELCOME_MSGS)}"
        await channel.send(message)


@bot.listen()
async def on_message(message: discord.Message):
    channel = message.channel
    content = message.content

    if not message.author.bot and channel.category_id in list(IMMERSION_CATEGORIES.keys()):
        allowed = match_lang(content, IMMERSION_CATEGORIES[channel.category_id]['allowed'])
        reply = IMMERSION_CATEGORIES[channel.category_id]['reply']
        if not allowed:
            await channel.send(reply, reference=message)
            # await message.interaction.response.send_message(reply, ephemeral=True) reference=message,


@bot.tree.command()
# @discord.app_commands.checks.has_role("bot tester")
async def convert(interaction, text: str):
    """Provides both conversions into simplified and traditional characters."""
    is_chinese = match_lang(text, ["zh-cn", "zh-tw", "zh"])
    if is_chinese:
        message = f"**简体：**{to_simplified(text)}\n**繁體：**{to_traditional(text)}"
        await interaction.response.send_message(message, ephemeral=True)
    else:
        await interaction.response.send_message("Wrong language input.", ephemeral=True)


@bot.tree.command()
# @discord.app_commands.checks.has_role("bot tester")
async def simplified(interaction, text: str):
    """Converts from traditional to simplified characters."""
    is_chinese = match_lang(text, ["zh-cn", "zh-tw", "zh"])
    if is_chinese:
        await interaction.response.send_message(to_simplified(text), ephemeral=True)
    else:
        await interaction.response.send_message("Wrong language input.", ephemeral=True)


@bot.tree.command()
# @discord.app_commands.checks.has_role("bot tester")
async def traditional(interaction, text: str):
    """Converts from simplified to traditional characters."""
    is_chinese = match_lang(text, ["zh-cn", "zh-tw", "zh"])
    if is_chinese:
        await interaction.response.send_message(to_traditional(text), ephemeral=True)
    else:
        await interaction.response.send_message("Wrong language input.", ephemeral=True)


@bot.tree.command()
# @discord.app_commands.checks.has_role("bot tester")
async def trans_zh(interaction, text: str):
    """Transliterates mandarin text using pinyin."""
    is_chinese = match_lang(text, ["zh-cn", "zh-tw", "zh"])
    if is_chinese:
        await interaction.response.send_message(py.get(text, format='diacritical', delimiter=' '), ephemeral=True)
    else:
        await interaction.response.send_message("Wrong language input.", ephemeral=True)


@bot.tree.command()
# @discord.app_commands.checks.has_role("bot tester")
async def trans_ru(interaction, text: str):
    """Transliterates russian text into latin characters."""
    is_russian = match_lang(text, ["ru"])
    if is_russian:
        await interaction.response.send_message(unidecode(text), ephemeral=False)
    else:
        await interaction.response.send_message("Wrong language input.", ephemeral=True)


@bot.tree.command()
# @discord.app_commands.checks.has_role("bot tester")
async def wiktionary(interaction, search: str, language: str):
    """Shows the first entry on Wiktionary (English) if it exists."""
    parser = WiktionaryParser()
    result = parser.fetch(search, language)
    result = result[0] if result else {}
    if result and result["definitions"]:
        ipa = "- " + "\n- ".join([n.replace("IPA: ", "") for n in result["pronunciations"]["text"] if "IPA" in n])
        pos = result["definitions"][0]['partOfSpeech']
        etymology = f">>> {result['etymology']}"
        defs = "- " + "\n- ".join(result["definitions"][0]["text"][1:])
        examples = "- " + "\n- ".join(result["definitions"][0]["examples"])

        etymology = (etymology[:1020] + "...") if len(etymology) >= 1024 else etymology
        defs = (defs[:1020] + "...") if len(defs) >= 1024 else defs
        examples = (examples[:1020] + "...") if len(examples) >= 1024 else examples

        gis = GoogleImagesSearch(GCS_DEVELOPER_KEY, GCS_CX)
        img_params = {
            "q": search,
            'num': 1,
            'fileType': 'jpg|gif|png',
            'imgSize': 'large',
            'rights': 'cc_publicdomain|cc_attribute|cc_sharealike|cc_noncommercial|cc_nonderived',
        }

        embed = discord.Embed(title=f"{search}",
                              url=f"https://en.wiktionary.org/wiki/{search.lower()}#{language.title()}",
                              color=discord.Color.blurple())
        if len(ipa) > 2:
            embed.add_field(name="Pronunciation", value=ipa)
        if len(pos) > 0:
            embed.add_field(name="Part of Speech", value=f"*{pos}*")
        if len(etymology) > 4:
            embed.add_field(name="Etymology", value=etymology, inline=False)
        embed.add_field(name="Definitions", value=defs, inline=False)
        if len(examples) > 2:
            embed.add_field(name="Examples", value=examples, inline=False)
        embed.set_footer(text=f"Wiktionary | {language.title()}")

        try:
            gis.search(search_params=img_params)
            img_url = gis.results()[0].url
            embed.set_thumbnail(url=img_url)
            print(img_url)
        except HttpError:
            pass
        except IndexError:
            pass

        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title=f"{search}",
                              url=f"https://en.wiktionary.org/wiki/{search.lower()}",
                              color=discord.Color.blurple(),
                              description="An entry for this word in language.title() could not be found.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


bot.run(BOT_TOKEN)
