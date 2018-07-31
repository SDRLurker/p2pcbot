#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pickle
import asyncio
from bithumb import AsyncBithumb
from datetime import datetime, timedelta
import telegram
from config import my_token, msql, web_host
from registry import Registry
from dao import DAO

import hashlib
import traceback
import logging

dao = DAO(msql)
ALARM_TMPL = '''%s %s %.2f %s!
%s'''
REGISTER_TMPL = '''%s %s %s %s(이/가) 등록되었습니다.'''
HELP_TMPL = '''[도움말]\n%s
ls
조건목록을 확인합니다.
rm 번호
번호에 해당하는 조건을 삭제합니다
set
웹을 통해 조건을 설정합니다.
%% 코인 숫자
해당 코인의 등락율이 해당 숫자(0.1) 이상, -숫자(-0.1) 이하면 알려주는 조건을 등록합니다.
cu 코인 숫자
해당 코인의 종가가 해당 숫자 이상이면 알려주는 조건을 등록합니다.
cd 코인 숫자
해당 코인의 종가가 해당 숫자 이하면 알려주는 조건을 등록합니다.'''

CHECK_DIC = {
    # q는 시세값, c는 conditions DB값
    '%': {'code': '%', 'cn': '등락율', 'quote':'rate', 'func':lambda q, c: q >= c or q <= -c, 'fn': '이상이하'},
    'cu': {'code': 'cu', 'cn': '종가', 'quote':'close', 'func':lambda q, c: q >= c, 'fn': '이상'},
    'cd': {'code': 'cd', 'cn': '종가', 'quote':'close', 'func':lambda q, c: q <= c, 'fn': '이하'},
}

def getLogger(name):
    pwd = os.getcwd()
    if not os.path.exists('%s/log' % pwd):
        os.makedirs('%s/log' % pwd)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')
    path = './log/p2pcbot.log'
    fileHandler = logging.FileHandler(path)
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
    return logger

def telegram_send_message(bot, chat_id, text):
    try:
        print( bot.send_message(chat_id=chat_id, text=text) )
    except telegram.error.Unauthorized as e:
        where_dic = {'userid': chat_id}
        dao.delete_condition(where_dic)
        logger.error('telegram_send_message(%s,%s) : %s' % (chat_id,text,str(e)) )
        print('telegram_send_message(%s,%s) : %s' % (chat_id,text,str(e)) )
    except Exception as e:
        # logger.error(traceback.format_exc())
        print(traceback.format_exc())
        logger.error('telegram_send_message : ' + str(e))
        print('telegram_send_message : ' + str(e))

def save_last_up():
    with open('p2pcbot.pic','wb') as f:
        pickle.dump(get_update.last_up, f)
        # logger.info("save %d %s %s" % (get_update.last_up, alarm_dict, ping_dict) )


def format_quote(quote_dic):
    s = ""
    eng_kor_dic = {
        'open': '시가', 'high': '고가', 'low': '저가', 'close': '종가',
        'change': '등락', 'rate': '등락율'
    }
    for key in quote_dic:
        if key in eng_kor_dic:
            s += "%s : %.2f\n" % (eng_kor_dic[key], quote_dic[key])
    return s

def proc_cond(cond, data, check_dic):
    userid, cid, currency, code, val = cond
    check_code = check_dic['code']
    check_quote = check_dic['quote']
    check_func = check_dic['func']
    cn = check_dic['cn']
    fn = check_dic['fn']

    if code == check_code and currency in data:
        quote_val = data[currency][check_quote]
        if check_func(quote_val, val):
            quote_str = format_quote(data[currency])
            alarm_msg = ALARM_TMPL % (currency, cn, val, fn, quote_str)
            telegram_send_message(bot, userid, alarm_msg)
            user = dao.get_member(userid)
            gap = user[0][1]
            if gap:
                next_datetime = datetime.now()
                next_datetime += timedelta(seconds=gap)
                set_dic = {'next': next_datetime.strftime('%Y-%m-%d %H:%M:%S')}
                where_dic = {'userid': userid, 'id': cid}
                dao.update_condition(set_dic, where_dic)


async def consume(queue, bot):
    while True:
        # https://gist.github.com/jakubczaplicki/8993755aa70a73c506c07a05c6f65da1
        try:
            data = await queue.get()
            ts = (datetime.now().strftime('%Y%m%d%H%M%S'), len(str(data)))
            print("consume : %s %d" % ts)    # 3
        except TimeoutError:
            print('TimeoutError', str(e))
        except:
            print("Unexpected error:", sys.exc_info()[0])
        conds = dao.get_next_conditions()
        # print("conds:%s" % conds)
        for cond in conds:
            for code in CHECK_DIC:
                check_dic = CHECK_DIC[code]
                proc_cond(cond, data, check_dic)

def make_session(chat_id):
    EXPIRE_SEC = 600
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    expire = now + timedelta(seconds=EXPIRE_SEC)
    expire_str = expire.strftime('%Y-%m-%d %H:%M:%S')
    id_time_str = str(chat_id) + " " + now_str
    hash_str = hashlib.sha224(id_time_str.encode()).hexdigest()
    set_dic = {'sess_id': hash_str, 'sess_expire': expire_str}
    dao.update_session(str(chat_id), set_dic)
    return hash_str

