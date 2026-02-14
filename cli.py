import discord
from curses import wrapper
from shutil import which
import subprocess
import easygui
import curses
import math
import time
import json
import sys
import os

settings={"token":{"name":"", "token":""}, "tokens":[], "bot_tokens":[], "bot_token":{"name":"", "token":""}, "app_id":-1, "cmd_name":"", "default_preset": -1, "presets":[], "randomize":False, "auto_leave":-1, "silent":True}
settings["default_preset"] = -1

def applySettings():
    f=open("settings.json", "w")
    f.write(json.dumps(settings))
    f.close()

if (os.path.isfile("settings.json")):
    f=open("settings.json", "r")
    try:
        settings = json.loads(f.read())
        f.close()
    except:
        pass

mainmenu=["Spam", "Edit Tokens", "Edit Application ID and Command", "Set Maximum Spam Count", "Edit Presets", "Randomize Messages", "Exit", "Start Bot", "Edit Bot Tokens", "Silent Messages", "Check Channels"]

stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(True)
loop = True
curmenu = mainmenu

def cinput(offsety=0, scr=stdscr, txt="", num_only=False):
    inputstr=txt
    curpos=0
    scr.addstr(offsety, 0, inputstr)
    while (True):
        stdscr.move(offsety, len(inputstr)-curpos)
        curses.setsyx(offsety, len(inputstr)-curpos)
        curses.doupdate()

        k=stdscr.getkey()
        if (k == "\n"):
            break
        elif (k == "KEY_BACKSPACE" or str.encode(k) == b'\x08'):
            if (curpos>=len(inputstr) and len(inputstr) != 0):
                continue
            elif (len(inputstr) == 0):
                break
            
            scr.addstr(offsety, len(inputstr)-1-curpos, inputstr[(len(inputstr)-curpos):]+" ")
            
            if (len(inputstr)>1):
                inputstr = inputstr[:(len(inputstr)-1-curpos)]+inputstr[(len(inputstr)-curpos):]
            else:
                inputstr = ""
        elif (k == "KEY_RIGHT"):
            if (curpos>0):
                curpos-=1
        elif (k == "KEY_LEFT"):
            if (curpos<len(inputstr)):
                curpos+=1
        elif (not num_only and len(k) == 1 or (k.isdigit() or k == "-" and len(inputstr) == 0) and num_only):
            scr.addstr(offsety, len(inputstr)-curpos, k+inputstr[(len(inputstr)-curpos):])
            inputstr = inputstr[:(len(inputstr)-curpos)]+k+inputstr[(len(inputstr)-curpos):]
    
    return inputstr

