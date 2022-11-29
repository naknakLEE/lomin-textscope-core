import io

from typing import List, Union
from PIL import Image
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm

from app.utils.logging import logger


class Word():
    def __init__(self, text="", bbox=[0., 0., 0., 0.]):
        self.text = text
        self.bbox = bbox


class PdfParser():
    y_font_offset = 0.7 * mm
    scale_font_size = 1.0
    
    def getStringLength(self, text: str) -> float:
        l = 0.0
        
        for t in text:
            if t.isdigit(): l += 0.67
            elif t.isspace(): l += 0.54
            elif t.isascii(): l += 0.6
            else: l += 1
        
        return l
    
    def setFontOffset(self, offset: float) -> None:
        """
        Set Font Offset (Millimeter)
        """
        self.y_font_offset = offset * mm
    
    def setFontScale(self, scale: float) -> None:
        self.scale_font_size = scale
    
    def export_pdf(self, outdir: str, wordss: List[List[Word]], images: List[Union[bytes, Image.Image]], save: bool = True) -> bytes:
        pdf = Canvas(outdir, pdfVersion=(1, 4))
        pdf.setCreator("Lomin")
        pdf.setAuthor("Textscope OCR")
        pdf.setProducer("Textscope Studio")
        
        # A4 size
        size_pdf_width = 210 * mm
        size_pdf_height = 297 * mm
        
        logger.debug(f"=======================> Total Image Count:{len(images)}")
        for index, words, image in zip(range(len(images)), wordss, images):
            logger.debug(f"=======================> Generate PDF To ImageCount:{index+1}")
            # 1. set page size to A4
            pdf.setPageSize((size_pdf_width, size_pdf_height))
            
            # 2. read image from given
            pil_image = image if isinstance(image, Image.Image) else Image.open(io.BytesIO(image))
            
            # 3. get image width heigth for scaling bbox coordinate to pdf coordinate
            size_image_width = pil_image.width
            size_image_height = pil_image.height
            
            # 4. get width, height scale
            scale_image_to_pdf_width = size_pdf_width / size_image_width
            scale_image_to_pdf_height = size_pdf_height / size_image_height
            
            # 4. re-set scale and get width, height offset
            # (drawImage will preserveAspectRatio with centered at # 6)
            scale_image_to_pdf = 0.0
            x_pdf_offset = 0
            y_pdf_offset = 0
            if scale_image_to_pdf_width > scale_image_to_pdf_height:
                ## white blank on left, right
                scale_image_to_pdf = scale_image_to_pdf_height
                x_pdf_offset = (size_pdf_width - (size_image_width * scale_image_to_pdf)) / 2
                y_pdf_offset = self.y_font_offset
            else:
                ## white blank on top, bottom
                scale_image_to_pdf = scale_image_to_pdf_width
                y_pdf_offset = (size_pdf_height - (size_image_height * scale_image_to_pdf)) / 2 + self.y_font_offset
            
            # 5. add text layer
            words.sort(key=lambda x: (x.bbox[1], x.bbox[0]))
            for word in words:
                if len(word.text) == 0: continue
                
                # 5-1. get text length
                text_length = self.getStringLength(word.text)
                
                x_image_box = word.bbox[0]
                y_image_box = word.bbox[1]
                
                x_pdf_box_length = (word.bbox[2] - word.bbox[0]) * scale_image_to_pdf
                y_pdf_box_length = (word.bbox[3] - word.bbox[1]) * scale_image_to_pdf
                
                x_pdf_box = x_image_box * scale_image_to_pdf + x_pdf_offset
                y_pdf_box = (size_image_height - y_image_box) * scale_image_to_pdf - y_pdf_box_length + y_pdf_offset
                
                font_size = y_pdf_box_length * self.scale_font_size
                
                text = pdf.beginText()
                text.setFont('nanumG', font_size)
                text.setTextOrigin(x_pdf_box, y_pdf_box)
                
                # text box horizen scale will disable when convert to PDF/A-1a
                font_width = pdf.stringWidth(word.text, 'nanumG', font_size)
                text.setHorizScale(100.0 * x_pdf_box_length / font_width)
                
                text.textLine(word.text.encode('utf-8'))
                
                pdf.drawText(text)
            
            # 6. add image layer
            pdf_image = ImageReader(pil_image)
            pdf.drawImage(pdf_image, 0, 0, width=size_pdf_width, height=size_pdf_height, preserveAspectRatio=True, anchor="c")
            
            pdf.showPage()
        
        # 7. save to file or return bytes
        result = None
        if save is True: result = pdf.save()
        else: result = pdf.getpdfdata()
        
        return result


def load_hangle_font():
    pdfmetrics.registerFont(TTFont('nanumG', "/workspace/app/assets/NanumGothic.ttf"))

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
    
    parser = PdfParser()
    parser.export_pdf("./pdf2pdfa/input/ocr.pdf", wordss, images)
