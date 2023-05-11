const { ButtonBuilder, ButtonStyle } = require('discord.js');


module.exports = {
    data: new ButtonBuilder()
            .setCustomId('nay')
            .setLabel('Nay')
            .setStyle(ButtonStyle.Danger),

    async execute(interaction) {
        console.log(`Nay vote from user ${interaction.member.id} on ${interaction.message.id}`);

        let ayeCount = 0;
        let nayCount = 0;

        for (let i = 0; i < interaction.client.quorums.list.length; i++) {

            const tempID = interaction.client.quorums.list[i].id;

            if (tempID == interaction.message.id) {

                if (interaction.client.quorums.list[i].nays.includes(interaction.member.id)) {
                    interaction.reply({ content: 'You already voted nay', ephemeral: true });
                    return;
                }

                console.log(`Entering vote from user ${interaction.member.id} to the quorum database`);
                interaction.client.quorums.list[i].nays.push(interaction.member.id);

                // handle when a user is changing vote
                if (interaction.client.quorums.list[i].ayes.includes(interaction.member.id)) {
                    interaction.reply({ content: 'Changing your vote to nay', ephemeral: true });
                    const index = interaction.client.quorums.list[i].ayes.indexOf(interaction.member.id);
                    interaction.client.quorums.list[i].ayes.splice(index, 1);
                } else {
                    interaction.reply({ content: 'Your vote has been received', ephemeral: true });
                }

                ayeCount = interaction.client.quorums.list[i].ayes.length;
                nayCount = interaction.client.quorums.list[i].nays.length;

                // update the embed
                const embed = interaction.message.embeds[0];
                embed.fields[interaction.client.quorumFieldIndex.ayes].value = ayeCount;
                embed.fields[interaction.client.quorumFieldIndex.nays].value = nayCount;
                interaction.message.edit({ embeds: [embed] });
                
                break;
            }
        }

        interaction.client.saveQuorums();
        const result = interaction.client.countVotes(ayeCount, nayCount, interaction);
        interaction.client.checkQuorumResult(result, interaction);
    },
};
