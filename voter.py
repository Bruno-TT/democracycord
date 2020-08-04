#importations
import discord, logging, asyncio, json, datetime
from bf_hl_gen import get_headline, is_number

vote_info_file_path = "vote_info.json"
with open(vote_info_file_path) as vote_info_file:
    vote_attributes=json.load(vote_info_file)

#setting up logging
logging.basicConfig(level=logging.INFO)

#creating the internal client object
client = discord.Client()

#votes dictionary
active_votes={}
members_with_active_votes=[]
alert_times=[3600,600,300,60,30,10,5,3,2,1]

#general class for a vote
class vote():
    
    #alternate constructor
    async def new(self, duration, intitiative_message, winCommand, percentNeeded, min_yes_votes, creator):
        #get the vote channel
        server=client.get_guild(588794934526607370)
        voteChannel=server.get_channel(588794994572263444)
        self.server_member=server.me

        self.min_yes_votes=min_yes_votes

        #send the voting message and store it in self.message
        message_base_text="New vote initiated! This is a vote in favor of {}\n{}% of the total people need to vote YES\nA minimum of {} people need to vote yes\nThe vote will last {} seconds.".format(intitiative_message, str(int(100*percentNeeded)), min_yes_votes, duration)
        self.message = await voteChannel.send(message_base_text)


        #add the voting options to the message
        await self.message.add_reaction("✅")
        await self.message.add_reaction("❎")

        self.message_link_str="https://discordapp.com/channels/588794934526607370/588794994572263444/{}".format(str(self.message.id))

        #add self to the votes list
        active_votes[self.message.id]=self

        #attributifying constructor parameters
        self.winCommand=winCommand
        self.percentNeeded=percentNeeded
        self.users_for, self.users_against=[], []
        self.user_reactions_for, self.user_reactions_against = {}, {}

        members_with_active_votes.append(creator)

        end_time=datetime.datetime.now()+datetime.timedelta(seconds=duration)

        countdown_messages=[]

        time_remaining=(end_time-datetime.datetime.now()).seconds
        prev_time_remaining=time_remaining
        while time_remaining>0:
            await asyncio.sleep(1)
            time_remaining=(end_time-datetime.datetime.now()).seconds
            for alert_time in alert_times:
                if time_remaining<alert_time and alert_time<prev_time_remaining:
                    await self.message.channel.send(content="The message at {} has {} seconds remaining".format(self.message_link_str, str(alert_time)), delete_after=1)
            prev_time_remaining=time_remaining

        #wait for the votes
        # await asyncio.sleep(duration)

        members_with_active_votes.remove(creator)

        for old_cd_message in countdown_messages:
            await old_cd_message.remove

        #finish the vote
        await self.remove()

    #called when the duration is over / the vote is ended 
    async def remove(self):

        #remove self from the votes dictionary
        del active_votes[self.message.id]


        #remove the bot's base votes
        await self.message.remove_reaction("✅", self.server_member)
        await self.message.remove_reaction("❎", self.server_member)
        
        # #for every reaction on the message
        # for reaction in self.message.reactions:

        #     #if the bot applied that reaction
        #     if client.user in await reaction.users().flatten():
                
        #         #remove the reaction
        #         await reaction.message.remove_reaction(reaction.emoji, reaction.message.guild.me)

        #getting the channel to send the results message to
        voteChannel=self.message.channel

        #make sure that the dicts and lists all match up (meaning nothing has fucced up)
        assert len(self.users_for)==len(self.user_reactions_for) and len(self.users_against)==len(self.user_reactions_against)

        votesFor=len(self.users_for)
        votesAgainst=len(self.users_against)

        #calculating the percentage of votes in favor of the initiative.
        if votesFor == 0 and votesAgainst == 0 : actualPercent=0
        else: actualPercent=votesFor/(votesFor + votesAgainst)

        #determining whether or not the initiative passed
        if actualPercent>=self.percentNeeded and votesFor>=self.min_yes_votes:
        
            #the initiative passed
            message="The vote at {} has finished. The initiative has PASSED".format(self.message_link_str)

            await voteChannel.send(content=message)

            #do the actual win command
            await self.winCommand()

        #otherwise
        else:

            #the initiative failed.
            message="The vote at {} has finished. The initiative has FAILED".format(self.message_link_str)

            await voteChannel.send(content=message)

    async def register_user_vote(self, user, reaction):

        #if the user somehow reacted with an emoji despite already having that vote registered
        if (reaction.emoji=="✅" and user in self.users_for) or (reaction.emoji=="❎" and user in self.users_against):
            
            # await user.send(content="how the fuck did you do that")
            pass
            return False

        #if the user previously voted AGAINST but has now voted FOR
        elif (reaction.emoji=="✅" and user in self.users_against):

            #remove them from the list of people that voted AGAINST
            self.users_against.remove(user)

            #remove their reaction from the message
            await self.user_reactions_against[user].remove(user)

            #remove their old reaction object from the dictionary
            del self.user_reactions_against[user]
            
            #add them to the list of users that voted FOR
            self.users_for.append(user)

            #add the reaction object to the FOR reaction objects dict
            self.user_reactions_for[user]=reaction
            
            #vote successfully registered
            return True 

        #if the user previously voted FOR but has now voted AGAINST
        elif (reaction.emoji=="❎" and user in self.users_for):
            
            #remove them from the list of people that voted FOR
            self.users_for.remove(user)

            #remove their reaction from the message
            await self.user_reactions_for[user].remove(user)

            #remove their old reaction object from the dictionary
            del self.user_reactions_for[user]

            #add them to the list of users that voted AGAINST
            self.users_against.append(user)

            #add the reaction object to the AGAINST reaction objects dict
            self.user_reactions_against[user]=reaction
        
            #successfully registered vote
            return True

        #if it was a clean FOR vote
        elif reaction.emoji=="✅":

            #add them to the list of users that voted FOR
            self.users_for.append(user)

            #add their reaction to the dictionary
            self.user_reactions_for[user]=reaction

            #successfully registered vote
            return True
        
        #if it was a clean AGAINST vote
        elif reaction.emoji=="❎":

            #add them to the list of users that voted AGAINST
            self.users_against.append(user)

            #add their reaction to the dictionary
            self.user_reactions_against[user]=reaction

            #successfully registered vote
            return True

        else:

            return False

    #called when a user removes their vote (by unreacting, not by adding another reaction)
    async def deregister_user_vote(self, user, reaction):

        #if the user removed their AGAINST reaction
        if reaction.emoji=="❎" and user in self.users_against:

            #remove them from the AGAINST list
            self.users_against.remove(user)

            #remove their reaction from the AGAINST dict
            del self.user_reactions_against[user]

            #success
            return True

        #if the user removed their FOR reaction
        elif reaction=="✅" and user in self.users_for:

            # remove them from the FOR list
            self.users_for.remove(user)

            #remove their reaction from the FOR list
            del self.user_reactions_for[user]

            #success
            return True

        #otherwise
        else:

            #oh god oh fuck we fucked up
            return False

