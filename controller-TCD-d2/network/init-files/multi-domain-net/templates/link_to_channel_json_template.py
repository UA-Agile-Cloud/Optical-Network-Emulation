# Build json with network configuration for a LINEAR topology
# LINK TO CHANNEL
import json

# Structures as given in database
link_id_struct = "link_id"
channel_struct = "channel"

# Definition of base values
links_no = 8
channel_no = 90
link_to_channel = {"link_to_channel":[]}
for link_id in range(1, links_no+1):
    for channel in range(1,channel_no+1):
        new_link_to_channel= {link_id_struct: link_id,  channel_struct: channel}
        link_to_channel["link_to_channel"].append(new_link_to_channel)

# Create json file to be stored in the json folder
# and called by the network builder
with open('link_to_channel.json', 'w') as fp:
    json.dump(link_to_channel, fp)
    fp.close()
