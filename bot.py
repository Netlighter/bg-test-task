import os
import requests

from PIL import Image

from vk_api import VkApi, VkUpload
from vk_api.bot_longpoll import VkBotEventType
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

from io import BytesIO

from config import API_TOKEN
from config import GROUP_ID
from config import API_VERSION


class Bot:

    def __init__(self, api_token, group_id, api_ver):
        self.vk_session = VkApi(token=api_token, api_version=api_ver)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkBotLongPoll(self.vk_session, group_id=group_id)
        self.allowed_commands = ['Начать', 'Привет бот']
        
        self.picture_kb = VkKeyboard(one_time=False, inline=True)
        self.picture_kb.add_callback_button(
            label="Пришли картинку",
            color=VkKeyboardColor.SECONDARY,
            payload={"type": "send_pic"},
        )
        self.upload = VkUpload(self.vk_session)
        print('Init done.')

    def main(self):
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.obj.message["text"] in self.allowed_commands:
                    self.user_id = event.obj.message["from_id"]
                    if "callback" not in event.obj.client_info["button_actions"]:
                        print(
                            f'Клиент user_id{event.obj.message["from_id"]} не поддерживает callback-кнопки.'
                        )

                    self.last_message = self.vk.messages.send(
                        user_id=self.user_id,
                        random_id=get_random_id(),
                        peer_id=self.user_id,
                        keyboard=self.picture_kb.get_keyboard(),
                        message=f"Привет, {self.get_user_name(self.user_id)}!",
                    )
                    
            elif event.type == VkBotEventType.MESSAGE_EVENT:
                if event.object.payload.get("type") == "send_pic":
                    filename = f"{event.obj.user_id}.jpg"
                    self.user_pic = self.get_user_profile_pic(self.user_id)
                    
                    resp = requests.get(self.user_pic)
                    if resp.status_code == 200:
                        
                        avatar = Image.open(BytesIO(resp.content))
                        
                        bg = Image.open('background.jpg')
                        bg.paste(avatar, (100,100))
                        bg.save(filename, quality=100)
                        
                        bg.close()
                        avatar.close()
                        
                    photo = self.upload.photo_messages(filename)

                    vk_photo_url = 'photo{}_{}'.format(
                        photo[0]['owner_id'], photo[0]['id']
                    )
                    
                    self.vk.messages.send(
                        user_id=self.user_id,
                        random_id=get_random_id(),
                        peer_id=self.user_id,
                        attachment=[vk_photo_url],
                    )
                    
                    self.vk.messages.edit(
                        peer_id=self.user_id,
                        message=f"Привет, {self.get_user_name(self.user_id)}!",
                        message_id=self.last_message)
                    
                    os.remove(filename)


    def get_user_name(self, user_id):
        return self.vk.users.get(user_id=user_id)[0]['first_name']
    
    def get_user_profile_pic(self, user_id):
        return self.vk.users.get(user_id=user_id, fields='photo_400_orig')[0]['photo_400_orig']

        

bot_instance = Bot(API_TOKEN, GROUP_ID, API_VERSION)

bot_instance.main()