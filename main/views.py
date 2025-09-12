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
                total_tags = 0
                
                for line in lines:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            
                            # metadata에서 정보 추출
                            metadata = data.get('metadata', {})
                            provenance = metadata.get('provenance', {})
                            
                            # Document 생성
                            document = Document.objects.create(
                                data_id=metadata.get('data_id', ''),
                                number_of_subjects=str(metadata.get('number_of_subjects', '')),
                                dialog_type=provenance.get('dialog_type', ''),
                                turn_cnt=str(provenance.get('turn_cnt', '')),
                                doc_id=provenance.get('doc_id', ''),
                                text=data.get('text', ''),
                                created_by=request.user
                            )
                            
                            # entities에서 PII 태그 생성
                            entities = data.get('entities', [])
                            for entity in entities:
                                try:
                                    # PII 카테고리 찾기
                                    pii_category = PIICategory.objects.filter(
                                        value=entity.get('entity_type')
                                    ).first()
                                    
                                    if pii_category:
                                        PIITag.objects.create(
                                            document=document,
                                            pii_category=pii_category,
                                            span_text=entity.get('span_text', ''),
                                            start_offset=entity.get('start_offset', 0),
                                            end_offset=entity.get('end_offset', 0),
                                            span_id=entity.get('span_id', ''),
                                            entity_id=entity.get('entity_id', ''),
                                            annotator=entity.get('annotator', ''),
                                            identifier_type=entity.get('identifier_type', ''),
                                            confidence=1.0,  # 기존 태그는 신뢰도 1.0으로 설정
                                            created_by=request.user
                                        )
                                        total_tags += 1
                                except Exception as e:
                                    # 개별 태그 생성 실패는 로그만 남기고 계속 진행
                                    print(f"태그 생성 실패: {e}")
                                    continue
                            
                            created_count += 1
                            
                        except json.JSONDecodeError as e:
                            print(f"JSON 파싱 오류: {e}")
                            continue
                        except Exception as e:
                            print(f"문서 처리 오류: {e}")
                            continue
                
                messages.success(request, f'{created_count}개의 문서와 {total_tags}개의 PII 태그가 성공적으로 업로드되었습니다.')
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
            start_pos = data.get('start_offset')
            end_pos = data.get('end_offset')
            span_text = data.get('span_text')
            confidence = data.get('confidence', 0.0)
            
            document = get_object_or_404(Document, pk=document_id)
            pii_category = get_object_or_404(PIICategory, value=pii_category_value)
            
            pii_tag = PIITag.objects.create(
                document=document,
                pii_category=pii_category,
                span_text=span_text,
                start_offset=start_pos,
                end_offset=end_pos,
                span_id=data.get('span_id', ''),
                entity_id=data.get('entity_id', ''),
                annotator=data.get('annotator', ''),
                identifier_type=data.get('identifier_type', ''),
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