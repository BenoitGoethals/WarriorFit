from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from warriorfit.data.model.db_model import Role  # type: ignore[attr-defined]


@dataclass(frozen=True)
class PageSpec:
    """
    Defines the PageSpec class which represents specifications and configurations for a page
    in a system or application.

    This class provides attributes to configure the UI factory, server factory, allowed roles,
    and information about the page's tab and group. The class is immutable due to the frozen=True
    dataclass decorator, ensuring the integrity of its instances.

    :ivar tab: Represents the name of the tab where the page belongs.
    :type tab: str
    :ivar group: Specifies the group to which the page belongs, such as "root", "Physical
                 Tests", "Cross/Runs", "Admin", or "About".
    :type group: str
    :ivar ui_factory: A callable responsible for generating the UI component for the page. It
                      takes no arguments and returns an optional UI component.
    :type ui_factory: Callable[[], Optional[Any]]
    :ivar server_factory: A callable responsible for creating the server logic for the page,
                          accepting three arguments. It can also be None if no server-side
                          logic is needed for the page.
    :type server_factory: Callable[[Any, Any, Any], Any] | None
    :ivar allowed_roles: A set of roles that are allowed to access the page. This ensures that only
                         permitted roles can interact with the page's functionalities.
    :type allowed_roles: set[Role]
    """

    tab: str
    group: str  # "root" | "Physical Tests" | "Cross/Runs" | "Admin" | "About"
    ui_factory: Callable[[], Any | None]
    server_factory: Callable[[Any, Any, Any], Any] | None
    allowed_roles: set[Role]


def get_pages() -> list[PageSpec]:
    """Return all page specs. Page modules are imported lazily so this can only be
    called after the DI container has been wired."""
    from warriorfit.ui.pages import (
        about,
        auditlog_events,
        combat_test,
        cross,
        cross_planning,
        cross_statics,
        dashboard_own_unit,
        functional_test,
        ind_test_show,
        march,
        mfft_eval,
        my_progress,
        own_unit,
        phef,
        privacy,
        reports,
        reserve_fitness_room,
        servicemen_overview,
        sessions,
        settings,
        status_application,
        status_login_user,
        status_tests,
        swim_test,
        test_analytics,
        usermanagement,
    )

    # To change visibility, modify `allowed_roles` here — not in navbar code.
    return [
        # Root-level pages
        PageSpec(
            tab="Welcome",
            group="root",
            ui_factory=status_login_user.get_ui,
            server_factory=status_login_user.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="My Progress",
            group="root",
            ui_factory=my_progress.get_ui,
            server_factory=my_progress.server,
            allowed_roles={Role.USER},
        ),
        PageSpec(
            tab="Dashboard",
            group="root",
            ui_factory=dashboard_own_unit.get_ui,
            server_factory=dashboard_own_unit.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="Status Unit",
            group="Physical Tests",
            ui_factory=own_unit.get_ui,
            server_factory=own_unit.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="Individual",
            group="Physical Tests",
            ui_factory=ind_test_show.get_ui,
            server_factory=ind_test_show.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="Reports",
            group="Physical Tests",
            ui_factory=reports.get_ui,
            server_factory=reports.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="Reserve Sport Area",
            group="root",
            ui_factory=reserve_fitness_room.get_ui,
            server_factory=reserve_fitness_room.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="Sessions",
            group="root",
            ui_factory=sessions.get_ui,
            server_factory=sessions.server,
            allowed_roles={Role.PLANNER},
        ),
        # Physical Tests (menu)
        PageSpec(
            tab="PHEF Tests",
            group="Physical Tests",
            ui_factory=phef.get_ui,
            server_factory=phef.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="Combat Tests",
            group="Physical Tests",
            ui_factory=combat_test.get_ui,
            server_factory=combat_test.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="MFFT Eval",
            group="Physical Tests",
            ui_factory=mfft_eval.get_ui,
            server_factory=mfft_eval.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="Analytics",
            group="Physical Tests",
            ui_factory=test_analytics.get_ui,
            server_factory=test_analytics.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="Functional Tests",
            group="Physical Tests",
            ui_factory=functional_test.get_ui,
            server_factory=functional_test.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="Swimming Tests",
            group="Physical Tests",
            ui_factory=swim_test.get_ui,
            server_factory=swim_test.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="March",
            group="Physical Tests",
            ui_factory=march.get_ui,
            server_factory=march.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="PHEF Not done",
            group="Physical Tests",
            ui_factory=status_tests.get_ui,
            server_factory=status_tests.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="Sessions",
            group="Physical Tests",
            ui_factory=sessions.get_ui,
            server_factory=sessions.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        # Cross/Runs (menu)
        PageSpec(
            tab="Cross Statics",
            group="Cross/Runs",
            ui_factory=cross_statics.get_ui,
            server_factory=cross_statics.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="Cross Planning",
            group="Cross/Runs",
            ui_factory=cross_planning.get_ui,
            server_factory=cross_planning.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        PageSpec(
            tab="Cross",
            group="Cross/Runs",
            ui_factory=cross.get_ui,
            server_factory=cross.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI},
        ),
        # Admin (menu)
        PageSpec(
            tab="Audit Logs",
            group="Admin",
            ui_factory=auditlog_events.get_ui,
            server_factory=auditlog_events.server,
            allowed_roles={Role.ADMIN},
        ),
        PageSpec(
            tab="User Management",
            group="Admin",
            ui_factory=usermanagement.get_ui,
            server_factory=usermanagement.server,
            allowed_roles={Role.ADMIN},
        ),
        PageSpec(
            tab="Settings",
            group="Admin",
            ui_factory=settings.get_ui,
            server_factory=settings.server,
            allowed_roles={Role.ADMIN},
        ),
        PageSpec(
            tab="Status Application",
            group="Admin",
            ui_factory=status_application.get_ui,
            server_factory=status_application.server,
            allowed_roles={Role.ADMIN},
        ),
        PageSpec(
            tab="Servicemen Overview",
            group="Admin",
            ui_factory=servicemen_overview.get_ui,
            server_factory=servicemen_overview.server,
            allowed_roles={Role.ADMIN},
        ),
        # About (menu)
        PageSpec(
            tab="About",
            group="About",
            ui_factory=about.get_ui,
            server_factory=about.server,
            allowed_roles={Role.ADMIN, Role.PTI, Role.APTI, Role.GUEST, Role.PLANNER},
        ),
        PageSpec(
            tab="Privacy",
            group="About",
            ui_factory=privacy.get_ui,
            server_factory=privacy.server,
            allowed_roles={
                Role.ADMIN,
                Role.PTI,
                Role.APTI,
                Role.GUEST,
                Role.PLANNER,
                Role.USER,
            },
        ),
    ]


def pages_for_role(role: Role | None) -> list[PageSpec]:
    if role is None:
        return []
    return [p for p in get_pages() if role in p.allowed_roles]
