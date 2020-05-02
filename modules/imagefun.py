import discord
from PIL import Image
import requests
from io import BytesIO


def is_valid_filetype(str):
	allowed_img_filetypes = ['.gif', '.jpg', 'jpeg', '.png', 'webp']
	for i in allowed_img_filetypes:
		if str.split("?")[0][-4:] == i:
			return True
	return False


async def read_image(message):
	args = message.clean_content.split(' ')
	if len(args) >= 2:
		if args[1][0:4] == "http" and is_valid_filetype(args[1]):
			try:
				response = requests.get(args[1])
			except requests.exceptions.ConnectionError:
				await message.channel.send("Your image is invalid!")
				return
			else:
				image = Image.open(BytesIO(response.content))
				return image
		else:
			if message.mentions:
				readURL = message.mentions[0].avatar_url
				response = requests.get(readURL)
				image = Image.open(BytesIO(response.content))
				return image
			else:
				await message.channel.send("Your URL is not properly formatted you dummy!")
				return
	else:
		if message.attachments:
			if is_valid_filetype(message.attachments[0].url):
				readURL = message.attachments[0].url
				response = requests.get(readURL)
				image = Image.open(BytesIO(response.content))
				return image
			else:
				await message.channel.send("Your attached image is not a valid file type! (png, jpg, gif)")
				return
		else:
			m = await message.channel.history(limit=20).flatten()
			for i in range(20):
				if m[i].attachments:
					if is_valid_filetype(m[i].attachments[0].url):
						readURL = m[i].attachments[0].url
						response = requests.get(readURL)
						image = Image.open(BytesIO(response.content))
						return image
				if m[i].embeds:
					if m[i].embeds[0].image:
						if is_valid_filetype(m[i].embeds[0].image.url):
							readURL = m[i].embeds[0].image.url
							response = requests.get(readURL)
							image = Image.open(BytesIO(response.content))
							return image

			await message.channel.send("You need to add an image to your message!")
			return


async def holding_imagemaker(message):
	# holding_input_image = "https://i.imgur.com/uYkGfzu.png"
	holding_base_image = "https://i.imgur.com/0mr6e6p.jpg"
	holding_mask = "https://i.imgur.com/DimDfNH.png"

	inner = await read_image(message)
	if inner is None:
		return

	response = requests.get(holding_base_image)
	im = Image.open(BytesIO(response.content))

	response = requests.get(holding_mask)
	im_mask = Image.open(BytesIO(response.content))


	# ratio of width/height, but multiplied by 1000 and floored
	# if its over 1000, the width is larger than the height
	# used for the scaling, honestly could probably be removed
	xyratio = (inner.size[0] / inner.size[1]) * 1000 // 1

	# the resized dimension of the inner image in pixels
	IM_SIZE = 260
	# creates the square image to be placed inside by resizing, cropping, and rotating the input image
	inside_img = inner.copy()
	if xyratio > 1000:
		inside_img = inside_img.resize((int(xyratio * IM_SIZE / 1000) // 1, IM_SIZE), Image.BILINEAR)
	else:
		inside_img = inside_img.resize((IM_SIZE, int(IM_SIZE * 1000 / xyratio) // 1), Image.BILINEAR)
	inside_img = inside_img.crop(((inside_img.size[0] - IM_SIZE) / 2, (inside_img.size[1] - IM_SIZE) / 2,
								  (inside_img.size[0] + IM_SIZE) / 2, (inside_img.size[1] + IM_SIZE) / 2))
	inside_img_prerotate = inside_img.copy()
	inside_img = inside_img.rotate(17, Image.BILINEAR, expand=True)
	inside_img.putalpha(Image.new("L", inside_img_prerotate.size, "white").rotate(17, expand=True))

	# the pixel position of the placed image on the background image
	P1, P2 = 123, 232

	# creates the image the same size as the template and places the inside image in the correct location
	bg = Image.new("RGBA", im.size, "rgb(0,0,0)")
	bg.paste(inside_img, box=(P1, P2, inside_img.size[0] + P1, inside_img.size[1] + P2),
			 mask=Image.new("L", inside_img_prerotate.size, "white").rotate(17, expand=True))

	# the final version of the image
	im_final = bg.copy()
	im_final.paste(im, mask=im_mask)
	im_final.save("holding.png")

	await message.channel.send(file=discord.File("holding.png"))
