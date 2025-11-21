"""Display helper for the Waveshare 7.3" e-paper panel."""

from waveshare_epd import epd7in3e
from PIL import Image

def display(image_path):
	"""Display the image at ``image_path`` on the e-paper panel."""
	try:
		epd = epd7in3e.EPD()
		epd.init()

		Himage = Image.open(image_path)
		Himage = Himage.resize((800, 480))
		epd.display(epd.getbuffer(Himage))

		epd.sleep()

	except IOError as e:
		print(e)
