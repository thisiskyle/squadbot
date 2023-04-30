


# get the total members of a guild, excluding bots
def get_member_count(guild):
    return len([m for m in guild.members if not m.bot])



# returns the number of members in guild with a matching role name
def get_role_count(guild, role_name):
    count = 0
    for member in guild.members:
        for role in member.roles:
            if role.name == role_name:
                count += 1
    return count
