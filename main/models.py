from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class PIICategory(models.Model):
    """PII 카테고리 모델"""
    value = models.CharField(max_length=50, unique=True, verbose_name="PII 값")
    background_color = models.CharField(max_length=7, verbose_name="배경색")
    description = models.CharField(max_length=200, blank=True, verbose_name="설명")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    
    class Meta:
        verbose_name = "PII 카테고리"
        verbose_name_plural = "PII 카테고리들"
        ordering = ['value']
    
    def __str__(self):
        return self.value

class Document(models.Model):
    """문서 모델"""
    data_id = models.CharField(max_length=200, verbose_name="data_id")
    number_of_subjects = models.TextField(verbose_name="number_of_subjects")
    dialog_type = models.TextField(verbose_name="dialog_type")
    turn_cnt = models.TextField(verbose_name="turn_cnt")
    doc_id = models.TextField(verbose_name="doc_id")
    text = models.TextField(verbose_name="text")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="작성자")
    
    class Meta:
        verbose_name = "문서"
        verbose_name_plural = "문서들"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.data_id

class PIITag(models.Model):
    """PII 태그 모델"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='pii_tags', verbose_name="문서")
    pii_category = models.ForeignKey(PIICategory, on_delete=models.CASCADE, verbose_name="PII 카테고리")
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
        return f"{self.document.data_id} - {self.pii_category.value}"
