from django.db import migrations


def preencher_ordem_das_opcoes(apps, schema_editor):
    Questao = apps.get_model('curriculo', 'Questao')
    Opcao = apps.get_model('curriculo', 'Opcao')

    for questao in Questao.objects.all().iterator():
        for ordem, opcao in enumerate(
            Opcao.objects
            .filter(questao_id=questao.id)
            .order_by('id'),
            start=1,
        ):
            if opcao.ordem != ordem:
                Opcao.objects.filter(
                    pk=opcao.pk
                ).update(
                    ordem=ordem
                )


class Migration(migrations.Migration):

    dependencies = [
        (
            'curriculo',
            '0007_alter_disciplina_autor',
        ),
    ]

    operations = [
        migrations.RunPython(
            preencher_ordem_das_opcoes,
            migrations.RunPython.noop,
        ),
    ]
