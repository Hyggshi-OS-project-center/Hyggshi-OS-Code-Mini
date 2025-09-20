# Version History

## [2.0.0] - 2025-09-20
### Added
- New Cython integration for faster window deployment:
  - `quick_window_deployment_cython.c`
  - `quick_window_deployment_cython.pyx`
  - `quick_window_deployment_cython.cp313-win_amd64.pyd`
  - `setup_quick_window.py`, `build_cython.py`, `compile_direct.py`
- New UI components:
  - `CustomTitleBar.py` for customizable title bar
  - `Debugger.py` for in-app debugging
- Autocomplete improvements:
  - `autcompleter.py`, `smart_autocomplete.py`
  - `autocomplete_history.db` (stores autocomplete history)

### Fixed
- Autocomplete not being activated
- General bug fixes

### Changed
- First version using new `.C` language file format

---

## [1.8.8] - 2025-09-17
### Fixed
- App not activating due to missing `typeScript_highlight.py`
- Logic engine call errors (`logicAI.lua` and `language_engine.cc` → required `.dll`)
- Dark mode issues (`Dark_mode.py`)

### Changed
- Renamed:
  - `logicAI.lua` → `logicAI.py`
  - `language_engine.cc` → `language_engine.py`
- Improved interface for a more professional look
- Updated `run.bat` for easier activation

### Added
- Splash/loading screen
- Sun mode (`Sun_mode.py`)
- Expanded language support (15+ languages, number approximate)
