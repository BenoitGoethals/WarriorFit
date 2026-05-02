"""
Dependency Injection Container for WarriorFit application.
"""

from dependency_injector import containers, providers

from warriorfit.config.application_config import ApplicationConfig
from warriorfit.data.repositories.consent_repository import ConsentRepository
from warriorfit.data.repositories.cross_repository import CrossRepository
from warriorfit.data.repositories.fitness_test_repository import FitnessTestRepository
from warriorfit.data.repositories.march_repository import MarchRepository
from warriorfit.data.repositories.mom_repository import MomRepository
from warriorfit.data.repositories.reservation_repository import ReservationRepository
from warriorfit.data.repositories.servicemen_repository import ServicemenRepository
from warriorfit.data.repositories.user_repository import UserRepository
from warriorfit.mom.broker import Broker
from warriorfit.services.be_mil_service import BEMILService
from warriorfit.services.data_collector import DataCollector
from warriorfit.services.mail_service import MailService
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.report_generator_csv import ReportGeneratorCsv
from warriorfit.services.report_generator_pdf import ReportGeneratorPdf
from warriorfit.services.reserve_fitness_room_service import ReserveFitnessRoomService
from warriorfit.services.service_consent import ConsentService
from warriorfit.services.service_cross import ServiceCross
from warriorfit.services.service_gdpr import GdprService
from warriorfit.services.service_march import ServiceMarch
from warriorfit.services.service_retention import RetentionService
from warriorfit.services.service_test import ServiceTest
from warriorfit.services.service_user import UserService
from warriorfit.ui.controllers.auditlog_events_controller import (
    AuditLogEventsController,
)
from warriorfit.ui.controllers.calendar_events_controller import (
    CalendarEventsController,
)
from warriorfit.ui.controllers.combat_controller import CombatController
from warriorfit.ui.controllers.cross_controller import CrossController
from warriorfit.ui.controllers.cross_planning_controller import CrossPlanningController
from warriorfit.ui.controllers.cross_statics_controller import CrossStaticsController
from warriorfit.ui.controllers.dashboard_own_unit_controller import (
    DashboardOwnUnitController,
)
from warriorfit.ui.controllers.functional_controller import FunctionalController
from warriorfit.ui.controllers.ind_test_show_controller import IndTestShowController
from warriorfit.ui.controllers.march_controller import MarchController
from warriorfit.ui.controllers.my_progress_controller import MyProgressController
from warriorfit.ui.controllers.own_unit_controller import OwnUnitController
from warriorfit.ui.controllers.phef_controller import PhefController
from warriorfit.ui.controllers.privacy_controller import PrivacyController
from warriorfit.ui.controllers.reports_controller import ReportsController
from warriorfit.ui.controllers.reserve_fitness_room_controller import (
    ReserveFitnessRoomController,
)
from warriorfit.ui.controllers.servicemen_overview_controller import (
    ServicemenOverviewController,
)
from warriorfit.ui.controllers.session_controller import SessionsController
from warriorfit.ui.controllers.setting_controller import SettingsController
from warriorfit.ui.controllers.status_log_user_controller import StatusLogUserController
from warriorfit.ui.controllers.status_tests_controller import StatusTestsController
from warriorfit.ui.controllers.status_application_controller import (
    StatusApplicationController,
)
from warriorfit.ui.controllers.swimming_controller import SwimmingController
from warriorfit.ui.controllers.usermanagement_controller import UserManagementController
from warriorfit.services.notify_mail import NotifyMail


