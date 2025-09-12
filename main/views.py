from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import os
from .models import Document, PIITag, PIICategory

def get_next_span_id(document):
    """문서의 다음 span_id 반환"""
    existing_spans = PIITag.objects.filter(document=document).exclude(span_id='').exclude(span_id__isnull=True)
    max_span_id = 0
    for tag in existing_spans:
        try:
            span_num = int(tag.span_id)
            max_span_id = max(max_span_id, span_num)
        except (ValueError, TypeError):
            continue
    return str(max_span_id + 1)

def get_next_entity_id(document):
    """문서의 다음 entity_id 반환"""
    existing_entities = PIITag.objects.filter(document=document).exclude(entity_id='').exclude(entity_id__isnull=True)
    max_entity_id = 0
    for tag in existing_entities:
        try:
            entity_num = int(tag.entity_id)
            max_entity_id = max(max_entity_id, entity_num)
        except (ValueError, TypeError):
            continue
    return str(max_entity_id + 1)

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
    
    # 이전/다음 문서 찾기
    all_documents = Document.objects.all().order_by('id')
    document_ids = list(all_documents.values_list('id', flat=True))
    
    current_index = document_ids.index(pk)
    prev_document = None
    next_document = None
    
    if current_index > 0:
        prev_document = all_documents[current_index - 1]
    if current_index < len(document_ids) - 1:
        next_document = all_documents[current_index + 1]
    
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
                                        # span_id와 entity_id가 비어있으면 자동 할당
                                        span_id = entity.get('span_id', '')
                                        entity_id = entity.get('entity_id', '')
                                        
                                        if not span_id:
                                            span_id = get_next_span_id(document)
                                        if not entity_id:
                                            entity_id = get_next_entity_id(document)
                                        
                                        # annotator가 비어있으면 Anonymous로 설정
                                        annotator_value = entity.get('annotator', '')
                                        if not annotator_value:
                                            annotator_value = "Anonymous"
                                        
                                        PIITag.objects.create(
                                            document=document,
                                            pii_category=pii_category,
                                            span_text=entity.get('span_text', ''),
                                            start_offset=entity.get('start_offset', 0),
                                            end_offset=entity.get('end_offset', 0),
                                            span_id=span_id,
                                            entity_id=entity_id,
                                            annotator=annotator_value,
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
            # Form 데이터 또는 JSON 데이터 처리
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                document_id = data.get('document_id')
                pii_category_value = data.get('pii_category')
                span_text = data.get('span_text')
                start_offset = data.get('start_offset')
                end_offset = data.get('end_offset')
                span_id = data.get('span_id', '')
                entity_id = data.get('entity_id', '')
                annotator = data.get('annotator', '')
                identifier_type = data.get('identifier_type', '')
                confidence = data.get('confidence', 0.0)
            else:
                # Form 데이터 처리
                document_id = request.POST.get('document_id')
                pii_category_value = request.POST.get('pii_category_value')
                span_text = request.POST.get('span_text')
                start_offset = request.POST.get('start_offset')
                end_offset = request.POST.get('end_offset')
                span_id = request.POST.get('span_id', '')
                entity_id = request.POST.get('entity_id', '')
                annotator = request.POST.get('annotator', '')
                identifier_type = request.POST.get('identifier_type', '')
                confidence = 0.0
            
            # 필수 필드 검증
            if not all([document_id, pii_category_value, span_text, start_offset, end_offset]):
                return JsonResponse({
                    'success': False,
                    'message': '필수 필드가 누락되었습니다.'
                })
            
            # 문서 조회
            document = get_object_or_404(Document, pk=document_id)
            pii_category = get_object_or_404(PIICategory, value=pii_category_value)
            
            # 중복 태그 검사 (같은 위치에 같은 태그가 있는지)
            existing_tag = PIITag.objects.filter(
                document=document,
                start_offset=start_offset,
                end_offset=end_offset,
                pii_category=pii_category
            ).first()
            
            if existing_tag:
                return JsonResponse({
                    'success': False,
                    'message': '해당 위치에 이미 같은 태그가 존재합니다.'
                })
            
            # span_id와 entity_id가 비어있으면 자동으로 증가하는 숫자 할당
            if not span_id:
                span_id = get_next_span_id(document)
            
            if not entity_id:
                entity_id = get_next_entity_id(document)
            
            # annotator가 비어있으면 Anonymous로 설정
            if not annotator:
                annotator = "Anonymous"
            
            # PII 태그 생성
            pii_tag = PIITag.objects.create(
                document=document,
                pii_category=pii_category,
                span_text=span_text,
                start_offset=int(start_offset),
                end_offset=int(end_offset),
                span_id=span_id,
                entity_id=entity_id,
                annotator=annotator,
                identifier_type=identifier_type,
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

@csrf_exempt
@login_required
def delete_pii_tag(request):
    """PII 태그 삭제 API"""
    if request.method == 'POST':
        try:
            # JSON 데이터 또는 Form 데이터 처리
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                tag_id = data.get('tag_id')
            else:
                tag_id = request.POST.get('tag_id')
            
            if not tag_id:
                return JsonResponse({
                    'success': False,
                    'message': '태그 ID가 필요합니다.'
                })
            
            # 태그 조회 및 권한 확인
            pii_tag = get_object_or_404(PIITag, id=tag_id)
            
            # 작성자 또는 관리자만 삭제 가능
            if pii_tag.created_by != request.user and not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'message': '삭제 권한이 없습니다.'
                })
            
            # 태그 삭제
            pii_tag.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'PII 태그가 삭제되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

