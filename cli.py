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

settings={"token":"", "bot_token":"", "app_id":-1, "cmd_name":"", "default_preset": -1, "presets":[], "randomize":False, "auto_leave":-1}
selpreset = -1

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

selpreset = settings["default_preset"]

mainmenu=["Spam", "Edit Token", "Edit Application ID and Command", "Set Maximum Spam Count", "Select Preset", "Edit Presets", "Randomize Messages", "Exit", "Start Bot", "Edit Bot Token"]

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
        elif (k == "KEY_BACKSPACE"):
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

def choice(array, offsety=0, scr=stdscr):
    global stdscr
    option=0
    ymax, xmax = scr.getmaxyx()
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
            numpos = len(array)
            if (numpos>=ymax):
                numpos=ymax-1
            scr.addstr(numpos+offsety, 0, k)
            while (True):
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
                elif (k == "KEY_BACKSPACE"):
                    if (len(num)<=1):
                        num=""
                        break
                    num = num[:-1]
                    scr.addstr(numpos+offsety, len(num), " ")
                elif (not k.isdigit):
                    num=""
            if (num!=""):
                if (int(num)<len(array)):
                    return option
        elif (k=="\n"):
            return option

guild_id=0

def clear():
    os.system('cls' if os.name == 'nt' else "printf '\033c'")

class spamClient(discord.Client):
    global stdscr
    global settings
    global selpreset
    global guild_id

    async def fetch_channels(self, guild, user):
        mchannels = []
        nchannels = []

        for channel in guild.channels:
            if (channel.type == discord.ChannelType.category):
                continue
            
            permissions = channel.permissions_for(user)
            
            if (not permissions.view_channel
                or not permissions.read_message_history
                or not permissions.read_messages
                or not permissions.use_application_commands
                or not permissions.send_messages
                ):
                continue
            
            if (not permissions.attach_files):
                nchannels.append(channel)
            else:
                mchannels.append(channel)
        return mchannels, nchannels

    async def on_ready(self):
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()
        clear()
        print(f"Logged in as {self.user}!")
        # get bot auth
        app=None
        for auth in await self.authorizations():
            if auth.application.id == settings["app_id"]:
                app = auth.application
        if (app == None):
            print("Application is not installed, or wrong ID was provided.")
            sys.exit(1)

        cmd=None
        for command in await app.bot.application_commands():
            if (command.name.lower().find(settings["cmd_name"].lower()) != -1):
                cmd=command
        
        if (cmd == None):
            print("Command not found. Typo or Wrong Application ID?")
            sys.exit(1)

        botType=0 # normie bot
        opt=None
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

        count=0
        channelcounts = {}
        
        for chan in mchannels:
            channelcounts[chan.id] = {"name":chan.name, "count":0}
        for chan in nchannels:
            channelcounts[chan.id] = {"name":chan.name, "count":0}

        while True:
            if (settings["auto_leave"] != -1 and count>=settings["auto_leave"]):
                print("Spam finished.")
                sys.exit(0)
            count+=1
            if (guild != None):
                mchannels, nchannels = await self.fetch_channels(guild, user)
            
            for channel in mchannels:
                cmd.target_channel = channel
                if (botType==0):
                    await cmd.__call__(channel=channel, **{opt.name:settings["presets"][selpreset]["spam"]})
                elif (botType==1):
                    await cmd.__call__(channel=channel, **{opt.name:settings["presets"][selpreset]["spam"], "randomize":settings["randomize"], "slowmode":channel.slowmode_delay>0})
                elif (botType==2):
                    await cmd.__call__(channel=channel, **{opt.name:settings["presets"][selpreset]["spam"], "randomize":settings["randomize"], "slowmode_delay":channel.slowmode_delay})
                elif (botType==3):
                    await cmd.__call__(channel=channel)
                channelcounts[channel.id]["count"] += 1

            for channel in nchannels:
                cmd.target_channel = channel
                if (botType==0):
                    await cmd.__call__(channel=channel, **{opt.name:settings[selpreset]["fallback"]})
                elif (botType==1):
                    await cmd.__call__(channel=channel, **{opt.name:settings[selpreset]["fallback"], "randomize":settings["randomize"], "slowmode":channel.slwmode_delay>0})
                elif (botType==2):
                    await cmd.__call__(channel=channel, **{opt.name:settings[selpreset]["fallback"], "randomize":settings["randomize"], "slowmode_delay":channel.slwmode_delay})
                elif (botType==3):
                    await cmd.__call__(channel=channel)
                channelcounts[channel.id]["count"] += 1

            clear()
            for chan in channelcounts.values():
                print(f"[{str(chan['count'])}] {chan['name']}")

