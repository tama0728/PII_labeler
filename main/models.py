from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Document(models.Model):
    """문서 모델"""
    title = models.CharField(max_length=200, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="작성자")
    
    class Meta:
        verbose_name = "문서"
        verbose_name_plural = "문서들"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class PIITag(models.Model):
    """PII 태그 모델"""
    PII_TYPES = [
        ('name', '이름'),
        ('email', '이메일'),
        ('phone', '전화번호'),
        ('address', '주소'),
        ('ssn', '주민등록번호'),
        ('credit_card', '신용카드번호'),
        ('other', '기타'),
    ]
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='pii_tags', verbose_name="문서")
    pii_type = models.CharField(max_length=20, choices=PII_TYPES, verbose_name="PII 유형")
    start_position = models.IntegerField(verbose_name="시작 위치")
    end_position = models.IntegerField(verbose_name="끝 위치")
    tagged_text = models.CharField(max_length=500, verbose_name="태그된 텍스트")
    confidence = models.FloatField(default=0.0, verbose_name="신뢰도")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="작성자")
    
    class Meta:
        verbose_name = "PII 태그"
        verbose_name_plural = "PII 태그들"
        ordering = ['start_position']
    
    def __str__(self):
        return f"{self.document.title} - {self.get_pii_type_display()}"
