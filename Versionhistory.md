# Version History

## [2.6.9] - 2025-11-7
### Added
- Git
- There are many other things
### Fixed
- fix output crash

## [2.3.0] - 2025-09-26
### Added
- Output_UI.py New upgraded new interface
### Fixed
- AttributeError: 'CompactOutputPanel' object has no attribute 'clear' on Output_UI.py
---
## [2.0.0] - 2025-09-20 
### Added
- New Cython integration for faster window deployment:
- quick_window_deployment_cython.c
- quick_window_deployment_cython.pyx 
- quick_window_deployment_cython.cp313-win_amd64.pyd
- setup_quick_window.py, build_cython.py, compile_direct.py
- New UI components:
- CustomTitleBar.py for customizable title bar
- Debugger.py for in-application debugging
- autcompleter.py, smart_autocomplete.py
- autocomplete_history.db (private autocomplete history database)
### Fixed
- Autocomplete not triggered
- Various additional issues
### Changed
- First version utilizing new “.C” language file type framework
---
## [1.8.8] - 2025-09-17 
### Fixed
- Empty activation due to typeScript_highlight.py missing
- Direct internal calls logic engine ( logicAI.lua , language_engine.cc → requires .dll )
- Dark_mode.py issues
### Changed
- Changed the name of:
- logicAI.lua → logicAI.py
- language_engine.cc  → language_engine.py
- run.bat
- dash → “advert” to modify toggle → “easier” for more straightforward activation
### Added
- Splash/loading screen
- Sun mode (Sun_mode.py)
- 15+ expanded language support (number estimated)
