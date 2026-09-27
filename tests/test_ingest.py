import zipfile

import pytest

from qanuntrace.ingest import Extractor


def test_csv_and_zip_provenance(tmp_path):
    csv=tmp_path/'sample.csv';csv.write_text('المادة,5\nحكم,٧',encoding='utf-8')
    rows=Extractor().read(csv)
    assert rows[0].locator=='row:1,column:1' and rows[0].status=='needs_review'
    z=tmp_path/'bundle.zip'
    with zipfile.ZipFile(z,'w') as out: out.write(csv,'sample.csv')
    assert Extractor().read(z)[0].source_name=='bundle.zip!sample.csv'

def test_zip_path_traversal_rejected(tmp_path):
    z=tmp_path/'bad.zip'
    with zipfile.ZipFile(z,'w') as out: out.writestr('../escape.txt','x')
    with pytest.raises(ValueError): Extractor().read(z)

def test_image_ocr_review_only():
    out=Extractor(ocr=lambda data,mime:'مادة ٥')._bytes('scan.png',b'fake-image',0)
    assert out[0].status=='needs_review' and out[0].locator=='image:ocr'
