import datetime
import json
import os
import requests
from bs4 import BeautifulSoup
import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View, Modal, TextInput
import logging


logging.basicConfig(level=logging.INFO)


LAST_RESET_FILE = 'key.json'

def get_last_reset(userkey):
    if os.path.exists(LAST_RESET_FILE):
        with open(LAST_RESET_FILE, 'r') as f:
            data = json.load(f)
        return data.get(str(userkey))
    return None

def set_last_reset(userkey, reset_time):
    data = {}
    if os.path.exists(LAST_RESET_FILE):
        with open(LAST_RESET_FILE, 'r') as f:
            data = json.load(f)
    data[str(userkey)] = reset_time
    with open(LAST_RESET_FILE, 'w') as f:
        json.dump(data, f)


class ResetHWIDModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Reset HWID")
        self.key = nextcord.ui.TextInput(label="User Key", required=True)
        self.add_item(self.key)

    async def callback(self, interaction: nextcord.Interaction):
        userkey = self.key.value
        current_time = datetime.datetime.now()

        last_reset = get_last_reset(userkey)
        if last_reset:
            last_reset_time = datetime.datetime.fromisoformat(last_reset)
            if (current_time - last_reset_time).total_seconds() < 3 * 3600:
                time_remaining = (3 * 3600 - (current_time - last_reset_time).total_seconds())
            hours, remainder = divmod(time_remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            embed = nextcord.Embed(
                description=f"คีย์นี้รีไปแล้วโปรดรออีก {int(hours)} ชั่วโมง {int(minutes)} นาที {int(seconds)} วินาที",
                color=nextcord.Color.red()
            )
            view = ResetHWIDButtonView()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        set_last_reset(userkey, current_time.isoformat())


        embed = nextcord.Embed(
            description=f"คุณแน่ใจหรือไม่ที่จะรีคีย์ {userkey}?",
            color=nextcord.Color.orange()
        )

        view = nextcord.ui.View()

        confirm_button = nextcord.ui.Button(label='[🟢] ยืนยัน', style=nextcord.ButtonStyle.green, custom_id='confirm_button')
        async def confirm_callback(interaction_confirm: nextcord.Interaction):
            await interaction_confirm.response.defer(ephemeral=True)
            try:

                login_url = 'https://konoro.sogod.online/login'
                session = requests.Session()
                response = session.get(login_url)
                soup = BeautifulSoup(response.text, 'html.parser')
                csrf_token = soup.find('input', {'name': 'csrf_test_name'})['value']
                login_data = {
                    'username': 'bangrus', # ใส่ user 
                   
                    'password': 'saran2549', #  ใส่ pass
                    'csrf_test_name': csrf_token,
                    'ip': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
                }
                response = session.post(login_url, data=login_data)

                if response.ok and "Dashboard" in response.text:
               
                    api_url = f'https://konoro.sogod.online/keys/reset?userkey={userkey}&reset=1'
                    api_response = session.get(api_url)

                    if api_response.ok:
                        if "ไม่พบคีย์ที่ต้องการรี" in api_response.text:
                            embed = nextcord.Embed(description=f'Reset HWID ไม่สำเร็จ: ไม่พบคีย์ที่ต้องการรี', color=nextcord.Color.red())
                        else:
                           
                            key_info_url = 'https://konoro.sogod.online/keys/api?draw=7&columns[0][data]=id&columns[0][name]=id_keys&columns[0][searchable]=true&columns[0][orderable]=true&columns[0][search][value]=&columns[0][search][regex]=false&columns[1][data]=game&columns[1][name]=&columns[1][searchable]=true&columns[1][orderable]=true&columns[1][search][value]=&columns[1][search][regex]=false&columns[2][data]=user_key&columns[2][name]=&columns[2][searchable]=true&columns[2][orderable]=true&columns[2][search][value]=&columns[2][search][regex]=false&columns[3][data]=devices&columns[3][name]=&columns[3][searchable]=true&columns[3][orderable]=true&columns[3][search][value]=&columns[3][search][regex]=false&columns[4][data]=duration&columns[4][name]=&columns[4][searchable]=true&columns[4][orderable]=true&columns[4][search][value]=&columns[4][search][regex]=false&columns[5][data]=expired&columns[5][name]=expired_date&columns[5][searchable]=true&columns[5][orderable]=true&columns[5][search][value]=&columns[5][search][regex]=false&columns[6][data]=&columns[6][name]=&columns[6][searchable]=true&columns[6][orderable]=true&columns[6][search][value]=&columns[6][search][regex]=false&order[0][column]=4&order[0][dir]=asc&start=0&length=10&search[value]=admin&search[regex]=false&_=1722138002284'
                            key_info_response = session.get(key_info_url)
                            key_info_data = key_info_response.json()

                            expired_time = None
                            for item in key_info_data['data']:
                                if item['user_key'] == userkey:
                                    expired_time = item['expired']
                                    break

                            if expired_time:
                                embed = nextcord.Embed(description=f'Reset HWID สำเร็จ เวลาคีย์คงเหลือ {expired_time}', color=nextcord.Color.green())
                            else:
                                embed = nextcord.Embed(description='Reset HWID สำเร็จ แต่ไม่สามารถดึงข้อมูลเวลาคีย์คงเหลือได้', color=nextcord.Color.green())

                            
                            notify_channel = interaction.guild.get_channel(1267018616247947335)
                            if notify_channel:
                                notify_embed = nextcord.Embed(
                                    title="HWID Reset Notification",
                                    description=f"Key: {userkey}\nUser: {interaction.user}\nTime: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                    color=nextcord.Color.blue()
                                )
                                await notify_channel.send(embed=notify_embed)
                    else:
                        embed = nextcord.Embed(description=f'Reset HWID ไม่สำเร็จ: {api_response.status_code}', color=nextcord.Color.red())
                else:
                    embed = nextcord.Embed(description='Login ไม่สำเร็จ', color=nextcord.Color.red())

                await interaction_confirm.followup.send(embed=embed, ephemeral=True)
            except nextcord.errors.NotFound as e:
                logging.error(f"Interaction error: {e}")
                embed = nextcord.Embed(description="Interaction has expired or webhook is invalid.", color=nextcord.Color.red())
                try:
                    await interaction_confirm.followup.send(embed=embed, ephemeral=True)
                except nextcord.errors.NotFound as e:
                    logging.error(f"Followup error: {e}")
                    pass
            except Exception as e:
                logging.error(f"General error: {e}")
                embed = nextcord.Embed(description=f"An error occurred: {e}", color=nextcord.Color.red())
                try:
                    await interaction_confirm.followup.send(embed=embed, ephemeral=True)
                except nextcord.errors.NotFound as e:
                    logging.error(f"Followup error: {e}")
                    pass

        confirm_button.callback = confirm_callback
        view.add_item(confirm_button)

        cancel_button = nextcord.ui.Button(label='[🔴] ยกเลิก', style=nextcord.ButtonStyle.red, custom_id='cancel_button')
        async def cancel_callback(interaction_cancel: nextcord.Interaction):
            await interaction_cancel.response.edit_message(content='ยกเลิกสำเร็จ', embed=None, view=None)

        cancel_button.callback = cancel_callback
        view.add_item(cancel_button)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
class ResetHWIDButton(nextcord.ui.Button):
    def __init__(self):
        super().__init__(label="ซื้อยศรีคีย์ได้ไม่จำกัดรีได้ตลอด", style=nextcord.ButtonStyle.primary)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.send_message("ติดต่อแอดมินรุส <@1162342015036567634> ราคา 450 บาท", ephemeral=True)

class ResetHWIDButtonView(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ResetHWIDButton())
class ResetHWIDView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label="[🔄] Reset HWID", style=nextcord.ButtonStyle.green)
    async def reset_hwid(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        modal = ResetHWIDModal()
        await interaction.response.send_modal(modal)

class topupView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ResetHWIDView().reset_hwid)

bot = commands.Bot(command_prefix='nyx!', help_command=None, intents=nextcord.Intents.all())
config = json.load(open('config.json', 'r', encoding='utf-8'))

@bot.event
async def on_ready():
    bot.add_view(topupView())
    print(f'LOGIN AS {bot.user}')

@bot.slash_command(name='setup', description='setup', guild_ids=[config['serverId']])
async def setup(interaction: nextcord.Interaction):
    if interaction.user.id not in config['ownerIds']:
        return await interaction.response.send_message(content='คุณไม่มีสิทธิ', ephemeral=True)
    embed = nextcord.Embed()
    embed.description = '''
```asciidoc
⚙️วิธีการReset Hardware ID (HWID)

> กรอกคีย์ Key ของคุณ 🔑
> รีได้แค่รอบละ3ชัวโมง  🕰️
```

'''

    embed.color = nextcord.Color.green()
    await interaction.channel.send(embed=embed, view=topupView())
    await interaction.response.send_message(content='success', ephemeral=True)

bot.run(config['token'])