def plus_update_id(u):
    # https://github.com/python-telegram-bot/python-telegram-bot/issues/26
    get_update.last_up = u.update_id + 1
    print("get_update.last_up 2 = %d" % get_update.last_up)
    save_last_up()

def list_conditions(userid):
    msg = "[조건목록]\n"
    rows = dao.get_conditions(userid)
    for row in rows:
        row_id = row[1]
        row_currency = row[2]
        row_code = row[3]
        row_val = row[4]
        for code in CHECK_DIC:
            if row_code == code:
                cn = CHECK_DIC[code]['cn']
                fn = CHECK_DIC[code]['fn']
                msg += "%02s. %s %s %s %s\n" % (row_id, row_currency, cn, row_val, fn)
    return msg

def get_update(bot):
    try:
        updates = bot.getUpdates(get_update.last_up)  # 업데이트 내역을 받아옵니다.
        # print("get_update %d %d" % (get_update.last_up, len(updates)))
        last_up_asis = get_update.last_up
        for u in updates:                             # 내역중 메세지를 출력합니다.
            msg = u.message
            if not u.message:
                msg = u.edited_message
            if not msg:
                plus_update_id(u)
                continue
            chat_id = msg.chat.id
            text = msg.text
            print(chat_id, text)
            if not text:
                logger.error('[get_update] chat_id=%s, text=None' % chat_id)
                print('msg=%s, chat_id=%s, text=None' % (msg,chat_id))
                plus_update_id(u)
                continue

            logger.info("[get_update] chat_id=%s, text=%s", chat_id, text)
            if text.lower() == "help":
                print(HELP_TMPL, web_host)
                msg = HELP_TMPL % web_host
                telegram_send_message(bot, chat_id, msg)
                plus_update_id(u)
                continue

            if text.lower() == "ls":
                msg = list_conditions(chat_id)
                # print(chat_id,msg)
                if msg:
                    telegram_send_message(bot, chat_id, msg)
                plus_update_id(u)
                continue

            if text.lower() == 'set':
                hash_str = make_session(chat_id)
                plus_update_id(u)
                msg = "설정주소\n" + web_host + "/" + hash_str
                telegram_send_message(bot, chat_id, msg)
                continue

            if text.lower().startswith('rm'):
                if len(text.split()) == 2 and text.split()[1].isdigit():
                    cid = text.split()[1]
                    where_dic = {'userid': chat_id, 'id': cid}
                    dao.delete_condition(where_dic)
                    msg = "%s 조건은 삭제되었습니다!" % cid
                else:
                    msg = "사용법) rm [조건번호]\n"
                    msg += "조건삭제 명령을 잘못 사용하였습니다!"
                telegram_send_message(bot, chat_id, msg)
                plus_update_id(u)
                continue

            if text.lower().startswith(tuple(CHECK_DIC.keys())):
                registry = Registry(chat_id)
                user_dict, cmd_dict = registry.proc_cmd(text)
                is_success, msg = registry.save_data(text, dao)
                if not is_success:
                    telegram_send_message(bot, chat_id, msg)
                    plus_update_id(u)
                    continue

                for code in CHECK_DIC:
                    check_dic = CHECK_DIC[code]
                    if code in cmd_dict:
                        currency = cmd_dict['currency']
                        val = cmd_dict[code]
                        cn = check_dic['cn']
                        fn = check_dic['fn']
                        msg = REGISTER_TMPL % (currency, cn, val, fn)

                        telegram_send_message(bot, chat_id, msg)
            plus_update_id(u)
    except Exception as e:
        # logger.error(traceback.format_exc())
        # print(traceback.format_exc())
        # logger.error('get_update : ' + str(e))
        print('get_update : ' + str(e))


def load_alarm():
    get_update.last_up = 0
    if os.path.exists("p2pcbot.pic"):
        f = open("p2pcbot.pic", "rb")
        get_update.last_up = pickle.load(f)
        # logger.info("load %d %s %s" % (get_update.last_up, alarm_dict, ping_dict) )
        f.close()
    return get_update.last_up


async def produce(queue, bot, exch=AsyncBithumb(1)):
    get_update.last_up = load_alarm()
    while True:
        get_update(bot)
        async with exch as data:    # async with에 클래스의 인스턴스 지정
            ts = (datetime.now().strftime('%Y%m%d%H%M%S'), len(str(data)))
            print("produce : %s %d" % ts)    # 3
            await queue.put(data)

if __name__ == "__main__":
    logger = getLogger('p2pcbot')
    exch_tuple = (AsyncBithumb(1),)
    bot = telegram.Bot(token=my_token)    # bot을 선언합니다.

    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)
    for exch in exch_tuple:
        loop.create_task(produce(queue, bot, exch))
        loop.create_task(consume(queue, bot))
    loop.run_forever()
