from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from curriculo.models import Fase


class PerfilUsuario(models.Model):
    XP_POR_NIVEL = 200
    VIDAS_MAXIMAS = 5

    TIPO_CHOICES = [
        ('aluno', 'Aluno (Jogador)'),
        ('professor', 'Professor (Criador)'),
    ]

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil',
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='aluno',
    )

    # ========================================================
    # GAMIFICAÇÃO
    # ========================================================

    xp_total = models.PositiveIntegerField(
        default=0
    )

    moedas = models.PositiveIntegerField(
        default=0
    )

    vidas = models.PositiveIntegerField(
        default=5
    )

    # ========================================================
    # PERSONALIZAÇÃO
    # ========================================================

    TEMAS = [
        ('tema-padrao', 'Noite Estrelada'),
        ('tema-floresta', 'Floresta Encantada'),
        ('tema-deserto', 'Deserto Escaldante'),
        ('tema-masmorra', 'Masmorra Sombria'),
        ('tema-aurora', 'Aurora Boreal'),
        ('tema-oceano', 'Oceano Profundo'),
    ]

    APARENCIA_CHOICES = [
        ('sistema', 'Seguir preferência do sistema'),
        ('claro', 'Modo claro'),
        ('escuro', 'Modo escuro'),
    ]

    tema_fundo = models.CharField(
        max_length=50,
        choices=TEMAS,
        default='tema-padrao',
    )

    aparencia_interface = models.CharField(
        max_length=20,
        choices=APARENCIA_CHOICES,
        default='escuro',
    )

    def __str__(self):
        return (
            f"{self.usuario.username} "
            f"({self.get_tipo_display()})"
        )

    @property
    def is_professor(self):
        return self.tipo == 'professor'

    @property
    def nivel(self):
        return (self.xp_total // self.XP_POR_NIVEL) + 1

    @property
    def xp_no_nivel(self):
        return self.xp_total % self.XP_POR_NIVEL

    @property
    def xp_proximo_nivel(self):
        return self.nivel * self.XP_POR_NIVEL

    @property
    def xp_faltante(self):
        return max(
            0,
            self.xp_proximo_nivel - self.xp_total,
        )

    @property
    def progresso_nivel(self):
        return min(
            100,
            round(
                (self.xp_no_nivel / self.XP_POR_NIVEL) * 100
            ),
        )


class ItemLoja(models.Model):
    TIPO_ITEM = [
        ('skin', 'Skin de Avatar'),
        ('tema', 'Tema da Trilha'),
        ('vida', 'Recarga de Vidas'),
    ]

    nome = models.CharField(
        max_length=100
    )

    descricao = models.TextField(
        blank=True
    )

    preco_moedas = models.PositiveIntegerField()

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_ITEM,
        default='skin',
    )

    icone_ou_imagem = models.ImageField(
        upload_to='itens_loja/',
        blank=True,
        null=True,
    )

    def __str__(self):
        return (
            f"{self.nome} "
            f"({self.preco_moedas} moedas)"
        )


class ItemComprado(models.Model):
    perfil = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='itens',
    )

    item = models.ForeignKey(
        ItemLoja,
        on_delete=models.CASCADE,
    )

    equipado = models.BooleanField(
        default=False
    )

    data_aquisicao = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['perfil', 'item'],
                name='unique_item_por_perfil',
            )
        ]

    def __str__(self):
        return (
            f"{self.perfil.usuario.username} "
            f"- {self.item.nome}"
        )


class ProgressoFase(models.Model):
    perfil = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='progressos',
    )

    fase = models.ForeignKey(
        Fase,
        on_delete=models.CASCADE,
    )

    concluida = models.BooleanField(
        default=False
    )

    erros = models.PositiveIntegerField(
        default=0
    )

    tentativas = models.PositiveIntegerField(
        default=0
    )

    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
    )

    # ========================================================
    # NOVOS INDICADORES DE DESEMPENHO
    # ========================================================

    melhor_aproveitamento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=(
            "Maior percentual obtido pelo aluno "
            "nesta fase."
        ),
    )

    data_ultima_tentativa = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['perfil', 'fase'],
                name='unique_progresso_por_perfil_fase',
            )
        ]

    def __str__(self):
        status = (
            "Concluída"
            if self.concluida
            else "Em andamento"
        )

        return (
            f"{self.perfil.usuario.username} "
            f"- {self.fase.titulo} "
            f"[{status}]"
        )


