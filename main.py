import discord
import json
import random
import langdetect
import pinyin
import os
import validators
import unicodedata
from datetime import datetime
from discord import app_commands
from discord.ext import commands
from chinese_converter import to_traditional, to_simplified
from googleapiclient.errors import HttpError
from lingua import Language, LanguageDetectorBuilder
from wiktionaryparser import WiktionaryParser
from google_images_search import GoogleImagesSearch
from unidecode import unidecode
import re


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
PINYIN = ['shuang', 'chuang', 'diang', 'cheng', 'liang', 'jiang', 'niang', 'jiong', 'qiang', 'shuai', 'xiang', 'xiong',
          'qiong', 'huang', 'shang', 'chuan', 'guang', 'chuai', 'chang', 'kuang', 'chong', 'shong', 'shuan', 'sheng',
          'heng', 'tong', 'biao', 'quan', 'guan', 'fang', 'tian', 'weng', 'shai', 'bian', 'dang', 'gong', 'diao',
          'dong', 'mian', 'reng', 'qing', 'kuan', 'geng', 'ning', 'chuo', 'kuai', 'hong', 'ting', 'ming', 'song',
          'ding', 'juan', 'mang', 'shan', 'chou', 'tiao', 'ceng', 'nian', 'kang', 'chun', 'chao', 'beng', 'shei',
          'duan', 'teng', 'ruan', 'bang', 'miao', 'piao', 'nong', 'xian', 'yuan', 'xuan', 'seng', 'jing', 'neng',
          'ping', 'shui', 'yong', 'wang', 'gang', 'lang', 'tang', 'chan', 'rang', 'chua', 'huan', 'pang', 'shun',
          'yang', 'shuo', 'cuan', 'sang', 'dian', 'bing', 'pian', 'leng', 'shou', 'luan', 'chui', 'shen', 'nuan',
          'shua', 'peng', 'long', 'tuan', 'shao', 'feng', 'liao', 'chen', 'cong', 'niao', 'guai', 'meng', 'xiao',
          'ling', 'lian', 'chai', 'suan', 'qian', 'kong', 'xing', 'huai', 'ying', 'deng', 'hang', 'jiao', 'nang',
          'jian', 'keng', 'cang', 'rong', 'qiao', 'nei', 'dan', 'run', 'duo', 'mei', 'cui', 'lün', 'tui', 'lin', 'wen',
          'qin', 'nen', 'niu', 'hao', 'gei', 'wan', 'nin', 'dou', 'cun', 'nüe', 'nun', 'pei', 'man', 'xia', 'lia',
          'min', 'lan', 'gui', 'hua', 'sui', 'lao', 'shi', 'sei', 'qie', 'diu', 'mai', 'tun', 'jin', 'tan', 'wai',
          'kao', 'ban', 'hai', 'hen', 'qia', 'ben', 'sao', 'hui', 'gan', 'pai', 'suo', 'ren', 'kua', 'hun', 'tie',
          'shu', 'cuo', 'rui', 'fei', 'she', 'kan', 'xiu', 'che', 'pan', 'nan', 'sai', 'cha', 'zun', 'lie', 'rao',
          'nai', 'tou', 'luo', 'liu', 'xun', 'mao', 'dun', 'dai', 'cou', 'nao', 'gou', 'nou', 'ran', 'san', 'jue',
          'fou', 'kai', 'gao', 'sha', 'die', 'gun', 'yun', 'kun', 'nia', 'yue', 'miu', 'yan', 'bin', 'cai', 'lei',
          'men', 'gai', 'pin', 'guo', 'tuo', 'kuo', 'sun', 'nie', 'qiu', 'sen', 'tao', 'yin', 'pen', 'hei', 'ken',
          'dao', 'you', 'han', 'xie', 'nuo', 'den', 'xin', 'bei', 'gua', 'ang', 'kou', 'cen', 'que', 'hou', 'bao',
          'kui', 'dui', 'huo', 'jiu', 'chu', 'bai', 'zuo', 'dei', 'cao', 'mou', 'qun', 'chi', 'lüe', 'pao', 'tai',
          'yao', 'ruo', 'sou', 'lai', 'lun', 'fen', 'jun', 'pou', 'gen', 'mie', 'wei', 'fan', 'jia', 'bie', 'rou',
          'can', 'pie', 'lou', 'jie', 'xue', 'ge', 'di', 'da', 'ao', 'ne', 'na', 'an', 'la', 'ha', 'ku', 'pa', 're',
          'ju', 'yu', 'ye', 'er', 'nü', 'gu', 'fo', 'qi', 'du', 'mo', 'bu', 'ei', 'si', 'ri', 'ca', 'ka', 'de', 'ya',
          'yi', 'lü', 'fu', 'me', 'se', 'bi', 'po', 'lo', 'ga', 'wa', 'hu', 'ke', 'su', 'ma', 'ni', 'ru', 'bo', 'ci',
          'ai', 'qu', 'ji', 'ce', 'tu', 'fa', 'xu', 'cu', 'mu', 'ba', 'ou', 'pu', 'lu', 'he', 'nu', 'le', 'li', 'sa',
          'wu', 'xi', 'en', 'te', 'mi', 'pi', 'wo', 'ti', 'ta', 'e', 'a']


