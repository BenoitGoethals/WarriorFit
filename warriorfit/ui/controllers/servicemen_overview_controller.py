"""Controller for the Admin 'Servicemen Overview' page — lists all servicemen
with their fields and a column per consent type showing grant status."""

from __future__ import annotations

import pandas as pd

from warriorfit.data.repositories.consent_repository import ConsentRepository
from warriorfit.data.repositories.servicemen_repository import ServicemenRepository
from warriorfit.services.service_consent import CURRENT_CONSENT_VERSIONS


class ServicemenOverviewController:
    """
    ServicemenOverviewController is responsible for managing and generating an overview
    of servicemen and their associated data. It aggregates servicemen information along
    with their consents into a tabular structure for further analysis or reporting purposes.

    The class interacts with `ServicemenRepository` to fetch servicemen details and
    `ConsentRepository` to retrieve active consents. It processes and combines this data
    to produce a structured dataframe containing servicemen information along with their
    consent statuses.

    :ivar servicemen_repository: Repository object for accessing servicemen data. If not provided,
        a default instance of `ServicemenRepository` is created.
    :type servicemen_repository: ServicemenRepository
    :ivar consent_repository: Repository object for accessing consent data. If not provided, a
        default instance of `ConsentRepository` is created.
    :type consent_repository: ConsentRepository
    """

    def __init__(
        self,
        servicemen_repository: ServicemenRepository | None = None,
        consent_repository: ConsentRepository | None = None,
    ):
        self._sm_repo = servicemen_repository or ServicemenRepository()
        self._consent_repo = consent_repository or ConsentRepository()

    async def overview_df(self) -> pd.DataFrame:
        """
        Generates an overview DataFrame containing detailed information about servicemen and their consent statuses.

        This method consolidates data from servicemen and active consents repositories, combines it with relevant attributes,
        and structures it into a pandas DataFrame. The resulting DataFrame includes metadata such as name, rank, unit,
        and additional attributes (e.g., para and ops test status). Furthermore, it includes consent details for different
        consent types.

        :return: A pandas DataFrame containing information about servicemen, including their attributes and consent statuses.
        :rtype: pd.DataFrame
        """
        servicemen = await self._sm_repo.list_all_with_unit() or []
        active = await self._consent_repo.list_all_active() or []

        consent_types = list(CURRENT_CONSENT_VERSIONS.keys())
        granted: dict[str, dict[str, str]] = {}
        for c in active:
            granted.setdefault(c.service_number, {})[c.consent_type] = (
                c.consent_given_at.isoformat() if c.consent_given_at else "yes"
            )

        rows: list[dict] = []
        for s in servicemen:
            row = {
                "Service #": s.service_number,
                "Last Name": s.last_name,
                "First Name": s.first_name,
                "Mail": s.mail,
                "Rank": getattr(s.rank, "name", str(s.rank)),
                "Gender": getattr(s.gender, "name", str(s.gender)),
                "Birthdate": s.birthdate.isoformat() if s.birthdate else "",
                "Unit": s.unit.name if s.unit else "",
                "Para": "yes" if s.para else "no",
                "Ops": "yes" if s.ops_test else "no",
            }
            sm_consents = granted.get(s.service_number, {})
            for ct in consent_types:
                col = ct.replace("_", " ").title()
                row[col] = sm_consents.get(ct, "—")
            rows.append(row)

        if not rows:
            cols = [
                "Service #",
                "Last Name",
                "First Name",
                "Mail",
                "Rank",
                "Gender",
                "Birthdate",
                "Unit",
                "Para",
                "Ops",
            ] + [ct.replace("_", " ").title() for ct in consent_types]
            return pd.DataFrame(columns=cols)
        return pd.DataFrame(rows)
