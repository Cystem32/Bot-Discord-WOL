# commands.py

import discord
from discord.ext import commands
import socket
import asyncio
import paramiko
import datetime
from config import *

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


#---------------------------------------------------
# La commande Wake
    @commands.command(name='wake', help='Allumer un serveur')
    async def wake(self, ctx):
        if ROLE_ID in [role.id for role in ctx.author.roles]:
            now = datetime.datetime.now()

            start_hour = int(START_HOUR)
            end_hour = int(END_HOUR)

            if start_hour <= now.hour and now.hour < end_hour:
                embed = discord.Embed(title='Allumer un serveur', description='Sélectionnez un serveur à allumer', color=0x3498db)
                view = WakeView()
                embed.set_footer(text='By Cystem32 🖥️')
                await ctx.send(embed=embed, view=view)
                await asyncio.sleep(10)
            else:
                embed = discord.Embed(title='Erreur', description=f'❌Erreur : la commande wake est uniquement disponible entre {start_hour}h et {end_hour}h.', color=0xff0000)
                await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title='Erreur', description='⛔Vous n\'avez pas le rôle nécessaire pour utiliser cette commande.', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)

    @wake.error
    async def wake_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            embed = discord.Embed(title='Erreur', description='⛔Vous n\'avez pas le rôle nécessaire pour utiliser cette commande.', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title='Erreur', description=f'❌Erreur : {error}', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)


#---------------------------------------------------
# La commande Shutdown
    @commands.command(name='shutdown', help='Éteindre un serveur')
    async def shutdown(self, ctx):
        if ROLE_ID in [role.id for role in ctx.author.roles]:
            view = ShutdownView()
            embed = discord.Embed(title='Éteindre un serveur', description='Sélectionnez un serveur à éteindre', color=0x3498db)
            for server in servers:
                button = ShutdownButton(server)
                view.add_item(button)
            await ctx.send(embed=embed, view=view)
        else:
            embed = discord.Embed(title='Erreur', description='⛔Vous n\'avez pas le rôle nécessaire pour utiliser cette commande.', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)


#---------------------------------------------------
# La commande Autooff
    @commands.command(name='autooff', help='Activer le système d\'arrêt automatique du serveur')
    async def autosleep(self, ctx):
        if ROLE_ID in [role.id for role in ctx.author.roles]:
            now = datetime.datetime.now()

            shutdown_hour = int(AUTO_OFF_HOUR)

            if now.hour < shutdown_hour:
                embed = discord.Embed(title='✔️Système d\'arrêt automatique', description=f'Le système d\'arrêt automatique est activé. Le serveur s\'éteindra à {shutdown_hour}h.', color=0x3498db)
                await ctx.send(embed=embed)

                await self.schedule_shutdown(shutdown_hour)
            else:
                embed = discord.Embed(title='Erreur', description=f'❌Erreur : l\'heure d\'arrêt automatique est déjà passée.', color=0xff0000)
                await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title='Erreur', description='⛔Vous n\'avez pas le rôle nécessaire pour utiliser cette commande.', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)

    async def schedule_shutdown(self, shutdown_hour):
        delay = (shutdown_hour - datetime.datetime.now().hour) * 3600

        await asyncio.sleep(delay)

        for server in servers:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(servers[server]['ip'], username= SSH_USER, password= SSH_PASSWORD)

                stdin, stdout, stderr = ssh.exec_command('sudo shutdown -h now')

                stdout.channel.recv_exit_status()

                ssh.close()

                embed = discord.Embed(title='Succès', description=f'✔️Le serveur {server} a été éteint.', color=0x00ff00)
                await self.bot.get_channel(LOG_CHANNEL).send(embed=embed)
            except Exception as e:
                embed = discord.Embed(title='Erreur', description=f'❌Erreur lors de l\'extinction du serveur {server} : {e}', color=0xff0000)
                await self.bot.get_channel(LOG_CHANNEL).send(embed=embed)


#---------------------------------------------------
# La commande Help
    @commands.command(name='aide', help='Affiche l\'aide du bot')
    async def help(self, ctx):
        embed = discord.Embed(title='Aide du bot', description='Liste des commandes disponibles', color=0x3498db)

        embed.add_field(name='`wake`', value='Allume un serveur', inline=False)
        embed.add_field(name='`shutdown`', value='Éteindre un serveur', inline=False)
        embed.add_field(name='`autooff`', value='Activer le système d\'arrêt automatique du serveur (Pour le desactiver faut redemarer le bot)', inline=False)
        embed.add_field(name='`stop`', value='Arrête le bot', inline=False)

        embed.set_footer(text='By Cystem32 🖥️')

        await ctx.send(embed=embed)


#---------------------------------------------------
# La commande Stop
    @commands.command(name='stop', help='Arrête le bot')
    async def stop(self, ctx):
        if ctx.author.id == OWNER_ID:
            await ctx.send('🔴Arrêt du bot...')
            await self.bot.close()
        else:
            embed = discord.Embed(title='Erreur', description='⛔Vous n\'êtes pas le propriétaire du serveur.', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)

class WakeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=server, description=f'Adresse IP : {servers[server]["ip"]}', emoji='💻') 
            for server in servers
        ]
        super().__init__(placeholder='📋Sélectionnez un serveur', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        server = self.values[0]
        mac = servers[server]['mac']
        ip = servers[server]['ip']

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            magic_packet = bytearray.fromhex('FF FF FF FF FF FF') + bytearray.fromhex(mac.replace(':', '') * 16)
            sock.sendto(magic_packet, ('255.255.255.255', 9))
            sock.close()

            embed = discord.Embed(title='Allumer un serveur', description=f'⚡Paquet WOL envoyé à {server} ({ip})', color=0x3498db)
            await interaction.response.send_message(embed=embed, ephemeral=True)

            await asyncio.sleep(WAIT_TIME)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ip, 22))
                sock.close()
                embed = discord.Embed(title='Information du serveur', description=f'✔️Le serveur {server} ({ip}) est maintenant allumé!', color=0x00ff00)
                await interaction.followup.send(embed=embed, ephemeral=True)
            except socket.error:
                embed = discord.Embed(title='Erreur du serveur', description=f'❌Erreur : le serveur {server} ({ip}) n\'est pas allumé.', color=0xff0000)
                await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title='Erreur de l\'envoie', description=f'❌Erreur lors de l\'envoi du paquet WOL à {server} ({ip}) : {e}', color=0xff0000)
            await interaction.followup.send(embed=embed, ephemeral=True)


#---------------------------------------------------
# Les UI
class WakeView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(WakeSelect())

class ShutdownButton(discord.ui.Button):
    def __init__(self, server):
        super().__init__(style=discord.ButtonStyle.danger, label="Éteindre le serveur")
        self.custom_id = server

    async def callback(self, interaction: discord.Interaction):
        server = self.custom_id
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(servers[server]['ip'], username= SSH_USER, password= SSH_PASSWORD)

            stdin, stdout, stderr = ssh.exec_command('sudo shutdown -h now')

            stdout.channel.recv_exit_status()

            ssh.close()

            embed = discord.Embed(title='Succès', description=f'✔️Le serveur {server} a été éteint.', color=0x00ff00)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            embed = discord.Embed(title='Erreur', description=f'❌Erreur lors de l\'extinction du serveur {server} : {e}', color=0xff0000)
            await interaction.response.send_message(embed=embed)

class ShutdownView(discord.ui.View):
    def __init__(self):
        super().__init__()


#---------------------------------------------------
async def setup(bot):
    await bot.add_cog(Commands(bot))