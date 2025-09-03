from django import forms
from .models import TempFile

class FileUploadForm(forms.ModelForm):
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '*/*'
        }),
        help_text='حداکثر اندازه فایل: 10MB'
    )
    
    expiry_minutes = forms.ChoiceField(
        choices=TempFile.EXPIRY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='مدت زمان انقضا'
    )
    
    max_downloads = forms.IntegerField(
        min_value=1,
        max_value=1000,
        initial=100,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='حداکثر تعداد دانلود'
    )
    
    class Meta:
        model = TempFile
        fields = ['file', 'expiry_minutes', 'max_downloads']
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1024 * 1024:  # 50MB
                raise forms.ValidationError('اندازه فایل نباید بیشتر از 10 مگابایت باشد.')
        return file


