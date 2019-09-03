from django.core.management import call_command
from django.core.management.base import CommandError

from django.test import TestCase
from django.core import mail
from django.conf import settings

from geotrek.authent.factories import StructureFactory
from geotrek.common.factories import AttachmentFactory
from geotrek.common.utils.testdata import get_dummy_uploaded_image
from geotrek.trekking.factories import POIFactory
from geotrek.infrastructure.factories import InfrastructureFactory, InfrastructureTypeFactory
from geotrek.infrastructure.models import InfrastructureType, Infrastructure
from geotrek.core.models import Usage, Path
from geotrek.core.factories import UsageFactory
from geotrek.core.factories import PathFactory

from easy_thumbnails.models import Thumbnail

from StringIO import StringIO
import os


class CommandTests(TestCase):
    def test_command_emails_manager(self):
        call_command('test_managers_emails')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, u'[%s] Test email for managers' % settings.TITLE)

    def test_command_unset_structure(self):
        structure1 = StructureFactory.create(name="coucou")
        structure2 = StructureFactory.create(name="coco")

        infratype1 = InfrastructureTypeFactory.create(label="annyeong", structure=structure1, pictogram=None)
        infratype2 = InfrastructureTypeFactory.create(label="annyeong", structure=structure2, pictogram=None)

        path = PathFactory.create(name="pass")
        usage1 = UsageFactory.create(usage="hello", structure=structure1)
        usage2 = UsageFactory.create(usage="hello", structure=structure2)
        path.usages.add(usage1)
        path.usages.add(usage2)

        infrastructure1 = InfrastructureFactory.create(name='pissenlit', type=infratype1)
        infrastructure2 = InfrastructureFactory.create(name='rhododendron', type=infratype2)

        self.assertEqual(InfrastructureType.objects.count(), 2)
        self.assertEqual(Usage.objects.count(), 2)

        self.assertEqual(infrastructure1.type.label, 'annyeong')
        self.assertEqual(infrastructure1.type.structure.name, 'coucou')
        self.assertEqual(infrastructure2.type.label, 'annyeong')
        self.assertEqual(infrastructure2.type.structure.name, 'coco')

        self.assertEqual(path.usages.count(), 2)
        self.assertEqual(usage1.structure.name, 'coucou')
        self.assertEqual(usage2.structure.name, 'coco')
        output = StringIO()
        call_command('unset_structure', '--all', verbosity=2, stdout=output)
        response = output.getvalue()
        self.assertIn("Create hello", response)
        self.assertEqual(InfrastructureType.objects.count(), 1)
        self.assertEqual(Usage.objects.count(), 1)

        infra = Infrastructure.objects.first()

        self.assertEqual(infra.type.label, 'annyeong')
        self.assertEqual(infra.type.structure, None)

        path_usages = Path.objects.first().usages.first()

        self.assertEqual(path_usages.usage, 'hello')
        self.assertEqual(path_usages.structure, None)

    def test_unset_structure_without_structure_keep_pk(self):
        structure = StructureFactory.create(name="Test")
        infratype_no_structure = InfrastructureTypeFactory.create(label="type1", structure=None, pictogram=None)
        InfrastructureFactory.create(name='infra1', type=infratype_no_structure)
        infratype_structure = InfrastructureTypeFactory.create(label="type2", structure=structure, pictogram=None)
        InfrastructureFactory.create(name='infra2', type=infratype_structure)

        self.assertEqual(InfrastructureType.objects.count(), 2)
        self.assertIsNone(infratype_no_structure.structure)
        self.assertIsNotNone(infratype_structure.structure)
        old_pk_no_structure = infratype_no_structure.pk
        old_pk_structure = infratype_structure.pk
        call_command('unset_structure', '--all', verbosity=0)
        type1 = InfrastructureType.objects.get(label="type1")
        type2 = InfrastructureType.objects.get(label="type1")
        new_pk_no_structure = type1.pk
        new_pk_structure = type2.pk

        self.assertEqual(old_pk_no_structure, new_pk_no_structure)
        self.assertNotEqual(old_pk_structure, new_pk_structure)

        self.assertIsNone(type1.structure)
        self.assertIsNone(type2.structure)

    def test_unset_structure_fail_no_model_not_all(self):
        InfrastructureTypeFactory.create(label="annyeong", structure=None, pictogram=None)
        with self.assertRaises(CommandError) as e:
            call_command('unset_structure', verbosity=0)
        self.assertIn("You should specify model", e.exception.message)

    def test_unset_structure_list(self):
        output = StringIO()
        call_command('unset_structure', '--list', verbosity=0, stdout=output)
        stdout = output.getvalue()
        # Some of them listed.
        self.assertIn('Organism', stdout)
        self.assertIn('File type', stdout)
        self.assertIn('Path source', stdout)

    def test_remove_thumbnails(self):
        output = StringIO()
        self.content = POIFactory(geom='SRID=%s;POINT(1 1)' % settings.SRID)
        self.picture = AttachmentFactory(content_object=self.content,
                                         attachment_file=get_dummy_uploaded_image())
        self.assertIsNotNone(self.content.thumbnail)
        self.assertTrue(os.path.exists(self.picture.attachment_file.path))
        self.assertTrue(os.path.exists("{path}.120x120_q85_crop.png".format(path=self.picture.attachment_file.path)))
        self.assertEqual(Thumbnail.objects.first().name, "{name}.120x120_q85_crop.png".format(
            name=self.picture.attachment_file.name
        ))
        call_command('remove_thumbnails', stdout=output)
        self.assertTrue(os.path.exists(self.picture.attachment_file.path))
        self.assertFalse(os.path.exists("{name}.120x120_q85_crop.png".format(name=self.picture.attachment_file.path)))
        self.assertEqual(Thumbnail.objects.count(), 0)
