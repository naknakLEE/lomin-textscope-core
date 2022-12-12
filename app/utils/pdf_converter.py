
import os
import subprocess
import shutil
from pathlib import Path
from app.utils.logging import logger

DEFAULT_LIBREOFFICECMD = "soffice"


class PDF2PDFAConvertor():

    writer_pdf_export_option = {
        "SelectPdfVersion": {
            "type": "long",
            "value": "1"
        },
        "UseLosslessCompression": {
            "type": "boolean",
            "value": "true"
        },
        "ReduceImageResolution": {
            "type": "boolean",
            "value": "false"
        },
        "Quality": {
            "type": "long",
            "value": "100"
        }
    }
    
    libreofficeExce = [
        "",
        "--headless",
        "--convert-to", "pdf:writer_pdf_Export:" + str(writer_pdf_export_option).replace("'", "\""),
        "--outdir", "",
        ""
    ]
    
    def __init__(self, libreoffice: str = DEFAULT_LIBREOFFICECMD):
        self.libreofficeExce[0] = libreoffice
    
    
    def convert(self, outputPath: str, inputPath: str, pdf_select_version: str):

        self.writer_pdf_export_option.get("SelectPdfVersion").update(
            value=pdf_select_version
        )
        self.libreofficeExce[5] = outputPath
        self.libreofficeExce[6] = inputPath
        
        with subprocess.Popen(self.libreofficeExce, stdout=subprocess.PIPE, stdin=subprocess.PIPE) as proc:
            try:
                logger.info("=======================> Start PDF Convert")
                logger.debug(f"=======================> outputPath Path: {outputPath}")
                logger.debug(f"=======================> inputPath Path: {inputPath}")
                # convert to PDF/A-1a
                out, err = proc.communicate(timeout=None)
                # logger.error(f"=======================> Subprocess Out: {out.decode()}")
                if(err is not None):
                    logger.error(f"=======================> Subprocess err: {err.decode()}")
                
                file_path = "/".join([outputPath, inputPath.split("/")[-1]])
                
                ds = list()
                with open(file_path, "rb") as p:
                    ds = p.readlines()
                
                # set metadata
                with open(file_path, "wb") as p:
                    for d in ds:
                        if   d[:10]  == b'<</Creator':        p.write(b'<</Creator<004C006F006D0069006E>\n')
                        elif d[:9]   == b'/Producer':         p.write(b'/Producer<005400650078007400730063006F00700065002000530074007500640069006F>\n')
                        elif d[3:17] == b'<pdf:Producer>':    p.write(b'   <pdf:Producer>Textscope Studio</pdf:Producer>\n')
                        elif d[3:20] == b'<xmp:CreatorTool>': p.write(b'   <xmp:CreatorTool>Textscope OCR Engine</xmp:CreatorTool>\n')
                        elif d[3:19] == b'<xmp:CreateDate>':  p.writelines([d, d.replace(b'CreateDate', b'ModifyDate')])
                        else: p.write(d)
                
                # shutil.chown(file_path, user=UID)
                # 빈파일(.end) 생성
                if(pdf_select_version == "1"):
                    end_file_path = file_path.replace(".pdf", ".end")
                    Path(end_file_path).touch()
                    # remove origin pdf
                    remove_path = os.path.dirname(inputPath)
                    shutil.rmtree(remove_path)                             
                    logger.info("=======================> Finish Convert PDF TO PDF/A")
                else:
                    logger.info("=======================>  Finish Convert PDF/A TO PDF")

            except subprocess.TimeoutExpired:
                proc.kill()
                outs, errs = proc.communicate()
                logger.info("=======================> proc timeout error: PDF to PDF/A converting")



if __name__ == "__main__":
    convertor = PDF2PDFAConvertor()
    convertor.convert("input/ocr.pdf")
