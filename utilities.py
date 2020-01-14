"""
+==============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║ 
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
 MARKET PEGGED ASSET PRICEFEEDS
+==============================+


data formatting and text pipe IPC utilities

litepresence 2019

"""
import os
import time
from pprint import pprint
from json import dumps as json_dumps
from json import loads as json_loads
from multiprocessing import Process, Value

ATTEMPTS = 3
PATH = str(os.path.dirname(os.path.abspath(__file__))) + "/"


def it(style, text):  
    """
    Color printing in terminal
    """
    emphasis = {
        "red": 91,
        "green": 92,
        "yellow": 93,
        "blue": 94,
        "purple": 95,
        "cyan": 96,
    }
    return ("\033[%sm" % emphasis[style]) + str(text) + "\033[0m"


def sigfig(price):
    """
    format price to max 8 significant figures, return as float
    """
    return float("{:g}".format(float("{:.8g}".format(price))))


def race_write(doc="", text=""):
    """
    Concurrent Write to File Operation
    """
    text = str(text)
    i = 0

    doc = PATH + "pipe/" + doc

    while True:
        try:
            time.sleep(0.05 * i ** 2)
            i += 1
            with open(doc, "w+") as f:
                f.write(text)
                f.close()
                break
        except Exception as e:
            msg = str(type(e).__name__) + str(e.args)
            msg += " race_write()"
            print(msg)
            try:
                f.close()
            except:
                pass
            continue
        finally:
            try:
                f.close()
            except:
                pass


def race_read_json(doc=""):
    """
    Concurrent Read JSON from File Operation
    """
    doc = PATH + "pipe/" + doc

    i = 0
    while True:
        try:
            time.sleep(0.05 * i ** 2)
            i += 1
            with open(doc, "r") as f:
                data = json_loads(f.read())
                f.close()
                return data
        except Exception as e:
            msg = str(type(e).__name__) + str(e.args)
            msg += " race_read_json()"
            print(msg)
            try:
                f.close()
            except:
                pass
            continue
        finally:
            try:
                f.close()
            except:
                pass


def from_iso_date(date):
    """
    returns unix epoch given YYYY-MM-DD
    """
    return int(time.mktime(time.strptime(str(date), "%Y-%m-%d %H:%M:%S")))


def ret_markets():
    """
    currently supported markets
    """
    return [
        "USD:CNY",
        "USD:EUR",
        "USD:GBP",
        "USD:RUB",
        "USD:JPY",
        "USD:KRW",
    ]


def refine_data(data):
    """
    ensure USD base
    sort dictionaries by key
    return only data in specified forex markets
    ensure values are all float format and to matching precision
    """
    
    markets = ret_markets()
    data2 = {}
    for k, v in data.items():
        if k[-3:] == "USD":
            data2[k[-3:] + ":" + k[:3]] = 1 / v
        else:
            data2[k] = v
    data = {}
    for k, v in data2.items():
        if k[-3:] == "CNH":
            data["USD:CNY"] = v
        else:
            data[k] = v
    for k, v in data2.items():
        if k[-3:] == "RUR":
            data["USD:RUB"] = v
        else:
            data[k] = v
    data = dict(sorted(data.items()))
    data = {k: sigfig(v) for k, v in data.items()}
    data = {k: v for k, v in data.items() if k in markets}
    return data


def process_request(site, method):
    """
    initialize an external request process, return process handle
    """
    race_write(f"{site}_forex.txt", {})
    signal = Value("i", 0)
    i = 0
    while (i < ATTEMPTS) and not signal.value:
        if i > 0:
            time.sleep(1)
        i += 1
        child = Process(target=method, args=(signal,))
        child.daemon = False
        child.start()
    return child
