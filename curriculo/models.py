from django.db import models
from django.contrib.auth.models import User

class Disciplina(models.Model):
    TEMAS = [
        ('tema-padrao', 'Noite Estrelada'),
        ('tema-floresta', 'Floresta Encantada'),
        ('tema-deserto', 'Deserto Escaldante'),
        ('tema-masmorra', 'Masmorra Sombria'),
        ('tema-aurora', 'Aurora Boreal'),
        ('tema-oceano', 'Oceano Profundo'),
    ]
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    descricao = models.TextField(blank=True)
    icone = models.CharField(max_length=50, default="book")
    ordem = models.PositiveIntegerField(default=1)
    ativo = models.BooleanField(default=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    tema = models.CharField(max_length=30, choices=TEMAS, default='tema-padrao')

    class Meta:
        ordering = ['ordem']
        verbose_name_plural = "Disciplinas"

    def __str__(self):
        return self.nome

class Modulo(models.Model):
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='modulos')
    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    ordem = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['ordem']
        verbose_name_plural = "Módulos"

    def __str__(self):
        return f"{self.disciplina.nome} - {self.titulo}"

class Fase(models.Model):
    TIPO_CHOICES = [
        ('teoria', 'Conteúdo Teórico'),
        ('quiz', 'Quiz / Exercícios'),
        ('desafio', 'Desafio de Recuperação'),
    ]
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, related_name='fases')
    titulo = models.CharField(max_length=150)
    ordem = models.PositiveIntegerField(default=1)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='quiz')
    xp_recompensa = models.PositiveIntegerField(default=50)
    moedas_recompensa = models.PositiveIntegerField(default=10)
    deslocamento_y = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordem']

    def __str__(self):
        return f"{self.modulo.titulo} - Fase {self.ordem}: {self.titulo}"

class Questao(models.Model):
    fase = models.ForeignKey(Fase, on_delete=models.CASCADE, related_name='questoes')
    enunciado = models.TextField()
    explicacao_erro = models.TextField(blank=True)

    class Meta:
        verbose_name = "Questão"
        verbose_name_plural = "Questões"

    def __str__(self):
        return f"Questão {self.id} ({self.fase.titulo})"

class Opcao(models.Model):
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, related_name='opcoes')
    texto = models.CharField(max_length=255)
    e_correta = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Opção"
        verbose_name_plural = "Opções"

    def __str__(self):
        return self.texto