import django
# Temporary fix for graphene_django
django.utils.encoding.force_text = django.utils.encoding.force_str
