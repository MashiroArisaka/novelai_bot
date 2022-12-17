import requests
import socket
import socks
import base64
import telebot
import random
import traceback
import time
import re
from sys import argv, exit

'''
用法：
pip3 install -U requests[socks] pyTelegramBotAPI

首先编辑 novelai_bot.py 按需修改bot token name、群组ID、回复txt等等的内容

运行用法：
python3 novelai_bot.py [参数(naifu|webui|file)] [你的naifu/webui网址]

列子：搭建 naifu bot，naifu地址是 "http://127.0.0.1:6969"，同时会发送图片+文件
python3 novelai_bot.py naifu "http://127.0.0.1:6969"

列子：搭建 webui bot，webui地址是 "http://127.0.0.1:7860"，只发文件
python3 novelai_bot.py webui file "http://127.0.0.1:7860"

列子：搭建 novelai官网 bot （需要修改添加自己账号的Bearer token）
python3 novelai_bot.py

'''

print(argv)
api_ip = argv[-1]

#需要要改为你的bot token和name
bot_token = '123456:xxx'
bot_name = '@xxx_bot'

#修改你的novelai官网账号Bearer token，如果是自建naifu和webui就不用理
novelai_token = 'Bearer eyxxx'

#群组白名单id | PS.不支持私聊，没写
group_id = ['-1001843728291', '-1234']

#私聊/非白名单群组的自动回复，按需修改
to_group_text = '请移动到隔壁测试群 https://t.me/xxx'

#Negative prompt 负面tag，自带鲨扶她伪娘tag，按需修改
Negative_default = f'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, ' \
          f'low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, bad feet, futa, futanari, yaoi'

#是否使用SOCKS5代理，按需修改自行开启和端口
#socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 1082)
#socket.socket = socks.socksocket

#按需修改你的出错回复
error_text = '获取失败，且已自动重试3次，仍然获取失败，请手动重试'

#按需修改你的help
help_text = '''
—用法 指令 + 英文关键词/英文描述短句
<code>/ai_nsfw_p</code> 是生成纵向图(可色色)
<code>/ai_nsfw_l</code> 是生成横向图(可色色)
<code>/ai_sfw_p</code> 是生成纵向图(全年龄)
<code>/ai_sfw_l</code> 是生成横向图(全年龄)

—可选参数
消息带上 <code>-seed=</code><code>数字</code> | 来指定seeds数
消息带上 <code>Negative prompt:</code> <code>想指定Negative prompt</code> | 来完全指定Negative prompt
消息带上 <code>###</code> <code>追加的Negative prompt</code> | 来追加Negative prompt

例如我想ru张兽耳萝莉图(纵向)
<code>/ai_nsfw_p loli, animal_ears</code>

列如我想ru张非常详细的可爱猫耳萝莉高清壁纸(横向)
<code>/ai_nsfw_l extremely detailed cat-ear moon cute loli girl</code>

更多英文关键词请见
https://wiki.installgentoo.com/wiki/Stable_Diffusion#Keywords
https://gelbooru.com/index.php?page=tags&s=list

此外bot没反应是因为排队中，多人用时可能需要排几分钟也说不定
'''

bot = telebot.TeleBot(bot_token, num_threads=4)
print(bot_name)

headers = {
    'authority': 'api.novelai.net',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    'dnt': '1',
    'authorization': novelai_token,
    # Already added when you pass json=
    # 'content-type': 'application/json',
    'accept': '*/*',
    'origin': 'https://novelai.net',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://novelai.net/',
    'accept-language': 'zh-CN,zh;q=0.9',
}


def session_for_src_addr(addr: str) -> requests.Session:
    """
    Create `Session` which will bind to the specified local address
    rather than auto-selecting it.
    """
    session = requests.Session()
    for prefix in ('http://', 'https://'):
        session.get_adapter(prefix).init_poolmanager(
            # those are default values from HTTPAdapter's constructor
            connections=requests.adapters.DEFAULT_POOLSIZE,
            maxsize=requests.adapters.DEFAULT_POOLSIZE,
            # This should be a tuple of (address, port). Port 0 means auto-selection.
            source_address=(addr, 0),
        )

    return session

