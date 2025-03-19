import hashlib
import hmac
import time
import aiohttp
import asyncio
from telebot.async_telebot import AsyncTeleBot
from binance import AsyncClient
from sympy import symbols, solve
channel = "" # telegram 
telegram_bot_token = '' 
api_key = "" # binacne 
api_secret = "" # binance
bot = AsyncTeleBot(telegram_bot_token)

host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url_z = '/wallet/withdraw_status'
query_param = ''


min_procent = 1.5
sleep_time = 4
msg_value = 0.2
black_list = ["QIUSDT", "GTCBTC", "BIFIUSDT", "GTCUSDT"]

async def gen_sign(method, url, query_string=None, payload_string=None):
    key = ''  # api key gate.io
    secret = ''  # secret gate.io

    t = time.time()
    m = hashlib.sha512()
    m.update((payload_string or "").encode('utf-8'))
    hashed_payload = m.hexdigest()
    s = f'{method}\n{url}\n{query_string or ""}\n{hashed_payload}\n{t}'
    sign = hmac.new(secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
    return {'KEY': key, 'Timestamp': str(t), 'SIGN': sign}

async def make_request(session, url, headers):
    async with session.get(url, headers=headers) as response:
        return await response.json()



async def sendmsg(msg):
    await bot.send_message(channel, msg, parse_mode="html")

async def get(url):
    async with aiohttp.ClientSession() as session:
        url = url
        try:
            async with session.get(url) as resp:
                data = await resp.json()
        except Exception as e:
            print('e')
            # await sendmsg(e)
    try:
        return data
    except Exception as e:
        print(e)
        # await sendmsg(e)
#    await session.close()

async def price():
    global prices, pairs
    binance_list = {}
    gateio_list = {}
    prices = {}
    pairs = {}

    async def gateio(): # получаем инфу с gate.io и записываем её в gateio_list.
        
        url = 'https://api.gateio.ws/api/v4/spot/tickers'
        try:
            data = await get(url) # получаем данные
            if data != None: # если не пусто в data
                for i in data:
                    if True == True:
                        currency_pair = i['currency_pair'].replace('_', '') # btc_usdt на btcusdt для удобства
                        if float(i['last']) != 0: 
                            if i["lowest_ask"] and i["highest_bid"] != None: # сheck bid and asks
                                pair_info = {}
                                pair_info['last'] = float(i['last'])
                                pair_info['ask'] = float(i["lowest_ask"])
                                pair_info['bid'] = float(i["highest_bid"])
                                pair_info['symbol'] = i['currency_pair']
                                gateio_list[currency_pair] = pair_info
            # print("gateio data")
        except Exception as e:
            print(e, " ~!~!~!~!~!~! Error Gate.io ~!~!~!~!~!~!~!")

    async def binance(): # get info from binace and whrite binance_list.
        url = 'https://api.binance.com/api/v3/ticker/24hr'
        data = await get(url)# получаем данные
        try:
            if data != None:
                for i in data:
                    if True == True:
                        if float(i['lastPrice']) != 0:
                            if i["askPrice"] and i["bidPrice"] != None:
                                pair_info = {}
                                pair_info['last'] = float(i['lastPrice'])
                                # print(pair_info)
                                pair_info["ask"] = float(i["askPrice"])
                                pair_info["bid"] = float(i["bidPrice"])
                                binance_list[i['symbol']] = pair_info
            # print("binance data")
        except Exception as e:
            print(e, " !!!!!! Error Binance !!!!!!!")

    async def sync(v1, v2, n1, n2):
        pairs = list(set(v1) & set(v2))
        # print(len(pairs))
        for i in pairs:
            info = {}
            info['last{}'.format(n1)] = v1[i]['last']
            info['ask{}'.format(n1)] = v1[i]['ask']
            info['bid{}'.format(n1)] = v1[i]['bid']
            info['last{}'.format(n2)] = v2[i]['last']
            info['symbol'] = gateio_list[i]['symbol']
            info["ask{}".format(n2)] = v2[i]["ask"]
            info["bid{}".format(n2)] = v2[i]["bid"]
            prices[i] = info
        # print("Sync!")
        return prices
    
    while True:
        await gateio()
        await binance()
        pairs = await sync(binance_list, gateio_list, n1="Binance", n2="Gateio")
        await asyncio.sleep(sleep_time)



async def arbitrage_finder(n1, n2):
    profit_list = {}
    client = await AsyncClient.create(api_key, api_secret)
    for i in pairs:
        print(i['symbol'])

    async def get_commission_binance(symbol):
        data = await client.get_asset_details()

        if symbol in data:
            if data[symbol]['withdrawStatus'] and data[symbol]['depositStatus'] == True:
                return data[symbol]

    async def get_commission_gateio(symbol):
        async with aiohttp.ClientSession() as session:
            sign_headers = await gen_sign('GET', prefix + url_z, query_param)
            headers.update(sign_headers)

            response = await make_request(session, host + prefix + url_z, headers)
            for i in response:
                if i['currency'] == symbol:
                    return i
        await session.close()


    async def fee_clac(pair, askGateio, bidBinance, askBinacne, bidGateio):
        base_symbol = prices[pair]['symbol'].split('_', 1)[0]
        split_result = prices[pair]['symbol'].split("_")
        after_underscore = split_result[1]
        binance = await get_commission_binance(base_symbol)
        gateio = await get_commission_gateio(after_underscore)
        if askGateio < bidBinance:
            print("Gate.io - Binance")
            if 'depositStatus' in gateio == True:
                if 'withdrawStatus' in gateio == True:            
                    if 'withdraw_fix_on_chains' in gateio:
                        x = symbols('x')
                        fe = gateio['withdraw_fix_on_chains']
                        min_value = min(float(value) for value in fe.values())
                        PriceBinanceAsk =  float(askGateio)
                        GateioPriceBid =  float(bidBinance)

                        BinanceWithdrawFee = float(min_value) # биржа 1 комиссия за вывод gateio 
                        GateioWithdrawFixBlockchain = float(binance['withdrawFee'])
                        solutions = solve(x < (((x / PriceBinanceAsk - x / PriceBinanceAsk * 0.00075) - BinanceWithdrawFee) * GateioPriceBid - ((x / PriceBinanceAsk - x / PriceBinanceAsk * 0.00075) - BinanceWithdrawFee) * GateioPriceBid * 0.00075) - GateioWithdrawFixBlockchain, x)
                                # numeric_solutions = [sol.evalf() for sol in solutions if sol.is_real]
                                
                        print(str(solutions))
                        print(str(solutions).split('(')[1].split('<')[0].strip(), '')

                        asd = str(solutions).split('(')[1].split('<')[0].strip(), ''
                        ret = {}
                        ret['min'] = asd
                        ret['sy'] = split_result[1]
                        ret['tp'] = "Gate.io - Binance"
                        return ret
            else:
                return 0
        else:
            print("Binance - Gate.io")
            # Объявляем символьную переменную x
            if 'depositStatus' in gateio == True:
                if 'withdrawStatus' in gateio == True:
                    if 'withdraw_fix_on_chains' in gateio:
                        x = symbols('x')
                        fe = gateio['withdraw_fix_on_chains']
                        min_value = min(float(value) for value in fe.values())
                        PriceBinanceAsk =  float(askBinacne)
                        GateioPriceBid =  float(bidGateio)
                        BinanceWithdrawFee = float(binance['withdrawFee']) # биржа 1 комиссия за вывод 
                        GateioWithdrawFixBlockchain = float(min_value)

                        solutions = solve(x < (((x / PriceBinanceAsk - x / PriceBinanceAsk * 0.00075) - BinanceWithdrawFee) * GateioPriceBid - ((x / PriceBinanceAsk - x / PriceBinanceAsk * 0.00075) - BinanceWithdrawFee) * GateioPriceBid * 0.00075) - GateioWithdrawFixBlockchain, x)
                        # numeric_solutions = [sol.evalf() for sol in solutions if sol.is_real]
                        
                        print(str(solutions))
                        print(str(solutions).split('(')[1].split('<')[0].strip(), '')

                        asd = str(solutions).split('(')[1].split('<')[0].strip(), ''
                        ret = {}
                        ret['min'] = asd
                        ret['sy'] = split_result[1]
                        ret['tp'] = "Binance - Gate.io"
                        return ret
            else:
                return 0




        
    async def checker():
        for i in pairs:
            if i not in black_list:
                if i in profit_list:
                    if profit_list[i]['status'] == False:
                        # print(i, profit_list[i]['profit'])
                        min_summ = await fee_clac(i, prices[i]['askGateio'], prices[i]['bidBinance'], prices[i]['askBinance'], prices[i]['bidGateio'])
                        print(min_summ)
                        if min_summ != 0:
                            msg = "• Пара: {} {}💎 \n• Цена на Binance.com: {}📉 \n• Цена на Gate.io: {}📊 \n• Разница: {}<strong>%</strong> \n• Биды на Binance.com: {} \n• Аски на Binance.com: {}\n• Биды на Gate.io: {} \n• Аски на Gate.io: {} \n Минимальная сумма для профита: {} {}".format(i, min_summ['tp'], str(prices[i]['lastBinance']), str(prices[i]['lastGateio']), round(profit_list[i]['profit'], 5), str(prices[i]['bidBinance']), str(prices[i]['askBinance']), str(prices[i]['bidGateio']), str(prices[i]['askGateio']), min_summ['min'][0], min_summ['sy'])
                            await sendmsg(msg)
                            profit_list[i]['status'] = True


    while True:
        await asyncio.sleep(8)
        # print(pairs)
        for i in pairs:
            profit = abs((float(prices[i]['bid{}'.format(n1)]) - float(prices[i]['ask{}'.format(n2)])) / float(prices[i]['bid{}'.format(n1)]) *100)
            # print(i, round(profit, 4))
            if profit > min_procent:
                if i not in profit_list:
                    info = {}
                    info['status'] = False
                    info['last_profit'] = profit
                    info['profit'] = profit
                    profit_list[i] = info
                    # sendmsg
                    # print(i, profit)
                else:
                    profit_list[i]['profit'] = profit
                    if profit - profit_list[i]['last_profit'] >= msg_value:
                        profit_list[i]['last_profit'] = profit
                        profit_list[i]['status'] = False
                        # print(i, profit)
                    elif (profit - profit_list[i]['last_profit']) <= -msg_value:
                        profit_list[i]['last_profit'] = profit
                        profit_list[i]['status'] = False
                        # print(i, profit)
        await checker()


async def run():
    price_task = price()
    arbitrage_finder_task = arbitrage_finder("Binance", "Gateio",)
    await asyncio.gather(price_task, arbitrage_finder_task)

asyncio.run(run())