def choice(array, offsety=0, scr=stdscr, option=0):
    global stdscr
    ymax, xmax = scr.getmaxyx()

    if (len(array) <= option):
        option = len(array)-1

    while True:
        scr.clear()
        for i,v in enumerate(array):
            if (i > (ymax-1)*math.floor(option/(ymax-1))+ymax-2-offsety):
                break
            elif (i < (ymax-1)*math.floor(option/(ymax-1))):
                continue
            if (i != option):
                scr.addstr(math.floor(i%(ymax-1))+offsety, 0, "  "+str(i)+"- "+ v)
            else:
                scr.addstr(math.floor(i%(ymax-1))+offsety, 0, "> "+str(i)+"- "+ v)
        
        pary, parx = scr.getparyx()
        if (pary==-1):
            pary=0
            parx=0
        curpos = math.floor(option%(ymax-1))+offsety+pary
        stdscr.move(curpos, 0)
        curses.setsyx(curpos, 0)

        numpos = len(array)
        if (numpos>=ymax):
            numpos=ymax-1

        if (len(array)>ymax):
            if (option-ymax+1<0):
                scr.addstr(numpos+offsety, 0, "↓")
            else:
                scr.addstr(numpos+offsety, 0, "↑")
        curses.doupdate()
        scr.refresh()
        k=stdscr.getkey()
        
        if ((k=="KEY_LEFT" or k=="KEY_UP") and option != 0):
            option-=1
        elif ((k=="KEY_RIGHT" or k=="KEY_DOWN") and option < len(array)-1):
            option+=1
        elif (k.isdigit()):
            num=k
            scr.clear()
            if (int(num)<len(array)):
                option=int(num)
            scr.addstr(numpos+offsety, 0, num)
            while (True):
                scr.clear()
                for i,v in enumerate(array):
                    if (i > (ymax-1)*math.floor(option/(ymax-1))+ymax-2-offsety):
                        break
                    elif (i < (ymax-1)*math.floor(option/(ymax-1))):
                        continue
                    if (i != option):
                        scr.addstr(math.floor(i%(ymax-1))+offsety, 0, "  "+str(i)+"- "+ v)
                    else:
                        scr.addstr(math.floor(i%(ymax-1))+offsety, 0, "> "+str(i)+"- "+ v)
                curpos = math.floor(option%(ymax-1))+offsety+pary
                stdscr.move(curpos, 0)
                curses.setsyx(curpos, 0)
                scr.addstr(numpos+offsety, 0, num)
                curses.doupdate()
                scr.refresh()
                k=stdscr.getkey()
                if (k.isdigit()):
                    scr.addstr(numpos+offsety, len(num), k)
                    num+=k
                    if (int(num)<len(array)):
                        option=int(num)
                elif (k == "\n"):
                    break
                elif (k == "KEY_BACKSPACE" or str.encode(k) == b'\x08'):
                    if (len(num)<=1):
                        num=""
                        break
                    num = num[:-1]
                    scr.addstr(numpos+offsety, 0, num)
                elif (not k.isdigit):
                    num=""
            if (num!=""):
                if (int(num)<len(array)):
                    return option
        elif (k=="\n"):
            return option

guild_id=0
user_spam=False
check_chan=False

def clear():
    os.system('cls' if os.name == 'nt' else "printf '\033c'")

