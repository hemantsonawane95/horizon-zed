from django.views import generic


class IndexView(generic.TemplateView):
    template_name = 'vprotect/task_console/index.html'
