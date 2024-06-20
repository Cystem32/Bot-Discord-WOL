# commands.py

import discord
from discord.ext import commands
import socket
import asyncio
import paramiko
import datetime
from config import *

# Custom Select Menu for server selection
class WakeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=server, description=f'Adresse IP : {servers[server]["ip"]}', emoji='💻') 
            for server in servers
        ]
        super().__init__(placeholder='Sélectionnez un serveur', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        server = self.values[0]
        mac = servers[server]['mac']
        ip = servers[server]['ip']

        # Envoie du paquet WOL
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            magic_packet = bytearray.fromhex('FF FF FF FF FF FF') + bytearray.fromhex(mac.replace(':', '') * 16)
            sock.sendto(magic_packet, ('255.255.255.255', 9))
            sock.close()

            embed = discord.Embed(title='Allumer un serveur', description=f'Paquet WOL envoyé à {server} ({ip})', color=0x3498db)
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Vérification si le serveur est allumé
            await asyncio.sleep(WAIT_TIME)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ip, 22))
                sock.close()
                embed = discord.Embed(title='Information du serveur', description=f'Le serveur {server} ({ip}) est maintenant allumé!', color=0x00ff00)
                await interaction.followup.send(embed=embed, ephemeral=True)
            except socket.error:
                embed = discord.Embed(title='Erreur du serveur', description=f'Erreur : le serveur {server} ({ip}) n\'est pas allumé.', color=0xff0000)
                await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title='Erreur de l\'envoie', description=f'Erreur lors de l\'envoi du paquet WOL à {server} ({ip}) : {e}', color=0xff0000)
            await interaction.followup.send(embed=embed, ephemeral=True)

# View for wake command
class WakeView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(WakeSelect())

# View for shutdown command
class ShutdownView(discord.ui.View):
    def __init__(self):
        super().__init__()

# Button for shutdown command
class ShutdownButton(discord.ui.Button):
    def __init__(self, server):
        super().__init__(style=discord.ButtonStyle.danger, label="Éteindre le serveur")
        self.custom_id = server

    async def callback(self, interaction: discord.Interaction):
        server = self.custom_id
        try:
            # Connexion au serveur via SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(servers[server]['ip'], username= SSH_USER, password= SSH_PASSWORD)

            # Exécution de la commande pour éteindre le serveur
            stdin, stdout, stderr = ssh.exec_command('sudo shutdown -h now')

            # Attente de la fin de l'exécution de la commande
            stdout.channel.recv_exit_status()

            # Déconnexion du serveur
            ssh.close()

            embed = discord.Embed(title='Succès', description=f'Le serveur {server} a été éteint.', color=0x00ff00)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            embed = discord.Embed(title='Erreur', description=f'Erreur lors de l\'extinction du serveur {server} : {e}', color=0xff0000)
            await interaction.response.send_message(embed=embed)

# Cog for the commands
class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Wake command
    @commands.command(name='wake', help='Allumer un serveur')
    async def wake(self, ctx):
        if ROLE_ID in [role.id for role in ctx.author.roles]:
            # Get the current time
            now = datetime.datetime.now()

            # Get the allowed hours from the config file
            start_hour = int(START_HOUR)
            end_hour = int(END_HOUR)

            # Check if the current time is within the allowed hours
            if start_hour <= now.hour and now.hour < end_hour:
                embed = discord.Embed(title='Allumer un serveur', description='Sélectionnez un serveur à allumer', color=0x3498db)
                view = WakeView()
                embed.set_footer(text='By Cystem32')
                await ctx.send(embed=embed, view=view)
                await asyncio.sleep(10)
            else:
                embed = discord.Embed(title='Erreur', description=f'Erreur : la commande wake est uniquement disponible entre {start_hour}h et {end_hour}h.', color=0xff0000)
                await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title='Erreur', description='Vous n\'avez pas le rôle nécessaire pour utiliser cette commande.', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)

    # Error handling for wake command
    @wake.error
    async def wake_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            embed = discord.Embed(title='Erreur', description='Vous n\'avez pas le rôle nécessaire pour utiliser cette commande.', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title='Erreur', description=f'Erreur : {error}', color=0xff0000)
            await ctx.send(embed=embed,ephemeral=True)

    # Update server statistics
    async def update_stats(self, message):
        while True:
            embed = discord.Embed(title='Statistiques des serveurs', color=0x3498db)
            for server in servers:
                ip = servers[server]['ip']
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((ip, 22))
                    sock.close()
                    status = '🟢'
                except socket.error:
                    status = '🔴'
                embed.add_field(name=server, value=f'Adresse IP : {ip} {status}', inline=False)
            await message.edit(embed=embed)
            await asyncio.sleep(5)

    # Stats command
    @commands.command(name='stats', help='Affiche les statistiques des serveurs')
    async def stats(self, ctx):
        if ctx.author.id == OWNER_ID:
            embed = discord.Embed(title='Statistiques des serveurs', color=0x3498db)
            message = await ctx.send(embed=embed)
            await self.update_stats(message)
        else:
            embed = discord.Embed(title='Erreur', description='Vous n\'êtes pas le propriétaire du serveur.', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)

    # Error handling for stats command
    @stats.error
    async def stats_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(title='Erreur', description='Vous n\'êtes pas le propriétaire du serveur.', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title='Erreur', description=f'Erreur : {error}', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)

    # Shutdown command
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
            embed = discord.Embed(title='Erreur', description='Vous n\'avez pas le rôle nécessaire pour utiliser cette commande.', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)

    # Help command
    @commands.command(name='aide', help='Affiche l\'aide du bot')
    async def help(self, ctx):
        embed = discord.Embed(title='Aide du bot', description='Liste des commandes disponibles', color=0x3498db)

        embed.add_field(name='`wake`', value='Allume un serveur', inline=False)
        embed.add_field(name='`stats`', value='Affiche les statistiques des serveurs', inline=False)
        embed.add_field(name='`shutdown`', value='Éteindre un serveur', inline=False)
        embed.add_field(name='`rename`', value='Changer le surnom du bot', inline=False)
        embed.add_field(name='`stop`', value='Arrête le bot', inline=False)

        embed.set_footer(text='By Cystem32')

        await ctx.send(embed=embed)

    # Rename command
    @commands.command(name='rename', help='Changer le surnom du bot')
    async def setnick(self, ctx, *, new_nickname):
        if ctx.author.id == OWNER_ID:
            try:
                await ctx.guild.me.edit(nick=new_nickname)
                embed = discord.Embed(title='Succès', description=f'Le surnom du bot a été changé en {new_nickname}', color=0x00ff00)
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(title='Erreur', description='Le bot n\'a pas les permissions nécessaires pour changer son surnom.', color=0xff0000)
                await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title='Erreur', description='Vous n\'avez pas le rôle nécessaire pour utiliser cette commande.', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)

    # Stop command
    @commands.command(name='stop', help='Arrête le bot')
    async def stop(self, ctx):
        if ctx.author.id == OWNER_ID:
            await ctx.send('Arrêt du bot...')
            await self.bot.close()
        else:
            embed = discord.Embed(title='Erreur', description='Vous n\'êtes pas le propriétaire du serveur.', color=0xff0000)
            await ctx.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Commands(bot))

# Copyright (c) 2024 Cystem32