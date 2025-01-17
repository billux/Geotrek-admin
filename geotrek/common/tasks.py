from __future__ import absolute_import

import importlib
import sys
from celery import Task, shared_task, current_task
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User


class GeotrekImportTask(Task):
    '''
    Task destined to define a on_failure callback
    This callback is called upon exception if need be by celery.
     It trigger the final update state and sets the relevant informations
     to be displayed on the web interface.
    '''
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        filename = kwargs.get('filename', '')
        class_name = kwargs.get('name', '')
        self.update_state(
            task_id,
            'FAILURE',
            {
                'exc_type': type(exc).__name__,
                'exc_message': unicode(exc),
                'filename': filename.split('/').pop(-1),
                'parser': class_name,
                'name': self.name
            }
        )


@shared_task(base=GeotrekImportTask, name='geotrek.common.import-file')
def import_datas(**kwargs):
    class_name = kwargs.get('name')
    filename = kwargs.get('filename')
    module_name = kwargs.get('module')
    encoding = kwargs.get('encoding')
    user_pk = kwargs.get('user', None)
    try:
        module = importlib.import_module(module_name)
        Parser = getattr(module, class_name)
    except ImportError:
        raise ImportError("Failed to import parser class '{0}' from module '{1}'".format(
            class_name, module_name))

    def progress_cb(progress, line, eid):
        current_task.update_state(
            state='PROGRESS',
            meta={
                'current': int(100 * progress),
                'total': 100,
                'filename': filename.split('/').pop(-1),
                'parser': class_name,
                'name': current_task.name
            }
        )
        sys.stdout.write(
            "{progress:02d}%".format(progress=int(100 * progress)))

    user = user_pk and User.objects.get(pk=user_pk)

    try:
        parser = Parser(progress_cb=progress_cb, user=user, encoding=encoding)
        parser.parse(filename)
    except Exception as e:
        raise e

    return {
        'current': 100,
        'total': 100,
        'filename': filename.split('/').pop(-1),
        'parser': class_name,
        'report': parser.report(output_format='html').replace('$celery_id', current_task.request.id),
        'name': current_task.name
    }


@shared_task(base=GeotrekImportTask, name='geotrek.common.import-web')
def import_datas_from_web(**kwargs):
    class_name = kwargs.get('name')
    module_name = kwargs.get('module')
    user_pk = kwargs.get('user', None)
    try:
        module = importlib.import_module(module_name)
        Parser = getattr(module, class_name)
    except ImportError:
        raise ImportError("Failed to import parser class '{0}' from module '{1}'".format(
            class_name, module_name))

    def progress_cb(progress, line, eid):
        current_task.update_state(
            state='PROGRESS',
            meta={
                'current': int(100 * progress),
                'total': 100,
                'filename': _("Import from web."),
                'parser': class_name,
                'name': current_task.name
            }
        )
        sys.stdout.write(
            "{progress:02d}%".format(progress=int(100 * progress)))

    user = user_pk and User.objects.get(pk=user_pk)

    try:
        parser = Parser(progress_cb=progress_cb, user=user)
        parser.parse()
    except Exception as e:
        raise e

    return {
        'current': 100,
        'total': 100,
        'filename': _("Import from web."),
        'parser': class_name,
        'report': parser.report(output_format='html').replace('$celery_id', current_task.request.id),
        'name': current_task.name
    }
