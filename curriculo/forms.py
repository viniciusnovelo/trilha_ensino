from django import forms
from .models import Disciplina, Modulo, Fase, Questao

class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ['nome', 'slug', 'descricao', 'tema', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full bg-slate-100 border border-slate-300 rounded-lg p-3 outline-none'}),
            'slug': forms.TextInput(attrs={'class': 'w-full bg-slate-100 border border-slate-300 rounded-lg p-3 outline-none'}),
            'descricao': forms.Textarea(attrs={'class': 'w-full bg-slate-100 border border-slate-300 rounded-lg p-3', 'rows': 3}),
            'tema': forms.Select(attrs={'class': 'w-full bg-slate-100 border border-slate-300 rounded-lg p-3 outline-none'}),
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