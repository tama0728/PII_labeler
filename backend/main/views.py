from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.views.decorators.csrf import csrf_exempt
import json
import os
from .models import Document, PIICategory, PIITag


def index(request):
    """메인 페이지"""
    try:
        if request.user.is_authenticated:
            documents = Document.objects.filter(created_by=request.user).order_by('created_at')
        else:
            documents = []
        return render(request, 'main/index.html', {'documents': documents})
    except Exception as e:
        return render(request, 'main/index.html', {'documents': [], 'error': str(e)})


@login_required
def document_list(request):
    """문서 목록 페이지"""
    documents = Document.objects.filter(created_by=request.user).order_by('created_at')
    return render(request, 'main/document_list.html', {'documents': documents})


@login_required
def document_detail(request, pk):
    """문서 상세 페이지"""
    document = get_object_or_404(Document, pk=pk, created_by=request.user)
    pii_tags = PIITag.objects.filter(document=document).order_by('start_offset')
    pii_categories = PIICategory.objects.all().order_by('created_at')
    
    # 이전/다음 문서 찾기 (현재 사용자의 문서만)
    prev_document = Document.objects.filter(pk__lt=pk, created_by=request.user).order_by('-pk').first()
    next_document = Document.objects.filter(pk__gt=pk, created_by=request.user).order_by('pk').first()
    
    # PII 태그들을 JSON 형태로 변환
    pii_tags_json = []
    for tag in pii_tags:
        pii_tags_json.append({
            'id': tag.id,
            'start': tag.start_offset,
            'end': tag.end_offset,
            'text': tag.span_text,
            'color': tag.pii_category.background_color,
            'category': tag.pii_category.value,
            'span_id': tag.span_id,
            'entity_id': tag.entity_id,
            'annotator': tag.annotator,
            'identifier_type': tag.identifier_type
        })
    
    return render(request, 'main/document_detail.html', {
        'document': document,
        'pii_tags': pii_tags,
        'pii_tags_json': json.dumps(pii_tags_json),
        'pii_categories': pii_categories,
        'prev_document': prev_document,
        'next_document': next_document,
    })


