# Project Retrospectives - WarriorFit

---

## Phase 1 - Initiation & Project Charter (Nov 2025) ✅

### Completed
- Project scope and vision defined
- Backlog initialized
- Repository set up

### What Went Well ✅
- Define user stories and acceptance criteria
- Technogical chosens and tools selected
- scoped out project timeline

### What Didn't Go Well ❌
- javascript prototype vue.js :  overhead of learning
- use cases: switch to userstories, more agile, freedom of choice

### What I Learned 💡
- setup UI with shiny UI kit : mvc framework 
- sqlqchemy : ORM mapped object relational database
- docker deployment :  containerization

### Improvements for Next Phase 🎯
- take more time to understand the project scope
- take more think how to implement the userstorors

### Notes
ult

## Phase 2 - Architecture & Structure (Dec 2025) ✅
---

### Sprint 1 - [DEC 2025]

#### Completed This Sprint
- Set up database schema and models with comprehensive relationships
- Created ER diagrams and UML documentation
- Established repository pattern with SQLAlchemy ORM
- Implemented thread-safe singleton pattern for service layer
- Built initial page structure with role-based access control
- Added comprehensive docstrings across codebase

#### What Went Well ✅
- Clean separation of concerns (repository, service, controller, UI layers)
- Strong type hints and model relationships
- Documentation-first approach with detailed schema definitions
- Thread-safe singleton implementation for better concurrency

#### What Didn't Go Well ❌
- Some refactoring needed for async handling
- Initial database dialect configuration issues
- Multiple iterations needed on model relationships

#### What I Learned 💡
- SQLAlchemy relationship management and type annotations
- Thread-safe singleton patterns with `ABCMeta`
- Importance of comprehensive database schema documentation
- Role-based access control implementation in Shiny framework

#### Action Items for Next Sprint 🎯
- [x] Optimize async operations across controllers
- [x] Enhance DataFrame handling for UI components
- [x] Improve error handling and logging

#### Notes
- Version bumped to 0.5.0 marking completion of architecture phase
- Test database environment configured (`warriorfit_test`)


### Phase 2 Summary

#### Overall Achievements
- Technical foundation: Complete layered architecture (Repository → Service → Controller → UI)
- Database structure: Comprehensive schema with proper relationships and foreign keys
- UML diagrams: Entity-relationship diagrams and architecture documentation
- Working skeleton: Base application with authentication and role-based navigation

#### Key Learnings from Phase 2
- Proper async/await patterns in Python web applications
- SQLAlchemy's `Mapped` type annotations for better type safety
- Thread-safe design patterns for service layer
- Importance of test data and separate test environments

#### What to Carry Forward to Phase 3
- Continue comprehensive docstring practice
- Maintain strict type hints and annotations
- Keep test environment aligned with development changes
- Document architectural decisions as they're made

---

## Phase 3 - Development & Iterations (Jan 2026)

### Sprint 1 - Core Features [Early Jan 2026]

#### Completed This Sprint
- Implemented fitness test pages (PHEF, Swim, March tests)
- Built Cross statistics controller with async data collection
- Added DataGrid components with sorting and filtering
- Created dashboard for own unit view
- Implemented time parsing utilities for various formats
- Enhanced service cross relationship handling

#### What Went Well ✅
- Consistent DataFrame-based approach across all pages
- Improved UI/UX with DataGrid configurations
- Better async handling in controllers
- Time format parsing supports multiple formats (hh:mm:ss with milliseconds)

#### What Didn't Go Well ❌
- Multiple iterations needed for DataGrid rendering with None values
- Some runtime errors with missing attributes in service_cross
- Inconsistent datetime formatting in dropdowns

#### What I Learned 💡
- DataGrid best practices for null-safe rendering
- Reactive programming patterns in Shiny
- Importance of defensive programming (checking None values)
- Time format standardization challenges

#### Action Items for Next Sprint 🎯
- [x] Add status monitoring page
- [x] Implement broker messaging system
- [x] Enhance search functionality

#### Sprint Metrics
- Version: 0.5.0 → pre-alpha 1.0
- Major features: 5+ test types implemented
- UI pages: 10+ pages created

---

### Sprint 2 - Monitoring & Communication [Mid Jan 2026]

#### Completed This Sprint
- Added Status Application page with server monitoring
- Implemented Broker messaging system with SMTP integration
- Enhanced log monitoring with filtering (last 300 lines, info-level filtering)
- Added mail server health checks
- Integrated PTI selection in fitness room reservations
- Improved error handling for socket and runtime errors

