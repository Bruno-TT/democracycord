#importations
import discord, logging

#setting up logging
logging.basicConfig(level=logging.INFO)

#creating the internal client object
client = discord.Client()

#votes dictionary
active_votes={}

#general class for a vote
class vote():
    
    #alternate constructor
    async def new(self, duration):
        #get the vote channel
        voteChannel=client.get_guild(588794934526607370).get_channel(588794994572263444)

        #send the voting message and store it in self.message
        self.message = await voteChannel.send("new vote initiated")

        #add the voting options to the message
        await self.message.add_reaction("✅")
        await self.message.add_reaction("❎")

        #add self to the votes list
        active_votes[self.message.id]=self

    #called when the duration is over / the vote is ended 
    async def remove(self):

        #remove self from the votes dictionary
        del active_votes[self]

        #TODO: process the message's reactions
        print(self.message.reactions)

    #called whenever someone votes.
    async def registerVote(self, voter):

        #DEBUG
        print("vote registered")

        #alert them their vote has been registered.
        await voter.send(content="thanks for voting! Your vote has been registered.")

        #DEBUG: print the current reactions
        print(self.message.reactions)

#whenever a message comes in
@client.event
async def on_message(message):

    #if someone wants to make a new vote
    if message.content=="!newVote":
        
        #TODO: register the vote
        v=vote()
        await v.new(100)

#when a reaction is added
@client.event
async def on_reaction_add(reaction, user):

    #DEBUG
    print("someone just reacted!")
    
    #if it wasn't me who reacted
    #TODO: fix
    if (not reaction.me) and (reaction.message.id in active_votes):

        #DEBUG
        print("someone just voted")

        #register the vote
        await active_votes[reaction.message.id].registerVote(user)

#get the key from the gitignored file
keyFile="key.txt"
keyFileObject=open(keyFile)
API_KEY=keyFileObject.read()
keyFileObject.close()

#connect
client.run(API_KEY)
