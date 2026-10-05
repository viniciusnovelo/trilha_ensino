from django.db import migrations, models
import django.db.models.deletion


def criar_materias_iniciais(apps, schema_editor):
    Materia = apps.get_model('curriculo', 'Materia')
    Disciplina = apps.get_model('curriculo', 'Disciplina')

    materias = [
        {
            'nome': 'Matemática',
            'slug': 'matematica',
            'descricao': 'Funções, álgebra, geometria e raciocínio matemático.',
            'icone': 'calculator',
            'ordem': 1,
            'ativo': True,
        },
        {
            'nome': 'Física',
            'slug': 'fisica',
            'descricao': 'Movimento, forças, energia e fenômenos físicos.',
            'icone': 'atom',
            'ordem': 2,
            'ativo': True,
        },
        {
            'nome': 'Geografia',
            'slug': 'geografia',
            'descricao': 'Espaço geográfico, sociedade, natureza e território.',
            'icone': 'globe',
            'ordem': 3,
            'ativo': True,
        },
        {
            'nome': 'Biologia',
            'slug': 'biologia',
            'descricao': 'Vida, células, genética, ecologia e evolução.',
            'icone': 'leaf',
            'ordem': 4,
            'ativo': True,
        },
    ]

    objetos = {}

    for dados in materias:
        materia, _ = Materia.objects.update_or_create(
            slug=dados['slug'],
            defaults=dados,
        )
        objetos[dados['slug']] = materia

    # Mantém o jogo de exemplo já existente dentro da matéria correta.
    try:
        mestre = Disciplina.objects.get(slug='mestre-das-funcoes')
        mestre.materia = objetos['matematica']
        mestre.save(update_fields=['materia'])
    except Disciplina.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('curriculo', '0004_alter_disciplina_tema'),
    ]

    operations = [
        migrations.CreateModel(
            name='Materia',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'nome',
                    models.CharField(max_length=100),
                ),
                (
                    'slug',
                    models.SlugField(unique=True),
                ),
                (
                    'descricao',
                    models.TextField(blank=True),
                ),
                (
                    'icone',
                    models.CharField(
                        default='book',
                        max_length=50,
                    ),
                ),
                (
                    'ordem',
                    models.PositiveIntegerField(default=1),
                ),
                (
                    'ativo',
                    models.BooleanField(default=True),
                ),
            ],
            options={
                'verbose_name': 'Matéria',
                'verbose_name_plural': 'Matérias',
                'ordering': ['ordem', 'id'],
            },
        ),
        migrations.AddField(
            model_name='disciplina',
            name='materia',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='jogos',
                to='curriculo.materia',
            ),
        ),
        migrations.RunPython(
            criar_materias_iniciais,
            migrations.RunPython.noop,
        ),
    ]
