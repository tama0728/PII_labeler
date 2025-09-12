from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import os
from .models import Document, PIITag, PIICategory

def index(request):
    """메인 페이지"""
    try:
        documents = Document.objects.all()[:10]  # 최근 10개 문서
    except Exception as e:
        # 데이터베이스 연결 오류시 빈 리스트 반환
        documents = []
    return render(request, 'main/index.html', {'documents': documents})

@login_required
def document_list(request):
    """문서 목록"""
    documents = Document.objects.filter(created_by=request.user)
    return render(request, 'main/document_list.html', {'documents': documents})

@login_required
def document_detail(request, pk):
    """문서 상세"""
    document = get_object_or_404(Document, pk=pk)
    pii_tags = document.pii_tags.all()
    pii_categories = PIICategory.objects.all()
    return render(request, 'main/document_detail.html', {
        'document': document,
        'pii_tags': pii_tags,
        'pii_categories': pii_categories
    })

@login_required
def document_create(request):
    """JSONL 파일 업로드로 문서 생성"""
    if request.method == 'POST':
        uploaded_file = request.FILES.get('jsonl_file')
        
        if uploaded_file and uploaded_file.name.endswith('.jsonl'):
            try:
                # 파일 내용 읽기
                content = uploaded_file.read().decode('utf-8')
                lines = content.strip().split('\n')
                
                created_count = 0
                for line in lines:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            document = Document.objects.create(
                                data_id=data.get('data_id', ''),
                                number_of_subjects=data.get('number_of_subjects', ''),
                                dialog_type=data.get('dialog_type', ''),
                                turn_cnt=data.get('turn_cnt', ''),
                                doc_id=data.get('doc_id', ''),
                                text=data.get('text', ''),
                                created_by=request.user
                            )
                            created_count += 1
                        except json.JSONDecodeError:
                            continue
                
                messages.success(request, f'{created_count}개의 문서가 성공적으로 업로드되었습니다.')
                return redirect('document_list')
                
            except Exception as e:
                messages.error(request, f'파일 처리 중 오류가 발생했습니다: {str(e)}')
        else:
            messages.error(request, 'JSONL 파일을 선택해주세요.')
    
    return render(request, 'main/document_create.html')

@login_required
@csrf_exempt
def add_pii_tag(request):
    """PII 태그 추가 (AJAX)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            document_id = data.get('document_id')
            pii_category_value = data.get('pii_category')
            start_pos = data.get('start_position')
            end_pos = data.get('end_position')
            tagged_text = data.get('tagged_text')
            confidence = data.get('confidence', 0.0)
            
            document = get_object_or_404(Document, pk=document_id)
            pii_category = get_object_or_404(PIICategory, value=pii_category_value)
            
            pii_tag = PIITag.objects.create(
                document=document,
                pii_category=pii_category,
                start_position=start_pos,
                end_position=end_pos,
                tagged_text=tagged_text,
                confidence=confidence,
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'tag_id': pii_tag.id,
                'message': 'PII 태그가 추가되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

def register(request):
    """회원가입"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, f'환영합니다, {username}님!')
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})