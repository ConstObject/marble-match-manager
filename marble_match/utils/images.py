from PIL import Image


def get_concat_h(im1, im2):
    dst = Image.new('RGB', (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst


def get_concat_v(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst


def add_overlay(anything):
    vs_image = Image.open('overlay.png')
    anything.paste(vs_image, (0, 0), vs_image)
    return anything



def create_image(file1: str, file2: str) -> str:
    image1 = Image.open(f'{file1}.png')
    image2 = Image.open(f'{file2}.png')
    add_overlay(get_concat_h(image1, image2)).save(f'{file1}x{file2}.png')
    return f'{file1}x{file2}.png'
