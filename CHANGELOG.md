# Changelog

All notable changes to PartDesignUpgrade are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.5.0] - 2026-10-18

### Changed

- The addon is no longer a workbench: it calls no `Gui.addWorkbench` and
  declares no `<workbench>` content in `package.xml`. A **workbench
  manipulator** contributes the commands to the *Part Design Helper Features*
  toolbar and to the **Part Design** menu of the stock Part Design workbench,
  so nothing is added to the workbench switcher.
- The assembly **Collision Detector** and its report dock are now part of this
  addon (they used to live in a separate companion addon).
- The standalone "AddOn Tools" toolbar was removed: every button is now in
  Part Design's own toolbar, so there are no duplicated buttons.

### Added

- `PartDesignUpgrade_Collision`: assembly collision detector (all bodies become
  transparent, interpenetrating parts are highlighted in red and the report is
  shown in a dock window; it re-runs automatically after every change).

## [0.4.0] - 2026-09-20

### Added

- First public release: **Create Pipe**, **Subtractive Pipe**, **Create Rib
  Between Faces**, **Assembly Cut**, **Automatic symmetry (Mirror)** and
  **Weight / Volume** helpers.