def startSpam():
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
    
    # start spam
    if (idstr == ""):
        return

    # wip
    stdscr.clear()
    stdscr.addstr(0, 0, "Logging in...")
    stdscr.refresh()
    
    guild_id = int(idstr)
    client = spamClient()
    client.run(settings["token"], log_handler=None)
    sys.exit(0)
    return

def doAction(option):
    global selpreset
    global settings
    global curmenu
    global stdscr
    global loop
    global sc

    if (curmenu == mainmenu):
        if (option==0):
            stdscr.clear()
            fn=0
            if (selpreset == -1):
                stdscr.addstr(fn, 0, "Must specify preset.")
                fn+=1

            if (settings["token"] == ""):
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
            stdscr.clear()
            stdscr.addstr(0, 0, "New Token: ")
            stdscr.move(1, 0)
            curses.setsyx(1, 0)
            curses.doupdate()
            tkstr=cinput(1)
            settings["token"] = tkstr
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
            stdscr.clear()
            stdscr.addstr(0, 0, "Select Preset:")
            array=["Return"]
            for preset in settings["presets"]:
                array.append(preset["name"])

            menu = stdscr.subwin(1, 0)
            menu.box()
            preset = choice(array, 0, menu)
            if (preset != 0):
                selpreset = preset-1
        elif (option == 5):
            while True:
                presetmenu=["Return", "Add Preset", "Edit Preset", "Delete Preset", "Set Default Preset", "Clone Preset"]
                option = choice(presetmenu)

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

                    if (spammsg == ""):
                        continue

                    fallbackmsg = easygui.textbox("Enter Fallback Message", "Prompt", codebox=True)

                    if (fallbackmsg == ""):
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

                    if (preset < selpreset):
                        selpreset = selpreset-1
                    elif (preset == selpreset):
                        selpreset = -1

                    del settings["presets"][preset]
                    applySettings()
                elif (option == 4):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Select Preset to set as default:")
                    array=["Return"]
                    for i,preset in enumerate(settings["presets"]):
                        if (i != settings["default_preset"]):
                            array.append("  "+preset["name"])
                        else:
                            array.append("* "+preset["name"])

                    menu = stdscr.subwin(1, 0)
                    menu.box()
                    preset = choice(array, 0, menu)-1
                    if (preset == -1):
                        continue

                    settings["default_preset"] = preset
                    applySettings()
                elif (option == 5):
                    stdscr.clear()
                    stdscr.addstr(0, 0, "Select Preset to clone:")
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

        elif (option == 6):
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
        elif (option == 7):
            loop = False
        elif (option == 8):
            if (settings["bot_token"] == ""):
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
                    p=subprocess.Popen(["botenv/bin/python3", "bot.py", settings["bot_token"]], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                    stdscr.addstr(1, 0, f"Process has been launched at PID: {p.pid}")
                    stdscr.addstr(2, 0, "Press any key to continue...")
                    stdscr.getkey() 
                else:
                    subprocess.Popen([term, "-e", os.path.abspath("botenv/bin/python3") + " bot.py "+settings["bot_token"]], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            elif (os.name == "nt"):
                subprocess.Popen(["botenv\\Scripts\\python", "bot.py", settings["bot_token"]], creationflags=subprocess.CREATE_NEW_CONSOLE, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        elif (option == 9):
            stdscr.clear()
            stdscr.addstr(0, 0, "New Bot Token: ")
            stdscr.move(1, 0)
            curses.setsyx(1, 0)
            curses.doupdate()
            tkstr=cinput(1)
            settings["bot_token"] = tkstr
            applySettings()

def main(stdscr):
    global loop
    global selpreset
    
    menu = stdscr.subwin(len(curmenu)+1, 70, 1, 0)
    menu.box()
    while (loop):
        stdscr.clear()
        if (selpreset == -1):
            stdscr.addstr(0, 0, "Current Preset: None Selected")
        else:
            if (len(settings["presets"]) > selpreset):
                stdscr.addstr(0, 0, "Current Preset: \""+settings["presets"][selpreset]["name"]+"\"")
        stdscr.addstr(len(curmenu)+2, 0, "Discord Spammer v2.0 - guns.lol/orangypea <3")
        stdscr.refresh()
        doAction(choice(curmenu, 0, menu))



main(stdscr)

curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()
