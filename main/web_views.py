"""
웹 페이지 뷰들 (템플릿 렌더링)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import HttpResponse

from .models import Document, PIICategory
from .forms import JSONLUploadForm, DocumentSelectionForm
from .services import DocumentService


def index(request):
    """메인 페이지"""
    try:
        documents = Document.objects.all()[:10]  # 최근 10개 문서
    except Exception:
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
    
    # 이전/다음 문서 찾기
    prev_document, next_document = DocumentService.get_navigation_documents(pk)
    
    return render(request, 'main/document_detail.html', {
        'document': document,
        'pii_tags': pii_tags,
        'pii_categories': pii_categories,
        'prev_document': prev_document,
        'next_document': next_document
    })


@login_required
def document_create(request):
    """JSONL 파일 업로드로 문서 생성"""
    if request.method == 'POST':
        form = JSONLUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['jsonl_file']
            
            try:
                # 파일 내용 읽기
                content = uploaded_file.read().decode('utf-8')
                
                # 서비스 레이어를 통한 처리
                created_count, total_tags = DocumentService.process_jsonl_upload(
                    content, request.user
                )
                
                messages.success(
                    request, 
                    f'{created_count}개의 문서와 {total_tags}개의 PII 태그가 성공적으로 업로드되었습니다.'
                )
                return redirect('document_list')
                
            except Exception as e:
                messages.error(request, f'파일 처리 중 오류가 발생했습니다: {str(e)}')
        else:
            messages.error(request, '올바른 JSONL 파일을 선택해주세요.')
    else:
        form = JSONLUploadForm()
    
    return render(request, 'main/document_create.html', {'form': form})


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


@login_required
def download_jsonl(request):
    """선택된 문서들을 JSONL 형식으로 다운로드"""
    if request.method == 'POST':
        try:
            # 두 가지 방식으로 문서 ID 받기
            selected_doc_ids = request.POST.getlist('selected_documents')
            bulk_doc_ids = request.POST.getlist('document_ids')
            
            document_ids = selected_doc_ids if selected_doc_ids else bulk_doc_ids
            
            if not document_ids:
                messages.error(request, '다운로드할 문서를 선택해주세요.')
                return redirect('document_list')
            
            # 선택된 문서들 조회
            documents = Document.objects.filter(
                id__in=document_ids,
                created_by=request.user
            )
            
            if not documents.exists():
                messages.error(request, '선택된 문서를 찾을 수 없습니다.')
                return redirect('document_list')
            
            # 서비스 레이어를 통한 JSONL 생성
            jsonl_content = DocumentService.generate_jsonl_data(list(documents))
            
            # HTTP 응답 생성
            response = HttpResponse(
                jsonl_content,
                content_type='application/json; charset=utf-8'
            )
            response['Content-Disposition'] = f'attachment; filename="documents_{len(documents)}.jsonl"'
            
            messages.success(request, f'{len(documents)}개의 문서가 JSONL 파일로 다운로드되었습니다.')
            return response
            
        except Exception as e:
            messages.error(request, f'다운로드 중 오류가 발생했습니다: {str(e)}')
            return redirect('document_list')
    
    return redirect('document_list')