def get(input, type, seed, novelai_api_url, Negative):
    if 'l' in type :
        width, height = 768, 512
    else:
        width, height = 512, 768

    if 'naifu' in argv:
        json_data = {
            "prompt": input,
            "seed": seed,
            "n_samples": 1,
            "sampler": "k_euler_ancestral",
            "width": width,
            "height": height,
            "scale": 11,
            "steps": 28,
            'uc': Negative,
        }

    elif 'webui' in argv:
        input = input.replace('{', '(').replace('}', ')')

        json_data = {
            'fn_index': 52,
            'data': [
                input,  # prompt
                Negative,  # Negative
                'None',
                'None',
                28, #Sampling Steps
                'Euler a',
                False,
                False,
                1,
                1,
                11,  # CFG Scale
                seed,
                -1,
                0,
                0,
                0,
                False,
                height, width,
                False,
                0.7,
                0,
                0,
                'None',
                False,
                False,
                False,
                False,
                '',
                'Seed',
                '',
                'Nothing',
                '',
                True,
                False,
                False,
                None,
            ],
        }

    else:
        if 'nsfw' in type:
            model = 'nai-diffusion'
        else:
            model = 'safe-diffusion'

        json_data = {
            'input': input,
            'model': model,
            'parameters': {
                'width': width,
                'height': height,
                'scale': 11,
                'sampler': 'k_euler_ancestral',
                'steps': 28,
                'seed': seed,
                'n_samples': 1,
                'ucPreset': 0,
                'qualityToggle': True,
                'uc': Negative,
            },
        }


    if 'naifu' in argv :
        req = requests.post(novelai_api_url, json=json_data, timeout=120).json()
        data = req
        output = req["output"]
        for x in output:
            img_data = x #img = base64.b64decode(x)
        img_data_b = base64.b64decode(img_data)

    elif 'webui' in argv:
        response = requests.post(novelai_api_url, json=json_data, timeout=120).json()
        data = response.get('data')[0][0]
        #print(response_data)
        name = data.get('name')
        name_url = f'{api_ip}/file={name}'
        f = requests.get(name_url)
        img_data_b = f.content

    else:
        response = requests.post(novelai_api_url, headers=headers, json=json_data, timeout=120)
        data = response.content.split()
        img_data = str(data[-1]).split('data:')[-1].encode()
        data = response.text
        img_data_b = base64.decodebytes(img_data)

    return data, img_data_b



