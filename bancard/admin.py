from django.contrib import admin
from .models import Card, Transaction, Reversion


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    readonly_fields = (
        "last4",
        "exp_year",
        "exp_month",
        "brand",
        "type",
        "user",
        "is_active",
        "is_default",
    )
    list_display = ("user", "is_active", "is_default")
    list_filter = ("is_active", "is_default")
    search_fields = ("user",)
    ordering = ("-created_at",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    readonly_fields = (
        "id",
        "user",
        "payment",
        "status",
        "amount",
        "customer_ip_address",
        "tx_description",
        "response_description",
        "authorization_code",
        "created_at",
        "updated_at",
        "token",
        "raw_response",
    )
    list_display = ("id", "user", "amount", "status", "authorization_code")
    list_filter = ("status",)
    search_fields = ("user", "tx_description", "authorization_code")
    ordering = ("-created_at",)


class TransactionInline(admin.TabularInline):
    model = Transaction
    readonly_fields = (
        "id",
        "status",
        "tx_description",
        "response_description",
        "authorization_code",
        "created_at",
    )
    ordering = ("-created_at",)
    extra = 0
    min_num = 0
    max_num = 0
    can_delete = False


@admin.register(Reversion)
class ReversionAdmin(admin.ModelAdmin):
    list_display = ("id", "transaction", "status", "response_description")
    search_fields = ("transaction__id", "transaction__authorization_code")
    readonly_fields = ("status", "transaction", "response_description", "raw_response")
