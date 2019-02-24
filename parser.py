#from wand.color import Color
#from wand.image import Image
#from wand.drawing import Drawing
#from wand.compat import nested
#from wand.display import display
#
#with Drawing() as draw:
#    with Image(width=1000, height=100, background=Color('lightblue')) as img:
#        draw.font_family = 'Indie Flower'
#        draw.font_size = 40.0
#        draw.push()
#        draw.fill_color = Color('hsl(0%, 0%, 0%)')
#        draw.text(0,int(img.height/2 + 20), 'Hello, world!')
#        draw.pop()
#        draw(img)
#        img.save(filename='image.png')
#        display(img)

class Parser:
    def __init__(self):
        self.text_buffer = ""
        self.image_buffer = []

    def print_text(self, text):
        self.text_buffer += text

    def print_image(self, image):
        self.image_buffer.append(image)


class USTParser(Parser):
    def frame(meta, files):
        pass

    def exp(meta, frames):
        pass

    def batch(meta, exps):
        pass
