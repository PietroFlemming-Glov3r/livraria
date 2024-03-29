from rest_framework.serializers import ModelSerializer, CharField, SerializerMethodField
from rest_framework import serializers

from livraria.models import Compra, ItensCompra


class ItensCompraSerializer(ModelSerializer):
    class Meta:
        model = ItensCompra
        fields = ["livro", "quantidade"]
        depth = 2
        total = SerializerMethodField()
        def get_total(self, instance):
            return instance.quantidade * instance.livro.preco

class CompraSerializer(ModelSerializer):
    class Meta:
        model = Compra
        usuario = CharField(source="usuario.email", read_only=True)
        status = CharField(source="get_status_display", read_only=True)
        fields = ("id", "usuario", "status", "total", "itens")
        itens = ItensCompraSerializer(many=True, read_only=True)
    
    def update(self, instance, validated_data):
        itens = validated_data.pop("itens")
        if itens:
            instance.itens.all().delete()
            for item in itens:
                ItensCompra.objects.create(compra=instance, **item)
        instance.save()
        return instance

    
class CriarEditarItensCompraSerializer(ModelSerializer):
    class Meta:
        model = ItensCompra
        fields = ("livro", "quantidade")

class CriarEditarCompraSerializer(ModelSerializer):
    itens = CriarEditarItensCompraSerializer(many=True) # Aqui mudou

    class Meta:
        model = Compra
        fields = ("usuario", "itens")

    def create(self, validated_data):
        itens = validated_data.pop("itens")
        compra = Compra.objects.create(**validated_data)
        for item in itens:
            item["preco_item"] = item["livro"].preco # Coloca o preço do livro no item de compra
            ItensCompra.objects.create(compra=compra, **item)
        compra.save()
        return compra
    def validate(self, data):
        if data["quantidade"] > data["livro"].quantidade:
            raise serializers.ValidationError(
                {"quantidade": "Quantidade solicitada não disponível em estoque."}
            )
        return data

class ComprasSerializer(ModelSerializer):
    itens = ItensCompraSerializer(many=True)
    usuario = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Compra
        fields = ("id", "usuario", "status", "total", "itens")