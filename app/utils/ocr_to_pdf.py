import io

from typing import List, Union
from PIL import Image
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader


class Word():
    def __init__(self, text="", bbox=[0., 0., 0., 0.]):
        self.text = text
        self.bbox = bbox


class PdfParser():
    def export_pdf(self, wordss: List[List[Word]], images: List[Union[bytes, Image.Image]], dpi=300) -> bytes:
        pdf = Canvas("ocr.pdf")
        pdf.setCreator("Textscope Studio")

        for words, image in zip(wordss, images):
            im = image if isinstance(image, Image.Image) else Image.open(io.BytesIO(image))
            im_width = im.size[0]
            im_height= im.size[1]

            width = 595
            height = 842
            dpi_w = width / im_width * dpi
            dpi_h = height / im_height * dpi
            
            im = ImageReader(im)
            pdf.drawImage(im, 0, 0, width=width, height=height)       
            
            for word in words:
                word_text_list = word.text
                for i, value in enumerate(word_text_list):
                    if not len(value): continue
                    box = word.bbox[i]
                    font_size = (box[3] - box[1]) * dpi_h / dpi

                    text = pdf.beginText()
                    text.setFont('nanumG', font_size)
                    text.setTextRenderMode(3)  # double invisible        
                    r_width = box[0] * dpi_w / dpi
                    
                    r_height_offset = 0
                    r_height = height + r_height_offset - box[3] * dpi_h / dpi
                    
                    if r_height > height: r_height = height - 10
                    if r_height < 0: r_height = 10  

                    text.setTextOrigin(r_width, r_height)
                    
                    box_width = (box[2] - box[0]) * dpi_w / dpi
                    font_width = pdf.stringWidth(value, 'nanumG', font_size)
                    
                    text.setHorizScale(100.0 * box_width / font_width)
                    
                    text.textLine(value)
                    
                    pdf.drawText(text)                                                              

            pdf.showPage()
        
        # return pdf.save()
        return pdf.getpdfdata()


def load_hangle_font():
    font_path = Path("/workspace/app/assets/NanumGothic.ttf")
    with font_path.open("rb") as f:
            ttf_bytes = f.read()
    ttf = io.BytesIO(ttf_bytes)
    
    setattr(ttf, "name", "(nanumG).ttf)")
    pdfmetrics.registerFont(TTFont('nanumG', ttf))
load_hangle_font()


if __name__ == "__main__":
    load_hangle_font()
    
    wordss = list()
    images = list()
    
    wordss.append(
        [
            Word("하나은행의", [554.5842895507812, 78.95536041259766, 662.9601440429688, 99.55071258544922]),
            Word("자산입니다.", [672.9632568359375, 79.35218048095703, 788.5719604492188, 100.09361267089844])
        ],
    )
    
    image = None
    with open("a.png", "rb") as file:
        image = file.read()
    
    images.append(
        image
    )
    
    PdfParser.export_pdf(wordss,images,200)