#### What Went Well ✅
- Comprehensive status monitoring gives real-time system health
- Broker messaging provides reliable notification system
- Log filtering helps focus on relevant information
- SMTP authentication with logging fallback

#### What Didn't Go Well ❌
- Socket connection errors required explicit error handling
- Mail server configuration needed multiple iterations
- Log file reading initially only 100 lines (extended to 300)

#### What I Learned 💡
- System monitoring best practices
- SMTP authentication patterns
- Socket error handling (`gaierror`, `RuntimeError`)
- Log file parsing and filtering techniques

#### Action Items for Next Sprint 🎯
- [x] Complete alpha testing
- [x] Add search functionality
- [x] Refactor refresh logic

#### Sprint Metrics
- Version: pre-alpha 1.0 → alpha 1.0 RC
- New features: Status monitoring, Broker messaging
- Bug fixes: 5+ error handling improvements

---

### Sprint 3 - Testing & Bug Fixes [Late Jan 2026]

#### Completed This Sprint
- Completed all test cases in test plan
- Added searchable serial number modal across test pages
- Implemented unique march validation
- Fixed refresh logic bugs (refresh_tick updates)
- Refactored Page base class with centralized refresh_tick
- Enhanced username validation with regex and length checks
- Fixed PHEF scoring logic with combined score thresholds

#### What Went Well ✅
- Systematic bug fixing across multiple components
- Consistent search modal implementation
- Better validation at repository and service layers
- Centralized refresh logic in base Page class

#### What Didn't Go Well ❌
- Refresh bugs affected multiple pages (required widespread fixes)
- Initial validation was too permissive
- PHEF scoring needed refactoring for accuracy

#### What I Learned 💡
- Importance of centralized base class logic
- Multi-layer validation (repository, service, controller)
- Testing reveals edge cases not caught in development
- Refresh state management in reactive frameworks

#### Action Items for Next Sprint 🎯
- [x] Deploy and document deployment process
- [x] Add final documentation
- [x] Prepare for RC release

#### Sprint Metrics
- Version: alpha 1.0 RC → 1.1 RC
- Test cases completed: All test cases marked complete
- Bug fixes: 10+ refresh, validation, and logic fixes

---

### Sprint 4 - Deployment & Documentation [Latest Jan 2026]

#### Completed This Sprint
- Revamped deployment script with detailed logging and error handling
- Updated installation documentation
- Enhanced README with test URLs and Git repository links
- Added screenshots to cross app documentation
- Improved UI consistency (placeholders, button labels, widths)
- Centralized JavaScript handlers in Page base class
- Fixed multiple data bugs (march sorting, serial number handling)

#### What Went Well ✅
- Deployment script much more robust with conditional container management
- Comprehensive documentation updates
- UI polish improved user experience
- Centralized patterns reduce code duplication

#### What Didn't Go Well ❌
- Minor typos in documentation needed fixes
- Some data sorting issues discovered late
- Missing serial_number cases required defensive coding

#### What I Learned 💡
- Deployment automation and error handling best practices
- Documentation is critical for handoff/demo
- UI consistency matters for professional appearance
- Always check for None/missing data in production logic

#### Action Items for Next Sprint 🎯
- [x] Final UI enhancements
- [x] Complete documentation review
- [x] Prepare demo materials

#### Sprint Metrics
- Version: 1.1 RC (current)
- Documentation: Multiple comprehensive docs added
- Deployment: Fully automated with error handling 

---

## Phase 4 - Testing & Validation (Jan 2026) ✅

### Testing Sprint - Alpha Testing [Jan 2026]

#### Testing Completed
- Comprehensive test plan with all test cases marked complete
- Integration testing across all fitness test types
- User interface testing on all pages
- Database relationship validation
- Error handling verification (None checks, missing data)
- Notification system testing (email, Broker)

#### Bugs Found & Fixed
- **Refresh Logic**: Multiple pages had inconsistent refresh_tick handling
- **Data Validation**: March uniqueness not enforced across layers
- **Scoring Logic**: PHEF combined score thresholds needed refactoring
- **UI Issues**: DataGrid rendering with None values caused errors
- **Search Functionality**: Serial number search needed enhancement
- **Sorting**: March data required sorting by service_number
- **Error Handling**: ServiceMen None checks to prevent runtime errors
- **Username Validation**: Regex and length validation too permissive

