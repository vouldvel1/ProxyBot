"""
Генератор QR-кодов
"""

import qrcode
import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)

class QRGenerator:
    """Генератор QR-кодов"""

    @staticmethod
    def generate_qr_code(data: str, size: int = 10, border: int = 4) -> bytes:
        """Генерировать QR-код"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Создаем изображение
            img = qr.make_image(fill_color="black", back_color="white")

            # Конвертируем в bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)

            logger.info("QR-код успешно сгенерирован")
            return img_buffer.getvalue()

        except Exception as e:
            logger.error(f"Ошибка генерации QR-кода: {e}")
            raise

    @staticmethod
    def generate_subscription_qr(subscription_url: str) -> bytes:
        """Генерировать QR-код для подписки"""
        return QRGenerator.generate_qr_code(subscription_url)

qr_generator = QRGenerator()
