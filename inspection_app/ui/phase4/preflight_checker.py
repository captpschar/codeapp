"""
Pre-export validation checker.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from typing import List, Tuple
from ...core.inspection_item import InspectionItem


class PreflightChecker(QWidget):
    """Check items before export."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._issues: List[Tuple[str, str]] = []  # (item_id, issue)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create checker UI."""
        layout = QVBoxLayout(self)

        # Header
        self._status_label = QLabel("Checking...")
        self._status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._status_label)

        # Issue list
        self._issue_list = QListWidget()
        layout.addWidget(self._issue_list)

        # Summary
        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet("color: #666;")
        layout.addWidget(self._summary_label)

    def check_items(self, items: List[InspectionItem]) -> bool:
        """
        Check items for issues.

        Returns True if all items pass.
        """
        self._issues.clear()
        self._issue_list.clear()

        for item in items:
            issues = self._check_item(item)
            for issue in issues:
                self._issues.append((item.id, issue))
                list_item = QListWidgetItem(f"⚠️ {item.user_location}: {issue}")
                self._issue_list.addItem(list_item)

        # Update status
        if self._issues:
            self._status_label.setText("❌ Issues Found")
            self._status_label.setStyleSheet("font-weight: bold; color: #F44336;")
            self._summary_label.setText(
                f"{len(self._issues)} issue(s) found. Fix before exporting."
            )
            return False
        else:
            self._status_label.setText("✅ Ready to Export")
            self._status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
            self._summary_label.setText(
                f"{len(items)} item(s) ready for export."
            )
            return True

    def _check_item(self, item: InspectionItem) -> List[str]:
        """Check single item for issues."""
        issues = []

        if not item.final_approval:
            issues.append("Not approved")

        if not item.photo_edited_path:
            issues.append("No edited photo")

        if not item.snapshot_path:
            issues.append("No code snapshot")

        if not item.llm_suggested_term:
            issues.append("No code reference")

        return issues

    def get_issues(self) -> List[Tuple[str, str]]:
        """Get list of issues."""
        return self._issues

    def has_issues(self) -> bool:
        """Check if there are any issues."""
        return len(self._issues) > 0

    def clear(self) -> None:
        """Clear checker state."""
        self._issues.clear()
        self._issue_list.clear()
        self._status_label.setText("Ready to check")
        self._status_label.setStyleSheet("font-weight: bold;")
        self._summary_label.setText("")