@bot.message_handler(commands=['ai_nsfw_p','ai_nsfw_l', 'ai_sfw_p', 'ai_sfw_l', 'ai_any_p', 'ai_any_l', 'start', 'help'])
def send(message):
    #print(message)

    try:
        if message.chat.type == 'supergroup' :
            chat_id = str(message.chat.id)
            type = []
            if chat_id in group_id :
                #print(message)
                print(f'name is {message.from_user.first_name}')
                message_text = str(message.text)

                model = None

                if '/ai_nsfw_p' in message_text :
                    name = 'ai_nsfw_p'
                    type.append('p')
                    type.append('nsfw')
                elif '/ai_nsfw_l' in message_text :
                    name = 'ai_nsfw_l'
                    type.append('l')
                    type.append('nsfw')
                elif '/ai_sfw_p' in message_text :
                    name = 'ai_sfw_p'
                    type.append('p')
                elif '/ai_sfw_l' in message_text :
                    name = 'ai_sfw_l'
                    type.append('l')
                elif '/start' in message_text :
                    name = ''
                    message_text = ''
                elif '/help' in message_text :
                    name = ''
                    message_text = ''

                if 'file' in argv:
                    picture_status = None
                else:
                    picture_status = True

                if 'naifu' in argv:
                    novelai_api_url = f'{api_ip}/generate'
                elif 'webui' in argv:
                    novelai_api_url = f'{api_ip}/run/predict/'
                else:
                    novelai_api_url = 'https://api.novelai.net/ai/generate-image'


                seed = random.randint(0, 2 ** 32)

                bot_name_l = ['@ai_loli_bot', '@ai_loli_test_bot']
                for i in range(len(bot_name_l)):
                    message_text = message_text.replace(f'{bot_name_l[i]}', '')

                message_text = message_text.replace(f'{bot_name}', '').replace(f'/{name}', '').replace('\n', ',').replace(', ,', ',').replace(',,', ',')

                Negative = None
                Negative_add = ''
                Negative_l = ['Negative prompt:', 'Negative-prompt:', 'Negative_prompt:', 'Negativeprompt:',
                              'Negative prompt', 'Negative-prompt', 'Negative_prompt', 'Negativeprompt',
                              'negative prompt:', 'negative-prompt:', 'negative_prompt:', 'negativeprompt:',
                              'negative prompt', 'negative-prompt', 'negative_prompt', 'negativeprompt',
                              ]

                if 'Negative' in message_text or 'negative' in message_text:
                    message_text = message_text.replace(',Negative', 'Negative').replace(',negative', 'negative')
                    for i in Negative_l:
                        if i in message_text:
                            x = message_text.split(i)
                            message_text = x[0].strip()
                            Negative = x[-1].replace(' :', '').replace('：', '').strip()
                            print(f'Negative --- {Negative}')
                            break

                if '###' in message_text:
                    x = message_text.split('###')
                    message_text = x[0].strip()
                    Negative_add = x[-1].strip()
                    Negative_add = f',{Negative_add}'
                    print(f'Negative_add --- {Negative_add}')

                if '-seed=' in message_text :
                    seed_txt = re.compile(r'-seed=\d*').findall(message_text)[-1]
                    seed_txt = str(seed_txt)
                    message_text = message_text.replace(seed_txt, '')
                    seed = seed_txt.replace('-seed=', '')
                    if seed:
                        seed = int(seed)
                        print(f'-seed={seed}')

                if message_text:
                    if 'best quality' not in message_text and 'best_quality' not in message_text :
                        message_text = 'best quality, ' + message_text

                    if 'masterpiece' not in message_text:
                        message_text = 'masterpiece, ' + message_text

                input = message_text.replace(',,', ',')

                print(f'input --- {input}')

                if not Negative:
                    Negative = f'{Negative_default}{Negative_add}'

                if input :
                    try:
                        start = time.time()

                        try:
                            data, img_data_b = get(input, type, seed, novelai_api_url, Negative)
                        except Exception as ex:
                            traceback.print_exc()
                            print('---获取失败1次-等待5秒重试---')
                            try:
                                time.sleep(5)
                                data, img_data_b = get(input, type, seed, novelai_api_url, Negative)
                            except Exception as ex:
                                print('---获取失败2次-等待5秒重试---')
                                try:
                                    time.sleep(5)
                                    data, img_data_b = get(input, type, seed, novelai_api_url, Negative)
                                except Exception as ex:
                                    start = time.time()
                                    try:
                                        #print(f'---data---\n{data}')
                                        print(f'---data---')
                                    except Exception as ex:
                                        print(f'---data---error')
                                    print('---获取失败3次---')

                        end = time.time()
                        time_consuming = f'生成耗时:{round(end - start, 2)}s'
                        print(time_consuming)

                        if 'naifu' in argv:
                            caption_txt = f'{seed} | naifu | {time_consuming}'
                        elif 'webui' in argv:
                            caption_txt = f'{seed} | webui | {time_consuming}'
                        else:
                            caption_txt = f'{seed} | novelai | {time_consuming}'

                        start = time.time()

                        #发送图片
                        if picture_status:
                            try:
                                bot.send_photo(
                                    chat_id=message.chat.id,
                                    reply_to_message_id = message.message_id,
                                    photo=img_data_b,
                                    #parse_mode="Markdown",
                                    caption=caption_txt,
                                )
                            except Exception as ex:
                                time.sleep(10)
                                bot.send_photo(
                                    chat_id=message.chat.id,
                                    reply_to_message_id = message.message_id,
                                    photo=img_data_b,
                                    #parse_mode="Markdown",
                                    caption=caption_txt,
                                )

                        #发送文件
                        try:
                            bot.send_document(
                                chat_id=message.chat.id,
                                reply_to_message_id = message.message_id,
                                document=img_data_b,
                                #parse_mode="Markdown",
                                caption=caption_txt,
                                visible_file_name=f'{seed}.png',
                            )
                        except Exception as ex:
                            time.sleep(10)
                            bot.send_document(
                                chat_id=message.chat.id,
                                reply_to_message_id = message.message_id,
                                document=img_data_b,
                                #parse_mode="Markdown",
                                caption=caption_txt,
                                visible_file_name=f'{seed}.png',
                            )

                        end = time.time()
                        time_consuming = f'发送耗时:{round(end - start, 2)}s'
                        print(time_consuming)

                    except Exception as ex:
                        traceback.print_exc()
                        print('---获取失败4次-彻底失败---')
                        bot.send_message(
                            chat_id=message.chat.id,
                            reply_to_message_id=message.message_id,
                            text = error_text
                        )
                else:
                    bot.send_message(
                        chat_id=message.chat.id,
                        reply_to_message_id=message.message_id,
                        text=help_text,
                        parse_mode="HTML"
                    )
            else:
                bot.send_message(
                    chat_id=message.chat.id,
                    reply_to_message_id=message.message_id,
                    text=to_group_text,
                    parse_mode="HTML"
                )
        else:
            bot.reply_to(message, text=to_group_text)
    except Exception as ex:
        traceback.print_exc()
        print('---全局错误---')

if __name__ == '__main__':
    while True:
        try:
            bot.polling()
        except Exception as ex:
            print(f'出现如下异常\n{ex}\n')
            traceback.print_exc()
        time.sleep(5)