class spamClient(discord.Client):
    global stdscr
    global settings
    global settings
    global guild_id
    global user_spam
    global check_chan

    async def fetch_channels(self, guild, user):
        mchannels = []
        nchannels = []

        for channel in guild.channels:
            if (channel.type == discord.ChannelType.category or channel.type == discord.ChannelType.forum):
                continue
            
            permissions = channel.permissions_for(user)
            
            if (not permissions.view_channel
                or not permissions.read_message_history
                or not permissions.read_messages
                or ((not permissions.use_application_commands or not permissions.use_external_apps) and not user_spam)
                or not permissions.send_messages
                ):
                continue
            
            if (not permissions.attach_files):
                nchannels.append(channel)
            else:
                mchannels.append(channel)
        return mchannels, nchannels

    async def on_ready(self):
        print(f"Logged in as {self.user}!")
        app=None
        cmd=None
        botType=0 # normie bot
        opt=None

        if (not user_spam):
            for auth in await self.authorizations():
                if auth.application.id == settings["app_id"]:
                    app = auth.application
            if (app == None):
                print("Application is not installed, or wrong ID was provided.")
                sys.exit(1)

            for command in await app.bot.application_commands():
                if (command.name.lower().find(settings["cmd_name"].lower()) != -1):
                    cmd=command
            
            if (cmd == None):
                print("Command not found. Typo or Wrong Application ID?")
                sys.exit(1)

            for i,option in enumerate(cmd.options):
                if (option.name == "slowmode"):
                    botType = 1 # new bot
                elif (option.name == "slowmode_delay"):
                    botType = 2 # old bot
                
                if (i==0):
                    opt=option

            if (len(cmd.options) == 0):
                botType = 3 # cucked bot (predefined spam msg)

            if (opt == None and botType == 0):
                print("Option not found. Unsupported Bot?")
                sys.exit(1)
        else:
            botType = 4 # user bot
        
        guild = self.get_guild(guild_id)

        mchannels=[] # m = media
        nchannels=[] # n = no media
        user = None

        if (guild == None):
            # perhaps a channel

            channel=self.get_channel(guild_id)
            if (channel == None):
                print("Server/Channel not found. Wrong ID? Server/Channel Unavailable?")
                sys.exit(1)

            if (channel.guild != None):
                user = channel.guild.get_member(self.user.id)
                permissions = channel.permissions_for(user)

                if (not permissions.attach_files):
                    nchannels.append(channel)
                else:
                    mchannels.append(channel)
            else:
                mchannels.append(channel)
        else:
            user = guild.get_member(self.user.id)
            mchannels, nchannels = await self.fetch_channels(guild, user)
        
        clear()
        
        if (check_chan):
            mchannels, nchannels = await self.fetch_channels(guild, user)

            for chan in mchannels:
                print(chan.name+" ["+str(chan.id)+"] - media")
            
            for chan in nchannels:
                print(chan.name+" ["+str(chan.id)+"] - text-only")
            print("Close this window or press `Ctrl+C` to quit.")
            sys.exit(0)
            return

        count=0
        channelcounts = {}
        
        for chan in mchannels:
            channelcounts[chan.id] = {"name":chan.name, "count":0}
        for chan in nchannels:
            channelcounts[chan.id] = {"name":chan.name, "count":0}

        clear()
        for chan in channelcounts.values():
            print(f"[{str(chan['count'])}] {chan['name']}")

        lastSpam = {}

        while True:
            if (len(channelcounts) == 0):
                print("No channels available.")
                sys.exit(1)

            if (settings["auto_leave"] != -1 and count>=settings["auto_leave"]):
                print("Spam finished.")
                sys.exit(0)
            count+=1
            if (guild != None):
                mchannels, nchannels = await self.fetch_channels(guild, user)
                idlist = []
                for chan in mchannels:
                    idlist.append(chan.id)
                    if not chan.id in channelcounts:
                        channelcounts[chan.id] = {"name":chan.name, "count":0}
                    elif chan.id in channelcounts and channelcounts[chan.id]["name"].endswith(" [Unavailable]"):
                        channelcounts[chan.id]["name"] = channelcounts[chan.id]["name"].replace(" [Unavailable]", "")
                
                for chan in nchannels:
                    idlist.append(chan.id)
                    if not chan.id in channelcounts:
                        channelcounts[chan.id] = {"name":chan.name, "count":0}
                    elif chan.id in channelcounts and channelcounts[chan.id]["name"].endswith(" [Unavailable]"):
                        channelcounts[chan.id] = channelcounts[chan.id]["name"].replace(" [Unavailable]", "")
                
                for chan in channelcounts.keys():
                    if not chan in idlist and not channelcounts[chan]["name"].endswith(" [Unavailable]"):
                        channelcounts[chan]["name"] = channelcounts[chan]["name"]+" [Unavailable]"
            
            for channel in mchannels:
                try:
                    if (channel.id in lastSpam and lastSpam[channel.id] + channel.slowmode_delay > time.time()):
                        continue
                    if (botType != 4):
                        cmd.target_channel = channel
                    if (botType==0):
                        await cmd.__call__(channel=channel, **{opt.name:settings["presets"][settings["default_preset"]]["spam"]})
                    elif (botType==1):
                        await cmd.__call__(channel=channel, **{opt.name:settings["presets"][settings["default_preset"]]["spam"], "randomize":settings["randomize"], "slowmode":channel.slowmode_delay>0, "silent":settings["silent"]})
                    elif (botType==2):
                        await cmd.__call__(channel=channel, **{opt.name:settings["presets"][settings["default_preset"]]["spam"], "randomize":settings["randomize"], "slowmode_delay":channel.slowmode_delay})
                    elif (botType==3):
                        await cmd.__call__(channel=channel)
                    elif (botType==4):
                        for i in range(0,5):
                            await channel.send(settings["presets"][settings["default_preset"]]["spam"], silent=settings["silent"])
                    
                    channelcounts[channel.id]["count"] += 1
                    lastSpam[channel.id] = time.time()
                    clear()
                    for chan in channelcounts.values():
                        print(f"[{str(chan['count'])}] {chan['name']}")
                except:
                    pass
            for channel in nchannels:
                try:
                    if (channel.id in lastSpam and lastSpam[channel.id] + channel.slowmode_delay > time.time()):
                        continue
                    if (botType != 4):
                        cmd.target_channel = channel
                    if (botType==0):
                        await cmd.__call__(channel=channel, **{opt.name:settings["presets"][settings["default_preset"]]["fallback"]})
                    elif (botType==1):
                        await cmd.__call__(channel=channel, **{opt.name:settings["presets"][settings["default_preset"]]["fallback"], "randomize":settings["randomize"], "slowmode":channel.slowmode_delay>0, "silent":settings["silent"]})
                    elif (botType==2):
                        await cmd.__call__(channel=channel, **{opt.name:settings["presets"][settings["default_preset"]]["fallback"], "randomize":settings["randomize"], "slowmode_delay":channel.slowmode_delay})
                    elif (botType==3):
                        await cmd.__call__(channel=channel)
                    elif (botType==4):
                        for i in range(0,5):
                            await channel.send(settings["presets"][settings["default_preset"]]["fallback"], silent=settings["silent"])
                    
                    channelcounts[channel.id]["count"] += 1
                    lastSpam[channel.id] = time.time()
                    clear()
                    for chan in channelcounts.values():
                        print(f"[{str(chan['count'])}] {chan['name']}")
                except:
                    pass