class Container(containers.DeclarativeContainer):
    """
    Application-wide Dependency Injection Container.

    This container defines all application dependencies and their lifecycles.
    Repositories are singletons to maintain consistent database connections.
    Services are singletons to maintain state and share instances across the application.
    """

    wiring_config = containers.WiringConfiguration(
        modules=[
            # App server factory
            "warriorfit.ui.app_server",
            # Pages (use @inject + Provide[Container.xxx_controller])
            "warriorfit.ui.pages.phef",
            "warriorfit.ui.pages.cross",
            "warriorfit.ui.pages.march",
            "warriorfit.ui.pages.reserve_fitness_room",
            "warriorfit.ui.pages.usermanagement",
            "warriorfit.ui.pages.calendar_events",
            "warriorfit.ui.pages.cross_statics",
            "warriorfit.ui.pages.functional_test",
            "warriorfit.ui.pages.cross_planning",
            "warriorfit.ui.pages.auditlog_events",
            "warriorfit.ui.pages.status_login_user",
            "warriorfit.ui.pages.status_tests",
            "warriorfit.ui.pages.swim_test",
            "warriorfit.ui.pages.sessions",
            "warriorfit.ui.pages.combat_test",
            "warriorfit.ui.pages.dashboard_own_unit",
            "warriorfit.ui.pages.reports",
            "warriorfit.ui.pages.status_application",
            "warriorfit.ui.pages.about",
            "warriorfit.ui.pages.ind_test_show",
            "warriorfit.ui.pages.own_unit",
            "warriorfit.ui.pages.settings",
            "warriorfit.ui.pages.privacy",
            "warriorfit.ui.pages.my_progress",
            "warriorfit.ui.pages.servicemen_overview",
        ]
    )

    # Configuration
    config = providers.Singleton(ApplicationConfig)

    # Repositories (Singletons) - all repositories accept config via DI
    user_repository = providers.Singleton(
        UserRepository,
        config=config,
    )

    servicemen_repository = providers.Singleton(
        ServicemenRepository,
        config=config,
    )

    fitness_test_repository = providers.Singleton(
        FitnessTestRepository,
        config=config,
    )

    cross_repository = providers.Singleton(
        CrossRepository,
        config=config,
    )

    march_repository = providers.Singleton(
        MarchRepository,
        config=config,
    )

    reservation_repository = providers.Singleton(
        ReservationRepository,
        config=config,
    )

    mom_repository = providers.Singleton(
        MomRepository,
        config=config,
    )

    consent_repository = providers.Singleton(
        ConsentRepository,
        config=config,
    )

    # External Services
    be_mil_service = providers.Singleton(
        BEMILService,
        config=config,
    )

    military_service = providers.Singleton(
        MilitaryService,
        repo=servicemen_repository,
        be_mil_service=be_mil_service,
    )

    # Message Queue / Broker
    broker = providers.Singleton(
        Broker,
        mom_repository=mom_repository,
        be_mil_service=be_mil_service,
        config=config,
    )

    # Mail Service
    mail_service = providers.Singleton(
        MailService,
        config=config,
    )

    # Notify Mail
    notify_mail = providers.Singleton(
        NotifyMail,
        mail_service=mail_service,
        config=config,
    )

    # Application Services (with repository injection)
    user_service = providers.Singleton(
        UserService,
        user_repository=user_repository,
        config=config,
    )

    test_service = providers.Singleton(
        ServiceTest,
        fitness_test_repository=fitness_test_repository,
        user_repository=user_repository,
        config=config,
        notify_mail=notify_mail,
    )

    cross_service = providers.Singleton(
        ServiceCross,
        cross_repository=cross_repository,
        user_repository=user_repository,
        military_service=military_service,
        config=config,
    )

    march_service = providers.Singleton(
        ServiceMarch,
        march_repository=march_repository,
        user_repository=user_repository,
        military_service=military_service,
        config=config,
        notify_mail=notify_mail,
    )

    reserve_fitness_room_service = providers.Singleton(
        ReserveFitnessRoomService,
        reservation_repository=reservation_repository,
        servicemen_repository=servicemen_repository,
        user_repository=user_repository,
        config=config,
        notify_mail=notify_mail,
    )

    # GDPR services
    consent_service = providers.Singleton(
        ConsentService,
        consent_repository=consent_repository,
        user_repository=user_repository,
        config=config,
    )

    gdpr_service = providers.Singleton(
        GdprService,
        user_repository=user_repository,
        servicemen_repository=servicemen_repository,
        fitness_test_repository=fitness_test_repository,
        march_repository=march_repository,
        consent_repository=consent_repository,
        config=config,
    )

    retention_service = providers.Singleton(
        RetentionService,
        user_repository=user_repository,
        config=config,
    )

    # Data Collector
    data_collector = providers.Singleton(
        DataCollector,
        service_test=test_service,
        service_march=march_service,
        military_service=military_service,
        config=config,
    )

    # Report Generators
    report_generator_pdf = providers.Singleton(
        ReportGeneratorPdf,
        cross_service=cross_service,
        military_service=military_service,
        service_test=test_service,
        config=config,
    )

    report_generator_csv = providers.Singleton(
        ReportGeneratorCsv,
        military_service=military_service,
        service_test=test_service,
        config=config,
    )

    # Controllers
    phef_controller = providers.Singleton(
        PhefController, service=test_service, mil_service=military_service
    )
    cross_controller = providers.Singleton(
        CrossController,
        service=cross_service,
        mil_service=military_service,
        pdf_gen=report_generator_pdf,
    )
    march_controller = providers.Singleton(
        MarchController, service=march_service, mil_service=military_service
    )
    reserve_fitness_room_controller = providers.Singleton(
        ReserveFitnessRoomController, service=reserve_fitness_room_service
    )
    usermanagement_controller = providers.Singleton(
        UserManagementController,
        mil_service=military_service,
        user_service=user_service,
    )
    calendar_events_controller = providers.Singleton(
        CalendarEventsController, test_service=test_service, cross_service=cross_service
    )
    cross_statics_controller = providers.Singleton(
        CrossStaticsController, service=cross_service, mil_service=military_service
    )
    functional_controller = providers.Singleton(
        FunctionalController, service=test_service, mil_service=military_service
    )
    cross_planning_controller = providers.Singleton(
        CrossPlanningController, service=cross_service
    )
    auditlog_events_controller = providers.Singleton(
        AuditLogEventsController, user_service=user_service
    )
    status_log_user_controller = providers.Singleton(
        StatusLogUserController, service=test_service
    )
    status_tests_controller = providers.Singleton(
        StatusTestsController,
        mil_service=military_service,
        data_collector=data_collector,
        config=config,
    )
    swimming_controller = providers.Singleton(
        SwimmingController, service=test_service, mil_service=military_service
    )
    sessions_controller = providers.Singleton(
        SessionsController,
        service=test_service,
        mil_service=military_service,
        mail_service=mail_service,
        config=config,
    )
    combat_controller = providers.Singleton(
        CombatController, service=test_service, mil_service=military_service
    )
    dashboard_own_unit_controller = providers.Singleton(
        DashboardOwnUnitController,
        test_service=test_service,
        mil_service=military_service,
        march_service=march_service,
        config=config,
    )
    reports_controller = providers.Singleton(
        ReportsController, csv_gen=report_generator_csv, pdf_gen=report_generator_pdf
    )
    status_application_controller = providers.Singleton(
        StatusApplicationController, repo=user_repository, config=config
    )
    ind_test_show_controller = providers.Singleton(
        IndTestShowController,
        mil_service=military_service,
        data_collector=data_collector,
        report_generator_pdf=report_generator_pdf,
    )
    own_unit_controller = providers.Singleton(
        OwnUnitController,
        mil_service=military_service,
        data_collector=data_collector,
        test_service=test_service,
        march_service=march_service,
        config=config,
        report_generator_pdf=report_generator_pdf,
    )
    settings_controller = providers.Singleton(SettingsController, config=config)
    privacy_controller = providers.Singleton(
        PrivacyController,
        gdpr_service=gdpr_service,
        consent_service=consent_service,
    )
    my_progress_controller = providers.Singleton(
        MyProgressController,
        data_collector=data_collector,
    )
    servicemen_overview_controller = providers.Singleton(
        ServicemenOverviewController,
        servicemen_repository=servicemen_repository,
        consent_repository=consent_repository,
    )
