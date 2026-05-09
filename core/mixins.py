class ImageCleanupMixin:
    """
    Apaga automaticamente a imagem antiga do storage quando uma nova é enviada.
    Subclasses devem definir `image_fields` com os nomes dos campos de imagem.
    """
    image_fields: list[str] = []

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = self.__class__.objects.get(pk=self.pk)
                for field_name in self.image_fields:
                    old_file = getattr(old, field_name)
                    new_file = getattr(self, field_name)
                    if old_file and old_file.name != (new_file.name if new_file else None):
                        try:
                            old_file.delete(save=False)
                        except Exception:
                            pass
            except self.__class__.DoesNotExist:
                pass
        super().save(*args, **kwargs)