#whenever a message comes in
@client.event
async def on_message(message):

    commands=message.content.split(" ")

    if commands[0]=="!buzzfeed" and is_number(commands[1]):
        n=min(25,int(commands[1]))
        await message.channel.send(content="\n".join([get_headline() for i in range(n)]))

    if message.content=="!ring" and "ringing" in message.channel.name:

        for _ in range(5):
            for member in [member for member in message.channel.members if member!=message.author]:
                # while 1:
                try:
                    await member.send(content="ring ring!")
                    # break
                except AttributeError:
                    pass
                    # continue

            await message.channel.send(content="@here")

    if message.content=="!ring toggle":

        author=message.author

        role=message.channel.guild.get_role(707265471086329886)

        member_has_role=role in author.roles

        if member_has_role:await author.remove_roles(role)
        else: await author.add_roles(role)
        

    #if the message was sent to the vote-creation channel
    if message.channel.id==707556037334401135:

        #if someone wants to make a new vote
        #if it's a !newVote commeand and the person doesn't have an active vote
        if commands[0]=="!vote" and message.author not in members_with_active_votes:
            
            #if it's a vote to mute
            if len(commands)==3 and commands[1]=="mute" and len(message.mentions)==1:

                #set up the vote
                win_proportion=vote_attributes["mute_proportion"]
                duration=vote_attributes["mute_duration"]
                min_yes_votes=vote_attributes["mute_min_yes_votes"]
                mutePerson=message.mentions[0]
                initiative_message="muting {0}".format(mutePerson.display_name)
                winCommand=(lambda x=mutePerson: x.edit(mute=True))
                creator=message.author
                v=vote()
                await v.new(duration, initiative_message, winCommand, win_proportion, min_yes_votes, creator)

            #if it's a vote to unmute
            if len(commands)==3 and commands[1]=="unmute" and len(message.mentions)==1:

                #and they've tagged someone

                #set up the vote
                win_proportion=vote_attributes["unmute_proportion"]
                duration=vote_attributes["unmute_duration"]
                min_yes_votes=vote_attributes["unmute_min_yes_votes"]
                unmutePerson=message.mentions[0]
                initiative_message="unmuting {0}".format(unmutePerson.display_name)
                winCommand=(lambda x=unmutePerson: x.edit(mute=False))
                creator=message.author
                v=vote()
                await v.new(duration, initiative_message, winCommand, win_proportion, min_yes_votes ,creator)

            #if it's a voice kick command
            if len(commands)==3 and commands[1]=="disconnect" and len(message.mentions)==1:

                #set up the vote
                win_proportion=vote_attributes["disconnect_proportion"]
                duration=vote_attributes["disconnect_duration"]
                min_yes_votes=vote_attributes["disconnect_min_yes_votes"]
                kickPerson=message.mentions[0]
                initiative_message="disconnecting {0}".format(kickPerson.display_name)
                winCommand=(lambda x=kickPerson: x.edit(voice_channel=None))
                creator=message.author
                v=vote()
                await v.new(duration, initiative_message, winCommand, win_proportion, min_yes_votes, creator)


            #if it's a vote to rename someone
            elif len(commands)>=4 and commands[1]=="rename" and len(message.mentions)==1:

                #reconstruct the name
                new_name=" ".join(commands[3:])

                if len(new_name)<=32:

                    #set up the vote

                    win_proportion=vote_attributes["rename_proportion"]
                    duration=vote_attributes["rename_duration"]
                    min_yes_votes=vote_attributes["rename_min_yes_votes"]

                    #the person to rename
                    rename_person=message.mentions[0]

                    #the initiative message that is sent in the message
                    initiative_message="renaming {} to {}".format(rename_person.display_name, new_name)
                    
                    #the actual command to rename them
                    async def winCommand(x=rename_person, new_name=new_name):
                        await x.edit(nick="Changing Nickname...")
                        await asyncio.sleep(2)
                        await x.edit(nick=new_name)


                    creator=message.author

                    #instantiate a vote object
                    v=vote()
                    await v.new(duration, initiative_message, winCommand, win_proportion, min_yes_votes, creator)
                
                else:

                    await message.channel.send(content="Error: discord only supports nicknames of length 32 or less.")

            elif len(commands)>=3 and commands[1]=="ban" and len(message.mentions)==1:

                #set up the vote

                win_proportion=vote_attributes["ban_proportion"]
                duration=vote_attributes["ban_duration"]
                min_yes_votes=vote_attributes["ban_min_yes_votes"]

                #the person to ban
                ban_person=message.mentions[0]

                #the initiative message that is sent in the message
                initiative_message="banning {}".format(ban_person.display_name)
                
                #the actual command to ban them
                winCommand=(lambda x=ban_person: x.ban(reason="DEMOCRACY", delete_message_days=0))

                creator=message.author

                #instantiate a vote object
                v=vote()
                await v.new(duration, initiative_message, winCommand, win_proportion, min_yes_votes, creator)

            elif len(commands)>=3 and commands[1]=="rename_server":

                #set up the vote

                win_proportion=vote_attributes["server_rename_proportion"]
                duration=vote_attributes["server_rename_duration"]
                min_yes_votes=vote_attributes["server_rename_min_yes_votes"]

                #the person to ban
                # ban_person=message.mentions[0]
                new_name=" ".join(commands[2:])

                #the initiative message that is sent in the message
                initiative_message="renaming the server to {}".format(new_name)
                
                #the actual command to ban them
                winCommand=(lambda new_name=new_name, server=message.channel.guild:server.edit(name=new_name))

                creator=message.author

                #instantiate a vote object
                v=vote()
                await v.new(duration, initiative_message, winCommand, win_proportion, min_yes_votes, creator)
            
            
            elif len(commands)==2 and commands[1]=="unban":

                channel=message.channel
                server=channel.guild
                banned_users=[ban_entry.user.name for ban_entry in await server.bans()]
                text=""
                for n,banned_user in enumerate(banned_users):
                    text+="{} : {}".format(str(n), banned_user)
                await channel.send(content=text)
            
                        
            elif len(commands)>=3 and commands[1]=="unban":

                unban_user_index=int(commands[2])

                channel=message.channel

                server=channel.guild

                banned_users=[ban_entry.user for ban_entry in await server.bans()]

                unban_user=banned_users[unban_user_index]



                #set up the vote

                win_proportion=vote_attributes["unban_proportion"]
                duration=vote_attributes["unban_duration"]
                min_yes_votes=vote_attributes["unban_min_yes_votes"]

                #the initiative message that is sent in the message
                initiative_message="unbanning {}".format(unban_user.name)
                
                #the actual command to ban them
                winCommand=(lambda sever=server, unban_person=unban_user:server.unban(unban_person))

                creator=message.author

                #instantiate a vote object
                v=vote()
                await v.new(duration, initiative_message, winCommand, win_proportion, min_yes_votes, creator)
                
            elif len(commands)>=2 and commands[1]=="bot_status":

                status=" ".join(commands[2:])
                

                initiative_message=f"Changing the bot's status to {status}"

                winCommand=lambda x=status:client.change_presence(activity=discord.Game(x))

                win_proportion=vote_attributes["bot_status_proportion"]
                duration=vote_attributes["bot_status_duration"]
                min_yes_votes=vote_attributes["bot_status_min_yes_votes"]
                
                creator=message.author
                v=vote()
                await v.new(duration, initiative_message, winCommand, win_proportion, min_yes_votes, creator)


        
        #help command implementation
        if message.content=="!voteHelp":

            #send help message
            await message.channel.send(content="[this is WIP sory] possible syntaxes: '!newVote mute @Bruno'")
            

