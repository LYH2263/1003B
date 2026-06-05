import os
from io import BytesIO
from datetime import datetime
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


class ContractPDFGenerator:
    def __init__(self):
        self.register_fonts()
        self.styles = self.get_styles()

    def register_fonts(self):
        font_paths = [
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/msyh.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        ]

        font_registered = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    font_registered = True
                    break
                except:
                    continue

        if not font_registered:
            pdfmetrics.registerFont(TTFont('ChineseFont', 'Helvetica'))

    def get_styles(self):
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='ContractTitle',
            fontName='ChineseFont',
            fontSize=18,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.black,
        ))

        styles.add(ParagraphStyle(
            name='ContractSubtitle',
            fontName='ChineseFont',
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=15,
            textColor=colors.grey,
        ))

        styles.add(ParagraphStyle(
            name='ContractNormal',
            fontName='ChineseFont',
            fontSize=11,
            leading=18,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            firstLineIndent=22,
        ))

        styles.add(ParagraphStyle(
            name='ContractSection',
            fontName='ChineseFont',
            fontSize=12,
            leading=20,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.black,
        ))

        styles.add(ParagraphStyle(
            name='ContractTableHeader',
            fontName='ChineseFont',
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
        ))

        styles.add(ParagraphStyle(
            name='ContractTableCell',
            fontName='ChineseFont',
            fontSize=10,
            leading=14,
        ))

        styles.add(ParagraphStyle(
            name='ContractSignature',
            fontName='ChineseFont',
            fontSize=11,
            leading=16,
            spaceBefore=30,
        ))

        return styles

    def generate_contract(self, loan, contract_number):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2.5 * cm,
            leftMargin=2.5 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2.5 * cm,
        )

        story = []
        story.append(Paragraph('图书借阅协议', self.styles['ContractTitle']))
        story.append(Paragraph(f'合同编号：{contract_number}', self.styles['ContractSubtitle']))
        story.append(Spacer(1, 0.5 * cm))

        story.append(Paragraph(
            '甲方（出借方）：龙猫图书馆',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            f'乙方（借阅方）：{loan.user.get_full_name() or loan.user.username}',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            f'乙方身份证/学号：{loan.user.username}',
            self.styles['ContractNormal']
        ))
        story.append(Spacer(1, 0.5 * cm))

        story.append(Paragraph(
            '根据《中华人民共和国合同法》及相关法律法规，甲乙双方在平等、自愿、公平的基础上，就图书借阅事宜达成如下协议：',
            self.styles['ContractNormal']
        ))
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph('第一条 借阅图书信息', self.styles['ContractSection']))

        book_data = [
            [Paragraph('项目', self.styles['ContractTableHeader']),
             Paragraph('内容', self.styles['ContractTableHeader'])],
            [Paragraph('图书名称', self.styles['ContractTableCell']),
             Paragraph(loan.book.title, self.styles['ContractTableCell'])],
            [Paragraph('作者', self.styles['ContractTableCell']),
             Paragraph(loan.book.author, self.styles['ContractTableCell'])],
            [Paragraph('ISBN', self.styles['ContractTableCell']),
             Paragraph(loan.book.isbn, self.styles['ContractTableCell'])],
            [Paragraph('分类', self.styles['ContractTableCell']),
             Paragraph(loan.book.category.name if loan.book.category else '未分类', self.styles['ContractTableCell'])],
        ]

        book_table = Table(book_data, colWidths=[4 * cm, 11 * cm])
        book_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(book_table)
        story.append(Spacer(1, 0.5 * cm))

        story.append(Paragraph('第二条 借阅期限', self.styles['ContractSection']))
        story.append(Paragraph(
            f'1. 借阅起始日期：{loan.borrow_date.strftime("%Y年%m月%d日")}',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            f'2. 应还日期：{loan.due_date.strftime("%Y年%m月%d日")}',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '3. 乙方如需续借，应在到期前通过系统申请，经甲方批准后方可续借。',
            self.styles['ContractNormal']
        ))
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph('第三条 双方权利与义务', self.styles['ContractSection']))
        story.append(Paragraph(
            '（一）甲方权利与义务：',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '1. 甲方有权按照本协议约定收回图书；',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '2. 甲方应保证所出借图书内容完整、无缺页；',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '3. 甲方应按照规定对逾期归还行为进行处理。',
            self.styles['ContractNormal']
        ))

        story.append(Paragraph(
            '（二）乙方权利与义务：',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '1. 乙方有权在借阅期限内正常使用所借图书；',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '2. 乙方应爱护图书，不得涂改、勾画、裁剪、撕毁；',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '3. 乙方应按期归还图书，逾期应承担相应责任。',
            self.styles['ContractNormal']
        ))
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph('第四条 违约条款', self.styles['ContractSection']))
        story.append(Paragraph(
            '1. 乙方逾期未还图书，每逾期一日，应支付违约金人民币 0.5 元；',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '2. 乙方遗失或严重损坏图书，应按图书原价的 2-3 倍赔偿；',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '3. 乙方有下列情形之一的，甲方有权暂停其借阅资格：',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '   （1）逾期超过 30 天未归还图书；',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '   （2）一年内累计遗失、损坏图书 3 册以上；',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '   （3）其他严重违反图书馆规章制度的行为。',
            self.styles['ContractNormal']
        ))
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph('第五条 其他约定', self.styles['ContractSection']))
        story.append(Paragraph(
            '1. 本协议自双方签字（或电子签章）之日起生效；',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '2. 本协议一式两份，甲乙双方各执一份，具有同等法律效力；',
            self.styles['ContractNormal']
        ))
        story.append(Paragraph(
            '3. 本协议未尽事宜，双方可另行协商补充。',
            self.styles['ContractNormal']
        ))
        story.append(Spacer(1, 1 * cm))

        signature_data = [
            [Paragraph('甲方（出借方）签章：', self.styles['ContractSignature']),
             Paragraph('乙方（借阅方）签章：', self.styles['ContractSignature'])],
            [Spacer(1, 1.5 * cm), Spacer(1, 1.5 * cm)],
            [Paragraph('龙猫图书馆（公章）', self.styles['ContractTableCell']),
             Paragraph('', self.styles['ContractTableCell'])],
            [Paragraph(f'日期：{datetime.now().strftime("%Y年%m月%d日")}', self.styles['ContractTableCell']),
             Paragraph(f'日期：_______________', self.styles['ContractTableCell'])],
        ]

        signature_table = Table(signature_data, colWidths=[7.5 * cm, 7.5 * cm])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(signature_table)

        doc.build(story)
        buffer.seek(0)
        return buffer


