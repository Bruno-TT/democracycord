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
        self.message = await voteChannel.send("New vote initiated! This is a vote in favor of {0}. {1}% or more of the total votes need to be in favor for the initiative to be passed.".format(intitiative_message, 100*percentNeeded))


        #add the voting options to the message
        await self.message.add_reaction("✅")
        await self.message.add_reaction("❎")

        #add self to the votes list
        active_votes[self.message.id]=self

        #attributifying constructor parameters
        self.winCommand=winCommand
        self.percentNeeded=percentNeeded

        #wait for the votes
        await asyncio.sleep(duration)

        #finish the vote
        await self.remove()


    #called when the duration is over / the vote is ended 
    async def remove(self):

        #remove self from the votes dictionary
        del active_votes[self.message.id]
        
        #TODO: fix
        #for every reaction on the message
        for reaction in self.message.reactions:

            #if the bot applied that reaction
            if client.user in await reaction.users().flatten():
                
                #remove the reaction
                await reaction.message.remove_reaction(reaction.emoji, reaction.message.guild.me)

        #getting the channel to send the results message to
        voteChannel=self.message.channel

        #getting all the reactions to iterate through
        allReactions=self.message.reactions

        votesFor=0
        votesAgainst=0

        #TODO: FIX
        #iterating through all the reactions
        for reaction in allReactions:
            

            #if it's the pro votes
            if reaction.emoji=="✅":

                #register the number of votes for
                votesFor=reaction.count
            
            #if it's the con votes
            if reaction.emoji=="❎":

                #register the number of votes against
                votesAgainst=reaction.count

        #calculating the percentage of votes in favor of the initiative.
        actualPercent=votesFor/(votesFor + votesAgainst)

        #determining whether or not the initiative passed
        if actualPercent>=self.percentNeeded:
        
            #the initiative passed
            message="The vote at https://discordapp.com/channels/588794934526607370/588794994572263444/{0} has finished. The initiative has PASSED".format(self.message.id)

            #do the actual win command
            await winCommand()

        #otherwise
        else:

            #the initiative failed.
            message="The vote at https://discordapp.com/channels/588794934526607370/588794994572263444/{0} has finished. The initiative has FAILED".format(self.message.id)

        await voteChannel.send(content=message)

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
                duration=10
                initiative_message="muting {0}".format(message.mentions[0].nick)
                mutePerson=message.mentions[0]
                winCommand=(lambda x=mutePerson: x.edit(mute=True))
                v=vote()
                await v.new(duration, initiative_message, winCommand, 0.75)


    
    #help command implementation
    if message.content=="!voteHelp":

        #send help message
        await message.channel.send(content="possible syntaxes: '!newVote mute @Bruno'")
        

#when a reaction is added
@client.event
async def on_reaction_add(reaction, user):
    
    #if it wasn't me who reacted
    if (reaction.message.id in active_votes) and (user != client.user):

        #register the vote
        await user.send(content="Thanks for voting! Your vote has been registered.")
    
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

        #add a base vote
        await reaction.message.add_reaction(reaction.emoji)
    
    #if the vote was on a voting message
    if (reaction.message.id in active_votes) and (client.user != user):

        #notify the user
        await user.send(content="Your vote has been de-registered. Did you change your mind?")



#get the key from the gitignored file
keyFile="key.txt"
keyFileObject=open(keyFile)
API_KEY=keyFileObject.read()
keyFileObject.close()

#connect
client.run(API_KEY)
