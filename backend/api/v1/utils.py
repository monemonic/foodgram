import reportlab
import io
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.generic.base import RedirectView
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

from foodgram.models import Recipe


class SearchRedirectView(RedirectView):
    """Перенаправление коротких ссылок на страницу рецепта."""

    def get_redirect_url(self, *args, **kwargs):
        full_path = (self.request.get_full_path()).replace("/s", "", 1)
        link = get_object_or_404(Recipe, short_url=full_path)
        url = self.request.build_absolute_uri(f"/api/recipes/{link.pk}/")
        return url


def create_shopping_cart_pdf(shopping_cart_ingredients):
    """Создание списка покупок для последующей отправки."""
    LAST_RECODR_IN_PAGE = 23
    reportlab.rl_config.TTFSearchPath.append(str(settings.BASE_DIR) + "fonts/")
    pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))
    buffer = io.BytesIO()
    shopping_cart = canvas.Canvas(buffer)

    shopping_cart.setFont("DejaVuSans", 15)
    shopping_cart.drawString(230, 800, "Список покупок")

    shopping_cart.setFont("DejaVuSans", 12)
    count = 1
    position_record = 770

    for ing in shopping_cart_ingredients:
        shopping_cart.drawString(
            50, position_record, f"{count}. {ing[0]} - {ing[2]}{ing[1]}"
        )
        if count == LAST_RECODR_IN_PAGE:
            shopping_cart.showPage()
        position_record -= 30
        count += 1
        if count == 23:
            position_record = 770
            shopping_cart.showPage()

    shopping_cart.showPage()
    shopping_cart.save()
    buffer.seek(0)

    return buffer
