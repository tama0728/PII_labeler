"""
API 뷰들 (JSON 응답)
"""
import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

from .services import PIITagService


@method_decorator([csrf_exempt, login_required], name='dispatch')
class AddPIITagAPIView(View):
    """PII 태그 추가 API"""
    
    def post(self, request):
        try:
            # JSON 데이터 또는 Form 데이터 처리
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = {
                    'document_id': request.POST.get('document_id'),
                    'pii_category': request.POST.get('pii_category_value'),
                    'span_text': request.POST.get('span_text'),
                    'start_offset': request.POST.get('start_offset'),
                    'end_offset': request.POST.get('end_offset'),
                    'span_id': request.POST.get('span_id', ''),
                    'entity_id': request.POST.get('entity_id', ''),
                    'annotator': request.POST.get('annotator', ''),
                    'identifier_type': request.POST.get('identifier_type', ''),
                    'confidence': 0.0
                }
            
            success, pii_tag, message = PIITagService.create_pii_tag(data, request.user)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'tag_id': pii_tag.id,
                    'message': message
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': message
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'오류가 발생했습니다: {str(e)}'
            })


@method_decorator([csrf_exempt, login_required], name='dispatch')
class DeletePIITagAPIView(View):
    """PII 태그 삭제 API"""
    
    def post(self, request):
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
            
            success, message = PIITagService.delete_pii_tag(tag_id, request.user)
            
            return JsonResponse({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'오류가 발생했습니다: {str(e)}'
            })


@method_decorator([csrf_exempt, login_required], name='dispatch')
class UpdatePIITagAPIView(View):
    """PII 태그 업데이트 API"""
    
    def post(self, request):
        try:
            # JSON 데이터 또는 Form 데이터 처리
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                tag_id = data.get('tag_id')
            else:
                tag_id = request.POST.get('tag_id')
                data = {
                    'pii_category_value': request.POST.get('pii_category_value'),
                    'identifier_type': request.POST.get('identifier_type', ''),
                    'entity_id': request.POST.get('entity_id', '')
                }
            
            if not tag_id:
                return JsonResponse({
                    'success': False,
                    'message': '태그 ID가 필요합니다.'
                })
            
            success, pii_tag, message = PIITagService.update_pii_tag(tag_id, data, request.user)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'tag_id': pii_tag.id,
                    'new_category': pii_tag.pii_category.value,
                    'new_color': pii_tag.pii_category.background_color
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': message
                })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'오류가 발생했습니다: {str(e)}'
            })


@method_decorator([csrf_exempt, login_required], name='dispatch')
class DeleteDocumentAPIView(View):
    """문서 삭제 API"""
    
    def post(self, request):
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
            
            success, message = PIITagService.delete_document(document_id, request.user)
            
            return JsonResponse({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'오류가 발생했습니다: {str(e)}'
            })


@method_decorator([csrf_exempt, login_required], name='dispatch')
class BulkDeleteDocumentsAPIView(View):
    """여러 문서 일괄 삭제 API"""
    
    def post(self, request):
        try:
            document_ids = request.POST.getlist('document_ids')
            
            if not document_ids:
                return JsonResponse({
                    'success': False,
                    'message': '삭제할 문서를 선택해주세요.'
                })
            
            deleted_count, message = PIITagService.bulk_delete_documents(document_ids, request.user)
            
            return JsonResponse({
                'success': True,
                'deleted_count': deleted_count,
                'message': message
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'오류가 발생했습니다: {str(e)}'
            })


# 기존 함수 기반 뷰들을 위한 래퍼 함수들 (하위 호환성)
add_pii_tag = AddPIITagAPIView.as_view()
delete_pii_tag = DeletePIITagAPIView.as_view()
update_pii_tag = UpdatePIITagAPIView.as_view()
delete_document = DeleteDocumentAPIView.as_view()
bulk_delete_documents = BulkDeleteDocumentsAPIView.as_view()