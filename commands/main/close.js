const { SlashCommandBuilder } = require('discord.js');
//const { quorumChannelId, quorumsFile } = require('../../config_test.json');
const { quorumChannelId, quorumsFile } = require('../../config.json');
const fs = require('node:fs');


module.exports = {

    data: new SlashCommandBuilder()
            .setName('close')
            .setDescription('Manually close a quorum in its current state. Empty votes will be counted as Aye')
            .addStringOption(options =>
                options.setName('id')
                .setDescription('The quorum id to close')
                .setRequired(true)
            ),


    async execute(interaction) {

        const qID = interaction.options.getString('id');

        // get quorum from database
        for (let i = 0; i < interaction.client.quorums.list.length; i++) {
            if (interaction.client.quorums.list[i].id == qID) {

                const quorum = interaction.client.quorums.list[i];
                const memberCount = interaction.guild.members.cache.filter(m => !m.user.bot).size;
                let nayCount = quorum.nays.length;
                let ayeCount = quorum.ayes.length; + (memberCount - nayCount);
                // count the left over votes as aye
                ayeCount += memberCount - (nayCount + ayeCount);

                // call countVotes to get a result
                const result = interaction.client.countVotes(ayeCount, nayCount, interaction);
                interaction.client.closeQuorum(result, qID, interaction.client);
                interaction.reply({ content: `Quorum ${qID} closed`, ephemeral: true });
                return;
            }
        }

        interaction.reply({ content: `Quorum ${qID} not found in ${quorumsFile}`, ephemeral: true });
    }
}

