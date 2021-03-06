from os import terminal_size
import discord
import json
import asyncio
import datetime
import config
from discord.utils import get
import os
from discord import *
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix='.',intents=discord.Intents().all() ,case_insensitive=True)
client.remove_command("help")

@client.event
async def on_ready():
	print('hello')
	await client.change_presence(status=discord.Status.online,activity=discord.Game("Dm to Contact Mods"))
	client.add_view(Panel_View())

@client.command()
async def blacklist(ctx,who:discord.Member):
	with open("blacklisted.json") as j:
		data = json.load(j)

	if who.id in data:
		return await ctx.send(f"The user `who` is already blacklisted!")
	else:
		data.append(who.id)

		with open('blacklisted.json', 'w') as j:
			json.dump(data, j, indent=4)

		return await ctx.send(f"Successfully blacklisted `who`")

@client.command()
async def unblacklist(ctx,who:discord.Member):
	with open("blacklisted.json") as j:
		data = json.load(j)

	if who.id not in data:
		return await ctx.send(f"The user `who` is not blacklisted!")
	else:
		data.pop(data.index(who.id))

		with open('blacklisted.json', 'w') as j:
			json.dump(data, j, indent=4)

		return await ctx.send(f"Successfully Unblacklisted `who`")

class Panel_View(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=None)

	@discord.ui.button(label="Close",style=discord.ButtonStyle.gray,emoji="🔒",custom_id='close')
	async def call(self, button, i):
			channel = i.channel
			with open('tickets.json') as j:
				data = json.load(j)
				
				for x in data:
					
					if x['ticket_id'] == channel.id:

						confirm_view = discord.ui.View(timeout=10)

						ok = discord.ui.Button(
							label="Close",
							style=discord.ButtonStyle.danger
						)

						nope = discord.ui.Button(
							label="Cancel",
							style=discord.ButtonStyle.gray
						)

						async def n(i):
							await i.message.delete()
							return await i.response.defer()

						async def o(i):
							
							await i.response.edit_message(content=f"Ticket will be deleted in a few seconds",view=None)
							await asyncio.sleep(3)
							await channel.delete()

							opener = client.get_user(x['user_id'])
							if not opener:
								opener = await client.fetch_user(x['user_id'])
						
							await opener.send(f"`<< Thread Closed >>`\n>>> \nThank you for messaging Fox mail. Hope we answered your questions. If you have any more questions, feel free to DM us again!\n\nPlease note that your thread is now closed. If you message again, you will open another thread.")

							data.pop(data.index(x))

							with open('tickets.json', 'w') as j:
								json.dump(data, j, indent=4)

						ok.callback = o
						nope.callback = n

						confirm_view.add_item(ok)
						confirm_view.add_item(nope)

						async def timeout():
							msg = await i.original_message()
							for each in confirm_view.children:
								each.disabled = True
							await msg.edit(f"You didn't respond in time!",view=confirm_view)

						confirm_view.on_timeout = timeout

						await i.response.send_message("Are you sure you want to close this ticket?",view=confirm_view)

@client.event
async def on_message(msg):

	if msg.author == client.user:
		return

	with open("blacklisted.json") as j:
		data = json.load(j)

		if msg.author.id in data:
			return
		
	if msg.content.lower() == ".close":
		
		return await client.process_commands(msg)

	if msg.channel.type is discord.ChannelType.private:
		with open('tickets.json') as tickets:
			data = json.load(tickets)

			yes = False

			guild = client.get_guild(config.guild_id)
			if not guild:
				guild = await client.fetch_guild(config.guild_id)

			for x in data:

				if x['user_id'] == msg.author.id:

					yes = True

				else:

					yes = False

			if yes == True:
				
				ticket = guild.get_channel(x['ticket_id'])
				if not ticket:
					ticket = await guild.fetch_channel(x['ticket_id'])
				for i,each in enumerate(msg.attachments):
					end = each.filename.split(".")
					await each.save(f"{ticket.id}-{msg.id}-{i}.{end[1]}")
				
				files = []
				for filename in os.listdir():
					if filename.startswith(f"{ticket.id}-{msg.id}"):
						files.append(discord.File(f"{filename}"))
				await ticket.send(f"**{msg.author.name}:** {msg.content}",files=files)
				for fil in files:
					os.remove(fil.filename)

			if yes == False:

				ticket = await guild.create_text_channel(f"{msg.author.name} ticket")

				await ticket.set_permissions(guild.default_role, view_channel=False)

				for each in config.role_ids:
					e = guild.get_role(each)
					if not e:
						e = await guild.fetch_roles(each)
					await ticket.set_permissions(e, view_channel=True)
				
				new_ticket = {
					"user_id" : msg.author.id,
					"ticket_id" : ticket.id
				}

				await msg.channel.send(f"Thank you for your message! Our mod team will reply to you here as soon as possible.")

				ticket_e = discord.Embed(
					title=f"{msg.author.name} needs help!!",
					description=f"{msg.content}\n\nTo close this ticket click on the button below or type `.close`",
					color=discord.Color.embed_background()
				)

				try:
					ticket_e.set_thumbnail(url=msg.author.avatar.url)
				except:
					ticket_e.set_thumbnail(url="https://i.ibb.co/9qsTvYG/f-removebg-preview.png")
				try:
					ticket_e.set_footer(icon_url=client.user.avatar.url,text="Fox mail support")
				except:
					pass
				await ticket.send("@here",embed=ticket_e,view=Panel_View(),files=msg.attachments)

				data.append(new_ticket)

				with open('tickets.json', 'w') as j:
					json.dump(data, j, indent=4)

	with open('tickets.json') as h:
		data = json.load(h)

		for x in data:

			if msg.channel.id == x['ticket_id']:
				
				ticket_user = client.get_user(x['user_id'])

				if not ticket_user:
					ticket_user = await client.fetch_user(x['user_id'])

				await ticket_user.send(f"{msg.content}")
				
	
	await client.process_commands(msg)
				
@client.command()
async def close(ctx):

	with open('tickets.json') as j:
		data = json.load(j)
		
		for x in data:
			
			if x['ticket_id'] == ctx.channel.id:

				confirm_view = discord.ui.View(timeout=10)

				ok = discord.ui.Button(
					label="Close",
					style=discord.ButtonStyle.danger
				)

				nope = discord.ui.Button(
					label="Cancel",
					style=discord.ButtonStyle.gray
				)

				async def n(i):
					await i.message.delete()
					return await i.response.defer()

				async def o(i):
					
					await i.response.edit_message(content=f"Ticket will be deleted in a few seconds",view=None)
					await asyncio.sleep(3)
					await ctx.channel.delete()

					opener = client.get_user(x['user_id'])
					if not opener:
						opener = await client.fetch_user(x['user_id'])
				
					await opener.send(f"`<< Thread Closed >>`\n>>> \nThank you for messaging Fox mail. Hope we answered your questions. If you have any more questions, feel free to DM us again!\n\nPlease note that your thread is now closed. If you message again, you will open another thread.")

					data.pop(data.index(x))

					with open('tickets.json', 'w') as j:
						json.dump(data, j, indent=4)

				ok.callback = o
				nope.callback = n

				confirm_view.add_item(ok)
				confirm_view.add_item(nope)

				async def timeout():
					for each in confirm_view.children:
						each.disabled = True
					await msg.edit(f"You didn't respond in time!",view=confirm_view)

				confirm_view.on_timeout = timeout

				msg = await ctx.send("Are you sure you want to close this ticket?",view=confirm_view)

client.run(config.token)