def match_lang(text, iso_lang):
    # detector = LanguageDetectorBuilder.from_all_languages().build()
    result_a = langdetect.detect(text)
    # result_b = detector.detect_language_of(text).iso_code_639_1.name.lower()
    print(result_a)
    for each in iso_lang:
        if result_a == each:
            return True
    return False


def remove_pinyin(input_string):
    input_string = ''.join(c for c in unicodedata.normalize('NFD', input_string) if unicodedata.category(c) != 'Mn')
    for syllable in PINYIN:
        input_string = input_string.replace(syllable, '')
    return input_string


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
        content = remove_pinyin(content) if channel.category_id == "1182926926160072746" else content
        is_nonspacing = match_lang(content, ["zh-cn", "zh-tw", "zh", "jp", "ko"])
        word_count = len(content) if is_nonspacing else len(content.split())
        if word_count > 8:
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
async def trans_zh(interaction, text: str, style: app_commands.Choice[str]):
    """Transliterates mandarin text using pinyin."""
    is_chinese = match_lang(text, ["zh-cn", "zh-tw", "zh"])
    if is_chinese:
        await interaction.response.send_message(pinyin.get(text, format=style.value, delimiter=' '), ephemeral=True)
    else:
        await interaction.response.send_message("Wrong language input.", ephemeral=True)


@bot.tree.command()
@app_commands.describe(text="Cyrillic text that will be transliterated.")
# @discord.app_commands.checks.has_role("bot tester")
async def trans_cyrillic(interaction, text: str):
    """Transliterates cyrillic text into latin characters."""
    is_cyrillic = bool(re.search('[а-яА-Я]', text))
    if is_cyrillic:
        await interaction.response.send_message(unidecode(text), ephemeral=True)
    else:
        await interaction.response.send_message("Wrong input.", ephemeral=True)


@bot.tree.command()
@app_commands.describe(search="Search prompt.", language="Language to search in.")
# @discord.app_commands.checks.has_role("bot tester")
async def wiktionary(interaction, search: str, language: str):
    """Shows the first entry on Wiktionary (English) if it exists."""
    parser = WiktionaryParser()
    result = parser.fetch(search, language)
    print(search, language, result)
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
                              description=f"An entry for this word in {language.title()} could not be fetched, click on the link to go to Wiktionary.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


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
        embed.set_footer(text=f"{interaction.user.display_name} | {data['name']}",
                         icon_url=interaction.user.display_avatar)
        if validators.url(image):
            embed.set_image(url=image)

        await channel.send(embed=embed)
        if ping.value:
            await channel.send(content="<@&1183618548048875582>")
        await interaction.response.send_message("👍✅", ephemeral=True)

bot.run(BOT_TOKEN)