def startSpam():
    global user_spam
    global settings
    global guild_id
    global curmenu
    global stdscr
    global loop
    
    stdscr.addstr(0, 0, "Server or Channel ID: ")
    stdscr.move(1, 0)
    curses.setsyx(1, 0)
    curses.doupdate()
    idstr=cinput(1, num_only=True)
    
    if (idstr==""):
        return

    menu=["Bot Spam", "User Spam", "Return"]
    option=choice(menu)
    if (option==2):
        return
    elif (option==1):
        user_spam=True

    # start spam

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()
    clear()
    
    guild_id = int(idstr)
    client = spamClient()
    client.run(settings["token"]["token"])
    sys.exit(0)
    return

def doAction(option):
    global check_chan
    global user_spam
    global settings
    global guild_id
    global curmenu
    global stdscr
    global loop
    global sc

    if (curmenu == mainmenu):
        if (option==0):
            stdscr.clear()
            fn=0
            if (settings["default_preset"] == -1):
                stdscr.addstr(fn, 0, "Must specify preset.")
                fn+=1

            if (settings["token"]["token"] == ""):
                stdscr.addstr(fn, 0, "Must specify token.")
                fn+=1

            if (settings["app_id"] == -1):
                stdscr.addstr(fn, 0, "Must specify application ID.")
                fn+=1

            if (settings["cmd_name"] == ""):
                stdscr.addstr(fn, 0, "Must specify command name.")
                fn+=1

            if (fn == 0):
                startSpam()
            else:
                stdscr.addstr(fn, 0, "Press any key to continue...")
                stdscr.getkey()
        elif (option == 1):
            menu = stdscr.subwin(9+1, 70, 1, 0)
            menu.box()
            prevopt=0
            while True:
                stdscr.clear()
                stdscr.addstr(0, 0, "Select Token:")
                stdscr.refresh()
                array=["Return", "Add Token", "Remove Token", "Rename Token"]
                for tk in settings["tokens"]:
                    if (tk["token"] == settings["token"]["token"]):
                        array.append("* "+tk["name"])
                    else:
                        array.append("  "+tk["name"])
                option = choice(array, 0, menu, prevopt)
                prevopt=option
                if (option == 0):
                    break
                elif (option == 1):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Name: ")
                    stdscr.refresh()
                    stdscr.move(1, 0)
                    curses.setsyx(1, 0)
                    curses.doupdate()
                    namestr=cinput(1)
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Token: ")
                    stdscr.refresh()
                    stdscr.move(1, 0)
                    curses.setsyx(1, 0)
                    curses.doupdate()
                    tkstr=cinput(1)
                    if (tkstr==""):
                        continue
                    brk = False
                    for token in settings["tokens"]:
                        if (token["token"] == tkstr):
                            stdscr.clear()
                            stdscr.addstr(0, 0, f"Token already exists as \"{token['name']}\"!")
                            stdscr.refresh()
                            time.sleep(2)
                            brk = True
                            break
                    if (brk):
                        continue
                    settings["tokens"].append({"name":namestr, "token":tkstr})
                    if (settings["token"]["token"] == ""):
                        settings["token"] = {"name":namestr, "token":tkstr}
                    applySettings()
                elif (option == 2):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Select Token to DELETE:")
                    stdscr.refresh()
                    menu = stdscr.subwin(9+1, 70, 1, 0)
                    menu.box()
                    array=["Return"]
                    for token in settings["tokens"]:
                        array.append(token["name"])

                    token = choice(array, 0, menu)
                    if (token==0):
                        continue
                    if (settings["tokens"][token-1]["token"] == settings["token"]["token"]):
                        settings["token"]["token"] = ""
                    del settings["tokens"][token-1]
                    applySettings()
                elif (option == 3):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Select Token to Rename:")
                    stdscr.refresh()
                    menu = stdscr.subwin(9+1, 70, 1, 0)
                    menu.box()
                    array=["Return"]
                    for token in settings["tokens"]:
                        array.append(token["name"])

                    token = choice(array, 0, menu)-1
                    if (token==-1):
                        continue

                    stdscr.clear()
                    stdscr.addstr(0, 0, "New Token Name: ")
                    stdscr.move(1, 0)
                    curses.setsyx(1, 0)
                    curses.doupdate()
                    stdscr.refresh()
                    namestr=cinput(1)
                    
                    if (namestr == ""):
                        continue
                    if (settings["tokens"][token-1]["token"] == settings["token"]["token"]):
                        settings["token"]["name"] = namestr
                    settings["tokens"][token]["name"] = namestr
                    applySettings()
                else:
                    settings["token"] = settings["tokens"][option-4]
                    applySettings()
                    
        elif (option == 2):
            stdscr.clear()
            stdscr.addstr(0, 0, "Application ID: ")
            stdscr.move(1, 0)
            curses.setsyx(1, 0)
            curses.doupdate()
            idstr=cinput(1, num_only=True)

            stdscr.addstr(2, 0, "Command Name: ")
            stdscr.move(3, 0)
            curses.setsyx(3, 0)
            curses.doupdate()
            cmdstr=cinput(3)
            if (idstr.isdigit()):
                settings["app_id"] = int(idstr)
            if (cmdstr != ""):
                settings["cmd_name"] = cmdstr
            applySettings()
        elif (option == 3):
            stdscr.clear()
            stdscr.addstr(0, 0, "Maximum Spam Count: ")
            stdscr.move(1, 0)
            curses.setsyx(1, 0)
            curses.doupdate()
            maxstr=cinput(1, txt=str(settings["auto_leave"]), num_only=True)
            if (maxstr.lstrip("-+").isdigit()):
                settings["auto_leave"] = int(maxstr)
                applySettings()
        elif (option == 4):
            prevopt=0
            while True:
                presetmenu=["Return", "Add Preset", "Edit Preset", "Delete Preset", "Clone Preset"]
                for i,preset in enumerate(settings["presets"]):
                    if (i != settings["default_preset"]):
                        presetmenu.append("  "+preset["name"])
                    else:
                        presetmenu.append("* "+preset["name"])
                option = choice(presetmenu, option=prevopt)

                prevopt=option
                if (option==0):
                    break
                elif (option==1):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Preset Name: ")
                    stdscr.move(1, 0)
                    curses.setsyx(1, 0)
                    curses.doupdate()
                    namestr=cinput(1)
                    
                    if (namestr == ""):
                        continue

                    stdscr.addstr(2, 0, "Spam Message Prompted")
                    spammsg = easygui.textbox("Enter Spam Message", "Prompt", codebox=True)

                    if (spammsg == "" or spammsg == None):
                        continue

                    fallbackmsg = easygui.textbox("Enter Fallback Message", "Prompt", codebox=True)

                    if (fallbackmsg == "" or fallbackmsg == None):
                        fallbackmsg = spammsg
                    
                    settings["presets"].append({"name":namestr, "spam":spammsg, "fallback":fallbackmsg})
                    applySettings()
                elif (option == 2):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Select Preset to Edit:")
                    array=["Return"]
                    for preset in settings["presets"]:
                        array.append(preset["name"])

                    menu = stdscr.subwin(1, 0)
                    menu.box()
                    preset = choice(array, 0, menu)-1
                    if (preset == -1):
                        continue
                    optionarray=["Return", "Edit Name", "Edit Spam Message", "Edit Fallback Message"]
                    while (True):
                        option=choice(optionarray)
                        if (option == 0):
                            break
                        elif (option == 1):
                            stdscr.clear()
                            stdscr.addstr(0, 0, "Preset Name: ")
                            stdscr.move(1, 0)
                            curses.setsyx(1, 0)
                            curses.doupdate()
                            namestr=cinput(1, txt=settings["presets"][preset]["name"])
                            
                            if (namestr == ""):
                                continue

                            settings["presets"][preset]["name"] = namestr
                        elif (option == 2):
                            spammsg = easygui.textbox("Enter Spam Message", "Prompt", settings["presets"][preset]["spam"], codebox=True)

                            if (spammsg == ""):
                                continue

                            if (not isinstance(spammsg, str)):
                                continue
                            settings["presets"][preset]["spam"] = spammsg
                        elif (option == 3):
                            fallbackmsg = easygui.textbox("Enter Fallback Message", "Prompt", settings["presets"][preset]["fallback"], codebox=True)

                            if (fallbackmsg == ""):
                                continue

                            if (not isinstance(fallbackmsg, str)):
                                continue

                            settings["presets"][preset]["fallback"] = fallbackmsg
                        applySettings()
                elif (option == 3):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Select Preset to DELETE:")
                    array=["Return"]
                    for preset in settings["presets"]:
                        array.append(preset["name"])

                    menu = stdscr.subwin(1, 0)
                    menu.box()
                    preset = choice(array, 0, menu)-1
                    if (preset == -1):
                        continue

                    if (preset < settings["default_preset"]):
                        settings["default_preset"] = settings["default_preset"]-1
                    elif (preset == settings["default_preset"]):
                        settings["default_preset"] = -1

                    if (preset < settings["default_preset"]):
                        settings["default_preset"] = settings["default_preset"]-1
                    elif (preset == settings["default_preset"]):
                        settings["default_preset"] = -1

                    del settings["presets"][preset]
                    applySettings()
                elif (option == 4):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Select Preset to Clone:")
                    array=["Return"]
                    for preset in settings["presets"]:
                        array.append(preset["name"])

                    menu = stdscr.subwin(1, 0)
                    menu.box()
                    preset = choice(array, 0, menu)-1
                    if (preset == -1):
                        continue
                    preset = settings["presets"][preset]
                    
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Cloned Preset Name: ")
                    stdscr.move(1, 0)
                    curses.setsyx(1, 0)
                    curses.doupdate()
                    namestr=cinput(1)
                    
                    if (namestr == ""):
                        continue

                    settings["presets"].append({"name":namestr, "spam":preset["spam"], "fallback":preset["fallback"]})
                    applySettings()
                else:
                    settings["default_preset"] = option-5
                    applySettings()

        elif (option == 5):
            stdscr.clear()
            stdscr.addstr(0, 0, "Randomize last 5 characters of message?")
            array=[]
            if (settings["randomize"]):
                array.append("* Yes")
                array.append("  No")
            else:
                array.append("  Yes")
                array.append("* No")

            menu = stdscr.subwin(1, 0)
            menu.box()
            option = choice(array, 0, menu)

            settings["randomize"] = (option == 0)
            applySettings()
        elif (option == 6):
            loop = False
        elif (option == 7):
            if (settings["bot_token"]["token"] == ""):
                stdscr.clear()
                stdscr.addstr(0, 0, "Must specify bot token.")
                stdscr.addstr(1, 0, "Press any key to continue...")
                stdscr.getkey()
                return
            if (os.name == "posix"):
                # get terminal
                term = ""
                terminals=["st", "xfce4-terminal", "konsole", "xterm", "gnome-terminal"]

                for terminal in terminals:
                    if (which(terminal) is not None):
                        term = terminal
                        break
                if (term == ""):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "No supported terminal emulators found.")
                    p=subprocess.Popen(["botenv/bin/python3", "bot.py", settings["bot_token"]["token"]], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                    stdscr.addstr(1, 0, f"Process has been launched at PID: {p.pid}")
                    stdscr.addstr(2, 0, "Press any key to continue...")
                    stdscr.getkey() 
                else:
                    subprocess.Popen([term, "-e", "\""+os.path.abspath("botenv/bin/python3")+"\"" + " bot.py "+settings["bot_token"]["token"]], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            elif (os.name == "nt"):
                try:
                    subprocess.Popen(["botenv\\Scripts\\python", "bot.py", settings["bot_token"]["token"]], creationflags=subprocess.CREATE_NEW_CONSOLE)
                except Exception as e:
                    stdscr.clear()
                    stdscr.addstr(0, 0, str(e))
                    stdscr.getkey()
        elif (option == 8):
            menu = stdscr.subwin(9+1, 70, 1, 0)
            menu.box()
            prevopt=0
            while True:
                stdscr.clear()
                stdscr.addstr(0, 0, "Select Bot Token:")
                stdscr.refresh()
                array=["Return", "Add Token", "Remove Token", "Rename Token"]
                for token in settings["bot_tokens"]:
                    if (token["token"] == settings["bot_token"]["token"]):
                        array.append("* "+token["name"])
                    else:
                        array.append("  "+token["name"])
                option = choice(array, 0, menu, prevopt)
                prevopt = option
                if (option == 0):
                    break
                elif (option == 1):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "New Token Name: ")
                    stdscr.refresh()
                    stdscr.move(1, 0)
                    curses.setsyx(1, 0)
                    curses.doupdate()
                    namestr=cinput(1)
                    stdscr.clear()
                    stdscr.addstr(0, 0, "New Token: ")
                    stdscr.refresh()
                    stdscr.move(1, 0)
                    curses.setsyx(1, 0)
                    curses.doupdate()
                    tkstr=cinput(1)
                    if (tkstr==""):
                        continue
                    brk = False
                    for token in settings["bot_tokens"]:
                        if (token["token"] == tkstr):
                            stdscr.clear()
                            stdscr.addstr(0, 0, f"Token already exists as \"{token['name']}\"!")
                            stdscr.refresh()
                            time.sleep(2)
                            brk = True
                            break
                    if (brk):
                        continue
                    settings["bot_tokens"].append({"name":namestr, "token":tkstr})
                    if (settings["bot_token"]["token"] == ""):
                        settings["bot_token"] = {"name":namestr, "token":tkstr}
                    applySettings()
                elif (option == 2):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Select Token to DELETE:")
                    stdscr.refresh()
                    menu = stdscr.subwin(9+1, 70, 1, 0)
                    menu.box()
                    array=["Return"]
                    for token in settings["bot_tokens"]:
                        array.append(token["name"])

                    token = choice(array, 0, menu)
                    if (token==0):
                        continue
                    if (settings["bot_tokens"][token-1]["token"] == settings["bot_token"]["token"]):
                        settings["bot_token"]["token"] = ""
                    del settings["bot_tokens"][token-1]
                    applySettings()
                elif (option == 3):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Select Token to Rename:")
                    stdscr.refresh()
                    menu = stdscr.subwin(9+1, 70, 1, 0)
                    menu.box()
                    array=["Return"]
                    for token in settings["bot_tokens"]:
                        array.append(token["name"])

                    token = choice(array, 0, menu)-1
                    if (token==-1):
                        continue

                    stdscr.clear()
                    stdscr.addstr(0, 0, "New Token Name: ")
                    stdscr.move(1, 0)
                    curses.setsyx(1, 0)
                    curses.doupdate()
                    stdscr.refresh()
                    namestr=cinput(1)
                    
                    if (namestr == ""):
                        continue
                    if (settings["bot_tokens"][token-1]["token"] == settings["bot_token"]["token"]):
                        settings["bot_token"]["name"] = namestr
                    settings["bot_tokens"][token]["name"] = namestr
                    applySettings()
                else:
                    settings["bot_token"] = settings["bot_tokens"][option-4]
                    applySettings()
                    
        elif (option == 9):
            stdscr.clear()
            stdscr.addstr(0, 0, "Send Silent Messages?")
            array=[]
            if (settings["silent"]):
                array.append("* Yes")
                array.append("  No")
            else:
                array.append("  Yes")
                array.append("* No")

            menu = stdscr.subwin(1, 0)
            menu.box()
            option = choice(array, 0, menu)

            settings["silent"] = (option == 0)
            applySettings()
        elif (option == 10):
            stdscr.clear()
            stdscr.addstr(0, 0, "Check Server or Channel ID: ")
            stdscr.move(1, 0)
            curses.setsyx(1, 0)
            curses.doupdate()
            idstr=cinput(1, num_only=True)
            
            if (idstr==""):
                return
            
            curses.nocbreak()
            stdscr.keypad(False)
            curses.echo()
            curses.endwin()
            clear()
            
            guild_id = int(idstr)
            check_chan = True
            user_spam = True
            client = spamClient()
            client.run(settings["token"]["token"])
            sys.exit(0)
            return
            

def main(stdscr):
    global loop
    global settings

    menu = stdscr.subwin(10, 70, 1, 0)
    menu.box()
    opt = 0
    while (loop):
        stdscr.clear()
        if (settings["default_preset"] == -1):
            stdscr.addstr(0, 0, "Current Preset: None Selected")
        else:
            if (len(settings["presets"]) > settings["default_preset"]):
                stdscr.addstr(0, 0, "Current Preset: \""+settings["presets"][settings["default_preset"]]["name"]+"\"")
        stdscr.addstr(11, 0, "Discord Spammer v2.0 - peabox.org <3")
        stdscr.addstr(13, 0, "Current User Token: \""+settings["token"]["name"]+"\"")
        stdscr.addstr(14, 0, "Current Bot Token: \""+settings["bot_token"]["name"]+"\"")
        stdscr.refresh()
        opt = choice(curmenu, 0, menu, opt)
        doAction(opt)

ymax, xmax = stdscr.getmaxyx()
if (ymax <= 14 or xmax <= 70):
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()
    print("Terminal screen too small! (below or equal to 14 columns/below or equal to 70 rows)")
    sys.exit(1)
else:
    main(stdscr)
curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()