@login_required
def document_create(request):
    """문서 생성 페이지"""
    if request.method == 'POST':
        if 'jsonl_file' in request.FILES:
            # JSONL 파일 처리
            jsonl_file = request.FILES['jsonl_file']
            if jsonl_file.name.endswith('.jsonl'):
                try:
                    content = jsonl_file.read().decode('utf-8')
                    lines = [line for line in content.strip().split('\n') if line.strip()]

                    # 1) 파싱하여 업로드 대상 data_id 수집
                    parsed_rows = []
                    upload_data_ids = []
                    for line in lines:
                        data = json.loads(line)
                        metadata = data.get('metadata', {})
                        data_id_value = metadata.get('data_id', '')
                        parsed_rows.append((data, metadata, data_id_value))
                        upload_data_ids.append(data_id_value)

                    # 2) 파일 내부 data_id 중복 검사
                    duplicate_in_file = {x for x in upload_data_ids if upload_data_ids.count(x) > 1}
                    if duplicate_in_file:
                        messages.error(
                            request,
                            f"업로드 파일 내 중복 data_id가 발견되어 업로드를 중단했습니다: {', '.join(sorted(duplicate_in_file))}"
                        )
                        return render(request, 'main/document_create.html')

                    # 3) DB 중복 검사 (사용자 기준)
                    existing = set(
                        Document.objects.filter(
                            data_id__in=upload_data_ids,
                            created_by=request.user
                        ).values_list('data_id', flat=True)
                    )
                    if existing:
                        messages.error(
                            request,
                            f"이미 존재하는 data_id가 있어 업로드를 중단했습니다: {', '.join(sorted(existing))}"
                        )
                        return render(request, 'main/document_create.html')

                    # 4) 트랜잭션으로 일괄 생성. 중간 오류 시 전체 롤백
                    with transaction.atomic():
                        for data, metadata, data_id_value in parsed_rows:
                            document = Document.objects.create(
                                data_id=data_id_value,
                                number_of_subjects=metadata.get('number_of_subjects', 0),
                                provenance=json.dumps(metadata.get('provenance', {}), ensure_ascii=False),
                                text=data.get('text', ''),
                                created_by=request.user
                            )

                            # 엔티티 처리
                            entities = data.get('entities', [])
                            for entity in entities:
                                pii_category = PIICategory.objects.filter(
                                    value=entity.get('entity_type', '')
                                ).first()

                                if pii_category:
                                    span_id = entity.get('span_id', '')
                                    entity_id = entity.get('entity_id', '')
                                    annotator = entity.get('annotator', 'Anonymous')
                                    identifier_type = entity.get('identifier_type', 'quasi')
                                    if not span_id:
                                        span_id = PIITag.objects.filter(document=document).count()+1
                                    if not entity_id:
                                        entity_id = PIITag.objects.filter(document=document).count()+1
                                    if not annotator:
                                        annotator = 'Anonymous'
                                    if not identifier_type:
                                        identifier_type = 'quasi'

                                    # 공백 트림 처리
                                    original_span_text = entity.get('span_text', '')
                                    trimmed_span_text = original_span_text.strip()
                                    start_offset = entity.get('start_offset', 0)
                                    end_offset = entity.get('end_offset', 0)
                                    
                                    # 트림된 텍스트가 원본과 다르면 offset 조정
                                    if trimmed_span_text != original_span_text:
                                        left_trim_count = len(original_span_text) - len(original_span_text.lstrip())
                                        right_trim_count = len(original_span_text) - len(original_span_text.rstrip())
                                        
                                        # offset 조정
                                        start_offset = start_offset + left_trim_count
                                        end_offset = end_offset - right_trim_count
                                        
                                        # end_offset이 start_offset보다 작아지지 않도록 보정
                                        if end_offset <= start_offset:
                                            end_offset = start_offset + len(trimmed_span_text)
                                    if pii_category == "MASK":
                                        pii_category = "MISC"
                                    if trimmed_span_text == "" or end_offset == 0:
                                        continue
                                    PIITag.objects.create(
                                        document=document,
                                        pii_category=pii_category,
                                        span_text=trimmed_span_text,
                                        start_offset=start_offset,
                                        end_offset=end_offset,
                                        span_id=span_id,
                                        entity_id=entity_id,
                                        annotator=annotator,
                                        identifier_type=identifier_type,
                                        created_by=request.user
                                    )

                    messages.success(request, 'JSONL 파일이 성공적으로 업로드되었습니다.')
                    return redirect('document_list')
                    
                except Exception as e:
                    messages.error(request, f'파일 처리 중 오류가 발생했습니다: {str(e)}')
            else:
                messages.error(request, 'JSONL 파일만 업로드할 수 있습니다.')
    
    return render(request, 'main/document_create.html')


