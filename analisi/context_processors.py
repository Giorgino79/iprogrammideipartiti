from .models import Partito


def partiti_header(request):
    return {'partiti_header': Partito.objects.all()}
