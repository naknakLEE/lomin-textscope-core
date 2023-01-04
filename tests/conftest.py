
import pytest

def pytest_addoption(parser):
    parser.addoption("--document_dir", action="store", default=None, help="OCR Document Directory")
    parser.addoption("--pdf_file_name", action="store", default=None, help="Created PDF File Name")
    parser.addoption("--pdf_dir", action="store", default=None, help="Request PUT PDF Directory")

@pytest.fixture(scope="session")
def post_ocr_args(request):
    args = {}
    args['document_dir']  = request.config.getoption("--document_dir")    
    args['pdf_file_name'] = request.config.getoption("--pdf_file_name")    
    return args

@pytest.fixture(scope="session")
def put_pdf_arg(request):    
    arg = {
        "pdf_dir": request.config.getoption("--pdf_dir")   
    }

    return arg