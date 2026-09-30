from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Disciplina, Modulo, Fase, Questao

class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ['nome', 'slug', 'descricao', 'tema']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full bg-slate-100 border border-slate-300 rounded-lg p-3 outline-none'}),
            'slug': forms.TextInput(attrs={'class': 'w-full bg-slate-100 border border-slate-300 rounded-lg p-3 outline-none'}),
            'descricao': forms.Textarea(attrs={'class': 'w-full bg-slate-100 border border-slate-300 rounded-lg p-3', 'rows': 3}),
            'tema': forms.Select(attrs={'class': 'w-full bg-slate-100 border border-slate-300 rounded-lg p-3 outline-none', 'id': 'tema-trilha-form'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'w-6 h-6 text-indigo-600 rounded'}),
        }

class ModuloForm(forms.ModelForm):
    class Meta:
        model = Modulo
        fields = ['titulo', 'descricao', 'ordem']

class FaseForm(forms.ModelForm):
    class Meta:
        model = Fase
        fields = ['modulo', 'titulo', 'ordem', 'tipo', 'xp_recompensa', 'moedas_recompensa']
    
    def __init__(self, trilha_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['modulo'].queryset = Modulo.objects.filter(disciplina_id=trilha_id)

class QuestaoForm(forms.ModelForm):
    class Meta:
        model = Questao
        fields = ['enunciado', 'explicacao_erro']

class CadastroUsuarioForm(UserCreationForm):
    """Formulário público de criação de conta.

    Contas novas entram sempre como aluno. A promoção para
    professor continua sendo uma decisão administrativa.
    """

    first_name = forms.CharField(
        label='Nome',
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white outline-none focus:border-indigo-400',
                'autocomplete': 'given-name',
            }
        ),
    )

    last_name = forms.CharField(
        label='Sobrenome',
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white outline-none focus:border-indigo-400',
                'autocomplete': 'family-name',
            }
        ),
    )

    email = forms.EmailField(
        label='E-mail',
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white outline-none focus:border-indigo-400',
                'autocomplete': 'email',
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        )
        widgets = {
            'username': forms.TextInput(
                attrs={
                    'class': 'w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-white outline-none focus:border-indigo-400',
                    'autocomplete': 'username',
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'Já existe uma conta cadastrada com este e-mail.'
            )
        return email
