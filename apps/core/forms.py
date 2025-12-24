from django import forms
from .models import RestaurantCompany, Branch
from django.contrib.auth import get_user_model

User = get_user_model()

class CompanyForm(forms.ModelForm):
    new_manager_email = forms.EmailField(
        label="البريد الإلكتروني",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'manager@example.com'}),
        required=True
    )
    new_manager_username = forms.CharField(
        label="اسم مستخدم المدير العام",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Manager Username'}),
        required=True
    )
    new_manager_password = forms.CharField(
        label="كلمة المرور",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '******'}),
        required=True
    )

    class Meta:
        model = RestaurantCompany
        fields = ['name', 'subscription_status'] # Removed manager
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المطعم/الشركة'}),
            'subscription_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'اسم الشركة',
            'subscription_status': 'اشتراك نشط',
        }

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('new_manager_username')
        
        # التأكد من عدم تكرار اسم المستخدم
        if username and User.objects.filter(username=username).exists():
             raise forms.ValidationError(f"اسم المستخدم '{username}' موجود بالفعل.")
        
        return cleaned_data

class BranchForm(forms.ModelForm):
    # خيار إنشاء مدير جديد إجباري (لضمان العزل)
    new_manager_email = forms.EmailField(
        label="البريد الإلكتروني للمدير",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'branch@example.com'}),
        required=True
    )
    new_manager_username = forms.CharField(
        required=True, 
        label="اسم المستخدم للمدير الجديد",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    new_manager_password = forms.CharField(
        required=True, 
        label="كلمة المرور",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '******'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_superuser:
            self.fields['company'] = forms.ModelChoiceField(
                queryset=RestaurantCompany.objects.all(),
                label="الشركة التابعة",
                widget=forms.Select(attrs={'class': 'form-select'})
            )

    class Meta:
        model = Branch
        fields = ['name', 'location', 'waste_threshold'] # Removed manager
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: فرع الرياض - العليا'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الرياض، شارع العليا'}),
            'waste_threshold': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'النسبة المئوية %'}),
        }
        labels = {
            'name': 'اسم الفرع',
            'location': 'الموقع',
            'waste_threshold': 'حد الهدر المسموح (%)',
        }

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('new_manager_username')

        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError(f"اسم المستخدم '{username}' موجود بالفعل.")
        
        return cleaned_data
