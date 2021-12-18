import requests
import common.utilities as ut

phunk_id = "1"

if len(phunk_id) == 1:
    phunk_id = "00" + phunk_id
elif len(phunk_id) == 2:
    phunk_id = "0" + phunk_id


link_nft_image = "https://phunks.s3.us-east-2.amazonaws.com/images/phunk"+phunk_id+".png"

response = requests.get(link_nft_image)
file = open("phunk"+phunk_id+".png", "wb")
file.write(response.content)
file.close()

ut.create_background("phunk"+phunk_id+".png", (96, 131, 151))