@csrf_exempt
@login_required
def update_pii_tag(request):
    """PII 태그 업데이트 API"""
    if request.method == 'POST':
        try:
            # JSON 데이터 또는 Form 데이터 처리
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                tag_id = data.get('tag_id')
                pii_category_value = data.get('pii_category_value')
                identifier_type = data.get('identifier_type', '')
                entity_id = data.get('entity_id', '')
            else:
                tag_id = request.POST.get('tag_id')
                pii_category_value = request.POST.get('pii_category_value')
                identifier_type = request.POST.get('identifier_type', '')
                entity_id = request.POST.get('entity_id', '')
            
            if not tag_id or not pii_category_value:
                return JsonResponse({
                    'success': False,
                    'message': '태그 ID와 PII 카테고리가 필요합니다.'
                })
            
            # 태그 조회 및 권한 확인
            pii_tag = get_object_or_404(PIITag, id=tag_id)
            
            # 작성자 또는 관리자만 수정 가능
            if pii_tag.created_by != request.user and not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'message': '수정 권한이 없습니다.'
                })
            
            # PII 카테고리 조회
            pii_category = get_object_or_404(PIICategory, value=pii_category_value)
            
            # 식별자 유형이 공백이면 default로 설정
            if not identifier_type:
                identifier_type = 'default'
            
            # 태그 업데이트
            pii_tag.pii_category = pii_category
            pii_tag.identifier_type = identifier_type
            pii_tag.annotator = request.user.username  # 어노테이터를 현재 사용자로 업데이트
            
            # entity_id 업데이트 (제공된 경우)
            if entity_id:
                pii_tag.entity_id = entity_id
            
            pii_tag.save()
            
            return JsonResponse({
                'success': True,
                'message': 'PII 태그가 업데이트되었습니다.',
                'tag_id': pii_tag.id,
                'new_category': pii_category.value,
                'new_color': pii_category.background_color
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

@csrf_exempt
@login_required
def delete_document(request):
    """문서 삭제 API"""
    if request.method == 'POST':
        try:
            # JSON 데이터 또는 Form 데이터 처리
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                document_id = data.get('document_id')
            else:
                document_id = request.POST.get('document_id')
            
            if not document_id:
                return JsonResponse({
                    'success': False,
                    'message': '문서 ID가 필요합니다.'
                })
            
            # 문서 조회 및 권한 확인
            document = get_object_or_404(Document, id=document_id)
            
            # 작성자 또는 관리자만 삭제 가능
            if document.created_by != request.user and not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'message': '삭제 권한이 없습니다.'
                })
            
            # 관련 PII 태그들도 함께 삭제
            document.pii_tags.all().delete()
            
            # 문서 삭제
            document.delete()
            
            return JsonResponse({
                'success': True,
                'message': '문서가 삭제되었습니다.'
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

@login_required
def download_jsonl(request):
    """선택된 문서들을 JSONL 형식으로 다운로드"""
    if request.method == 'POST':
        try:
            # 두 가지 방식으로 문서 ID 받기 (기존 방식과 새로운 방식)
            selected_doc_ids = request.POST.getlist('selected_documents')
            bulk_doc_ids = request.POST.getlist('document_ids')
            
            # 둘 중 하나라도 있으면 사용
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
            
            # JSONL 데이터 생성
            jsonl_lines = []
            for document in documents:
                # PII 태그들 조회
                pii_tags = document.pii_tags.all()
                
                # entities 배열 생성
                entities = []
                for tag in pii_tags:
                    entity = {
                        "span_text": tag.span_text,
                        "entity_type": tag.pii_category.value,
                        "start_offset": tag.start_offset,
                        "end_offset": tag.end_offset,
                        "span_id": tag.span_id,
                        "entity_id": tag.entity_id,
                        "annotator": tag.annotator,
                        "identifier_type": tag.identifier_type
                    }
                    entities.append(entity)
                
                # JSON 객체 생성
                json_obj = {
                    "metadata": {
                        "data_id": document.data_id,
                        "number_of_subjects": int(document.number_of_subjects) if document.number_of_subjects.isdigit() else 0,
                        "provenance": {
                            "dialog_type": document.dialog_type,
                            "turn_cnt": int(float(document.turn_cnt)) if document.turn_cnt.replace('.', '').isdigit() else 0,
                            "doc_id": document.doc_id
                        }
                    },
                    "text": document.text,
                    "entities": entities
                }
                
                jsonl_lines.append(json.dumps(json_obj, ensure_ascii=False))
            
            # JSONL 파일 내용 생성
            jsonl_content = '\n'.join(jsonl_lines)
            
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

@csrf_exempt
@login_required
def bulk_delete_documents(request):
    """여러 문서 일괄 삭제"""
    if request.method == 'POST':
        try:
            document_ids = request.POST.getlist('document_ids')
            
            if not document_ids:
                return JsonResponse({
                    'success': False,
                    'message': '삭제할 문서를 선택해주세요.'
                })
            
            deleted_count = 0
            for document_id in document_ids:
                try:
                    document = get_object_or_404(Document, pk=document_id)
                    
                    # 권한 확인 (작성자 또는 관리자만 삭제 가능)
                    if document.created_by == request.user or request.user.is_staff:
                        # 관련 PII 태그들도 함께 삭제
                        document.pii_tags.all().delete()
                        document.delete()
                        deleted_count += 1
                except Exception as e:
                    print(f"문서 {document_id} 삭제 실패: {e}")
                    continue
            
            return JsonResponse({
                'success': True,
                'deleted_count': deleted_count,
                'message': f'{deleted_count}개 문서가 삭제되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})