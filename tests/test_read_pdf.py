import q
import re
import traceback


if False:

    " JVM and tika "

    import tika
    tika.initVM()

    from tika import parser

    raw = parser.from_file('./data/20190417181644xqqs.pdf', xmlContent=True)
    print(raw["metadata"])
    print(raw['content'])
    q.d()
    open("aaaa.html", "w").write(raw['content'])

if True:
    """
        https://github.com/pikepdf/pikepdf/
        操作对象是 整个 pdf 的页面
        不支持中文，没找到 encoding 设置
        文档 JUST LIKE SHIT
    """

    import pikepdf

    # Elegant, Pythonic API
    # with pikepdf.open('./data/Paperid975.pdf') as pdf:
    # with pikepdf.open('./data/20190417181644xqqs.pdf') as pdf:
    with pikepdf.open("./data/20200324164938兴全趋势投资混合型证券投资基金（LOF）2019年度报告.pdf") as pdf:
        num_pages = len(pdf.pages)
        # del pdf.pages[:2]
        # del pdf.pages[5:]
        # del pdf.pages[-2]
        # del pdf.pages[-3]
        del pdf.pages[62:]
        del pdf.pages[:-3]
        pdf.save('output.2.pdf')
        q.d()

    exit()

if True:
    """
        https://github.com/pymupdf/PyMuPDF
            brew install mupdf-tools
            pip install /Users/yangyang/Downloads/PyMuPDF-1.18.4-cp37-cp37m-macosx_10_9_x86_64.whl
            export ARCHFLAGS='-arch x86_64'

        GO TO HELL !
    """

    import fitz
    import sys
    from operator import itemgetter

    # ==============================================================================
    # Main Program
    # ==============================================================================
    # ifile = "./data/20190417181644xqqs.pdf"
    ifile = "./data/20200324164938兴全趋势投资混合型证券投资基金（LOF）2019年度报告.pdf"
    ofile = ifile + ".txt"

    doc = fitz.open(ifile)
    pages = len(doc)

    fout = open(ofile, "wb")
    q.d()
    for page in doc:
        blocks = page.getTextBlocks()
        sb = sorted(blocks, key=itemgetter(1, 0))
        for b in sb:
            fout.write(b[4].encode("utf-8"))

    fout.close()

if False:
    """
        fuck that
    """
    import tabula

    path = './data/20190417181644xqqs.pdf'
    tabula.convert_into(path, "./data/20190417181644xqqs.pdf" + '.csv', pages='9')

if False:
    """
        https://github.com/jsvine/pdfplumber
        看上去不错
    """
    import pdfplumber

    with pdfplumber.open('./data/20190417181644xqqs.pdf') as pdf:
        first_page = pdf.pages[0]
        print(first_page.chars[0])

        for page in pdf.pages:
            for table in page.extract_tables():
                # print(table)
                for row in table:
                    print(row)
                print('---------- 分割线 ----------')

if False:
    """
        纯粹 python 实现
        https://github.com/pdfminer/pdfminer.six
        表格的支持不好，换行和空格不稳定
    """

    import pdfminer
    import pdfminer.high_level

    # text = pdfminer.high_level.extract_text('./data/Paperid975.pdf')
    text = pdfminer.high_level.extract_text('./data/20190417181644xqqs.pdf')
    # pdfminer.high_level.extract_text_to_fp

    print("text:", text)
    open("aaa.txt", "w").write(text)
    q.d()









