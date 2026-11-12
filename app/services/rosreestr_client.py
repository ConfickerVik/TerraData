import asyncio
import logging
import os
import random
import uuid
from typing import Any

import httpx
from fake_useragent import UserAgent

from app.services.rosreestr_converter import RosreestrPdfConverter

logger = logging.getLogger(__name__)


class RosreestrClient:
    def __init__(self, pdf_converter: RosreestrPdfConverter | None = None):
        """
        Client for interacting with Rosreestr LK to get property information.
        :param pdf_converter: An instance of RosreestrPdfConverter to reuse its captcha solver.
        """
        self.base_url = "https://lk.rosreestr.ru/account-back"
        self.pdf_converter = pdf_converter
        self.ua = UserAgent()
        self.max_tries = 5

    def _get_random_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://lk.rosreestr.ru/",
            "Origin": "https://lk.rosreestr.ru",
        }

    def _normalize_cadastral_number(self, cad_num: str) -> str:
        """
        Implements the specific normalization logic from ownershipApi:
        removes leading zeros from the last part of the cadastral number.
        """
        parts = cad_num.split(":")
        if len(parts) < 4:
            return cad_num

        last_part = parts[-1]
        # Logic from ownershipApi: strip leading zeros if the first part length > 2
        if len(parts[0]) > 2:
            # Find first non-zero character in last part
            stripped_last_part = last_part.lstrip("0")
            if not stripped_last_part:  # Case where last part is all zeros
                stripped_last_part = "0"
            parts[-1] = stripped_last_part

        return ":".join(parts)

    async def _solve_captcha(
        self, client: httpx.AsyncClient, headers: dict[str, str]
    ) -> str | None:
        """
        Gets captcha image and solves it using the shared pdf_converter model.
        """
        if not self.pdf_converter:
            self.pdf_converter = RosreestrPdfConverter()

        try:
            resp = await client.get(f"{self.base_url}/captcha.png", headers=headers)
            if resp.status_code != 200:
                return None

            captcha_path = f"captcha_{uuid.uuid4()}.png"
            with open(captcha_path, "wb") as f:
                f.write(resp.content)

            # Use the OCR logic from the converter
            captcha_text = self.pdf_converter.solve_captcha(captcha_path)

            if os.path.exists(captcha_path):
                os.remove(captcha_path)

            return captcha_text
        except Exception as e:
            logger.error(f"Captcha solve error: {e}")
            return None

    async def get_full_info(self, cad_num: str) -> dict[str, Any] | None:
        """
        Gets complete information about a property by its cadastral number.
        Returns the raw JSON response from Rosreestr.
        """
        normalized_cad = self._normalize_cadastral_number(cad_num)

        async with httpx.AsyncClient(verify=False) as client:
            for attempt in range(self.max_tries):
                headers = self._get_random_headers()

                # 1. Solve Captcha
                captcha = await self._solve_captcha(client, headers)
                if not captcha:
                    continue

                # 2. Prepare Payload
                payload = {
                    "cadNumbers": [normalized_cad],
                    "captcha": captcha,
                    "filterType": "cadastral",
                }

                try:
                    # 3. Request Information
                    response = await client.post(
                        f"{self.base_url}/on", json=payload, headers=headers, timeout=30.0
                    )

                    if response.status_code == 200:
                        content = response.text
                        if "Wrong captcha" in content or "Произошла ошибка получения" in content:
                            logger.info(
                                f"Attempt {attempt + 1}: Wrong captcha or Rosreestr error. Retrying..."
                            )
                            continue

                        return response.json()

                    logger.warning(f"Attempt {attempt + 1}: Received status {response.status_code}")
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed: {e}")

                # Small delay between retries to avoid rate limiting
                await asyncio.sleep(random.uniform(1.0, 3.0))

            logger.error(f"Failed to get info for {cad_num} after {self.max_tries} attempts")
            return None

    async def search_by_address(self, address: str) -> dict[str, Any] | None:
        """
        Search for cadastral numbers by address.
        """
        async with httpx.AsyncClient(verify=False) as client:
            headers = self._get_random_headers()
            url = f"{self.base_url}/address/search?term={address}&objType=all"
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.json()
            except Exception as e:
                logger.error(f"Address search error: {e}")
            return None
