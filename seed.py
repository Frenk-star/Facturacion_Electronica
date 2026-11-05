"""Entrada compatible para ejecutar la carga de demostración existente."""

import os


def run_seeder():
    """Delega al comando idempotente seed_demo conservando esta entrada pública."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FacturacionSunat.settings")
    import django

    django.setup()
    from django.core.management import call_command

    call_command("seed_demo")


if __name__ == "__main__":
    run_seeder()