class ProgressoModulo(models.Model):
    """
    Estado de um módulo para um aluno.

    O primeiro módulo é liberado automaticamente. Ao concluir
    um módulo, o aluno recebe uma chave para o próximo módulo.
    A chave permanece disponível até que o aluno a utilize no
    cadeado do módulo correspondente.
    """

    perfil = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='progressos_modulo',
    )

    modulo = models.ForeignKey(
        'curriculo.Modulo',
        on_delete=models.CASCADE,
        related_name='progressos_aluno',
    )

    desbloqueado = models.BooleanField(
        default=False,
    )

    chave_disponivel = models.BooleanField(
        default=False,
    )

    concluido = models.BooleanField(
        default=False,
    )

    data_desbloqueio = models.DateTimeField(
        null=True,
        blank=True,
    )

    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['perfil', 'modulo'],
                name='unique_progresso_por_perfil_modulo',
            )
        ]

    def __str__(self):
        status = (
            'Concluído'
            if self.concluido
            else 'Desbloqueado'
            if self.desbloqueado
            else 'Chave disponível'
            if self.chave_disponivel
            else 'Bloqueado'
        )

        return (
            f"{self.perfil.usuario.username} - "
            f"{self.modulo.titulo} [{status}]"
        )


class TentativaFase(models.Model):
    """
    Representa UMA execução completa de uma fase.

    Diferente de ProgressoFase, que representa o estado atual
    do aluno, esta tabela preserva o histórico das tentativas.
    """

    perfil = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='tentativas_fase',
    )

    fase = models.ForeignKey(
        Fase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tentativas',
    )

    # Snapshot para preservar o histórico mesmo que a fase
    # seja excluída ou tenha seu título alterado depois.
    fase_titulo_snapshot = models.CharField(
        max_length=150
    )

    iniciada_em = models.DateTimeField(
        auto_now_add=True
    )

    finalizada_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    total_questoes = models.PositiveIntegerField(
        default=0
    )

    acertos = models.PositiveIntegerField(
        default=0
    )

    erros = models.PositiveIntegerField(
        default=0
    )

    aproveitamento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Percentual de aproveitamento da tentativa.",
    )

    aprovado = models.BooleanField(
        default=False
    )

    xp_ganho = models.PositiveIntegerField(
        default=0
    )

    moedas_ganhas = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        ordering = ['-iniciada_em']

    def __str__(self):
        status = (
            "Aprovado"
            if self.aprovado
            else "Não concluído"
        )

        return (
            f"{self.perfil.usuario.username} - "
            f"{self.fase_titulo_snapshot} - "
            f"{self.aproveitamento}% - "
            f"{status}"
        )


class RespostaTentativa(models.Model):
    """
    Guarda a resposta dada para cada questão dentro de uma
    TentativaFase.
    """

    tentativa = models.ForeignKey(
        TentativaFase,
        on_delete=models.CASCADE,
        related_name='respostas',
    )

    questao = models.ForeignKey(
        'curriculo.Questao',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='respostas_historicas',
    )

    opcao_escolhida = models.ForeignKey(
        'curriculo.Opcao',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='respostas_historicas',
    )

    # Snapshots para preservar o conteúdo histórico.
    texto_questao_snapshot = models.TextField()

    texto_opcao_snapshot = models.CharField(
        max_length=255
    )

    correta = models.BooleanField(
        default=False
    )

    respondida_em = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['id']

        constraints = [
            models.UniqueConstraint(
                fields=['tentativa', 'questao'],
                name='unique_questao_por_tentativa',
            )
        ]

    def __str__(self):
        status = (
            "Correta"
            if self.correta
            else "Incorreta"
        )

        return (
            f"Tentativa #{self.tentativa.id} - "
            f"{status}"
        )


@receiver(post_save, sender=User)
def criar_perfil(sender, instance, created, **kwargs):
    """
    Cria automaticamente o PerfilUsuario quando um User novo
    é criado.
    """

    if created:
        PerfilUsuario.objects.get_or_create(
            usuario=instance
        )