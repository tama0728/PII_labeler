"""
Django Forms
"""
from django import forms
from .models import PIITag, PIICategory


class JSONLUploadForm(forms.Form):
    """JSONL 파일 업로드 폼"""
    jsonl_file = forms.FileField(
        label='JSONL 파일',
        help_text='업로드할 JSONL 파일을 선택하세요.',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.jsonl'
        })
    )

    def clean_jsonl_file(self):
        file = self.cleaned_data['jsonl_file']
        if not file.name.endswith('.jsonl'):
            raise forms.ValidationError('JSONL 파일만 업로드 가능합니다.')
        return file


class PIITagForm(forms.ModelForm):
    """PII 태그 폼"""
    
    class Meta:
        model = PIITag
        fields = [
            'pii_category', 'span_text', 'start_offset', 'end_offset',
            'span_id', 'entity_id', 'annotator', 'identifier_type', 'confidence'
        ]
        widgets = {
            'pii_category': forms.Select(attrs={'class': 'form-select'}),
            'span_text': forms.TextInput(attrs={'class': 'form-control'}),
            'start_offset': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'end_offset': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'span_id': forms.TextInput(attrs={'class': 'form-control'}),
            'entity_id': forms.TextInput(attrs={'class': 'form-control'}),
            'annotator': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Anonymous'
            }),
            'identifier_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'default'
            }),
            'confidence': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '1',
                'step': '0.1'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 기본값 설정
        self.fields['confidence'].initial = 0.0
        self.fields['annotator'].initial = 'Anonymous'
        self.fields['identifier_type'].initial = 'default'

    def clean(self):
        cleaned_data = super().clean()
        start_offset = cleaned_data.get('start_offset')
        end_offset = cleaned_data.get('end_offset')

        if start_offset is not None and end_offset is not None:
            if start_offset >= end_offset:
                raise forms.ValidationError('시작 오프셋은 끝 오프셋보다 작아야 합니다.')

        return cleaned_data


class PIITagUpdateForm(forms.Form):
    """PII 태그 업데이트 폼"""
    tag_id = forms.IntegerField(widget=forms.HiddenInput())
    pii_category_value = forms.ModelChoiceField(
        queryset=PIICategory.objects.all(),
        to_field_name='value',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    identifier_type = forms.CharField(
        max_length=100,
        required=False,
        initial='default',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    entity_id = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class DocumentSelectionForm(forms.Form):
    """문서 선택 폼"""
    selected_documents = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Document
        self.fields['selected_documents'].queryset = Document.objects.filter(
            created_by=user
        )