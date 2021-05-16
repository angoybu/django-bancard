import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .operations import callback


@csrf_exempt
def callback_view(request):
    if request.method == "POST":
        try:
            data = json.loads(str(request.body, "utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        response, status = callback(data)
        return JsonResponse(response, status=status)
    else:
        return JsonResponse({"error": "Method not allowed."}, status=405)
