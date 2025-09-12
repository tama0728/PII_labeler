from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Document, PIITag

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
    return render(request, 'main/document_detail.html', {
        'document': document,
        'pii_tags': pii_tags
    })

@login_required
def document_create(request):
    """문서 생성"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if title and content:
            document = Document.objects.create(
                title=title,
                content=content,
                created_by=request.user
            )
            messages.success(request, '문서가 성공적으로 생성되었습니다.')
            return redirect('document_detail', pk=document.pk)
        else:
            messages.error(request, '제목과 내용을 모두 입력해주세요.')
    
    return render(request, 'main/document_create.html')

@login_required
@csrf_exempt
def add_pii_tag(request):
    """PII 태그 추가 (AJAX)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            document_id = data.get('document_id')
            pii_type = data.get('pii_type')
            start_pos = data.get('start_position')
            end_pos = data.get('end_position')
            tagged_text = data.get('tagged_text')
            confidence = data.get('confidence', 0.0)
            
            document = get_object_or_404(Document, pk=document_id)
            
            pii_tag = PIITag.objects.create(
                document=document,
                pii_type=pii_type,
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