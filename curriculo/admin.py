from django.contrib import admin
from .models import Materia, Disciplina, Modulo, Fase, Questao, Opcao

class OpcaoInline(admin.TabularInline):
    model = Opcao
    extra = 4

@admin.register(Questao)
class QuestaoAdmin(admin.ModelAdmin):
    inlines = [OpcaoInline]
    list_display = ('enunciado_curto', 'fase')
    list_filter = ('fase__modulo__disciplina', 'fase')

    def enunciado_curto(self, obj):
        return obj.enunciado[:60] + "..." if len(obj.enunciado) > 60 else obj.enunciado

class QuestaoInline(admin.StackedInline):
    model = Questao
    extra = 1

@admin.register(Fase)
class FaseAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'modulo', 'ordem', 'tipo', 'xp_recompensa', 'moedas_recompensa')
    list_filter = ('modulo__disciplina', 'tipo')
    inlines = [QuestaoInline]

@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'disciplina', 'ordem')
    list_filter = ('disciplina',)

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ordem', 'ativo', 'total_jogos')
    prepopulated_fields = {'slug': ('nome',)}
    list_filter = ('ativo',)

    def total_jogos(self, obj):
        return obj.jogos.count()

    total_jogos.short_description = 'Jogos'


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'materia', 'ordem', 'ativo')
    prepopulated_fields = {'slug': ('nome',)}