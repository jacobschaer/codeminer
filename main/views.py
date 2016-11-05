from django.shortcuts import render
from main.models.repository import RepositoryForm
from main.models import Repository, History, Change
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

def repository(request, repository_id):
    # First, find last "alive" revisions of all files
    alive_results = Change.objects.filter(
                        changeset__repository_id = repository_id,
                        current_file__isnull=False,
                        history__isnull=False).order_by('history', '-current_file__revision').values(
                            'current_file__path', 'history').distinct()

    # Now, find the "dead" files
    dead_results = Change.objects.filter(
            changeset__repository_id = repository_id,
            current_file__isnull=True,
            history__isnull=False).order_by('history', '-previous_file__revision').values('history').distinct()

    dead_histories = [x['history'] for x in dead_results]

    # Produce final list
    results = []
    last_seen_history = None

    for query_result in alive_results:
        history = query_result['history']
        # We're going reverse chronologically, so the first time we see a 
        # history we also have the latest file name
        if history != last_seen_history:
            result = {'id' : history, 'path' : query_result['current_file__path']}
            if history in dead_histories:
                result['state'] = 'dead'
            else:
                result['state'] = 'alive'
            results.append(result)
            last_seen_history = history
    return render(request, 'main/repository.html', {'histories': results})
