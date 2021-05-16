from django.http import HttpRequest


def get_visitor_ip_address(request: HttpRequest) -> str:
    """
    Gets the IP address of current visitor.

    :param request: the HttpRequest object.
    :returns: the IP address.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