#### What Went Well ✅
- Systematic bug tracking through GitHub issues and PRs
- Quick iteration cycle for fixes
- Comprehensive test coverage revealed edge cases
- Defensive programming practices caught production issues early

#### What Didn't Go Well ❌
- Some architectural issues (refresh logic) required widespread refactoring
- Testing phase revealed bugs that should have been caught earlier
- Multiple iterations needed for validation logic

#### What I Learned 💡
- Importance of early and continuous testing
- Centralized patterns prevent widespread bugs
- Edge case testing is critical (empty lists, None values, missing attributes)
- User testing reveals UX issues not apparent to developers

---

## Phase 5 - Polish & Current State (Jan 2026) 🚀

### Current Release: 1.1 RC

#### Delivered Features
- **Core Fitness Tests**: PHEF, Swim, March, Cross statistics
- **Session Management**: Create, view, manage test sessions
- **Reservation System**: Fitness room reservations with PTI selection
- **User Management**: Authentication, role-based access, user CRUD
- **Dashboard**: Unit-specific dashboards with real-time data
- **Status Monitoring**: Application health monitoring with log viewing
- **Notification System**: Email notifications via Broker/SMTP
- **Search Functionality**: Serial number search with modal interface
- **Reports**: Test result reporting across all fitness types

#### Demo Materials
- README with comprehensive project documentation
- Screenshots in crossapp.md documentation
- Video demo link added to documentation
- Installation guide with deploy.sh automation
- Test URLs for mailserver and HR simulator

#### Current Status & Next Steps
- Version: 1.1 RC (Release Candidate)
- Status: Feature complete, polish phase
- Recent focus: UI consistency, documentation, deployment automation
- Outstanding: Final demo preparation, potential production deployment

---

## Project-Wide Retrospective (Current - Jan 2026)

### Overall Success Factors
- **Clean Architecture**: Layered design (Repository → Service → Controller → UI) made code maintainable
- **Type Safety**: Comprehensive type hints caught errors early
- **Documentation**: Docstrings and external docs improved clarity
- **Incremental Development**: Sprint-based approach allowed steady progress
- **Version Control**: Git workflow with feature branches and PRs kept changes organized

### Major Challenges Overcome
- **Async Programming**: Mastered async/await patterns in Python web framework
- **Database Relationships**: Complex foreign key relationships with SQLAlchemy
- **Reactive UI**: Learning Shiny's reactive programming model
- **Data Handling**: DataFrame-based UI with null-safe rendering
- **Error Resilience**: Comprehensive error handling across all layers
- **Deployment Automation**: Robust deployment with container management

### Technical Debt Created
- Some code duplication in test pages (could be further abstracted)
- Async handling could be more consistent across controllers
- Test coverage could be more comprehensive (unit tests vs integration tests)
- Some legacy code patterns remain from early development

### What I Would Do Differently Next Time
- Start with comprehensive test suite from day one (TDD approach)
- Design centralized patterns earlier (like base Page class)
- More prototyping of UI/UX before full implementation
- Earlier focus on deployment automation
- More frequent code reviews and refactoring sessions

### Skills Developed
- **Python Web Frameworks**: Shiny for Python, FastAPI patterns
- **SQLAlchemy ORM**: Advanced relationships, type annotations, async queries
- **Reactive Programming**: Understanding reactive patterns and state management
- **Docker & Deployment**: Container orchestration and automation
- **Database Design**: ER modeling, schema design, relationship management
- **Documentation**: Technical writing, architectural documentation
- **Git Workflow**: Feature branches, PRs, semantic versioning

### Favorite Wins 🎉
- Clean layered architecture that made changes easy
- Comprehensive status monitoring page showing real-time system health
- Smooth DataGrid UI with sorting and searching
- Automated deployment script saving hours of manual work
- All test cases completed and passing
- Professional documentation that tells the project story

### Project Metrics
- **Total duration**: ~3 months (Nov 2025 - Jan 2026)
- **Total sprints**: 6 sprints across 3 phases
- **Total features delivered**: 15+ major features
- **Current version**: 1.1 RC
- **Git commits**: 100+ commits
- **Pull requests**: 20+ PRs with code review
- **Test pages**: 10+ interactive pages
- **Documentation files**: 5+ comprehensive docs

