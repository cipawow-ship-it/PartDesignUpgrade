# -*- coding: utf-8 -*-
"""Contribute the PartDesignUpgrade commands to the PartDesign workbench."""


class PartDesignUpgradeManipulator:
    """Append the PartDesignUpgrade buttons to the Part Design Helper Features toolbar."""

    def modifyToolBars(self):
        return [
            {"append": "PartDesignUpgrade_Pipe", "toolBar": "Part Design Helper Features"},
            {"append": "PartDesignUpgrade_SubtractPipe", "toolBar": "Part Design Helper Features"},
            {"append": "PartDesignUpgrade_FaceRib", "toolBar": "Part Design Helper Features"},
            {"append": "PartDesignUpgrade_Cut", "toolBar": "Part Design Helper Features"},
            {"append": "PartDesignUpgrade_Weight", "toolBar": "Part Design Helper Features"},
        ]