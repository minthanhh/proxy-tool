import csv
import io
from typing import Optional

import structlog

from easyproxy.pool.models import ProxyCreate, ProxyProtocol

logger = structlog.get_logger(__name__)


def parse_txt(content: str) -> list[ProxyCreate]:
    proxies: list[ProxyCreate] = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(":")
        if len(parts) < 2:
            logger.warning("Invalid TXT line", line=line_no, content=stripped)
            continue
        address = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            logger.warning("Invalid port in TXT line", line=line_no, content=stripped)
            continue
        protocol = ProxyProtocol.HTTP
        username: Optional[str] = None
        password: Optional[str] = None
        region: Optional[str] = None
        if len(parts) >= 3 and parts[2]:
            try:
                protocol = ProxyProtocol(parts[2].lower())
            except ValueError:
                logger.warning("Invalid protocol in TXT line", line=line_no, content=stripped)
                continue
        if len(parts) >= 4 and parts[3]:
            username = parts[3]
        if len(parts) >= 5 and parts[4]:
            password = parts[4]
        if len(parts) >= 6 and parts[5]:
            region = parts[5]
        try:
            proxies.append(
                ProxyCreate(
                    address=address,
                    port=port,
                    protocol=protocol,
                    username=username,
                    password=password,
                    region=region,
                    source="file",
                )
            )
        except ValueError as e:
            logger.warning("Invalid proxy in TXT line", line=line_no, error=str(e))
            continue
    return proxies


def parse_csv(content: str) -> list[ProxyCreate]:
    proxies: list[ProxyCreate] = []
    reader = csv.reader(io.StringIO(content))
    headers: list[str] = []
    for line_no, row in enumerate(reader, start=1):
        if line_no == 1:
            first = row[0].strip().lower() if row else ""
            if first in ("ip", "address", "host"):
                headers = [h.strip().lower() for h in row]
                continue
        if len(row) < 2:
            logger.warning("Invalid CSV row", line=line_no)
            continue
        if headers:
            row_map = dict(zip(headers, row))
            address = row_map.get("ip") or row_map.get("address") or row_map.get("host") or ""
            port_str = row_map.get("port", "")
            protocol_str = row_map.get("protocol", "")
            username = row_map.get("username") or None
            password = row_map.get("password") or None
            region = row_map.get("region") or None
        else:
            address = row[0].strip()
            port_str = row[1].strip()
            protocol_str = row[2].strip() if len(row) >= 3 else ""
            username = row[3].strip() if len(row) >= 4 and row[3].strip() else None
            password = row[4].strip() if len(row) >= 5 and row[4].strip() else None
            region = row[5].strip() if len(row) >= 6 and row[5].strip() else None

        if not address:
            logger.warning("Empty address in CSV row", line=line_no)
            continue
        try:
            port = int(port_str)
        except (ValueError, TypeError):
            logger.warning("Invalid port in CSV row", line=line_no)
            continue
        protocol = ProxyProtocol.HTTP
        if protocol_str:
            try:
                protocol = ProxyProtocol(protocol_str.lower())
            except ValueError:
                logger.warning("Invalid protocol in CSV row", line=line_no)
                continue
        try:
            proxies.append(
                ProxyCreate(
                    address=address,
                    port=port,
                    protocol=protocol,
                    username=username or None,
                    password=password or None,
                    region=region or None,
                    source="file",
                )
            )
        except ValueError as e:
            logger.warning("Invalid proxy in CSV row", line=line_no, error=str(e))
            continue
    return proxies


class Importer:
    def __init__(self, manager):
        self._manager = manager
        self.imported = 0
        self.skipped = 0
        self.errors: list[str] = []

    async def import_txt(self, content: str) -> dict:
        self.imported = 0
        self.skipped = 0
        self.errors = []
        proxies = parse_txt(content)
        for proxy in proxies:
            try:
                await self._manager.add(proxy)
                self.imported += 1
            except ValueError:
                self.skipped += 1
            except Exception as e:
                self.errors.append(str(e))
        logger.info("Import TXT complete", imported=self.imported, skipped=self.skipped, errors=len(self.errors))
        return self._result()

    async def import_csv(self, content: str) -> dict:
        self.imported = 0
        self.skipped = 0
        self.errors = []
        proxies = parse_csv(content)
        for proxy in proxies:
            try:
                await self._manager.add(proxy)
                self.imported += 1
            except ValueError:
                self.skipped += 1
            except Exception as e:
                self.errors.append(str(e))
        logger.info("Import CSV complete", imported=self.imported, skipped=self.skipped, errors=len(self.errors))
        return self._result()

    def _result(self) -> dict:
        return {
            "imported": self.imported,
            "skipped": self.skipped,
            "errors": self.errors,
        }