#when a reaction is added
@client.event
async def on_reaction_add(reaction, user):
    
    #if it wasn't me who reacted
    if (reaction.message.id in active_votes) and (user != client.user):

        #get the vote object
        vote=active_votes[reaction.message.id]

        #call the register_user_vote command
        voting_success=await vote.register_user_vote(user, reaction)

        #register the vote
        if voting_success:
            pass
            # await user.send(content="Thanks for voting! Your vote has been registered.")
        else:
            pass
            # await user.send(content="You fucced it up boi. How did u do that.")
    
    #if there's now multiple reactions and the client has reacted to the message, remove the reaction
    if (reaction.count>1) and (client.user in await reaction.users().flatten()):

        #remove the base vote from the message
        await reaction.message.remove_reaction(reaction.emoji, reaction.message.guild.me)

    #if someone reacted with an illegal reaction to a voting message
    if (reaction.message.id in active_votes) and reaction.emoji not in ("✅","❎"):

        #remove the reaction
        await reaction.message.remove_reaction(reaction.emoji, user)
    
#when a reaction is removed
@client.event
async def on_reaction_remove(reaction, user):

    #if there's no longer reactions, it's a voting message, and the emoji is a voting emoji
    if (reaction.count<1) and (reaction.message.id in active_votes) and (reaction.emoji in ("✅","❎")):

        #add a base reaction
        await reaction.message.add_reaction(reaction.emoji)
    
    #if the vote was on a voting message and it wasn't me who removed the reaction and it was a vote removal
    if (reaction.message.id in active_votes) and (client.user != user) and (reaction.emoji in ("✅","❎")):

        vote=active_votes[reaction.message.id]

        removal_success=await vote.deregister_user_vote(user, reaction)
        
        if removal_success:

            #notify the user
            # await user.send(content="Your vote has been de-registered. Did you change your mind?")
            pass
        
        else:

            # await user.send(content="Error deregistering vote. Fuck you.")
            pass



#get the key from the gitignored file
keyFile="key.txt"
keyFileObject=open(keyFile)
API_KEY=keyFileObject.read()
keyFileObject.close()

#connect
client.run(API_KEY)
