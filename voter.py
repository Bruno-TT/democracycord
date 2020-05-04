#importations
import discord, logging, asyncio

#setting up logging
logging.basicConfig(level=logging.INFO)

#creating the internal client object
client = discord.Client()

#votes dictionary
active_votes={}

#general class for a vote
class vote():
    
    #alternate constructor
    async def new(self, duration, intitiative_message, winCommand, percentNeeded):
        #get the vote channel
        voteChannel=client.get_guild(588794934526607370).get_channel(588794994572263444)

        #send the voting message and store it in self.message
        self.message = await voteChannel.send("New vote initiated! This is a vote in favor of {}. {}% or more of the total votes need to be in favor for the initiative to be passed. The vote will last {} seconds.".format(intitiative_message, 100*percentNeeded, duration))


        #add the voting options to the message
        await self.message.add_reaction("✅")
        await self.message.add_reaction("❎")

        #add self to the votes list
        active_votes[self.message.id]=self

        #attributifying constructor parameters
        self.winCommand=winCommand
        self.percentNeeded=percentNeeded
        self.users_for, self.users_against=[], []
        self.user_reactions_for, self.user_reactions_against = {}, {}

        #wait for the votes
        await asyncio.sleep(duration)

        #finish the vote
        await self.remove()

    #called when the duration is over / the vote is ended 
    async def remove(self):

        #remove self from the votes dictionary
        del active_votes[self.message.id]
        
        #for every reaction on the message
        for reaction in self.message.reactions:

            #if the bot applied that reaction
            if client.user in await reaction.users().flatten():
                
                #remove the reaction
                await reaction.message.remove_reaction(reaction.emoji, reaction.message.guild.me)

        #getting the channel to send the results message to
        voteChannel=self.message.channel

        #make sure that the
        assert len(self.users_for)==len(self.user_reactions_for) and len(self.users_against)==len(self.user_reactions_against)

        votesFor=len(self.users_for)
        votesAgainst=len(self.users_against)

        #calculating the percentage of votes in favor of the initiative.
        actualPercent=votesFor/(votesFor + votesAgainst)

        #determining whether or not the initiative passed
        if actualPercent>=self.percentNeeded:
        
            #the initiative passed
            message="The vote at https://discordapp.com/channels/588794934526607370/588794994572263444/{0} has finished. The initiative has PASSED".format(self.message.id)

            #do the actual win command
            await self.winCommand()

        #otherwise
        else:

            #the initiative failed.
            message="The vote at https://discordapp.com/channels/588794934526607370/588794994572263444/{0} has finished. The initiative has FAILED".format(self.message.id)

        await voteChannel.send(content=message)

    async def register_user_vote(self, user, reaction):

        #if the user somehow reacted with an emoji despite already having that vote registered
        if (reaction.emoji=="✅" and user in self.users_for) or (reaction.emoji=="❎" and user in self.users_against):
            
            await user.send(content="how the fuck did you do that")
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

    async def deregister_user_vote(self, user, reaction):
        if reaction.emoji=="❎" and user in self.users_against:
            self.users_against.remove(user)
            del self.user_reactions_against[user]
            return True
        elif reaction=="✅" and user in self.users_for:
            self.users_for.remove(user)
            del self.user_reactions_for[user]
            return True
        else:
            return False

#whenever a message comes in
@client.event
async def on_message(message):

    commands=message.content.split(" ")

    #if someone wants to make a new vote
    if commands[0]=="!newVote":
        
        #if it's a vote to mute
        if len(commands)==3 and commands[1]=="mute":

            #and they've tagged someone
            if len(message.mentions)==1:

                #set up the vote
                win_proportion=0.66
                duration=60
                mutePerson=message.mentions[0]
                initiative_message="muting {0}".format(mutePerson.display_name)
                winCommand=(lambda x=mutePerson: x.edit(mute=True))
                v=vote()
                await v.new(duration, initiative_message, winCommand, win_proportion)

                #if it's a vote to mute
        if len(commands)==3 and commands[1]=="unmute":

            #and they've tagged someone
            if len(message.mentions)==1:

                #set up the vote
                win_proportion=0.66
                duration=60
                unmutePerson=message.mentions[0]
                initiative_message="unmuting {0}".format(unmutePerson.display_name)
                winCommand=(lambda x=unmutePerson: x.edit(mute=False))
                v=vote()
                await v.new(duration, initiative_message, winCommand, win_proportion)

        if len(commands)==3 and commands[1]=="voice_kick":

            #and they've tagged someone
            if len(message.mentions)==1:

                #set up the vote
                win_proportion=0.75
                duration=60
                kickPerson=message.mentions[0]
                initiative_message="voice kicking {0}".format(kickPerson.display_name)
                winCommand=(lambda x=kickPerson: x.edit(voice_channel=None))
                v=vote()
                await v.new(duration, initiative_message, winCommand, win_proportion)


        #if it's a vote to rename someone
        elif len(commands)>=4 and commands[1]=="rename":

            #and they've tagged someone
            if len(message.mentions)==1:

                #reconstruct the name
                new_name=" ".join(commands[3:])

                #set up the vote

                #50% of people need to vote 
                win_proportion=0.5

                #lasts 30 seconds
                duration=30

                #the person to rename
                rename_person=message.mentions[0]

                #the initiative message that is sent in the message
                initiative_message="renaming {} to {}".format(rename_person.display_name, new_name)
                
                #the actual command to rename them
                winCommand=(lambda x=rename_person: x.edit(nick=new_name))

                #instantiate a vote object
                v=vote()
                await v.new(duration, initiative_message, winCommand, win_proportion)



    
    #help command implementation
    if message.content=="!voteHelp":

        #send help message
        await message.channel.send(content="possible syntaxes: '!newVote mute @Bruno'")
        

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
            await user.send(content="Thanks for voting! Your vote has been registered.")
        else:
            await user.send(content="You fucced it up boi. How did u do that.")
    
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
            await user.send(content="Your vote has been de-registered. Did you change your mind?")
        
        else:

            await user.send(content="Error deregistering vote. Fuck you.")



#get the key from the gitignored file
keyFile="key.txt"
keyFileObject=open(keyFile)
API_KEY=keyFileObject.read()
keyFileObject.close()

#connect
client.run(API_KEY)
