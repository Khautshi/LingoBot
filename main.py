import discord
import json
import random
import langdetect
import pinyin
import os
import asyncio
import validators
from datetime import datetime
from discord import app_commands
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
with open('JSON/wod.json', mode='r', encoding='utf-8') as file:
    WOD = json.load(file)
    LANGS = [app_commands.Choice(name=f"{n} | {WOD[n]['name']}", value=n) for n in WOD]


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
        is_nonspacing = match_lang(content, ["zh-cn", "zh-tw", "zh", "jp"])
        word_count = len(content) if is_nonspacing else len(content.split())
        if word_count > 4:
            allowed = match_lang(content, IMMERSION_CATEGORIES[channel.category_id]['allowed'])
            reply = IMMERSION_CATEGORIES[channel.category_id]['reply']
            if not allowed:
                await channel.send(reply, reference=message)


@bot.tree.command()
@app_commands.describe(text="Chinese text that will be converted to both traditional and simplified characters.")
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
@app_commands.describe(text="Chinese text that will be converted to simplified characters.")
# @discord.app_commands.checks.has_role("bot tester")
async def simplified(interaction, text: str):
    """Converts from traditional to simplified characters."""
    is_chinese = match_lang(text, ["zh-cn", "zh-tw", "zh"])
    if is_chinese:
        await interaction.response.send_message(to_simplified(text), ephemeral=True)
    else:
        await interaction.response.send_message("Wrong language input.", ephemeral=True)


@bot.tree.command()
@app_commands.describe(text="Chinese text that will be converted to traditional characters.")
# @discord.app_commands.checks.has_role("bot tester")
async def traditional(interaction, text: str):
    """Converts from simplified to traditional characters."""
    is_chinese = match_lang(text, ["zh-cn", "zh-tw", "zh"])
    if is_chinese:
        await interaction.response.send_message(to_traditional(text), ephemeral=True)
    else:
        await interaction.response.send_message("Wrong language input.", ephemeral=True)


@bot.tree.command()
@app_commands.choices(style=[app_commands.Choice(name="Diacritical tone marking.", value="diacritical"),
                             app_commands.Choice(name="Numerical tone marking.", value="numerical"),
                             app_commands.Choice(name="No tone marking.", value="strip")])
@app_commands.describe(text="Chinese text, either simplified or traditional, that will be transliterated into pinyin.",
                       style="Pinyin format, default will show diacritics for tones.")
# @discord.app_commands.checks.has_role("bot tester")
async def trans_zh(interaction, text: str, style: app_commands.Choice[str] = "diacritical"):
    """Transliterates mandarin text using pinyin."""
    is_chinese = match_lang(text, ["zh-cn", "zh-tw", "zh"])
    if is_chinese:
        await interaction.response.send_message(pinyin.get(text, format=style, delimiter=' '), ephemeral=True)
    else:
        await interaction.response.send_message("Wrong language input.", ephemeral=True)


@bot.tree.command()
@app_commands.describe(text="Russian text that will be transliterated.")
# @discord.app_commands.checks.has_role("bot tester")
async def trans_ru(interaction, text: str):
    """Transliterates russian text into latin characters."""
    is_russian = match_lang(text, ["ru"])
    if is_russian:
        await interaction.response.send_message(unidecode(text), ephemeral=True)
    else:
        await interaction.response.send_message("Wrong language input.", ephemeral=True)


@bot.tree.command()
@app_commands.describe(search="Search prompt.", language="Language to search in.")
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


# @bot.tree.command()
# @app_commands.checks.has_role("WoD writer")
# @app_commands.choices(language=LANGS)
# async def wod(interaction, language: discord.app_commands.Choice[str]):
#     """Posts an embed containing word of the day."""
#
#     def check(message):
#         return message.author == interaction.user and message.channel == interaction.channel
#
#     channel = discord.utils.get(interaction.user.guild.channels, name="word-of-the-day")
#     timeout = 300
#     if channel:
#         data = WOD[language.value]
#
#         try:
#             await interaction.response.send_message(f"{data['word']}:", ephemeral=True)
#             msg_2 = await bot.wait_for("message", check=check, timeout=timeout)
#             word = msg_2.content
#             await msg_2.delete()
#
#             await interaction.followup.send(f"IPA:", ephemeral=True)
#             msg_3 = await bot.wait_for("message", check=check, timeout=timeout)
#             ipa = msg_3.content
#             await msg_3.delete()
#
#             await interaction.followup.send(f"{data['definition']}:", ephemeral=True)
#             msg_4 = await bot.wait_for("message", check=check, timeout=timeout)
#             definition = msg_4.content
#             await msg_4.delete()
#
#             await interaction.followup.send(f"{data['examples']}:", ephemeral=True)
#             msg_5 = await bot.wait_for("message", check=check, timeout=timeout)
#             example = msg_5.content
#             await msg_5.delete()
#
#             current_datetime = datetime.now()
#             today = current_datetime.strftime("%Y-%m-%d")
#
#             embed = discord.Embed(title=f"{word} {ipa}",
#                                   description=definition,
#                                   color=discord.Color.blurple())
#             embed.add_field(name=f"{data['examples']}", value=example, inline=False)
#             embed.set_author(name=f"{data['head']} | {today}")
#             embed.set_footer(text=f"{interaction.user.display_name} | {language.value}",
#                              icon_url=interaction.user.display_avatar)
#             await channel.send(embed=embed)
#         except asyncio.TimeoutError:
#             await interaction.followup.send("Timeout reached.", ephemeral=True)


@bot.tree.command()
@app_commands.checks.has_role("WoD writer")
@app_commands.choices(language=LANGS, ping=[app_commands.Choice(name="Enabled", value=1),
                                            app_commands.Choice(name="Disabled", value=0)])
@app_commands.describe(language="The language the word is in, pick one from the list.",
                       word="Word of the day.",
                       definition="Definition or an explanation of how it's used.",
                       example="One or more examples using the chosen word.",
                       ipa="Phonetic or phonemic transcription using IPA (International Phonetic Alphabet).",
                       etymology="Origin of the word.",
                       image="URL for the embedded image.",
                       ping="Whether or not to ping word of the day. Default is True.")
async def wod(interaction, language: app_commands.Choice[str], word: str, definition: str, example: str,
              ping: app_commands.Choice[int], ipa: str = None, etymology: str = None, image: str = None):
    """Posts an embed containing word of the day."""

    channel = discord.utils.get(interaction.user.guild.channels, name="word-of-the-day")

    if channel:
        data = WOD[language.value]
        today = datetime.now().strftime("%Y-%m-%d")
        title = f"{word} {ipa}" if ipa else word

        embed = discord.Embed(title=title, description=definition, color=discord.Color.blurple())

        embed.add_field(name=f"{data['examples']}", value=example, inline=False)
        if etymology:
            embed.add_field(name=f"{data['etymology']}", value=etymology, inline=False)
        embed.set_author(name=f"{data['head']} | {today}")
        embed.set_footer(text=f"{interaction.user.display_name} | {language.value}",
                         icon_url=interaction.user.display_avatar)
        if validators.url(image):
            embed.set_image(url=image)

        await channel.send(embed=embed)
        if ping:
            await channel.send(content="<@&1183618548048875582>")

bot.run(BOT_TOKEN)
