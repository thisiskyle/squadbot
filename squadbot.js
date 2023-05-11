
const fs = require('node:fs');
const path = require('node:path');
const { Client, Collection, Events, GatewayIntentBits } = require('discord.js');
//const { token, quorumsFile, quorumChannelId } = require('./config_test.json');
const { token, quorumsFile, quorumChannelId } = require('./config.json');

// Create a new client instance
const client = new Client({ 
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers,
    ],
});

client.commands = new Collection();
client.buttons = new Collection();


client.quorumStatus = {
    open: "Open",
    closed: "Closed",
};

client.quorumResult = {
    pass: "Approved",
    fail: "Rejected",
    undecided: "Undecided",

};

client.quorumFieldIndex = {
    ayes: 0,
    nays: 1,
    result: 2,
    status: 3,
    id: 4,
};

// save the quorums to a file
client.saveQuorums = () => {
    console.log(`Save quorums to ${quorumsFile}`);
    fs.writeFile(quorumsFile, JSON.stringify(client.quorums), (err) => {
        if (err) {
            throw err;
            console.error(err);
        }
    });
};

// count up the votes and return a result
client.countVotes = (ayeCount, nayCount, interaction) => {

    console.log("Counting votes");

    // TODO/cleanup: this isnt a great way to filter the bots out of the count
    const memberCount = interaction.guild.memberCount - 1;
    const totalVotes = ayeCount + nayCount;
    const votesNeededToWin = Math.floor(memberCount / 2) + 1;

    console.log(`With ${memberCount} members, ${votesNeededToWin} votes are needed to win`);
    console.log(`Ayes: ${ayeCount} | Nays: ${nayCount}`);

    if (totalVotes == memberCount) {
        if (ayeCount > nayCount) {
            return interaction.client.quorumResult.pass;
        } else {
            return interaction.client.quorumResult.fail;
        }

    } else if (ayeCount >= votesNeededToWin) {
        return interaction.client.quorumResult.pass;

    } else if (nayCount >= votesNeededToWin) {
        return interaction.client.quorumResult.fail;
    }

    return interaction.client.quorumResult.undecided;
};


// checks if the quorum result is decisive and closes if it is
client.checkQuorumResult = (result, interaction) => {
    console.log("Checking result");
    console.log(`Result is ${result}`);
    if (result == interaction.client.quorumResult.undecided) {
        return;
    }

    interaction.client.closeQuorum(result, interaction.message.id);
};

// closes a quorum with the given result
client.closeQuorum = (result, qID) => {

    console.log("Closing Quorum");

    client.channels.fetch(quorumChannelId)
        .then((channel) => { 
            console.log("Quorum channel found"); 

            channel.messages.fetch(qID).then((message) => {
                console.log("Quorum message found"); 

                const embed = message.embeds[0];
                embed.fields[client.quorumFieldIndex.result].value = result;
                embed.fields[client.quorumFieldIndex.status].value = client.quorumStatus.closed;
                message.edit({ content: "", embeds: [embed], components: [] });
            });
        });
};


// load the quorums file
fs.readFile(path.join(__dirname, quorumsFile), (err, data) => {
    if (err) {
        console.error(`Failed to read ${quorumsFile}`);
        console.error(error);
        client.quorums = { list: [] };
    } else {
        client.quorums = JSON.parse(data);
    }
});


// reading command files
const commandsFoldersPath = path.join(__dirname, 'commands');
const commandFolders = fs.readdirSync(commandsFoldersPath);

for (const folder of commandFolders) {
	const commandsPath = path.join(commandsFoldersPath, folder);
	const commandFiles = fs.readdirSync(commandsPath).filter(file => file.endsWith('.js'));

    for (const file of commandFiles) {
        const filePath = path.join(commandsPath, file);
        const command = require(filePath);

        if ('data' in command && 'execute' in command) {
            console.log(`Reading command ${command.data.name}`);
            client.commands.set(command.data.name, command);
        } else {
            console.log(`[WARNING] The command at ${filePath} is missing a required "data" or "execute" property.`);
        }
    }
}

// reading button files
const buttonsPath = path.join(__dirname, 'buttons');
const buttonFiles = fs.readdirSync(buttonsPath).filter(file => file.endsWith('.js'));

for (const file of buttonFiles) {
    const filePath = path.join(buttonsPath, file);
    const button = require(filePath);

    // Set a new item in the Collection with the key as the button customId and the value as the exported module
    if ('data' in button && 'execute' in button) {
        console.log(`Reading button ${button.data.data.custom_id}`);
        client.buttons.set(button.data.data.custom_id, button);
    } else {
        console.log(`[WARNING] The button at ${filePath} is missing a required "data" or "execute" property.`);
    }
}



// reading event files
const eventsPath = path.join(__dirname, 'events');
const eventFiles = fs.readdirSync(eventsPath).filter(file => file.endsWith('.js'));

for (const file of eventFiles) {
	const filePath = path.join(eventsPath, file);
	const event = require(filePath);
	if (event.once) {
		client.once(event.name, (...args) => event.execute(...args));
	} else {
		client.on(event.name, (...args) => event.execute(...args));
	}
}


// Log in to Discord with your client's token
client.login(token);