def register(request):
    """사용자 등록"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})


@csrf_exempt
@login_required
def add_pii_tag(request):
    """PII 태그 추가"""
    if request.method == 'POST':
        try:
            document_id = request.POST.get('document_id')
            pii_category_value = request.POST.get('pii_category_value')
            span_text = request.POST.get('span_text')
            start_offset = int(request.POST.get('start_offset', 0))
            end_offset = int(request.POST.get('end_offset', 0))
            span_id = request.POST.get('span_id', '')
            entity_id = request.POST.get('entity_id', '')
            annotator = request.POST.get('annotator', 'Anonymous')
            identifier_type = request.POST.get('identifier_type', 'quasi')
            
            document = get_object_or_404(Document, id=document_id)
            pii_category = get_object_or_404(PIICategory, value=pii_category_value)
            
            # 공백 트림 처리
            original_span_text = span_text
            trimmed_span_text = span_text.strip()
            
            # 트림된 텍스트가 원본과 다르면 offset 조정
            if trimmed_span_text != original_span_text:
                left_trim_count = len(original_span_text) - len(original_span_text.lstrip())
                right_trim_count = len(original_span_text) - len(original_span_text.rstrip())
                
                # offset 조정
                adjusted_start_offset = start_offset + left_trim_count
                adjusted_end_offset = end_offset - right_trim_count
                
                # end_offset이 start_offset보다 작아지지 않도록 보정
                if adjusted_end_offset <= adjusted_start_offset:
                    adjusted_end_offset = adjusted_start_offset + len(trimmed_span_text)
                
                # 트림된 텍스트와 조정된 offset 사용
                span_text = trimmed_span_text
                start_offset = adjusted_start_offset
                end_offset = adjusted_end_offset
            
            # 중복 태그 확인 (조정된 offset으로)
            existing_tag = PIITag.objects.filter(
                document=document,
                start_offset=start_offset,
                end_offset=end_offset
            ).first()
            
            if existing_tag:
                return JsonResponse({'success': False, 'message': '이미 해당 위치에 태그가 있습니다.'})
            
            # 자동 ID 생성
            if not span_id:
                # 해당 문서의 모든 태그에서 가장 높은 span_id 찾기
                existing_tags = PIITag.objects.filter(document=document)
                if existing_tags.exists():
                    # 숫자인 span_id들만 필터링해서 가장 높은 값 찾기
                    numeric_span_ids = []
                    for tag in existing_tags:
                        try:
                            numeric_span_ids.append(int(tag.span_id))
                        except (ValueError, TypeError):
                            continue
                    
                    if numeric_span_ids:
                        max_span_id = max(numeric_span_ids)
                        span_id = str(max_span_id + 1)
                    else:
                        span_id = "1"
                else:
                    span_id = "1"
            
            if not entity_id:
                entity_id = span_id
            
            new_tag = PIITag.objects.create(
                document=document,
                pii_category=pii_category,
                span_text=span_text,
                start_offset=start_offset,
                end_offset=end_offset,
                span_id=span_id,
                entity_id=entity_id,
                annotator=annotator or 'Anonymous',
                identifier_type=identifier_type or 'quasi',
                created_by=request.user
            )
            
            # 새로 생성된 태그의 모든 정보를 반환
            return JsonResponse({
                'success': True,
                'tag': {
                    'id': new_tag.id,
                    'start': new_tag.start_offset,
                    'end': new_tag.end_offset,
                    'text': new_tag.span_text,
                    'color': new_tag.pii_category.background_color,
                    'category': new_tag.pii_category.value,
                    'span_id': new_tag.span_id,
                    'entity_id': new_tag.entity_id,
                    'annotator': new_tag.annotator,
                    'identifier_type': new_tag.identifier_type
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'})


@csrf_exempt
@login_required
def delete_pii_tag(request):
    """PII 태그 삭제"""
    if request.method == 'POST':
        try:
            tag_id = request.POST.get('tag_id')
            tag = get_object_or_404(PIITag, id=tag_id)
            
            # 삭제할 태그의 정보 저장
            document = tag.document
            deleted_entity_id = tag.entity_id
            deleted_span_id = tag.span_id
            
            # 삭제될 태그가 부모 태그인지 확인 (span_id == entity_id)
            is_parent_tag = str(deleted_span_id) == str(deleted_entity_id)
            
            # 부모 태그 삭제 시 자식 태그들 처리
            updated_tags = []
            if is_parent_tag:
                # 같은 entity_id를 가진 모든 자식 태그들 찾기
                child_tags = PIITag.objects.filter(
                    document=document,
                    entity_id=deleted_entity_id
                ).exclude(id=tag_id).order_by('span_id')
                
                if child_tags.exists():
                    # 다음으로 가장 낮은 span_id 찾기 (새로운 부모)
                    new_parent_span_id = min(int(child.span_id) for child in child_tags if child.span_id.isdigit())
                    new_parent_entity_id = str(new_parent_span_id)
                    
                    # 모든 자식 태그들의 entity_id를 새로운 부모로 변경
                    for child_tag in child_tags:
                        child_tag.entity_id = new_parent_entity_id
                        child_tag.save()
                        
                        # 업데이트된 태그 정보 저장
                        updated_tags.append({
                            'id': child_tag.id,
                            'start': child_tag.start_offset,
                            'end': child_tag.end_offset,
                            'text': child_tag.span_text,
                            'color': child_tag.pii_category.background_color,
                            'category': child_tag.pii_category.value,
                            'span_id': child_tag.span_id,
                            'entity_id': child_tag.entity_id,
                            'annotator': child_tag.annotator,
                            'identifier_type': child_tag.identifier_type
                        })
            
            # 태그 삭제
            tag.delete()
            
            return JsonResponse({
                'success': True,
                'updated_tags': updated_tags,
                'deleted_tag_id': tag_id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'})


@csrf_exempt
@login_required
def update_pii_tag(request):
    """PII 태그 업데이트"""
    if request.method == 'POST':
        try:
            tag_id = request.POST.get('tag_id')
            pii_category_value = request.POST.get('pii_category_value')
            identifier_type = request.POST.get('identifier_type', 'quasi')
            entity_id = request.POST.get('entity_id', '')
            
            tag = get_object_or_404(PIITag, id=tag_id)
            
            if pii_category_value:
                pii_category = get_object_or_404(PIICategory, value=pii_category_value)
                tag.pii_category = pii_category
            
            tag.identifier_type = identifier_type or 'quasi'
            tag.entity_id = entity_id
            tag.annotator = request.user.username
            tag.save()
            
            return JsonResponse({'success': True, 'new_color': pii_category.background_color, 'new_category': tag.pii_category.value})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'})


@csrf_exempt
@login_required
def delete_document(request):
    """문서 삭제"""
    if request.method == 'POST':
        try:
            document_id = request.POST.get('document_id')
            document = get_object_or_404(Document, id=document_id)
            document.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'})


@csrf_exempt
@login_required
def bulk_delete_documents(request):
    """대량 문서 삭제"""
    if request.method == 'POST':
        try:
            document_ids = request.POST.getlist('document_ids')
            Document.objects.filter(id__in=document_ids).delete()
            return JsonResponse({'success': True, 'deleted_count': len(document_ids)})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'})


def download_jsonl(request):
    """JSONL 다운로드"""
    document_ids = request.POST.getlist('document_ids')
    documents = Document.objects.filter(id__in=document_ids)
    
    response = HttpResponse(content_type='application/jsonl')
    response['Content-Disposition'] = 'attachment; filename="documents.jsonl"'
    
    for document in documents:
        pii_tags = PIITag.objects.filter(document=document)
        
        # 메타데이터 구성
        try:
            provenance_obj = json.loads(document.provenance) if document.provenance else {}
        except Exception:
            provenance_obj = document.provenance or {}
        metadata = {
            'data_id': document.data_id,
            'number_of_subjects': document.number_of_subjects,
            'provenance': provenance_obj
        }
        
        # 엔티티 구성
        entities = []
        for tag in pii_tags:
            entities.append({
                'span_text': tag.span_text,
                'entity_type': tag.pii_category.value,
                'start_offset': tag.start_offset,
                'end_offset': tag.end_offset,
                'span_id': tag.span_id,
                'entity_id': tag.entity_id,
                'annotator': tag.annotator,
                'identifier_type': tag.identifier_type
            })
        
        # JSONL 라인 구성
        jsonl_data = {
            'metadata': metadata,
            'text': document.text,
            'entities': entities
        }
        
        response.write(json.dumps(jsonl_data, ensure_ascii=False) + '\n')
    
    return response