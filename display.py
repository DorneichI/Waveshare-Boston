import sys
import os
from waveshare_epd import epd7in3e
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

def display(image_path):
	try:
		epd = epd7in3e.EPD()
		epd.init()
		epd.Clear()

		Himage = Image.open(image_path)
		Himage = Himage.resize((800, 480))
		epd.display(epd.getbuffer(Himage))
		time.sleep(3)

		epd.sleep()

	except IOError as e:
		print(e)
