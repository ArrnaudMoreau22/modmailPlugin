from discord.ext import commands
from discord.ext.commands import has_permissions
import discord

class AutoMove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialisation avec des valeurs par défaut ou récupérées depuis une source de configuration
        self.init_ticket_category_id = None
        self.waiting_user_message_category_id = None
        self.waiting_staff_message_category_id = None
        self.closed_ticket_category_id = None
        self.staff_role_id = None
        self.staff_replied = {}
        self.bot.loop.create_task(self.load_ids_from_database())

    async def load_ids_from_database(self):
      config = await self.bot.api.get_config()
      self.init_ticket_category_id = config.get('init_ticket_category_id')
      self.waiting_user_message_category_id = config.get('waiting_user_message_category_id')
      self.waiting_staff_message_category_id = config.get('waiting_staff_message_category_id')
      self.closed_ticket_category_id = config.get('closed_ticket_category_id')
      self.staff_role_id = config.get('staff_role_id')

    async def save_id_to_database(self, key, value):
        await self.bot.api.update_config({key: value})

    async def move_channel(self, channel, category_id):
        if category_id is None:
            print("ID de catégorie non défini, fonctionnalité ignorée.")
            return

        target_category = self.bot.get_channel(category_id)
        if target_category is None:
            print(f"Catégorie avec l'ID {category_id} non trouvée.")
            return

        if channel.category_id == category_id:
            print(f"Canal déjà dans la catégorie '{target_category.name}'.")
            return

        try:
            await channel.edit(category=target_category)
            print(f"Canal '{channel.name}' déplacé vers la catégorie '{target_category.name}'.")
        except Exception as e:
            print(f"Impossible de déplacer le canal : {e}")

    @commands.command(name='initinfo', help='Affiche les commandes pour initialiser les variables des IDs.')
    @has_permissions(administrator=True)
    async def display_init_info(self, ctx):
        embed = discord.Embed(title="Initialisation des IDs",
                              description="Utilisez les commandes suivantes pour configurer les IDs nécessaires.",
                              color=discord.Color.blue())
        embed.add_field(name="Set Init Ticket Category ID", value="`?setinitcategory [ID]`", inline=False)
        embed.add_field(name="Set Staff ID", value="`?setstaffid [ID]`", inline=False)
        embed.add_field(name="Set User Message Category ID", value="`?setwaitingusermessagecategory [ID]`", inline=False)
        embed.add_field(name="Set Staff Message Category ID", value="`?setwaitingstaffmessagecategory [ID]`", inline=False)
        embed.add_field(name="Set Closed Ticket Category ID", value="`?setclosedcategory [ID]`", inline=False)
        embed.set_footer(text="Remplacez [ID] par l'ID réel de chaque catégorie ou rôle.")

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        # Marque le ticket comme n'ayant pas encore reçu de réponse du staff
        self.staff_replied[thread.id] = False
        await self.move_channel(thread.channel, self.init_ticket_category_id)

    @commands.Cog.listener()
    async def on_thread_reply(self, thread, from_mod, message, anonymous, plain):
        # Détermine la catégorie cible basée sur si le staff a répondu ou non
        if from_mod:
            self.staff_replied[thread.id] = True  # Marque que le staff a répondu
            await self.move_channel(thread.channel, self.waiting_staff_message_category_id)
        elif self.staff_replied.get(thread.id):  # Si le staff a déjà répondu
            await self.move_channel(thread.channel, self.waiting_user_message_category_id)
        # Pas besoin de déplacer le ticket si l'utilisateur répond et le staff n'a pas encore répondu
    @commands.Cog.listener()
    async def on_thread_close(self, thread, closer, silent, delete_channel, message, scheduled):
        closed_category_id = 1225751725361860669  # Catégorie pour les tickets fermés
        await self.move_channel(thread.channel, closed_category_id)

    @commands.command(name='setinitcategory', help='Définit l\'ID de la catégorie pour les nouveaux tickets.')
    @has_permissions(administrator=True)
    async def set_init_category(self, ctx, category_id: int):
        self.init_ticket_category_id = category_id
        await self.save_id_to_database('init_ticket_category_id', category_id)
        await ctx.send(f'Catégorie pour les nouveaux tickets mise à jour avec succès : <#{category_id}>')

    @commands.command(name='setstaffid', help='Définit l\'ID du rôle staff.')
    @has_permissions(administrator=True)
    async def set_staff_id(self, ctx, staff_role_id: int):
        self.staff_role_id = staff_role_id
        await self.save_id_to_database('staff_role_id', staff_role_id)
        await ctx.send(f'Catégorie pour les nouveaux tickets mise à jour avec succès : <@&{staff_role_id}>')

    @commands.command(name='setwaitingusermessagecategory', help='Définit l\'ID de la catégorie pour les messages des utilisateurs.')
    @has_permissions(administrator=True)
    async def set__waiting_user_message_category(self, ctx, category_id: int):
        self.waiting_user_message_category_id = category_id
        await self.save_id_to_database('waiting_user_message_category_id', category_id)
        await ctx.send(f'Catégorie pour les messages des utilisateurs mise à jour avec succès : <#{category_id}>')

    @commands.command(name='setwaitingstaffmessagecategory', help='Définit l\'ID de la catégorie pour les messages du staff.')
    @has_permissions(administrator=True)
    async def set_waiting_staff_message_category(self, ctx, category_id: int):
        self.waiting_staff_message_category_id = category_id
        await self.save_id_to_database('waiting_staff_message_category_id', category_id)
        await ctx.send(f'Catégorie pour les messages du staff mise à jour avec succès : <#{category_id}>')

    @commands.command(name='setclosedcategory', help='Définit l\'ID de la catégorie pour les tickets fermés.')
    @has_permissions(administrator=True)
    async def set_closed_category(self, ctx, category_id: int):
        self.closed_ticket_category_id = category_id
        await self.save_id_to_database('closed_ticket_category_id', category_id)
        await ctx.send(f'Catégorie pour les tickets fermés mise à jour avec succès : <#{category_id}>')

async def setup(bot):
    await bot.add_cog(AutoMove(bot))
