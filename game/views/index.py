from django.shortcuts import render

def index(request):
    return render(request, 'multimatch/web.html')
