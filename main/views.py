from django.shortcuts import render
from main.models.repository import Repository, RepositoryForm
from django.http import HttpResponseRedirect

def index(request):
    context = {
        'repositories': [x for x in Repository.objects.all()]
    }
    return render(request, 'main/index.html', context)

def add_repository(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RepositoryForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            form.save()
            return HttpResponseRedirect('/')
    else:
        form = RepositoryForm()
    return render(request, 'main/add_repository.html', {'form': form})

def delete_repository(request, repository_id):
    item = Repository.objects.get(pk=repository_id)
    item.delete()
    return HttpResponseRedirect('/')


def repository(request):
    pass