from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, FileResponse
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import transaction
from .models import Contract
from .services import ContractPDFGenerator, add_signature_to_pdf
from apps.books.models import LoanRecord
import os
from io import BytesIO
from PIL import Image as PILImage
import base64


def generate_contract_number():
    today = timezone.now().strftime('%Y%m%d')
    count = Contract.objects.filter(created_at__date=timezone.now().date()).count() + 1
    return f'HT{today}{count:04d}'


def create_contract_for_loan(loan):
    if hasattr(loan, 'contract'):
        return loan.contract

    contract_number = generate_contract_number()
    pdf_generator = ContractPDFGenerator()
    pdf_buffer = pdf_generator.generate_contract(loan, contract_number)

    contract = Contract.objects.create(
        loan=loan,
        contract_number=contract_number,
        status='pending'
    )

    filename = f'contract_{contract_number}.pdf'
    contract.unsigned_pdf.save(filename, ContentFile(pdf_buffer.getvalue()))
    contract.save()

    return contract


@login_required
def sign_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)

    if contract.loan.user != request.user:
        messages.error(request, '无权签署此合同')
        return redirect('my_loans')

    if contract.status == 'signed':
        messages.info(request, '此合同已签署')
        return redirect('my_loans')

    if request.method == 'POST':
        signature_data = request.POST.get('signature')
        if signature_data:
            try:
                format, imgstr = signature_data.split(';base64,')
                ext = format.split('/')[-1]
                signature_bytes = base64.b64decode(imgstr)

                sig_io = BytesIO(signature_bytes)
                img = PILImage.open(sig_io)
                img = img.convert('RGBA')
                background = PILImage.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img_io = BytesIO()
                background.save(img_io, format='PNG')
                img_io.seek(0)

                sig_filename = f'signature_{contract.contract_number}.png'
                contract.signature_image.save(sig_filename, ContentFile(img_io.getvalue()))

                signed_filename = f'signed_contract_{contract.contract_number}.pdf'
                signed_path = os.path.join(
                    os.path.dirname(contract.unsigned_pdf.path),
                    '..',
                    'signed',
                    signed_filename
                )
                os.makedirs(os.path.dirname(signed_path), exist_ok=True)

                add_signature_to_pdf(
                    contract.unsigned_pdf.path,
                    contract.signature_image.path,
                    signed_path
                )

                contract.signed_pdf.name = f'contracts/signed/{signed_filename}'
                contract.status = 'signed'
                contract.signed_at = timezone.now()
                contract.save()

                messages.success(request, '合同签署成功！')
                return redirect('my_loans')

            except Exception as e:
                messages.error(request, f'签署失败：{str(e)}')
                return redirect('sign_contract', pk=pk)

    return render(request, 'contracts/sign_contract.html', {'contract': contract})


@login_required
def download_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)

    if contract.loan.user != request.user and request.user.role != 'admin':
        messages.error(request, '无权下载此合同')
        return redirect('home')

    if contract.status != 'signed' or not contract.signed_pdf:
        messages.error(request, '合同尚未签署')
        return redirect('my_loans')

    return FileResponse(
        open(contract.signed_pdf.path, 'rb'),
        content_type='application/pdf',
        filename=f'借阅协议_{contract.contract_number}.pdf',
        as_attachment=True
    )


@login_required
def preview_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)

    if contract.loan.user != request.user and request.user.role != 'admin':
        return HttpResponse('无权预览此合同', status=403)

    pdf_file = contract.signed_pdf if contract.signed_pdf else contract.unsigned_pdf
    if not pdf_file:
        return HttpResponse('PDF文件不存在', status=404)

    return FileResponse(
        open(pdf_file.path, 'rb'),
        content_type='application/pdf',
        filename=f'借阅协议_{contract.contract_number}.pdf'
    )