def add_signature_to_pdf(unsigned_pdf_path, signature_image_path, output_path):
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.pdfbase import pdfmetrics

    reader = PdfReader(unsigned_pdf_path)
    writer = PdfWriter()

    packet = BytesIO()
    can = pdf_canvas.Canvas(packet, pagesize=A4)

    sig_img_width = 8 * cm
    sig_img_height = 3 * cm

    x_pos = 11 * cm
    y_pos = 6 * cm

    try:
        can.drawImage(
            signature_image_path,
            x_pos,
            y_pos,
            width=sig_img_width,
            height=sig_img_height,
            mask='auto'
        )
    except:
        pass

    try:
        if 'ChineseFont' in pdfmetrics.getRegisteredFontNames():
            can.setFont('ChineseFont', 10)
        else:
            can.setFont('Helvetica', 10)
    except:
        can.setFont('Helvetica', 10)

    today = datetime.now().strftime("%Y-%m-%d")
    can.drawString(x_pos, y_pos - 0.5 * cm, f"Signed: {today}")

    can.save()
    packet.seek(0)

    new_pdf = PdfReader(packet)
    for i, page in enumerate(reader.pages):
        if i == len(reader.pages) - 1:
            page.merge_page(new_pdf.pages[0])
        writer.add_page(page)

    with open(output_path, 'wb') as f:
        writer.write(f)

    return output_path
