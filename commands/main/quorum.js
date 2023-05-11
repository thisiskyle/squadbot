const { ActionRowBuilder, ButtonBuilder, ButtonStyle, SlashCommandBuilder, EmbedBuilder } = require('discord.js');
//const { quorumChannelId, quorumsFile } = require('../../config_test.json');
const { quorumChannelId, quorumsFile } = require('../../config.json');
const fs = require('node:fs');


module.exports = {

    data: new SlashCommandBuilder()
            .setName('quorum')
            .setDescription('Starts a quorum')
            .addStringOption(options =>
                options.setName('proposal')
                .setDescription('The proposal you are bringing to the quorum')
                .setRequired(true)
            ),


    async execute(interaction) {

        const qChannel = interaction.client.channels.cache.get(quorumChannelId);
        const interactionUser = await interaction.guild.members.fetch(interaction.user.id);
        const prop = interaction.options.getString('proposal');

        const buttonAye = interaction.client.buttons.get('aye');
        const buttonNay = interaction.client.buttons.get('nay');


        const row = new ActionRowBuilder()
            .addComponents(buttonAye.data, buttonNay.data);


        qChannel.send('---')
            .then(message => {

                const embed = new EmbedBuilder()
                    .setTitle("Official Quorum")
                    .setAuthor({ name: `${interactionUser.displayName}`, iconURL: `${interactionUser.displayAvatarURL()}`, url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' })
                    .setDescription(prop)
                    .addFields(
                        { name: "Ayes", value: "0", inline: true },
                        { name: "Nays", value: "0", inline: true },
                        { name: "Result", value: interaction.client.quorumResult.undecided, inline: false },
                        { name: "Status", value: interaction.client.quorumStatus.open, inline: false },
                        { name: "ID", value: `${message.id}`, inline: false },
                    );

                const embedreply = new EmbedBuilder()
                    .setTitle("New Quorum!")
                    .setDescription('A quorum has been called. Cast your vote!')
                    .setURL(message.url);

                interaction.client.quorums.list.push({ id: message.id, ayes: [], nays: [], });
                interaction.client.saveQuorums();

                interaction.reply({ embeds: [embedreply] });
                message.edit({ content: "", embeds: [embed], components: [row] })
            });
    },
};

