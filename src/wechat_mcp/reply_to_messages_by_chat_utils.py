from __future__ import annotations

import time
from typing import Any

from ApplicationServices import (
    AXUIElementPerformAction,
    AXUIElementSetAttributeValue,
    kAXRaiseAction,
    kAXTextAreaRole,
    kAXValueAttribute,
)
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    CGEventSetFlags,
    kCGHIDEventTap,
)

from .logging_config import logger
from .wechat_accessibility import dfs, get_wechat_ax_app


def press_return() -> None:
    """
    Synthesize a Return key press.
    """
    keycode_return = 36
    event_down = CGEventCreateKeyboardEvent(None, keycode_return, True)
    CGEventSetFlags(event_down, 0)
    event_up = CGEventCreateKeyboardEvent(None, keycode_return, False)
    CGEventSetFlags(event_up, 0)
    CGEventPost(kCGHIDEventTap, event_down)
    CGEventPost(kCGHIDEventTap, event_up)


def find_input_field(ax_app: Any, retries: int = 5, delay: float = 0.5):
    """
    Locate the chat input text area in the current WeChat window.

    Retries several times with a delay to allow the AX tree to settle
    after WeChat is activated.
    """

    def is_input(el, role, title, identifier):
        if role != kAXTextAreaRole:
            return False
        # WeChat 4.0.6+: identifier may be None, match by excluding
        # the search field (title="Search").
        if identifier == "chat_input_field":
            return True
        if title and title != "Search":
            return True
        return False

    for attempt in range(retries):
        input_field = dfs(ax_app, is_input)
        if input_field is not None:
            return input_field
        logger.info(
            "Input field not found, retrying (%d/%d)...", attempt + 1, retries
        )
        time.sleep(delay)

    raise RuntimeError(
        "Could not find WeChat chat input field via Accessibility API"
    )


def send_message(text: str) -> None:
    """
    Send a message in the currently open chat by focusing the input
    field, setting its value, and pressing Return.
    """
    logger.info("Sending message of length %d characters", len(text))
    ax_app = get_wechat_ax_app()
    input_field = find_input_field(ax_app)

    AXUIElementPerformAction(input_field, kAXRaiseAction)

    err = AXUIElementSetAttributeValue(input_field, kAXValueAttribute, text)
    if err != 0:
        raise RuntimeError(f"Failed to set input text, AX error {err}")

    time.sleep(0.1)
    press_return()
    logger.info("Message sent")
