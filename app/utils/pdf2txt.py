import os
import glob
import copy
import argparse
import pdf2image
import numpy as np
import xml.etree.ElementTree as ET

from PIL import Image
from typing import Optional, Dict
from pathlib import PurePath, Path
from functools import lru_cache

from pdfminer.layout import LAParams
from pdfminer.cmapdb import CMapDB
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdocument import PDFDocument


class Pdf2Image:
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = PurePath("/workspace", "assets").as_posix()
        self.data_dir = data_dir
        self.load_lexicon()

    @lru_cache(maxsize=10)
    def save_xml(
        self,
        fname: str,
        xml_path: str,
        maxpages: int = 0,
        caching: bool = True,
        debug: int = 0,
    ) -> None:
        PDFDocument.debug = debug
        PDFParser.debug = debug
        CMapDB.debug = debug
        PDFPageInterpreter.debug = debug

        rsrcmgr = PDFResourceManager(caching=caching)
        outfp = open(xml_path, "w", encoding="utf-8")
        device = XMLConverter(
            rsrcmgr, outfp, laparams=LAParams(), imagewriter=None, stripcontrol=False
        )

        with open(fname, "rb") as fp:
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.get_pages(
                fp,
                set(),
                maxpages=maxpages,
                password=b"",
                caching=caching,
                check_extractable=True,
            ):
                page.rotate = (page.rotate + 0) % 360
                interpreter.process_page(page)
        device.close()
        outfp.close()

    def load_lexicon(self):
        self.lexicon_dict = dict()

        for idx, lexicon in enumerate(
            glob.glob(os.path.join(self.data_dir, "lexicons", "*.txt"))
        ):
            all_texts = list()
            with open(lexicon) as f:
                all_texts.extend(f.read().splitlines())
            self.lexicon_dict[idx] = all_texts

    def parse_coordinate(self, bbox):
        x0, y0, x1, y1 = bbox.split(",")
        x0 = round(float(x0))
        y0 = round(float(y0))
        x1 = round(float(x1))
        y1 = round(float(y1))

        return x0, y0, x1, y1

    def get_integrated_box(self, boxes):
        return [
            np.min(boxes[:, 0]),
            np.min(boxes[:, 1]),
            np.max(boxes[:, 2]),
            np.max(boxes[:, 3]),
        ]

    def parse_texts(self, texts, height):
        box_list = list()
        text_list = list()
        textline_box_list = list()
        textline_char_list = list()
        for text in texts:
            if len(text.attrib) == 0:
                textline_box_array = np.array(textline_box_list)
                box_list.append(self.get_integrated_box(textline_box_array))
                text_list.append("".join(textline_char_list).replace(" ", ""))
                textline_char_list = list()
                textline_box_list = list()
                continue
            char_attr = text.attrib

            bbox = char_attr["bbox"]
            x0, _y0, x1, _y1 = self.parse_coordinate(bbox)
            y1 = height - _y0
            y0 = height - _y1

            char = text.text
            textline_box_list.append([x0, y0, x1, y1])
            textline_char_list.append(char)
        return box_list, text_list

    def resize_bbox(self, bbox, w_ratio, h_ratio):
        resized = copy.deepcopy(bbox)
        resized[:, 0] = resized[:, 0] * w_ratio
        resized[:, 1] = resized[:, 1] * h_ratio
        resized[:, 2] = resized[:, 2] * w_ratio
        resized[:, 3] = resized[:, 3] * h_ratio
        return resized.tolist()

    def read_xml(self, xml_path, page_num, page_size):
        bboxes = list()
        texts = list()

        doc = ET.parse(xml_path)
        pages = doc.findall("page")
        page = pages[page_num]
        page_attr = page.attrib
        width = round(float(page_attr["bbox"].split(",")[2]))
        height = round(float(page_attr["bbox"].split(",")[3]))
        _text_boxes = page.findall("textbox")

        for _text_box in _text_boxes:
            _text_lines = _text_box.findall("textline")
            for _text_line in _text_lines:
                _texts = _text_line.findall("text")
                _bboxes, _texts = self.parse_texts(_texts, height)
                bboxes.extend(_bboxes)
                texts.extend(_texts)

        bboxes = np.array(bboxes)
        bboxes = self.resize_bbox(
            bboxes, w_ratio=page_size[0] / width, h_ratio=page_size[1] / height
        )
        return {"boxes": bboxes, "texts": texts}

    def __call__(self, pages, page_num, pdf_path, xml_path) -> Image:
        page = pages[page_num]
        text_info = self.read_xml(
            xml_path=xml_path, page_num=page_num, page_size=page.size
        )
        return text_info


def parse_pdf_text(text_info: Dict) -> Dict:
    return {
        "texts": text_info.get("texts"),
        "boxes": text_info.get("boxes"),
        "scores": [1.0] * len(text_info.get("texts", [])),
        "classes": ["text"] * len(text_info.get("texts", [])),
    }


@lru_cache(maxsize=10)
def convert_path_to_image(pdf_path):
    pages = pdf2image.convert_from_path(pdf_path=pdf_path)
    return pages


def get_pdf_text_info(inputs: Dict):
    xml_dir = "/tmp"
    xml_path = PurePath(xml_dir, Path(inputs.get("image_path", "")).stem + ".xml")
    pdf_path = inputs.get("image_path")
    page_num = inputs.get("page", 1) - 1
    pdf2txt.save_xml(fname=pdf_path, xml_path=xml_path, maxpages=inputs.get("page"))

    doc = ET.parse(xml_path)
    pages = doc.findall("page")
    page = pages[page_num]
    textbox = page.findall("textbox")

    parsed_text_info = {}
    image_size = (0, 0)
    if len(textbox) > 0:
        pages = convert_path_to_image(pdf_path=pdf_path)
        text_info = pdf2txt(
            pages=pages, page_num=page_num, pdf_path=pdf_path, xml_path=xml_path
        )
        image_size = pages[page_num].size
        parsed_text_info = parse_pdf_text(text_info)
    return parsed_text_info, image_size


pdf2txt = Pdf2Image("/workspace/assets")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf_path", required=True, type=str)
    parser.add_argument("--page_num", required=False, type=str, default=0)
    parser.add_argument("--xml_path", required=False, type=str, default="/tmp/temp.xml")
    parser.add_argument(
        "--save_path", required=False, type=str, default="/tmp/temp.jpg"
    )
    args = parser.parse_args()

    from pyinstrument import Profiler

    profiler = Profiler()
    profiler.start()

    pdf2txt.save_xml(fname=args.pdf_path, xml_path=args.xml_path)
    pages = pdf2image.convert_from_path(pdf_path=args.pdf_path)
    text_info = pdf2txt(
        pages=pages,
        page_num=args.page_num,
        pdf_path=args.pdf_path,
        xml_path=args.xml_path,
    )
    texts = text_info.get("texts")
    boxes = text_info.get("boxes")
    image_array = np.array(pages[args.page_num])

    profiler.stop()
    print(profiler.output_text(unicode=True, color=True, show_all=True))
