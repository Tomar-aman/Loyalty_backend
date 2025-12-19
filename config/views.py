from django.http import HttpResponse

def caddy_ask(request):
    domain = request.GET.get("domain")

    if not domain:
        return HttpResponse("missing domain", status=400)

    # ALLOW ALL for now (we secure later)
    return HttpResponse("ok", status=200)
